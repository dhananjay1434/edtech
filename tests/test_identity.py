import pytest
from cde.db import DatabaseAdapter
from cde.indexes import ensure_indexes
from cde.services.identity import confirm_identity


@pytest.fixture
def db():
    a = DatabaseAdapter("mongodb://localhost:27017", "cde_test")
    for c in ("sheets", "students", "audit_events", "jobs"):
        a.db[c].delete_many({})
    ensure_indexes(a.db)
    a.db.students.insert_many([
        {"_id": "std1", "name": "Asha", "roster_id": "r1", "roll_number_normalized": "1"},
        {"_id": "std2", "name": "Ravi", "roster_id": "r1", "roll_number_normalized": "2"}])
    for i in (1, 2):
        a.db.sheets.insert_one({"_id": f"sh{i}", "exam_id": "e1", "batch_id": "b1",
                                "page_number": i, "student_id": None,
                                "rejection_reasons": [], "answers": []})
    return a


def test_confirm_binds(db):
    confirm_identity(db, "sh1", "std1", "admin1")
    assert db.db.sheets.find_one({"_id": "sh1"})["student_id"] == "std1"


def test_cannot_assign_unknown_student(db):
    with pytest.raises(ValueError, match="not on the roster"):
        confirm_identity(db, "sh1", "ghost", "admin1")
    assert db.db.students.count_documents({}) == 2


def test_one_student_one_sheet(db):
    confirm_identity(db, "sh1", "std1", "admin1")
    with pytest.raises(ValueError, match="already has sheet"):
        confirm_identity(db, "sh2", "std1", "admin1")


def test_cannot_reassign(db):
    confirm_identity(db, "sh1", "std1", "admin1")
    with pytest.raises(ValueError, match="already assigned"):
        confirm_identity(db, "sh1", "std2", "admin1")


def test_rejected_sheet_cannot_be_assigned(db):
    db.db.sheets.update_one({"_id": "sh2"}, {"$set": {"rejection_reasons": ["bad_ratio"]}})
    with pytest.raises(ValueError, match="rejected"):
        confirm_identity(db, "sh2", "std2", "admin1")


def test_grading_queued_only_when_answers_final(db):
    db.db.sheets.update_one({"_id": "sh1"}, {"$set": {"answers": [
        {"question_number": 1, "finalized": True}]}})
    confirm_identity(db, "sh1", "std1", "admin1")
    assert db.db.jobs.count_documents({"kind": "grade_sheet"}) == 1


def test_grading_not_queued_while_review_pending(db):
    db.db.sheets.update_one({"_id": "sh2"}, {"$set": {"answers": [
        {"question_number": 1, "finalized": False}]}})
    confirm_identity(db, "sh2", "std2", "admin1")
    assert db.db.jobs.count_documents({"kind": "grade_sheet"}) == 0
