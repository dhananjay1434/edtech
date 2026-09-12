import logging
from datetime import datetime
from typing import Dict

from cde.db import DatabaseAdapter
from cde.services.batches import render_page
from cde.storage import upload
from cde.omr_engine import process_omr_sheet
from cde.jobs.queue import complete_job

logger = logging.getLogger(__name__)


async def handle_read_sheet(db_adapter: DatabaseAdapter, job: Dict, owner: str) -> None:
    """Render one page, read its bubbles, store the answers, open review tasks."""
    sheet_id = job["entity_id"]
    sheet = db_adapter.db.sheets.find_one({"_id": sheet_id})
    if not sheet:
        raise ValueError(f"Sheet {sheet_id} not found")
    if sheet["state"] not in ("pending_read",):
        logger.info("sheet %s already read (state=%s); skipping", sheet_id, sheet["state"])
        complete_job(db_adapter.db, job["_id"], owner, job["fencing_token"])
        return

    batch = db_adapter.db.batches.find_one({"_id": sheet["batch_id"]})
    exam = db_adapter.db.exams.find_one({"_id": sheet["exam_id"]})

    from cde.storage import _download_bytes          # see note below
    pdf_bytes = _download_bytes(batch["original_pdf_key"])
    image_bytes = render_page(pdf_bytes, sheet["page_number"])

    image_key = upload(sheet_id, image_bytes, content_type="image/png")
    result = await process_omr_sheet(image_bytes, _key_map(exam))

    if result.layout_rejections:
        with db_adapter.unit_of_work() as s:
            db_adapter.db.sheets.update_one(
                {"_id": sheet_id},
                {"$set": {"state": "rejected_layout",
                          "rejection_reasons": result.layout_rejections,
                          "image_key": image_key,
                          "updated_at": datetime.utcnow()}}, session=s)
            complete_job(db_adapter.db, job["_id"], owner, job["fencing_token"], session=s)
        return

    from cde.services.grading import build_answer_docs, scope_answers_to_exam, \
        find_stray_marks_outside_exam, integer_question_numbers
    qc = exam["question_count"]
    scoped = scope_answers_to_exam(result.questions, qc)
    int_qs = integer_question_numbers(exam)
    answers = build_answer_docs(scoped, int_qs)
    stray = find_stray_marks_outside_exam(result.questions, qc)

    review_tasks = _build_review_tasks(sheet, image_bytes, scoped, int_qs)

    with db_adapter.unit_of_work() as s:
        db_adapter.db.sheets.update_one(
            {"_id": sheet_id},
            {"$set": {"state": "pending_identity",
                      "answers": answers,
                      "image_key": image_key,
                      "stray_marks_outside_exam": stray,
                      "omr_version": result.version,
                      "image_sha256": result.sha256,
                      "updated_at": datetime.utcnow()}}, session=s)
        if review_tasks:
            db_adapter.db.review_tasks.insert_many(review_tasks, session=s)
        complete_job(db_adapter.db, job["_id"], owner, job["fencing_token"], session=s)


async def handle_grade_sheet(db_adapter, job, owner):
    from cde.services.grading import grade_and_publish
    from cde.jobs.queue import complete_job
    sheet = db_adapter.db.sheets.find_one({"_id": job["entity_id"]})
    if sheet and sheet.get("state") == "published":
        complete_job(db_adapter.db, job["_id"], owner, job["fencing_token"])
        return
    grade_and_publish(db_adapter, job["entity_id"])
    _maybe_enqueue_diagnosis(db_adapter, job["entity_id"])
    complete_job(db_adapter.db, job["_id"], owner, job["fencing_token"])


def _maybe_enqueue_diagnosis(db_adapter, sheet_id: str, session=None) -> None:
    """Release B: queue AI diagnosis once a sheet is published. Safe to call
    even if rough work hasn't been uploaded yet — diagnose_sheet abstains
    per-question rather than failing when a rough sheet is missing. The
    idempotency key includes the rough-sheet upload count so a student
    uploading work *after* publication re-triggers diagnosis exactly once
    per upload, without ever double-queuing for the same upload."""
    import uuid
    from datetime import datetime
    sheet = db_adapter.db.sheets.find_one({"_id": sheet_id}, session=session)
    if not sheet or sheet.get("state") != "published":
        return
    key = f"diagnose:{sheet_id}:{sheet.get('grade_revision', 0)}:{sheet.get('rough_sheet_upload_count', 0)}"
    if db_adapter.db.jobs.find_one({"idempotency_key": key}, session=session):
        return
    db_adapter.db.jobs.insert_one({
        "_id": f"job_{uuid.uuid4().hex[:12]}", "kind": "diagnose_sheet",
        "entity_id": sheet_id, "batch_id": sheet.get("batch_id"),
        "status": "pending", "attempt_count": 0, "max_attempts": 5,
        "lease_owner": None, "lease_expires_at": None, "fencing_token": 0,
        "idempotency_key": key, "created_at": datetime.utcnow()}, session=session)


async def handle_diagnose_sheet(db_adapter, job, owner):
    from cde.services.diagnosis import diagnose_sheet
    from cde.jobs.queue import complete_job
    await diagnose_sheet(db_adapter, job["entity_id"])
    complete_job(db_adapter.db, job["_id"], owner, job["fencing_token"])


def _key_map(exam) -> dict:
    """MCQ questions only — integer questions have no correct_option and
    are never read by the OMR engine (see AnswerKeyEntry)."""
    return {int(e["question_number"]): e["correct_option"] for e in exam["answer_key"]
           if e.get("question_type", "mcq") == "mcq"}


def _build_review_tasks(sheet, image_bytes, scoped_questions, integer_questions=frozenset()):
    """One review task per uncertain bubble, plus one per Section-B integer
    question (always manual — never read from the image), matching the
    existing review_tasks schema."""
    import uuid
    from cde.routes.beta import _crop_bytes
    from cde.storage import upload_named
    tasks = []
    for q in scoped_questions:
        if q.question_number in integer_questions:
            tasks.append({
                "_id": str(uuid.uuid4()),
                "submission_id": sheet["_id"], "exam_id": sheet["exam_id"],
                "question_number": q.question_number, "kind": "integer_manual",
                "crop_id": None, "choices": [],
                "suggested_code": None,
                "reason": "Section B numerical answer — enter the value shown on the sheet",
                "revision": 1, "resolved": False, "claimed_by": None,
                "lease_expires_at": None, "created_at": datetime.utcnow()})
            continue
        if not q.needs_review:
            continue
        crop_id = upload_named(f"{sheet['_id']}-q{q.question_number}.png",
                               _crop_bytes(image_bytes, q.crop_box),
                               content_type="image/png")
        tasks.append({
            "_id": str(uuid.uuid4()),
            "submission_id": sheet["_id"], "exam_id": sheet["exam_id"],
            "question_number": q.question_number, "kind": "ambiguous",
            "crop_id": crop_id,
            "choices": [{"code": c, "label": f"Option {c}"} for c in "ABCD"] + [
                {"code": "BLANK", "label": "No bubble filled — blank, scores 0"},
                {"code": "MULTIPLE", "label": "More than one bubble filled — scores −1"},
            ],
            "suggested_code": q.selected_option, "reason": q.reason,
            "revision": 1, "resolved": False, "claimed_by": None,
            "lease_expires_at": None, "created_at": datetime.utcnow()})
    return tasks
