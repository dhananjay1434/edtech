"""
cde/services/diagnosis.py — Phase 5 (Release B) wiring around the existing
cde/diagnostics.py engine, which is left completely untouched per the guide
("do not weaken it").

Diagnoses every WRONG answer on a published sheet using the student's
uploaded rough-work photo (the simpler `rough_sheet_path` input path the
engine already supports — this pipeline does not implement the more
elaborate per-question verified-crop manifest system diagnose() also
supports, which is a separate, unbuilt feature).

Publication rule (from the guide): identity resolved AND layout valid AND
every answer finalized AND grade committed AND every wrong answer either
supported or explicitly abstained. The first four are already guaranteed by
the time a sheet reaches state="published" (see cde/services/grading.py);
this module is what satisfies the fifth.
"""
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List

from cde import diagnostics as diag_engine
from cde.services.exams import subject_for_question
from cde.storage import _download_bytes


def _local_abstain(reason: str) -> dict:
    """Build an abstention using diagnostics.py's own public Diagnostic
    model and contract — never a hand-rolled shape that could drift from it."""
    result = diag_engine.Diagnostic(
        schema_version="1.0", status="abstained", error_class=None, confidence=0,
        summary="The available verified work does not support a reliable error classification.",
        next_step="Ask a teacher to review the work or obtain a clearer written solution.",
        abstention_reason=reason, evidence=[],
    )
    data = result.model_dump()
    return {"evidence": data.pop("evidence"), **data}


async def diagnose_sheet(db_adapter, sheet_id: str) -> Dict[str, Any]:
    sheet = db_adapter.db.sheets.find_one({"_id": sheet_id})
    if not sheet:
        raise ValueError(f"Sheet {sheet_id} not found")
    if sheet.get("state") != "published":
        raise ValueError(f"Sheet {sheet_id} is not published yet — cannot diagnose")

    exam = db_adapter.db.exams.find_one({"_id": sheet["exam_id"]})
    grade_rev = db_adapter.db.grade_revisions.find_one(
        {"sheet_id": sheet_id}, sort=[("revision", -1)])
    if not grade_rev:
        raise ValueError(f"No grade_revision found for sheet {sheet_id}")

    key_by_q = {e["question_number"]: e for e in exam.get("answer_key", [])}
    wrong_awards = [a for a in grade_rev["awards"] if a["state"] == "incorrect"]

    rough_status = sheet.get("rough_sheet_status")
    rough_path = sheet.get("rough_sheet_path")

    results: List[Dict[str, Any]] = []
    tmp_path = None
    try:
        if rough_path:
            data = _download_bytes(rough_path)
            fd, tmp_path = tempfile.mkstemp(suffix=".png")
            with os.fdopen(fd, "wb") as f:
                f.write(data)

        for award in wrong_awards:
            q_num = award["question_number"]
            key_entry = key_by_q.get(q_num, {})
            subject = subject_for_question(exam, q_num)

            if not key_entry.get("question_text"):
                diagnostic_result = {"diagnostic": _local_abstain("missing_question_context"),
                                     "provider": None}
            elif not rough_path:
                reason = ("no_rough_work_provided" if rough_status == "none_provided"
                         else "missing_or_unmapped_work")
                diagnostic_result = {"diagnostic": _local_abstain(reason), "provider": None}
            else:
                context = {"question_number": q_num, "question_text": key_entry["question_text"],
                          "correct_option": key_entry.get("correct_option")}
                if key_entry.get("options"):
                    context["options"] = key_entry["options"]
                if subject:
                    context["domain"] = subject
                schema = diag_engine.Diagnostic.model_json_schema()
                diagnostic_result = await diag_engine.diagnose(
                    context=context, crops=[], prompt="", schema=schema,
                    rough_sheet_path=tmp_path,
                )

            doc = {
                "_id": f"diag:{sheet_id}:q{q_num}:r{grade_rev['revision']}",
                "sheet_id": sheet_id, "exam_id": sheet["exam_id"],
                "student_id": sheet["student_id"], "question_number": q_num,
                "grade_revision": grade_rev["revision"], "subject": subject,
                **diagnostic_result, "created_at": datetime.utcnow(),
            }
            with db_adapter.unit_of_work() as s:
                db_adapter.db.diagnostics.replace_one(
                    {"_id": doc["_id"]}, doc, upsert=True, session=s)
            results.append(doc)
    finally:
        if tmp_path:
            os.remove(tmp_path)

    with db_adapter.unit_of_work() as s:
        db_adapter.db.sheets.update_one(
            {"_id": sheet_id},
            {"$set": {"diagnostics_ready": True, "diagnostics_count": len(results)}},
            session=s)

    return {"sheet_id": sheet_id, "diagnosed_count": len(results)}
