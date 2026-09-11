import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from cde.api import app
from cde.db import DatabaseAdapter, get_db_adapter
from cde.indexes import ensure_indexes
from cde.routes.admin import verified_admin_claims

TEST_DB = DatabaseAdapter("mongodb://localhost:27017", "cde_test")


def _admin_claims():
    return {"sub": "admin1", "iss": "test-issuer", "realm_access": {"roles": ["admin"]}}


app.dependency_overrides[get_db_adapter] = lambda: TEST_DB
app.dependency_overrides[verified_admin_claims] = _admin_claims

client = TestClient(app)


def make_pdf(n):
    imgs = [Image.new("RGB", (827, 1169), "white") for _ in range(n)]
    buf = io.BytesIO()
    imgs[0].save(buf, format="PDF", save_all=True, append_images=imgs[1:])
    return buf.getvalue()


@pytest.fixture(autouse=True)
def clean_db():
    for c in ("rosters", "students", "exams", "batches", "sheets", "jobs", "audit_events", "review_tasks"):
        TEST_DB.db[c].delete_many({})
    ensure_indexes(TEST_DB.db)
    yield


def test_create_roster_then_exam_then_batch():
    r = client.post("/api/admin/rosters", json={
        "exam_class": "12A",
        "rows": [{"roll_number": "1", "name": "Asha"}, {"roll_number": "2", "name": "Ravi"}],
    })
    assert r.status_code == 200, r.text
    roster_id = r.json()["roster_id"]
    assert r.json()["student_count"] == 2

    students = client.get(f"/api/admin/rosters/{roster_id}/students")
    assert students.status_code == 200
    assert len(students.json()["students"]) == 2

    rosters = client.get("/api/admin/rosters")
    assert rosters.status_code == 200
    listed_roster = next(x for x in rosters.json()["rosters"] if x["id"] == roster_id)
    assert listed_roster["student_count"] == 2

    r = client.post("/api/admin/exams", json={
        "name": "Mock 1", "roster_id": roster_id, "question_count": 2,
        "answer_key": [{"question_number": 1, "correct_option": "A"},
                       {"question_number": 2, "correct_option": "B"}],
    })
    assert r.status_code == 200, r.text
    exam_id = r.json()["exam_id"]

    listed = client.get("/api/admin/exams")
    assert exam_id in [e["id"] for e in listed.json()["exams"]]

    pdf_bytes = make_pdf(3)
    r = client.post(f"/api/admin/exams/{exam_id}/batches",
                    files={"file": ("batch.pdf", pdf_bytes, "application/pdf")})
    assert r.status_code == 200, r.text
    batch_id = r.json()["batch_id"]
    assert r.json()["page_count"] == 3

    status = client.get(f"/api/admin/exams/{exam_id}/batches/{batch_id}")
    assert status.status_code == 200
    assert status.json()["page_count"] == 3
    assert len(status.json()["sheets"]) == 3
    assert status.json()["counts_by_state"] == {"pending_read": 3}


def test_duplicate_roll_number_rejected_with_422():
    r = client.post("/api/admin/rosters", json={
        "exam_class": "12A",
        "rows": [{"roll_number": "7", "name": "A"}, {"roll_number": "7", "name": "B"}],
    })
    assert r.status_code == 422


def test_unknown_exam_batch_upload_returns_404():
    pdf_bytes = make_pdf(1)
    r = client.post("/api/admin/exams/nope/batches",
                    files={"file": ("batch.pdf", pdf_bytes, "application/pdf")})
    assert r.status_code == 404


def test_admin_role_required():
    app.dependency_overrides[verified_admin_claims] = lambda: (_ for _ in ()).throw(
        __import__("fastapi").HTTPException(403, "Admin role required"))
    try:
        r = client.get("/api/admin/exams")
        assert r.status_code == 403
    finally:
        app.dependency_overrides[verified_admin_claims] = _admin_claims


def test_list_sheets_by_exam_and_state():
    roster = client.post("/api/admin/rosters", json={
        "exam_class": "12A", "rows": [{"roll_number": "1", "name": "Asha"}],
    }).json()
    exam_id = client.post("/api/admin/exams", json={
        "name": "Mock 1", "roster_id": roster["roster_id"], "question_count": 1,
        "answer_key": [{"question_number": 1, "correct_option": "A"}],
    }).json()["exam_id"]
    client.post(f"/api/admin/exams/{exam_id}/batches",
               files={"file": ("batch.pdf", make_pdf(2), "application/pdf")})

    all_sheets = client.get(f"/api/admin/exams/{exam_id}/sheets").json()["sheets"]
    assert len(all_sheets) == 2
    assert all_sheets[0]["page_number"] == 1

    filtered = client.get(f"/api/admin/exams/{exam_id}/sheets?state=pending_read").json()["sheets"]
    assert len(filtered) == 2

    none_identified = client.get(f"/api/admin/exams/{exam_id}/sheets?state=identified").json()["sheets"]
    assert none_identified == []


def test_exceptions_endpoint_reports_rejected_and_failed():
    roster = client.post("/api/admin/rosters", json={
        "exam_class": "12A", "rows": [{"roll_number": "1", "name": "Asha"}],
    }).json()
    exam_id = client.post("/api/admin/exams", json={
        "name": "Mock 1", "roster_id": roster["roster_id"], "question_count": 1,
        "answer_key": [{"question_number": 1, "correct_option": "A"}],
    }).json()["exam_id"]
    batch = client.post(f"/api/admin/exams/{exam_id}/batches",
                        files={"file": ("batch.pdf", make_pdf(1), "application/pdf")}).json()
    sheet_id = client.get(f"/api/admin/exams/{exam_id}/batches/{batch['batch_id']}").json()["sheets"][0]["sheet_id"]

    TEST_DB.db.sheets.update_one({"_id": sheet_id}, {"$set": {
        "state": "rejected_layout", "rejection_reasons": ["unexpected_aspect_ratio:0.5"]}})
    TEST_DB.db.jobs.update_one({"entity_id": sheet_id}, {"$set": {
        "status": "failed", "last_error": "boom"}})

    r = client.get(f"/api/admin/exams/{exam_id}/exceptions")
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data["rejected_layout"]) == 1
    assert data["rejected_layout"][0]["reasons"] == ["unexpected_aspect_ratio:0.5"]
    assert len(data["failed_jobs"]) == 1
    assert data["failed_jobs"][0]["last_error"] == "boom"


def test_integer_queue_lists_pending_and_excludes_resolved():
    TEST_DB.db.sheets.insert_one({
        "_id": "sh-int-q1", "exam_id": "eX", "batch_id": "b1", "page_number": 3,
        "state": "pending_identity", "student_id": None, "rejection_reasons": [],
        "image_key": "gridfs:abc123",
        "answers": [
            {"question_number": 1, "selected_option": "A", "state": "answered", "finalized": True},
            {"question_number": 2, "selected_option": None, "state": "pending_integer_entry", "finalized": False},
        ],
    })
    TEST_DB.db.sheets.insert_one({
        "_id": "sh-int-q2", "exam_id": "eX", "batch_id": "b1", "page_number": 4,
        "state": "pending_identity", "student_id": None, "rejection_reasons": [],
        "answers": [{"question_number": 1, "selected_option": "A", "state": "answered", "finalized": True}],
    })

    r = client.get("/api/admin/exams/eX/integer-queue")
    assert r.status_code == 200
    sheets = r.json()["sheets"]
    assert len(sheets) == 1
    assert sheets[0]["sheet_id"] == "sh-int-q1"
    assert sheets[0]["pending_questions"] == [2]
    assert sheets[0]["image_id"] == "abc123"


def test_resolve_integer_answer_via_route():
    roster = client.post("/api/admin/rosters", json={
        "exam_class": "12A", "rows": [{"roll_number": "1", "name": "Asha"}],
    }).json()
    student_id = client.get(f"/api/admin/rosters/{roster['roster_id']}/students").json()["students"][0]["id"]
    exam_id = client.post("/api/admin/exams", json={
        "name": "Mock 1", "roster_id": roster["roster_id"], "question_count": 2,
        "answer_key": [
            {"question_number": 1, "question_type": "mcq", "correct_option": "A"},
            {"question_number": 2, "question_type": "integer", "correct_value": 42},
        ],
    }).json()
    exam_id = exam_id["exam_id"]

    # Simulate a sheet already read by the worker, with an unresolved
    # integer question pending manual entry.
    TEST_DB.db.sheets.insert_one({
        "_id": "sh-int-1", "exam_id": exam_id, "batch_id": "b1", "page_number": 1,
        "state": "pending_identity", "student_id": None, "rejection_reasons": [],
        "answers": [
            {"question_number": 1, "selected_option": "A", "state": "answered", "finalized": True},
            {"question_number": 2, "selected_option": None, "state": "pending_integer_entry", "finalized": False},
        ],
    })
    TEST_DB.db.review_tasks.insert_one({
        "_id": "rt-int-1", "submission_id": "sh-int-1", "exam_id": exam_id,
        "question_number": 2, "kind": "integer_manual", "crop_id": None, "choices": [],
        "suggested_code": None, "reason": "Section B numerical answer",
        "revision": 1, "resolved": False, "claimed_by": None, "lease_expires_at": None,
    })

    r = client.post(f"/api/admin/sheets/sh-int-1/answers/2/integer", json={"value": 42})
    assert r.status_code == 200, r.text
    assert r.json() == {"sheet_id": "sh-int-1", "question_number": 2, "value": 42}

    sheet = TEST_DB.db.sheets.find_one({"_id": "sh-int-1"})
    q2 = next(a for a in sheet["answers"] if a["question_number"] == 2)
    assert q2["selected_option"] == "42" and q2["finalized"] is True and q2["state"] == "answered"

    task = TEST_DB.db.review_tasks.find_one({"_id": "rt-int-1"})
    assert task["resolved"] is True

    # Confirm identity now (last step before grading can be queued) and
    # verify the grade job was enqueued once everything is finalized.
    client.post("/api/admin/sheets/sh-int-1/identity", json={"student_id": student_id})
    assert TEST_DB.db.jobs.count_documents({"kind": "grade_sheet", "entity_id": "sh-int-1"}) == 1


def test_resolve_integer_answer_unknown_question_404():
    TEST_DB.db.sheets.insert_one({
        "_id": "sh-int-2", "exam_id": "e1", "batch_id": "b1", "page_number": 1,
        "state": "pending_identity", "student_id": None, "rejection_reasons": [],
        "answers": [{"question_number": 1, "selected_option": None,
                     "state": "pending_integer_entry", "finalized": False}],
    })
    r = client.post("/api/admin/sheets/sh-int-2/answers/99/integer", json={"value": 1})
    assert r.status_code == 404


def test_confirm_identity_via_route():
    roster = client.post("/api/admin/rosters", json={
        "exam_class": "12A", "rows": [{"roll_number": "1", "name": "Asha"}],
    }).json()
    student_id = client.get(f"/api/admin/rosters/{roster['roster_id']}/students").json()["students"][0]["id"]
    exam_id = client.post("/api/admin/exams", json={
        "name": "Mock 1", "roster_id": roster["roster_id"], "question_count": 1,
        "answer_key": [{"question_number": 1, "correct_option": "A"}],
    }).json()["exam_id"]
    batch = client.post(f"/api/admin/exams/{exam_id}/batches",
                        files={"file": ("batch.pdf", make_pdf(1), "application/pdf")}).json()
    sheet_id = client.get(f"/api/admin/exams/{exam_id}/batches/{batch['batch_id']}").json()["sheets"][0]["sheet_id"]

    r = client.post(f"/api/admin/sheets/{sheet_id}/identity", json={"student_id": student_id})
    assert r.status_code == 200, r.text
    assert r.json()["student_id"] == student_id
