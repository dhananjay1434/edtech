import pytest
from cde.db import DatabaseAdapter
from cde.indexes import ensure_indexes
from cde.services.rosters import RosterImport, import_roster, normalize_roll


@pytest.fixture
def db():
    a = DatabaseAdapter("mongodb://localhost:27017", "cde_test")
    for c in ("students", "rosters", "audit_events"):
        a.db[c].delete_many({})
    ensure_indexes(a.db)
    return a


def test_import_creates_students(db):
    r = import_roster(db, RosterImport(exam_class="12A", rows=[
        {"roll_number": "1", "name": "Asha"}, {"roll_number": "2", "name": "Ravi"}]), "admin1")
    assert r["student_count"] == 2
    assert db.db.students.count_documents({}) == 2


def test_duplicate_roll_rejected_and_nothing_written(db):
    with pytest.raises(ValueError, match="Duplicate roll number"):
        import_roster(db, RosterImport(exam_class="12A", rows=[
            {"roll_number": "7", "name": "Asha"}, {"roll_number": "7", "name": "Ravi"}]), "admin1")
    assert db.db.students.count_documents({}) == 0


def test_leading_zeros_preserved():
    assert normalize_roll("007") != normalize_roll("7")
