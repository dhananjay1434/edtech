"""Pure (DB-free) shaping of a student's rough-work diagnosis view.

Separated from the route so the three states — waiting for a result, still
processing, and ready — are each independently testable without Mongo.
Never includes evidence bboxes: no student-facing crop route exists, so
returning them would be a dead reference, not useful data.
"""
from typing import Any, Dict, List, Optional


def build_diagnosis_view(sheet: Optional[dict], docs: List[dict]) -> Dict[str, Any]:
    if not sheet or sheet.get("state") != "published":
        return {"status": "waiting_for_result"}

    if not sheet.get("diagnostics_ready"):
        return {"status": "processing", "rough_sheet_status": sheet.get("rough_sheet_status")}

    revision = sheet.get("grade_revision", 0)
    questions = []
    for doc in docs:
        if doc.get("grade_revision") != revision:
            continue
        diag = doc.get("diagnostic", {})
        questions.append({
            "question_number": doc["question_number"],
            "subject": doc.get("subject"),
            "status": diag.get("status"),
            "error_class": diag.get("error_class"),
            "confidence": diag.get("confidence"),
            "summary": diag.get("summary"),
            "next_step": diag.get("next_step"),
            "abstention_reason": diag.get("abstention_reason"),
            "reviewed": False,
        })
    questions.sort(key=lambda q: q["question_number"])

    return {
        "status": "ready",
        "rough_sheet_status": sheet.get("rough_sheet_status"),
        "grade_revision": revision,
        "questions": questions,
    }
