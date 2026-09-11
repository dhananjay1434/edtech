import hashlib, io, uuid
from datetime import datetime
from typing import Dict
import pypdfium2 as pdfium
from cde.storage import upload_named

MAX_PDF_BYTES = 200 * 1024 * 1024
MAX_PAGES = 120
RENDER_DPI = 300


def create_batch(db_adapter, exam_id: str, pdf_bytes: bytes, actor_id: str,
                 expected_sheet_count: int | None = None) -> Dict:
    """Store the PDF and create one sheet + one job per page. Grades nothing."""
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise ValueError(f"PDF exceeds {MAX_PDF_BYTES} bytes")
    if not db_adapter.db.exams.find_one({"_id": exam_id}):
        raise ValueError(f"Exam {exam_id} not found")

    page_count = len(pdfium.PdfDocument(io.BytesIO(pdf_bytes)))
    if not 1 <= page_count <= MAX_PAGES:
        raise ValueError(f"PDF has {page_count} pages; expected 1..{MAX_PAGES}")

    batch_id = f"batch_{uuid.uuid4().hex[:12]}"
    # Files are written BEFORE the transaction — GridFS is not transactional.
    storage_key = upload_named(f"{batch_id}.pdf", pdf_bytes, content_type="application/pdf")
    now = datetime.utcnow()
    matches = None if expected_sheet_count is None else page_count == expected_sheet_count

    with db_adapter.unit_of_work() as s:
        db_adapter.db.batches.insert_one({
            "_id": batch_id, "exam_id": exam_id,
            "original_pdf_key": storage_key,
            "original_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
            "page_count": page_count,
            "expected_sheet_count": expected_sheet_count,
            "count_matches_expected": matches,
            "state": "processing", "created_at": now, "created_by": actor_id}, session=s)

        sheets = [{
            "_id": f"sheet_{uuid.uuid4().hex[:12]}",
            "batch_id": batch_id, "exam_id": exam_id,
            "page_number": i + 1,                 # 1-based, as the admin sees it
            "state": "pending_read", "student_id": None,
            "rejection_reasons": [], "answers": [],
            "created_at": now} for i in range(page_count)]
        db_adapter.db.sheets.insert_many(sheets, session=s)

        db_adapter.db.jobs.insert_many([{
            "_id": f"job_{uuid.uuid4().hex[:12]}",
            "kind": "read_sheet", "entity_id": sh["_id"], "batch_id": batch_id,
            "status": "pending", "attempt_count": 0, "max_attempts": 5,
            "lease_owner": None, "lease_expires_at": None, "fencing_token": 0,
            "idempotency_key": f"read:{batch_id}:{sh['page_number']}",
            "last_error": None, "created_at": now} for sh in sheets], session=s)

    return {"batch_id": batch_id, "page_count": page_count,
            "count_matches_expected": matches}


def render_page(pdf_bytes: bytes, page_number: int) -> bytes:
    """Render one 1-based page to PNG bytes."""
    doc = pdfium.PdfDocument(io.BytesIO(pdf_bytes))
    bitmap = doc[page_number - 1].render(scale=RENDER_DPI / 72)
    buf = io.BytesIO()
    bitmap.to_pil().save(buf, format="PNG")
    return buf.getvalue()
