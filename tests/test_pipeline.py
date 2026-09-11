import asyncio, io, pytest
from PIL import Image
from cde.db import DatabaseAdapter
from cde.indexes import ensure_indexes
from cde.services.batches import create_batch
from cde.services.identity import confirm_identity
from cde.services.grading import grade_and_publish
from cde.jobs.worker import run_once


def make_pdf(n):
    imgs = [Image.new("RGB", (827, 1169), "white") for _ in range(n)]
    buf = io.BytesIO()
    imgs[0].save(buf, format="PDF", save_all=True, append_images=imgs[1:])
    return buf.getvalue()


@pytest.fixture
def db(monkeypatch):
    a = DatabaseAdapter("mongodb://localhost:27017", "cde_test")
    # cde.jobs.worker.run_once() uses the module-level db_adapter singleton
    # (which points at the production db per cde/config.py); redirect it to
    # this test's isolated database for the duration of the test.
    monkeypatch.setattr("cde.jobs.worker.db_adapter", a)
    for c in ("batches", "sheets", "jobs", "exams", "students", "rosters",
              "review_tasks", "grade_revisions", "report_revisions"):
        a.db[c].delete_many({})
    ensure_indexes(a.db)
    a.db.exams.insert_one({
        "_id": "e1", "question_count": 2,
        "marking_policy": {"correct_marks": "4.000", "wrong_marks": "-1.000",
                           "blank_marks": "0.000", "multiple_marks": "-1.000"},
        "answer_key": [{"question_number": 1, "correct_option": "A"},
                       {"question_number": 2, "correct_option": "B"}],
        "report_policy_revision": "score_only"})
    a.db.students.insert_one({"_id": "std1", "name": "Asha"})
    return a


def test_worker_drains_the_queue(db):
    create_batch(db, "e1", make_pdf(3), "admin1")
    assert db.db.jobs.count_documents({"status": "pending"}) == 3
    for _ in range(10):
        if not asyncio.run(run_once("w1")):
            break
    assert db.db.jobs.count_documents({"status": "pending"}) == 0


def test_blank_pages_are_rejected_not_graded(db):
    """Blank white pages have no marks — they must be rejected, not scored."""
    create_batch(db, "e1", make_pdf(2), "admin1")
    for _ in range(10):
        if not asyncio.run(run_once("w1")):
            break
    states = [s["state"] for s in db.db.sheets.find({})]
    assert all(s == "rejected_layout" for s in states), states


def test_grade_and_publish_produces_a_report(db):
    db.db.sheets.insert_one({
        "_id": "sh1", "exam_id": "e1", "batch_id": "b1", "page_number": 1,
        "student_id": "std1", "rejection_reasons": [],
        "answers": [{"question_number": 1, "selected_option": "A",
                     "state": "answered", "finalized": True},
                    {"question_number": 2, "selected_option": "C",
                     "state": "answered", "finalized": True}]})
    r = grade_and_publish(db, "sh1")
    assert r["score"] == "3.000"        # +4 correct, -1 wrong
    assert r["maximum"] == "8.000"
    assert db.db.report_revisions.count_documents({"state": "published"}) == 1


def test_unresolved_sheet_cannot_publish(db):
    db.db.sheets.insert_one({
        "_id": "sh2", "exam_id": "e1", "batch_id": "b1", "page_number": 2,
        "student_id": "std1", "rejection_reasons": [],
        "answers": [{"question_number": 1, "selected_option": None,
                     "state": "pending_review", "finalized": False},
                    {"question_number": 2, "selected_option": "B",
                     "state": "answered", "finalized": True}]})
    with pytest.raises(ValueError, match="not finalized"):
        grade_and_publish(db, "sh2")
    assert db.db.report_revisions.count_documents({"sheet_id": "sh2"}) == 0
