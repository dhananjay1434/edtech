import io, pytest
from PIL import Image
from cde.db import DatabaseAdapter
from cde.indexes import ensure_indexes
from cde.services.batches import create_batch, render_page


def make_pdf(n):
    imgs = [Image.new("RGB", (827, 1169), "white") for _ in range(n)]
    buf = io.BytesIO()
    imgs[0].save(buf, format="PDF", save_all=True, append_images=imgs[1:])
    return buf.getvalue()


@pytest.fixture
def db():
    a = DatabaseAdapter("mongodb://localhost:27017", "cde_test")
    for c in ("batches", "sheets", "jobs", "exams"):
        a.db[c].delete_many({})
    ensure_indexes(a.db)
    a.db.exams.insert_one({"_id": "exam1", "question_count": 75})
    return a


def test_45_pages_produce_45_sheets(db):
    r = create_batch(db, "exam1", make_pdf(45), "admin1")
    sheets = list(db.db.sheets.find({"batch_id": r["batch_id"]}))
    assert len(sheets) == 45
    assert sorted(s["page_number"] for s in sheets) == list(range(1, 46))


def test_every_sheet_gets_a_job(db):
    r = create_batch(db, "exam1", make_pdf(10), "admin1")
    assert db.db.jobs.count_documents({"batch_id": r["batch_id"]}) == 10


def test_page_count_mismatch_is_visible(db):
    r = create_batch(db, "exam1", make_pdf(44), "admin1", expected_sheet_count=45)
    assert r["count_matches_expected"] is False


def test_unknown_exam_rejected(db):
    with pytest.raises(ValueError, match="not found"):
        create_batch(db, "nope", make_pdf(2), "admin1")


def test_render_page(db):
    img = Image.open(io.BytesIO(render_page(make_pdf(3), 2)))
    assert img.width > 0
