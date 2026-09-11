from datetime import datetime
from typing import Dict
from pymongo import ReturnDocument


def confirm_identity(db_adapter, sheet_id: str, student_id: str, actor_id: str) -> Dict:
    """Bind one scanned sheet to one roster student."""
    with db_adapter.unit_of_work() as s:
        sheet = db_adapter.db.sheets.find_one({"_id": sheet_id}, session=s)
        if not sheet:
            raise ValueError(f"Sheet {sheet_id} not found")
        if sheet.get("student_id"):
            raise ValueError(f"Sheet {sheet_id} already assigned to {sheet['student_id']}")
        if sheet.get("rejection_reasons"):
            raise ValueError(
                f"Sheet {sheet_id} was rejected ({sheet['rejection_reasons']}); "
                "replace the scan before assigning.")

        if not db_adapter.db.students.find_one({"_id": student_id}, session=s):
            raise ValueError(
                f"Student {student_id} is not on the roster. Identity matching "
                "must never create a student.")

        clash = db_adapter.db.sheets.find_one(
            {"exam_id": sheet["exam_id"], "student_id": student_id}, session=s)
        if clash:
            raise ValueError(
                f"Student {student_id} already has sheet {clash['_id']} for this exam.")

        updated = db_adapter.db.sheets.find_one_and_update(
            {"_id": sheet_id, "student_id": None},
            {"$set": {"student_id": student_id, "identity_method": "admin_manual",
                      "identity_confirmed_by": actor_id,
                      "identity_confirmed_at": datetime.utcnow(),
                      "state": "identified"}},
            session=s, return_document=ReturnDocument.AFTER)
        if not updated:
            raise ValueError("Sheet was just assigned by someone else. Reload.")

        db_adapter.db.audit_events.insert_one({
            "kind": "identity_confirmed", "sheet_id": sheet_id,
            "student_id": student_id, "actor": actor_id,
            "at": datetime.utcnow()}, session=s)

        _maybe_enqueue_grade(db_adapter, updated, s)

    return {"sheet_id": sheet_id, "student_id": student_id, "state": "identified"}


def _maybe_enqueue_grade(db_adapter, sheet, session) -> None:
    """Queue grading once identity is set AND every answer is finalized."""
    import uuid
    if not sheet.get("student_id"):
        return
    if any(not a.get("finalized") for a in sheet.get("answers", [])):
        return
    key = f"grade:{sheet['_id']}:{len(sheet['answers'])}"
    if db_adapter.db.jobs.find_one({"idempotency_key": key}, session=session):
        return
    db_adapter.db.jobs.insert_one({
        "_id": f"job_{uuid.uuid4().hex[:12]}", "kind": "grade_sheet",
        "entity_id": sheet["_id"], "batch_id": sheet.get("batch_id"),
        "status": "pending", "attempt_count": 0, "max_attempts": 5,
        "lease_owner": None, "lease_expires_at": None, "fencing_token": 0,
        "idempotency_key": key, "created_at": datetime.utcnow()}, session=session)
