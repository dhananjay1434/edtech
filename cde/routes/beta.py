"""
beta.py — Beta-tier FastAPI routes.

Rough-sheet diagnostics layer (Gemini cognitive-diagnostic pipeline) plus
support routes for the real OMR bubble-sheet ingestion pipeline (the pipeline
itself runs via the durable job worker in cde.jobs.handlers, not an HTTP
upload route):

  - HITL review-task queue for ambiguous bubbles, backed by the
    `review_tasks` MongoDB collection (no mock state).
  - Rough-sheet ingestion + Gemini diagnostics (unchanged).
  - Production MongoDB aggregation for /insights.

No AWS S3 / Cloudflare R2 / local disk storage is used anywhere in this
module — everything goes through MongoDB GridFS (`cde.storage`). No
Temporal — background work uses FastAPI `BackgroundTasks`.
"""

from __future__ import annotations

import io
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from bson.errors import InvalidId
from bson.objectid import ObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image
from pydantic import BaseModel

from cde.db import get_db, get_db_adapter, DatabaseAdapter
from cde.auth import AuthorizationPort, get_auth_port
from cde.services.accounts import resolve_student_id
from cde.storage import upload as _upload_to_storage, upload_named as _upload_named, presign as _get_download_url
from cde.omr_engine import QuestionResult

logger = logging.getLogger(__name__)
beta_router = APIRouter()


def _verified_claims(authorization: str = Header(...),
                      auth_port: AuthorizationPort = Depends(get_auth_port)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    try:
        return auth_port.validate_token(authorization[7:])
    except Exception:
        raise HTTPException(401, "Invalid token")


def _require_admin_claims(claims: dict = Depends(_verified_claims)) -> dict:
    if "admin" not in claims.get("realm_access", {}).get("roles", []):
        raise HTTPException(403, "Admin role required")
    return claims


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------

class ClaimRequest(BaseModel):
    claimant: str
    lease_seconds: int = 120


class ResolveTaskRequest(BaseModel):
    """Matches web/src/api/contracts.ts `ResolutionCommand`."""
    expectedRevision: str
    decisionCode: str
    reason: str
    idempotencyKey: str


class OverrideRequest(BaseModel):
    """Teacher manually supplies an error explanation for a failed AI run."""
    question_number: int
    error_type: str          # e.g. "Conceptual Deficit"
    explanation: str         # teacher's free-text explanation


# ---------------------------------------------------------------------------
# Deterministic OMR + HITL ambiguity routing (Cascade Steps 1-2)
# ---------------------------------------------------------------------------

def _exam_answer_key(exam: Optional[dict]) -> Dict[int, str]:
    if not exam:
        return {}
    return {
        int(row["question_number"]): str(row["correct_option"]).strip().upper()
        for row in exam.get("answer_key", [])
        if "question_number" in row and row.get("correct_option")
    }


def _crop_bytes(image_bytes: bytes, box: tuple) -> bytes:
    im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    x0, y0, x1, y1 = box
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(im.width, x1), min(im.height, y1)
    crop = im.crop((x0, y0, x1, y1))
    buf = io.BytesIO()
    crop.save(buf, format="PNG")
    return buf.getvalue()


def _question_answer_doc(q: QuestionResult) -> Dict[str, Any]:
    """Build the `answers[]` entry for one question from an OMR decision.

    Clear (non-ambiguous) detections are finalized immediately. Ambiguous /
    multiple / low-confidence detections are left unfinalized with no
    selected_option — they are only finalized once a human resolves the
    matching review task.
    """
    if q.needs_review:
        return {
            "question_number": q.question_number,
            "selected_option": None,
            "state": "ambiguous",
            "finalized": False,
            "omr_reason": q.reason,
            "omr_confidence": q.confidence,
        }
    state = "blank" if q.selected_option is None else (
        "correct" if q.is_correct else "incorrect"
    )
    return {
        "question_number": q.question_number,
        "selected_option": q.selected_option,
        "state": state,
        "finalized": True,
        "omr_reason": q.reason,
        "omr_confidence": q.confidence,
    }


@beta_router.get("/api/submissions/{submission_id}")
async def get_submission(submission_id: str, db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    sub = db_adapter.db.submissions.find_one({"_id": submission_id})
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")
    return {
        "submission_id": submission_id,
        "state": sub.get("state", "Processing"),
        "score": sub.get("score"),
        "max_score": sub.get("max_score"),
        "created_at": (sub.get("created_at") or datetime.utcnow()).isoformat(),
    }


# ---------------------------------------------------------------------------
# HITL review-task queue (matches web/src/api/contracts.ts `ReviewTask`)
# ---------------------------------------------------------------------------

def _review_task_out(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "cropId": doc["crop_id"],
        "revision": str(doc.get("revision", 1)),
        "kind": doc.get("kind", "ambiguous"),
        "choices": doc.get("choices", []),
        "suggestedCode": doc.get("suggested_code"),
    }


@beta_router.get("/api/review-tasks")
async def get_global_review_tasks(db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    docs = list(
        db_adapter.db.review_tasks
        .find({"resolved": False})
        .sort("created_at", 1)
        .limit(50)
    )
    return [_review_task_out(d) for d in docs]


@beta_router.post("/api/review-tasks/{task_id}/claim")
async def claim_task(task_id: str, req: ClaimRequest, db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    from datetime import timedelta
    lease_expires = datetime.utcnow() + timedelta(seconds=req.lease_seconds)
    result = db_adapter.db.review_tasks.update_one(
        {"_id": task_id, "resolved": False},
        {"$set": {"claimed_by": req.claimant, "lease_expires_at": lease_expires}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found or already resolved.")
    return {"status": "claimed", "task_id": task_id}


@beta_router.post("/api/review-tasks/{task_id}/renew")
async def renew_task(task_id: str, req: ClaimRequest, db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    from datetime import timedelta
    lease_expires = datetime.utcnow() + timedelta(seconds=req.lease_seconds)
    result = db_adapter.db.review_tasks.update_one(
        {"_id": task_id, "claimed_by": req.claimant, "resolved": False},
        {"$set": {"lease_expires_at": lease_expires}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not claimed by this claimant, or already resolved.")
    return {"status": "renewed", "task_id": task_id}


@beta_router.post("/api/review-tasks/{task_id}/resolve")
async def resolve_task(
    task_id: str,
    req: ResolveTaskRequest,
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
):
    task = db_adapter.db.review_tasks.find_one({"_id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    if task.get("resolved"):
        raise HTTPException(status_code=409, detail="Task already resolved.")
    if str(task.get("revision", 1)) != req.expectedRevision:
        raise HTTPException(status_code=409, detail="Task revision changed — refresh and retry.")

    valid_codes = {c["code"] for c in task.get("choices", [])}
    if req.decisionCode not in valid_codes:
        raise HTTPException(status_code=422, detail="decisionCode is not one of this task's choices.")

    submission_id = task["submission_id"]
    exam_id = task["exam_id"]
    q_num = task["question_number"]

    exam = db_adapter.db.exams.find_one({"_id": exam_id})
    correct_option = _exam_answer_key(exam).get(q_num)
    final_state = "correct" if req.decisionCode == correct_option else "incorrect"

    db_adapter.db.review_tasks.update_one(
        {"_id": task_id},
        {"$set": {
            "resolved": True,
            "decision": req.decisionCode,
            "resolution_reason": req.reason,
            "idempotency_key": req.idempotencyKey,
            "resolved_at": datetime.utcnow(),
        }},
    )
    db_adapter.db.submissions.update_one(
        {"_id": submission_id, "answers.question_number": q_num},
        {"$set": {
            "answers.$.selected_option": req.decisionCode,
            "answers.$.state": final_state,
            "answers.$.finalized": True,
            "answers.$.resolved_by": "human_review",
            "answers.$.resolution_reason": req.reason,
        }},
    )

    # If nothing else is pending review for this submission, it's ready to
    # be finalized as graded; otherwise it stays in the admin queue.
    still_open = db_adapter.db.review_tasks.count_documents({
        "submission_id": submission_id, "resolved": False,
    })
    if still_open == 0:
        correct_count = next(db_adapter.db.submissions.aggregate([
            {"$match": {"_id": submission_id}},
            {"$unwind": "$answers"},
            {"$match": {"answers.state": "correct"}},
            {"$count": "n"},
        ]), {}).get("n", 0)
        db_adapter.db.submissions.update_one(
            {"_id": submission_id},
            {"$set": {"state": "Graded (Draft)", "score": correct_count, "updated_at": datetime.utcnow()}},
        )

    # The durable Phase-1 pipeline (cde.services.batches / .identity) stores
    # its records in `sheets`, not `submissions`, but review tasks it opens
    # reuse this same schema with `submission_id` holding the sheet id.
    # Finalize the answer there too, and queue grading once everything is
    # resolved.
    from pymongo import ReturnDocument
    from cde.services.identity import _maybe_enqueue_grade
    sheet = db_adapter.db.sheets.find_one({"_id": submission_id})
    if sheet:
        with db_adapter.unit_of_work() as sess:
            updated_sheet = db_adapter.db.sheets.find_one_and_update(
                {"_id": submission_id, "answers.question_number": q_num},
                {"$set": {
                    "answers.$.selected_option": req.decisionCode,
                    "answers.$.state": final_state,
                    "answers.$.finalized": True,
                    "answers.$.resolved_by": "human_review",
                    "answers.$.resolution_reason": req.reason,
                }},
                session=sess, return_document=ReturnDocument.AFTER,
            )
            if updated_sheet is not None:
                _maybe_enqueue_grade(db_adapter, updated_sheet, sess)

    return {"status": "resolved", "task_id": task_id}


@beta_router.get("/api/evidence/{crop_id}")
async def get_evidence(crop_id: str, db_adapter: DatabaseAdapter = Depends(get_db_adapter),
                        claims: dict = Depends(_require_admin_claims)):
    """Serve a cropped bubble/rough-sheet evidence image straight from GridFS.

    Admin-only: these crops back the HITL ambiguous-bubble review queue,
    which only admin/operator staff use — students never see them.
    """
    import gridfs

    fs = gridfs.GridFS(db_adapter.db)
    try:
        oid = ObjectId(crop_id)
        grid_out = fs.get(oid)
        return Response(content=grid_out.read(), media_type=grid_out.content_type or "image/png")
    except (InvalidId, gridfs.errors.NoFile):
        raise HTTPException(status_code=404, detail="Evidence image not found.")


# ---------------------------------------------------------------------------
# Rough-sheet ingestion (Gemini cognitive diagnostics) — unchanged
# ---------------------------------------------------------------------------

async def _trigger_rough_sheet_workflow(submission_id: str) -> None:
    """
    Directly run the Gemini AI diagnostics in a FastAPI Background Task.
    Temporal has been removed for simplicity and zero-cost deployment.
    """
    try:
        from cde.activities import diagnose_rough_sheet_if_present
        # Call the logic directly
        await diagnose_rough_sheet_if_present({"submission_id": submission_id})
        logger.info("Background AI diagnostics completed for %s", submission_id)
    except Exception as exc:
        logger.exception(
            "AI diagnostics failed for %s — marking for HITL", submission_id
        )
        # The HITL queue will surface this to the admin dashboard
        from cde.db import get_db as _get_db
        _get_db().submissions.update_one(
            {"_id": submission_id},
            {"$set": {
                "rough_sheet_analysis_status": "failed",
                "rough_sheet_analysis_error": str(exc),
            }},
        )


@beta_router.post("/api/exams/{exam_id}/submissions/{submission_id}/rough-sheets")
async def upload_rough_sheet(
    exam_id: str,
    submission_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
):
    """
    Accept a student's rough-sheet image, persist it, update MongoDB, and
    enqueue an async diagnostic workflow.
    """
    # Basic content-type guard — accept PNG and JPEG only
    if file.content_type not in {"image/png", "image/jpeg", "image/jpg"}:
        raise HTTPException(
            status_code=415,
            detail="Only PNG and JPEG rough sheets are accepted.",
        )

    data = await file.read()
    if len(data) > 20 * 1024 * 1024:  # 20 MB hard cap
        raise HTTPException(status_code=413, detail="Rough sheet exceeds 20 MB limit.")

    storage_key = _upload_to_storage(submission_id, data)

    db_adapter.db.submissions.update_one(
        {"_id": submission_id, "exam_id": exam_id},
        {"$set": {
            "rough_sheet_path": storage_key,
            "rough_sheet_analysis_status": "queued",
            "rough_sheet_uploaded_at": datetime.utcnow(),
        }},
        upsert=False,
    )

    # Kick off the diagnostics activity in the background (non-blocking)
    background_tasks.add_task(_trigger_rough_sheet_workflow, submission_id)

    download_url = _get_download_url(storage_key)
    return {
        "status": "success",
        "rough_sheet_path": storage_key,
        "download_url": download_url,
        "analysis_status": "queued",
    }


# ---------------------------------------------------------------------------
# HITL Admin Fallback Dashboard endpoints (rough-sheet diagnostics)
# ---------------------------------------------------------------------------

@beta_router.get("/api/admin/diagnostics-queue")
async def get_diagnostics_queue(
    exam_id: Optional[str] = None,
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
):
    """
    Return all submissions whose rough-sheet AI diagnostics failed or are
    pending manual override. Optionally filtered by exam_id.
    """
    match: dict = {"rough_sheet_analysis_status": {"$in": ["failed", "partial"]}}
    if exam_id:
        match["exam_id"] = exam_id

    pipeline = [
        {"$match": match},
        {"$project": {
            "_id": 1,
            "exam_id": 1,
            "student_id": 1,
            "rough_sheet_path": 1,
            "rough_sheet_analysis_status": 1,
            "rough_sheet_analysis_error": 1,
            "rough_sheet_uploaded_at": 1,
            "answers": {
                "$filter": {
                    "input": "$answers",
                    "as": "a",
                    "cond": {"$eq": ["$$a.state", "incorrect"]},
                }
            },
        }},
        {"$sort": {"rough_sheet_uploaded_at": -1}},
        {"$limit": 100},
    ]

    items = list(db_adapter.db.submissions.aggregate(pipeline))
    for item in items:
        item["id"] = str(item.pop("_id"))
        key = item.get("rough_sheet_path", "")
        item["download_url"] = _get_download_url(key)

    return {"queue": items, "total": len(items)}


@beta_router.post("/api/submissions/{submission_id}/rough-sheets/retry")
async def retry_rough_sheet_diagnostics(
    submission_id: str,
    background_tasks: BackgroundTasks,
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
):
    """
    Re-enqueue a failed AI diagnostic run. Only valid if a rough sheet was
    already uploaded.
    """
    sub = db_adapter.db.submissions.find_one(
        {"_id": submission_id},
        {"rough_sheet_path": 1, "rough_sheet_analysis_status": 1},
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")
    if not sub.get("rough_sheet_path"):
        raise HTTPException(status_code=400, detail="No rough sheet uploaded for this submission.")

    db_adapter.db.submissions.update_one(
        {"_id": submission_id},
        {"$set": {
            "rough_sheet_analysis_status": "queued",
            "rough_sheet_analysis_error": None,
        }},
    )
    background_tasks.add_task(_trigger_rough_sheet_workflow, submission_id)

    return {"status": "retrying", "submission_id": submission_id}


@beta_router.post("/api/submissions/{submission_id}/rough-sheets/override")
async def override_rough_sheet_diagnostics(
    submission_id: str,
    req: OverrideRequest,
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
):
    """
    Teacher manually supplies an error diagnosis when AI failed or abstained.
    Writes a synthetic diagnostic record into the answer so aggregations work.
    """
    sub = db_adapter.db.submissions.find_one(
        {"_id": submission_id, "answers.question_number": req.question_number},
        {"_id": 1},
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Submission or question not found.")

    manual_diagnostic = {
        "status": "classified",
        "error_class": req.error_type,
        "summary": req.explanation,
        "confidence": 1.0,
        "source": "human_override",
        "overridden_at": datetime.utcnow().isoformat(),
    }

    db_adapter.db.submissions.update_one(
        {"_id": submission_id, "answers.question_number": req.question_number},
        {"$set": {
            "answers.$.diagnostic": manual_diagnostic,
            "rough_sheet_analysis_status": "completed",
        }},
    )
    return {"status": "overridden", "submission_id": submission_id, "question_number": req.question_number}


# ---------------------------------------------------------------------------
# Production MongoDB aggregation for /insights
# ---------------------------------------------------------------------------

@beta_router.get("/api/exams/{exam_id}/insights")
async def get_class_insights(
    exam_id: str,
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
):
    """
    Aggregate AI-generated (and manually overridden) diagnostics across a
    class to surface common error patterns for the teacher dashboard.
    """
    pipeline = [
        {"$match": {"exam_id": exam_id}},
        {"$unwind": "$answers"},
        {
            "$match": {
                "answers.state": "incorrect",
                "answers.diagnostic": {"$exists": True},
                # Include both AI-classified and human-override records
                "answers.diagnostic.status": "classified",
            }
        },
        {
            "$group": {
                "_id": {
                    "question_number": "$answers.question_number",
                    "error_type": "$answers.diagnostic.error_class",
                },
                "count": {"$sum": 1},
                "explanations": {"$push": "$answers.diagnostic.summary"},
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": 50},
    ]

    try:
        results = list(db_adapter.db.submissions.aggregate(pipeline))
    except Exception as exc:
        logger.exception("Insights aggregation failed for exam %s: %s", exam_id, exc)
        raise HTTPException(status_code=500, detail="Aggregation failed.")

    formatted = [
        {
            "question_number": r["_id"]["question_number"],
            "error_type": r["_id"]["error_type"],
            "count": r["count"],
            "sample_explanation": r["explanations"][0] if r["explanations"] else "",
        }
        for r in results
    ]

    # If the DB has no data yet (e.g. local dev before any diagnostics run),
    # surface a clear empty state rather than falling back to mock data.
    return {"insights": formatted, "source": "live" if formatted else "empty"}


# ---------------------------------------------------------------------------
# Submission list (used by StudentExamView)
# ---------------------------------------------------------------------------

@beta_router.get("/api/exams/{exam_id}/submissions")
async def get_exam_submissions(
    exam_id: str,
    db_adapter: DatabaseAdapter = Depends(get_db_adapter),
):
    """Return submissions for the student exam view, read live from MongoDB."""
    docs = list(db_adapter.db.submissions.find(
        {"exam_id": exam_id},
        {"_id": 1, "state": 1, "rough_sheet_path": 1, "rough_sheet_analysis_status": 1,
         "score": 1, "max_score": 1},
    ))
    subs = [
        {
            "submission_id": str(d["_id"]),
            "exam_id": exam_id,
            "state": d.get("state", "Processing"),
            "score": d.get("score"),
            "max_score": d.get("max_score"),
            "rough_sheet_path": d.get("rough_sheet_path"),
            "download_url": _get_download_url(d.get("rough_sheet_path", "")),
            "analysis_status": d.get("rough_sheet_analysis_status", "not_uploaded"),
            "analysis_error": None,
        }
        for d in docs
    ]
    return {"submissions": subs}


# ---------------------------------------------------------------------------
# MongoDB GridFS Image Server (No-Credit-Card S3 Alternative)
# ---------------------------------------------------------------------------

@beta_router.get("/api/images/{file_id}")
async def get_image_from_gridfs(file_id: str, db_adapter: DatabaseAdapter = Depends(get_db_adapter),
                                 claims: dict = Depends(_verified_claims)):
    """
    Serve an image directly from MongoDB GridFS.
    Used by the frontend to render the rough sheets without needing AWS/Cloudflare.

    Access is restricted: admins may view any image; students may only view
    an image that belongs to one of their own sheets (checked by looking up
    the sheet doc that references this GridFS id, never by trusting the URL).
    """
    roles = claims.get("realm_access", {}).get("roles", [])
    if "admin" not in roles:
        if "student" not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        try:
            student_id = resolve_student_id(db_adapter, claims["iss"], claims["sub"])
        except PermissionError:
            raise HTTPException(status_code=403, detail="Account is not linked to a student")
        gridfs_key = f"gridfs:{file_id}"
        owns = db_adapter.db.sheets.find_one({
            "student_id": student_id,
            "$or": [{"image_key": gridfs_key}, {"rough_sheet_path": gridfs_key}],
        })
        if not owns:
            raise HTTPException(status_code=403, detail="Forbidden")

    import gridfs

    fs = gridfs.GridFS(db_adapter.db)
    try:
        oid = ObjectId(file_id)
        grid_out = fs.get(oid)
        return Response(content=grid_out.read(), media_type=grid_out.content_type)
    except (InvalidId, gridfs.errors.NoFile):
        raise HTTPException(status_code=404, detail="Image not found in database")
