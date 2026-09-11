from datetime import datetime
from typing import Any, Dict, List, Set
from cde.grading_core import grade_submission


def integer_question_numbers(exam: Dict[str, Any]) -> Set[int]:
    """Question numbers marked question_type="integer" in the exam's answer
    key. The OMR engine has no calibration for a numeric-answer grid and
    never reads these — see AnswerKeyEntry in cde/services/exams.py."""
    return {e["question_number"] for e in exam.get("answer_key", [])
            if e.get("question_type") == "integer"}


def scope_answers_to_exam(omr_questions: List[Any], question_count: int) -> List[Any]:
    """Keep only the rows this exam uses. The sheet has 180; the exam has ~75."""
    scoped = [q for q in omr_questions if q.question_number <= question_count]
    if len(scoped) != question_count:
        raise ValueError(f"Expected {question_count} questions, got {len(scoped)}")
    return scoped


def find_stray_marks_outside_exam(omr_questions: List[Any],
                                  question_count: int) -> List[int]:
    """Marks in unused rows. A human must look — never silently scored."""
    return [q.question_number for q in omr_questions
            if q.question_number > question_count and q.state != "blank"]


def build_answer_docs(scoped: List[Any],
                      integer_questions: Set[int] = frozenset()) -> List[Dict[str, Any]]:
    docs = []
    for q in scoped:
        if q.question_number in integer_questions:
            # Never trust an OMR reading here — the physical bubble grid
            # doesn't represent a digit grid. Always routed to a human.
            docs.append({"question_number": q.question_number, "selected_option": None,
                         "state": "pending_integer_entry", "finalized": False})
        elif q.needs_review:
            docs.append({"question_number": q.question_number, "selected_option": None,
                         "state": "pending_review", "finalized": False})
        elif q.state == "multiple":
            docs.append({"question_number": q.question_number, "selected_option": None,
                         "state": "invalid_multiple", "finalized": True})
        else:
            docs.append({"question_number": q.question_number,
                         "selected_option": q.selected_option,
                         "state": "blank" if q.selected_option is None else "answered",
                         "finalized": True})
    return docs


def grade_and_publish(db_adapter, sheet_id: str) -> Dict[str, Any]:
    """Score a fully-resolved sheet and publish its report, atomically."""
    with db_adapter.unit_of_work() as s:
        sheet = db_adapter.db.sheets.find_one({"_id": sheet_id}, session=s)
        if not sheet:
            raise ValueError(f"Sheet {sheet_id} not found")
        exam = db_adapter.db.exams.find_one({"_id": sheet["exam_id"]}, session=s)

        grade = grade_submission({
            "identity_confirmed": sheet.get("student_id") is not None,
            "alignment_confirmed": not sheet.get("rejection_reasons"),
            "question_count": exam["question_count"],
            "marking_policy": exam["marking_policy"],
            "answer_key": exam["answer_key"],
            "answers": sheet["answers"],
        })

        revision = sheet.get("grade_revision", 0) + 1
        awards = [{"question_number": a.question_number, "state": a.state,
                   "awarded_marks": str(a.awarded_marks),
                   "selected_option": a.selected_option} for a in grade.awards]

        db_adapter.db.grade_revisions.insert_one({
            "_id": f"{sheet_id}:r{revision}", "sheet_id": sheet_id,
            "student_id": sheet["student_id"], "exam_id": sheet["exam_id"],
            "revision": revision, "score": str(grade.score),
            "maximum": str(grade.maximum), "percentage": str(grade.percentage),
            "awards": awards, "created_at": datetime.utcnow()}, session=s)

        # Release A publishes score-only reports.
        db_adapter.db.report_revisions.insert_one({
            "_id": f"report:{sheet_id}:r{revision}",
            "exam_id": sheet["exam_id"], "student_id": sheet["student_id"],
            "sheet_id": sheet_id, "revision": revision,
            "report_policy": exam.get("report_policy_revision", "score_only"),
            "state": "published",
            "score": str(grade.score), "maximum": str(grade.maximum),
            "percentage": str(grade.percentage), "awards": awards,
            "published_at": datetime.utcnow()}, session=s)

        db_adapter.db.sheets.update_one(
            {"_id": sheet_id},
            {"$set": {"state": "published", "grade_revision": revision}}, session=s)

    return {"sheet_id": sheet_id, "score": str(grade.score),
            "maximum": str(grade.maximum), "revision": revision}
