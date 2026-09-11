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
    for c in ("sheets", "exams"):
        TEST_DB.db[c].delete_many({})
    ensure_indexes(TEST_DB.db)
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
