import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from cde.api import app
from cde.db import DatabaseAdapter, get_db_adapter
from cde.indexes import ensure_indexes
from cde.routes.student import current_student_id

TEST_DB = DatabaseAdapter("mongodb://localhost:27017", "cde_test")

app.dependency_overrides[get_db_adapter] = lambda: TEST_DB
app.dependency_overrides[current_student_id] = lambda: "std1"

client = TestClient(app)


def png_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), "white").save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture(autouse=True)
def clean_db():
    for c in ("sheets", "exams", "diagnostics", "entitlements"):
        TEST_DB.db[c].delete_many({})
    ensure_indexes(TEST_DB.db)
    TEST_DB.db.entitlements.insert_one(
        {"_id": "institute", "enabled": {"cognitive.diagnosis": True}})
    TEST_DB.db.sheets.insert_one({
        "_id": "sh1", "exam_id": "e1", "batch_id": "b1", "page_number": 1,
        "state": "pending_identity", "student_id": "std1", "rejection_reasons": [],
        "answers": [],
    })
    yield


def test_upload_rough_sheet_attaches_to_own_sheet():
    r = client.post("/api/me/exams/e1/rough-sheet",
                    files={"file": ("rough.png", png_bytes(), "image/png")})
    assert r.status_code == 200, r.text
    sheet = TEST_DB.db.sheets.find_one({"_id": "sh1"})
    assert sheet["rough_sheet_status"] == "uploaded"
    assert sheet["rough_sheet_path"]


def test_upload_rejects_wrong_content_type():
    r = client.post("/api/me/exams/e1/rough-sheet",
                    files={"file": ("rough.pdf", b"%PDF-1.4", "application/pdf")})
    assert r.status_code == 422


def test_upload_cannot_reach_another_students_sheet():
    """The route resolves the sheet via (exam_id, student_id) from the
    verified token — there is no way to pass another student's sheet id."""
    TEST_DB.db.sheets.insert_one({
        "_id": "sh2", "exam_id": "e1", "batch_id": "b1", "page_number": 2,
        "state": "pending_identity", "student_id": "std2", "rejection_reasons": [],
        "answers": [],
    })
    r = client.post("/api/me/exams/e1/rough-sheet",
                    files={"file": ("rough.png", png_bytes(), "image/png")})
    assert r.status_code == 200
    # Only std1's own sheet (sh1) was touched, not std2's (sh2).
    assert TEST_DB.db.sheets.find_one({"_id": "sh1"})["rough_sheet_status"] == "uploaded"
    assert "rough_sheet_status" not in TEST_DB.db.sheets.find_one({"_id": "sh2"})


def test_declare_no_rough_sheet():
    r = client.post("/api/me/exams/e1/rough-sheet/none")
    assert r.status_code == 200
    sheet = TEST_DB.db.sheets.find_one({"_id": "sh1"})
    assert sheet["rough_sheet_status"] == "none_provided"


def test_no_sheet_for_exam_returns_404():
    r = client.post("/api/me/exams/unknown-exam/rough-sheet",
                    files={"file": ("rough.png", png_bytes(), "image/png")})
    assert r.status_code == 404


def test_upload_is_404_when_feature_disabled():
    TEST_DB.db.entitlements.update_one(
        {"_id": "institute"}, {"$set": {"enabled.cognitive.diagnosis": False}})
    r = client.post("/api/me/exams/e1/rough-sheet",
                    files={"file": ("rough.png", png_bytes(), "image/png")})
    assert r.status_code == 404


def test_declare_none_is_404_when_feature_disabled():
    TEST_DB.db.entitlements.update_one(
        {"_id": "institute"}, {"$set": {"enabled.cognitive.diagnosis": False}})
    r = client.post("/api/me/exams/e1/rough-sheet/none")
    assert r.status_code == 404


def test_diagnosis_is_404_when_feature_disabled():
    TEST_DB.db.entitlements.update_one(
        {"_id": "institute"}, {"$set": {"enabled.cognitive.diagnosis": False}})
    r = client.get("/api/me/exams/e1/diagnosis")
    assert r.status_code == 404


def test_upload_resets_diagnostics_ready():
    TEST_DB.db.sheets.update_one({"_id": "sh1"}, {"$set": {"diagnostics_ready": True}})
    r = client.post("/api/me/exams/e1/rough-sheet",
                    files={"file": ("rough.png", png_bytes(), "image/png")})
    assert r.status_code == 200
    assert TEST_DB.db.sheets.find_one({"_id": "sh1"})["diagnostics_ready"] is False


def test_diagnosis_waiting_for_result_before_published():
    r = client.get("/api/me/exams/e1/diagnosis")
    assert r.status_code == 200
    assert r.json() == {"status": "waiting_for_result"}


def test_diagnosis_ready_shape():
    TEST_DB.db.sheets.update_one({"_id": "sh1"}, {"$set": {
        "state": "published", "diagnostics_ready": True, "grade_revision": 1,
        "rough_sheet_status": "uploaded"}})
    TEST_DB.db.diagnostics.insert_one({
        "_id": "diag:sh1:q1:r1", "sheet_id": "sh1", "exam_id": "e1", "student_id": "std1",
        "question_number": 1, "grade_revision": 1, "subject": "Physics",
        "diagnostic": {"status": "classified", "error_class": "Calculation Slip",
                       "confidence": 0.95, "summary": "s", "next_step": "n",
                       "abstention_reason": None, "evidence": [{"crop_id": "x"}]},
    })
    r = client.get("/api/me/exams/e1/diagnosis")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert body["grade_revision"] == 1
    assert len(body["questions"]) == 1
    q = body["questions"][0]
    assert q["question_number"] == 1
    assert q["error_class"] == "Calculation Slip"
    assert "evidence" not in q
