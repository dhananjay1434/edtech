import pytest
from cde.db import DatabaseAdapter
from cde.indexes import ensure_indexes
from cde.services.accounts import link_account, resolve_student_id


@pytest.fixture
def db():
    a = DatabaseAdapter("mongodb://localhost:27017", "cde_test")
    for c in ("account_links", "students", "report_revisions"):
        a.db[c].delete_many({})
    ensure_indexes(a.db)
    a.db.students.insert_many([
        {"_id": "std1", "roster_id": "r1", "roll_number_normalized": "1"},
        {"_id": "std2", "roster_id": "r1", "roll_number_normalized": "2"}])
    return a


def test_link_and_resolve(db):
    link_account(db, "iss", "subA", "std1")
    assert resolve_student_id(db, "iss", "subA") == "std1"


def test_cannot_link_non_roster_student(db):
    with pytest.raises(ValueError, match="non-roster"):
        link_account(db, "iss", "subX", "ghost")


def test_link_is_immutable(db):
    link_account(db, "iss", "subA", "std1")
    with pytest.raises(ValueError, match="different student"):
        link_account(db, "iss", "subA", "std2")


def test_unlinked_login_refused(db):
    with pytest.raises(PermissionError):
        resolve_student_id(db, "iss", "nobody")


def test_processing_payload_has_no_score():
    payload = {"status": "processing"}
    assert "score" not in payload and "answers" not in payload
