"""
cde/routes/admin.py — HTTP surface for the admin-facing pipeline built in
Phase 1 (cde.services.rosters/.exams/.batches/.identity). The pre-existing
cde/routes/alpha.py exposes a *different*, stub-backed ExamsService/
UploadsService (see PROJECT_STATUS.md) — this module deliberately does not
touch that path, and instead wires the real, tested pipeline.
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Body
from pymongo import ReturnDocument

from cde.db import DatabaseAdapter, get_db_adapter
from cde.auth import AuthorizationPort, get_auth_port
from cde.services.rosters import RosterImport, import_roster
from cde.services.exams import ExamCreate, create_exam
from cde.services.batches import create_batch
from cde.services.identity import confirm_identity, _maybe_enqueue_grade
from cde.features import catalog_view
from cde.services.entitlements import read_enabled, set_enabled

admin_router = APIRouter(prefix="/api/admin")


def verified_admin_claims(authorization: str = Header(...),
                          auth_port: AuthorizationPort = Depends(get_auth_port)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    try:
        claims = auth_port.validate_token(authorization[7:])
    except Exception:
        raise HTTPException(401, "Invalid token")
    roles = claims.get("realm_access", {}).get("roles", [])
    if "admin" not in roles:
        raise HTTPException(403, "Admin role required")
    return claims


@admin_router.get("/features")
def get_features(claims: dict = Depends(verified_admin_claims),
                 db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    return {"features": catalog_view(read_enabled(db_adapter))}


@admin_router.put("/features")
def put_features(payload: dict = Body(...),
                 claims: dict = Depends(verified_admin_claims),
                 db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    toggles = payload.get("enabled", {})
    try:
        enabled = set_enabled(db_adapter, toggles, actor_id=claims["sub"])
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    return {"features": catalog_view(enabled)}


@admin_router.post("/rosters")
def create_roster(payload: RosterImport,
                  claims: dict = Depends(verified_admin_claims),
                  db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    try:
        return import_roster(db_adapter, payload, actor_id=claims["sub"])
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@admin_router.post("/exams")
def create_new_exam(payload: ExamCreate,
                    claims: dict = Depends(verified_admin_claims),
                    db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    try:
        return create_exam(db_adapter, payload, actor_id=claims["sub"])
    except ValueError as exc:
        status = 404 if "not found" in str(exc) else 422
        raise HTTPException(status, str(exc))


@admin_router.get("/exams")
def list_exams(claims: dict = Depends(verified_admin_claims),
               db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    exams = list(db_adapter.db.exams.find({}, {"_id": 1, "name": 1, "question_count": 1}))
    return {"exams": [{"id": e["_id"], "name": e.get("name"),
                       "question_count": e["question_count"]} for e in exams]}


@admin_router.get("/rosters")
def list_rosters(claims: dict = Depends(verified_admin_claims),
                 db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    rosters = list(db_adapter.db.rosters.find({}, {"_id": 1, "exam_class": 1}))
    counts = {r["_id"]: db_adapter.db.students.count_documents({"roster_id": r["_id"]})
             for r in rosters}
    return {"rosters": [{"id": r["_id"], "exam_class": r["exam_class"],
                         "student_count": counts[r["_id"]]} for r in rosters]}


@admin_router.get("/rosters/{roster_id}/students")
def list_students(roster_id: str,
                  claims: dict = Depends(verified_admin_claims),
                  db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    students = list(db_adapter.db.students.find(
        {"roster_id": roster_id}, {"_id": 1, "name": 1, "roll_number": 1}))
    return {"students": [{"id": s["_id"], "name": s["name"],
                          "roll_number": s["roll_number"]} for s in students]}


@admin_router.post("/exams/{exam_id}/batches")
async def upload_batch(exam_id: str, file: UploadFile = File(...),
                       expected_sheet_count: Optional[int] = None,
                       claims: dict = Depends(verified_admin_claims),
                       db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    data = await file.read()
    try:
        return create_batch(db_adapter, exam_id, data, actor_id=claims["sub"],
                            expected_sheet_count=expected_sheet_count)
    except ValueError as exc:
        status = 404 if "not found" in str(exc) else 422
        raise HTTPException(status, str(exc))


@admin_router.get("/exams/{exam_id}/batches/{batch_id}")
def batch_status(exam_id: str, batch_id: str,
                 claims: dict = Depends(verified_admin_claims),
                 db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    batch = db_adapter.db.batches.find_one({"_id": batch_id, "exam_id": exam_id})
    if not batch:
        raise HTTPException(404, "Batch not found")
    sheets = list(db_adapter.db.sheets.find(
        {"batch_id": batch_id}, {"_id": 1, "page_number": 1, "state": 1, "student_id": 1}))
    counts: dict = {}
    for s in sheets:
        counts[s["state"]] = counts.get(s["state"], 0) + 1
    return {
        "batch_id": batch_id,
        "page_count": batch["page_count"],
        "expected_sheet_count": batch.get("expected_sheet_count"),
        "count_matches_expected": batch.get("count_matches_expected"),
        "counts_by_state": counts,
        "sheets": [{"sheet_id": s["_id"], "page_number": s["page_number"],
                    "state": s["state"], "student_id": s.get("student_id")}
                   for s in sorted(sheets, key=lambda x: x["page_number"])],
    }


@admin_router.get("/exams/{exam_id}/sheets")
def list_sheets(exam_id: str, state: Optional[str] = None,
                claims: dict = Depends(verified_admin_claims),
                db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    query = {"exam_id": exam_id}
    if state:
        query["state"] = state
    sheets = list(db_adapter.db.sheets.find(
        query, {"_id": 1, "page_number": 1, "state": 1, "student_id": 1, "image_key": 1}
    ).sort("page_number", 1))
    return {"sheets": [{
        "sheet_id": s["_id"], "page_number": s["page_number"], "state": s["state"],
        "student_id": s.get("student_id"),
        "image_id": (s["image_key"].split("gridfs:", 1)[-1] if s.get("image_key") else None),
    } for s in sheets]}


@admin_router.get("/exams/{exam_id}/exceptions")
def list_exceptions(exam_id: str,
                    claims: dict = Depends(verified_admin_claims),
                    db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    rejected = list(db_adapter.db.sheets.find(
        {"exam_id": exam_id, "state": "rejected_layout"},
        {"_id": 1, "page_number": 1, "rejection_reasons": 1}))
    stray = list(db_adapter.db.sheets.find(
        {"exam_id": exam_id, "stray_marks_outside_exam": {"$exists": True, "$not": {"$size": 0}}},
        {"_id": 1, "page_number": 1, "stray_marks_outside_exam": 1}))
    batch_ids = [b["_id"] for b in db_adapter.db.batches.find({"exam_id": exam_id}, {"_id": 1})]
    failed_jobs = list(db_adapter.db.jobs.find(
        {"batch_id": {"$in": batch_ids}, "status": "failed"},
        {"_id": 1, "kind": 1, "entity_id": 1, "last_error": 1, "attempt_count": 1}))
    return {
        "rejected_layout": [{"sheet_id": s["_id"], "page_number": s["page_number"],
                             "reasons": s.get("rejection_reasons", [])} for s in rejected],
        "stray_marks": [{"sheet_id": s["_id"], "page_number": s["page_number"],
                         "questions": s.get("stray_marks_outside_exam", [])} for s in stray],
        "failed_jobs": [{"job_id": j["_id"], "kind": j["kind"], "entity_id": j["entity_id"],
                         "last_error": j.get("last_error"), "attempt_count": j["attempt_count"]}
                        for j in failed_jobs],
    }


@admin_router.get("/exams/{exam_id}/integer-queue")
def list_pending_integer_answers(exam_id: str,
                                 claims: dict = Depends(verified_admin_claims),
                                 db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    sheets = list(db_adapter.db.sheets.find(
        {"exam_id": exam_id, "answers.state": "pending_integer_entry"},
        {"_id": 1, "page_number": 1, "image_key": 1, "answers": 1}))
    items = []
    for s in sheets:
        pending = [a["question_number"] for a in s.get("answers", [])
                  if a.get("state") == "pending_integer_entry"]
        if not pending:
            continue
        items.append({
            "sheet_id": s["_id"], "page_number": s["page_number"],
            "image_id": (s["image_key"].split("gridfs:", 1)[-1] if s.get("image_key") else None),
            "pending_questions": sorted(pending),
        })
    return {"sheets": items}


@admin_router.post("/sheets/{sheet_id}/answers/{question_number}/integer")
def resolve_integer_answer(sheet_id: str, question_number: int,
                           value: int = Body(..., embed=True, ge=0, le=9999),
                           claims: dict = Depends(verified_admin_claims),
                           db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    """Record the value an admin read directly off the scanned sheet for a
    Section-B numerical question. Never inferred from the image by us."""
    with db_adapter.unit_of_work() as s:
        sheet = db_adapter.db.sheets.find_one({"_id": sheet_id}, session=s)
        if not sheet:
            raise HTTPException(404, "Sheet not found")
        updated = db_adapter.db.sheets.find_one_and_update(
            {"_id": sheet_id, "answers.question_number": question_number},
            {"$set": {
                "answers.$.selected_option": str(value),
                "answers.$.state": "answered",
                "answers.$.finalized": True,
                "answers.$.resolved_by": "admin_manual_integer_entry",
            }},
            session=s, return_document=ReturnDocument.AFTER)
        if updated is None:
            raise HTTPException(404, f"Question {question_number} not found on sheet {sheet_id}")
        db_adapter.db.review_tasks.update_many(
            {"submission_id": sheet_id, "question_number": question_number,
             "kind": "integer_manual", "resolved": False},
            {"$set": {"resolved": True, "decision": str(value),
                      "resolved_at": datetime.utcnow()}},
            session=s)
        _maybe_enqueue_grade(db_adapter, updated, s)
    return {"sheet_id": sheet_id, "question_number": question_number, "value": value}


@admin_router.post("/sheets/{sheet_id}/identity")
def confirm_sheet_identity(sheet_id: str, student_id: str = Body(..., embed=True),
                           claims: dict = Depends(verified_admin_claims),
                           db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    try:
        return confirm_identity(db_adapter, sheet_id, student_id, actor_id=claims["sub"])
    except ValueError as exc:
        raise HTTPException(409, str(exc))
