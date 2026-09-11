import asyncio
import pytest
from cde.db import DatabaseAdapter
from cde.indexes import ensure_indexes
from cde.services.diagnosis import diagnose_sheet


@pytest.fixture
def db():
    a = DatabaseAdapter("mongodb://localhost:27017", "cde_test")
    for c in ("sheets", "exams", "grade_revisions", "diagnostics"):
        a.db[c].delete_many({})
    ensure_indexes(a.db)
    return a


def _exam(question_text=True):
    entry = {"question_number": 1, "question_type": "mcq", "correct_option": "A"}
    if question_text:
        entry["question_text"] = "What is 2 + 2?"
        entry["options"] = {"A": "4", "B": "5", "C": "3", "D": "6"}
    return {
        "_id": "e1", "question_count": 1,
        "answer_key": [entry],
        "subject_ranges": [{"subject": "Mathematics", "first_question": 1, "last_question": 1}],
    }


def _sheet(**kw):
    doc = {"_id": "sh1", "exam_id": "e1", "state": "published",
          "student_id": "std1", "batch_id": "b1", "page_number": 1}
    doc.update(kw)
    return doc


def _grade_rev(state="incorrect"):
    return {"_id": "sh1:r1", "sheet_id": "sh1", "revision": 1,
           "awards": [{"question_number": 1, "state": state, "awarded_marks": "-1.000",
                       "selected_option": "B"}]}


def test_no_rough_work_never_uploaded_abstains(db):
    db.db.exams.insert_one(_exam())
    db.db.sheets.insert_one(_sheet())
    db.db.grade_revisions.insert_one(_grade_rev())

    result = asyncio.run(diagnose_sheet(db, "sh1"))
    assert result["diagnosed_count"] == 1

    diag = db.db.diagnostics.find_one({"sheet_id": "sh1", "question_number": 1})
    assert diag["diagnostic"]["status"] == "abstained"
    assert diag["diagnostic"]["abstention_reason"] == "missing_or_unmapped_work"
    assert diag["provider"] is None


def test_explicit_no_rough_work_gets_distinct_reason(db):
    db.db.exams.insert_one(_exam())
    db.db.sheets.insert_one(_sheet(rough_sheet_status="none_provided"))
    db.db.grade_revisions.insert_one(_grade_rev())

    asyncio.run(diagnose_sheet(db, "sh1"))
    diag = db.db.diagnostics.find_one({"sheet_id": "sh1", "question_number": 1})
    assert diag["diagnostic"]["abstention_reason"] == "no_rough_work_provided"


def test_missing_question_text_abstains_without_calling_provider(db):
    from cde.storage import upload
    storage_key = upload("sh1", b"\x89PNG\r\n\x1a\nfake", content_type="image/png")
    db.db.exams.insert_one(_exam(question_text=False))
    db.db.sheets.insert_one(_sheet(rough_sheet_path=storage_key))
    db.db.grade_revisions.insert_one(_grade_rev())

    asyncio.run(diagnose_sheet(db, "sh1"))
    diag = db.db.diagnostics.find_one({"sheet_id": "sh1", "question_number": 1})
    assert diag["diagnostic"]["status"] == "abstained"
    assert diag["diagnostic"]["abstention_reason"] == "missing_question_context"


def test_correct_answers_are_never_diagnosed(db):
    db.db.exams.insert_one(_exam())
    db.db.sheets.insert_one(_sheet())
    db.db.grade_revisions.insert_one(_grade_rev(state="correct"))

    result = asyncio.run(diagnose_sheet(db, "sh1"))
    assert result["diagnosed_count"] == 0
    assert db.db.diagnostics.count_documents({}) == 0


def test_unpublished_sheet_refused(db):
    db.db.exams.insert_one(_exam())
    db.db.sheets.insert_one(_sheet(state="pending_identity"))
    db.db.grade_revisions.insert_one(_grade_rev())
    with pytest.raises(ValueError, match="not published"):
        asyncio.run(diagnose_sheet(db, "sh1"))


def test_marks_sheet_diagnostics_ready(db):
    db.db.exams.insert_one(_exam())
    db.db.sheets.insert_one(_sheet())
    db.db.grade_revisions.insert_one(_grade_rev())
    asyncio.run(diagnose_sheet(db, "sh1"))
    sheet = db.db.sheets.find_one({"_id": "sh1"})
    assert sheet["diagnostics_ready"] is True
