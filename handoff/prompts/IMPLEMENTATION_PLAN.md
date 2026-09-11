# Cognitive Diagnostic Engine — Implementation Plan (Authoritative)

**Status:** This supersedes the earlier Day-0 draft of this file. It adopts the hardened
migration plan's decisions wholesale, and restores concrete, corrected code for the parts
built first. Where the earlier draft and the hardened plan disagreed, **the hardened plan
wins** — see §1 for exactly what changed and why.

**Product:** React web app, one admin + ~45 students, one exam to start. No teacher role.

---

## 1. Corrections to the earlier draft (do not build the old version)

| Earlier draft said | Corrected decision | Why the correction is right |
|---|---|---|
| Custom student auth: bcrypt access codes + self-signed HS256 JWT, deliberately separate from Keycloak | **Extend the existing Keycloak** with `admin`/`student` roles and a browser client using Authorization Code + PKCE. Admin provisions accounts against roster rows and issues temporary credentials that must be replaced on first use. Persist an immutable Keycloak-subject → `student_id` mapping. | Rolling a second, weaker auth system beside a working one is how authorization gaps get created. `cde/auth.py` already does real JWKS-backed validation; a hand-rolled HS256 scheme with an env secret is strictly worse and would have to be torn out later anyway. |
| Mongo's silent no-transaction fallback is "a known, acceptable risk" at one-class scale | **Mandatory replica set.** Delete the fallback; fail readiness and refuse processing when transactions are unavailable. | The invariants this project is built on ("no lost sheet", "no lost human decision") are *implemented by* those transactions. Silently degrading them means the invariants are decorative. Scale is irrelevant — a single lost review decision on one student is the failure being prevented. |
| Don't fix Temporal; just call grading directly from the FastAPI route | Remove Temporal, but replace it with **Mongo-backed durable jobs** — leases, heartbeats, retry limits, fencing tokens, idempotency keys — committed in the same transaction as the domain change. | "Direct call in the request handler" is not a lighter orchestration choice, it's *no* orchestration. A 45-page batch is minutes of CPU work that must survive a worker restart; inline grading loses the whole batch on any crash or timeout. |
| Grade inline during the upload request | Persist the original PDF + a full **page manifest** first, then render and grade as independent per-sheet jobs. | Every page must be accounted for, including rejected ones. Inline processing cannot express "page 31 was rejected, pages 1–30 and 32–45 are fine." |
| Student uploads rough work after seeing their report | Students can upload rough work **during processing**, or explicitly declare "no rough work available" — before any score or wrong-answer list is visible. | Genuinely better, and I had it backwards. Requiring a published report first creates a deadlock: the report can't publish until diagnostics resolve, and diagnostics can't run without the rough work. |
| Cited "the already-working 97%-accurate OMR engine" as settled | **No production accuracy claim is justified yet.** One labeled page is not validation. Measure *confidently wrong* reads separately from review rate; block release on any known confidently-wrong case. | This was my overreach and the hardened plan is right to strike it. 97.2% on `page_10` with 0 errors is a promising signal from a single labeled page, nothing more. |

Also adopted from the hardened plan without change: the three release boundaries (§2), the
publication gate (§5), the Gap A–K decision table, and the acceptance gates.

---

## 2. Verified integration findings (do this before trusting anything else)

The hardened plan opens by saying implementation starts with verifying the reported
integration points. Two were checked and **both are broken today**:

**Finding 1 — the PDF path in the live endpoint cannot run.**
`cde/routes/beta.py:146` does `import fitz` (PyMuPDF) to convert an uploaded PDF to PNG.
`fitz`/`pymupdf` appears in **neither** `requirements.in` nor `requirements.lock`. Any PDF
upload to `POST /api/omr/upload` raises `ImportError` at request time. Meanwhile
`pypdfium2==5.13.0` *is* pinned — that's what the blueprint specified (§1.1) and what the
batch renderer below uses. **Do not add PyMuPDF; remove the `fitz` path and standardize on
pypdfium2.**

**Finding 2 — the diagnostics path cannot run in a clean install.**
`cde/diagnostics.py` and `cde/embeddings.py` both depend on `google-genai`, which is pinned
nowhere (`requirements.in` still lists `openai`, from the original OpenAI-based blueprint).
Add `google-genai` and drop `openai` unless something still uses it.

Both are one-line fixes, but they mean the "working end-to-end path" described in the audit
is only working in an environment with un-pinned packages installed by hand. Fix these first
or every later test result is meaningless.

---

## 3. Release boundaries

- **Walking skeleton** — roster, admin-issued accounts, batch PDF ingestion, manual identity
  confirmation, deterministic OMR, human bubble review, finalized **score-only** reports.
- **Diagnostic pilot** — validated identity OCR, question-paper images, rough-work upload,
  evidence-grounded diagnoses, personalized reports, cohort comparisons.
- **Content-enabled release** — admin-validated topic tags + populated practice bank unlock
  topic analysis and semantic recommendations.

The skeleton is **explicitly score-only**. Diagnostics are not silently skipped in a release
that promises them — the release simply doesn't promise them.

**On "today":** today is a target for *demonstrating the skeleton*, not deploying it. If the
Phase 0 gate fails, demo with synthetic data rather than putting real students through an
unverified system. Phase 0 as scoped below is realistically weeks, not hours; the hardened
plan agrees, and says so in its own words.

---

## 4. Phase 0 — one trustworthy path

### 4.1 Remove the silent transaction fallback

`cde/db.py` currently ends `unit_of_work()` with a bare `else: yield session` — a no-op
"transaction" whenever Mongo isn't a replica set. Delete that branch:

```python
@contextmanager
def unit_of_work(self) -> Generator[ClientSession, None, None]:
    if not self.check_replica_set():
        raise RuntimeError(
            "MongoDB is not a replica set; transactional writes are unavailable. "
            "Refusing to process — start Mongo with --replSet."
        )
    with self.get_session() as session:
        session.start_transaction(
            read_concern=ReadConcern("snapshot"),
            write_concern=WriteConcern(w="majority"),
            read_preference=ReadPreference.PRIMARY,
        )
        try:
            yield session
            session.commit_transaction()
        except Exception:
            session.abort_transaction()
            raise
```

`GET /health/ready` in `cde/routes/alpha.py` already 503s on a non-replica-set — that stays
and is now consistent with the write path rather than contradicting it.

### 4.2 Fix the known OMR regression, then add layout guards

Before any batch work: restore the density-relative guard in `_auto_header_cutoff`
(`cde/omr_engine/engine.py:109`), which `fix_cutoff.py` removed and which regressed page 1
from ~6 to 79 flagged:

```python
median_gap = float(np.median(diffs))
is_convincing = (
    diffs[i] >= 0.03 * h
    and (median_gap <= 0 or diffs[i] >= 2.5 * median_gap)
)
```

Re-run the full 10-page batch; **page 1 and page 4 must both come down together** — that pair
is the regression test. Then add explicit guards that block a sheet rather than guessing:

```python
def _validate_layout(im, calibration_evidence) -> list[str]:
    """Return blocking reasons; empty list means the sheet matches the expected layout."""
    reasons = []
    ratio = im.width / im.height
    if not (0.68 <= ratio <= 0.78):                      # A4-ish portrait, tune on real scans
        reasons.append(f"unexpected_aspect_ratio:{ratio:.3f}")
    if calibration_evidence["panels_calibrated"] < N_PANELS:
        reasons.append("insufficient_panel_evidence")
    if calibration_evidence["rows_calibrated"] < 30:      # of 36; tune against the batch
        reasons.append("insufficient_row_evidence")
    if calibration_evidence["points"] < 100:
        reasons.append("too_few_detected_marks")
    return reasons
```

A sheet with any blocking reason goes to admin review as `Rejected — Layout`, never to
grading. This is the guard that stops the silent-wrong-answers failure mode identified in the
audit (§3.4: a mismatched layout currently returns confident garbage rather than erroring).

### 4.3 Durable job collection

```python
# jobs collection — one document per unit of work
{
  "_id": "job_<uuid>",
  "kind": "render_sheet" | "grade_sheet" | "diagnose_question" | "publish_report",
  "batch_id": "...", "sheet_id": "...",
  "state": "pending" | "leased" | "done" | "failed",
  "attempts": 0, "max_attempts": 5,
  "lease_owner": None, "lease_expires_at": None,
  "fence": 0,                       # monotonically increments per lease; stale workers lose
  "idempotency_key": "<stable hash of inputs>",
  "last_error": None,
  "created_at": ..., "updated_at": ...,
}
```

Claim with a single atomic operation so two workers can never hold the same job:

```python
def claim_job(db, kind: str, owner: str, lease_seconds: int = 300):
    now = datetime.utcnow()
    return db.jobs.find_one_and_update(
        {"kind": kind, "state": {"$in": ["pending", "leased"]},
         "$or": [{"lease_expires_at": None}, {"lease_expires_at": {"$lt": now}}]},
        {"$set": {"state": "leased", "lease_owner": owner,
                  "lease_expires_at": now + timedelta(seconds=lease_seconds)},
         "$inc": {"fence": 1, "attempts": 1}},
        sort=[("created_at", 1)],
        return_document=ReturnDocument.AFTER,
    )
```

Workers heartbeat by extending `lease_expires_at` while holding the same `fence`; a write
carrying a stale `fence` is rejected. Jobs are inserted **inside the same transaction** as the
domain change that warrants them.

### 4.4 Batch ingestion with a full page manifest

```python
import pypdfium2 as pdfium   # pinned; do NOT use fitz

@admin_router.post("/api/admin/exams/{exam_id}/batches")
async def create_batch(exam_id: str, file: UploadFile = File(...),
                       user=Depends(require_role("admin")),
                       db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    pdf_bytes = await file.read()
    original_key = _upload_named(f"batch-{uuid.uuid4()}.pdf", pdf_bytes,
                                 content_type="application/pdf")   # bytes first, outside the txn

    doc = pdfium.PdfDocument(io.BytesIO(pdf_bytes))
    page_count = len(doc)
    batch_id = str(uuid.uuid4())

    with db_adapter.unit_of_work() as s:
        db_adapter.db.batches.insert_one({
            "_id": batch_id, "exam_id": exam_id,
            "original_pdf_key": original_key,
            "original_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
            "page_count": page_count,
            "expected_sheet_count": None,   # admin may set; mismatch is flagged, not silently accepted
            "state": "rendering", "created_at": datetime.utcnow(),
        }, session=s)

        # EVERY page gets a record up front, including ones that will later be rejected.
        sheets = [{
            "_id": str(uuid.uuid4()), "batch_id": batch_id, "exam_id": exam_id,
            "page_index": i, "state": "pending_render",
            "student_id": None, "rejection_reasons": [],
            "created_at": datetime.utcnow(),
        } for i in range(page_count)]
        db_adapter.db.sheets.insert_many(sheets, session=s)

        db_adapter.db.jobs.insert_many([{
            "_id": f"job_{uuid.uuid4()}", "kind": "render_sheet",
            "batch_id": batch_id, "sheet_id": sh["_id"],
            "state": "pending", "attempts": 0, "max_attempts": 5,
            "lease_owner": None, "lease_expires_at": None, "fence": 0,
            "idempotency_key": f"render:{batch_id}:{sh['page_index']}",
            "created_at": datetime.utcnow(),
        } for sh in sheets], session=s)

    return {"batch_id": batch_id, "page_count": page_count, "state": "rendering"}
```

The render/grade worker then, per sheet: rasterize that page at 300 dpi → run
`_validate_layout` → on any blocking reason set `state="rejected_layout"` with reasons and
stop; otherwise run `process_omr_sheet`, open `review_tasks` for ambiguous bubbles exactly as
`beta.py` already does, and set `state="pending_identity"`.

**Factor the crop/review-task creation out of `beta.py` into a shared service** both the old
route and the worker call — do not copy-paste it. The old inline route is retired once the
admin UI cuts over (Gap D: never leave two grading paths live).

### 4.5 Identity: manual first, OCR later, roster always authoritative

```python
@admin_router.post("/api/admin/sheets/{sheet_id}/identity")
def confirm_identity(sheet_id: str, req: IdentityConfirmRequest,
                     user=Depends(require_role("admin")),
                     db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    with db_adapter.unit_of_work() as s:
        student = db_adapter.db.students.find_one(
            {"_id": req.student_id, "exam_class": req.exam_class}, session=s)
        if not student:
            raise HTTPException(404, "Unknown student for this class.")

        # One student, one sheet per exam — a second match is a conflict, not an overwrite.
        clash = db_adapter.db.sheets.find_one(
            {"exam_id": req.exam_id, "student_id": req.student_id}, session=s)
        if clash and clash["_id"] != sheet_id:
            raise HTTPException(409, f"Student already matched to sheet {clash['_id']}.")

        updated = db_adapter.db.sheets.find_one_and_update(
            {"_id": sheet_id, "student_id": None},           # only ever claims an unclaimed sheet
            {"$set": {"student_id": req.student_id,
                      "identity_method": "admin_manual",
                      "identity_confirmed_by": user.user_id,
                      "identity_confirmed_at": datetime.utcnow(),
                      "state": "identified"}},
            session=s, return_document=ReturnDocument.AFTER)
        if not updated:
            raise HTTPException(409, "Sheet already resolved or not found.")

        db_adapter.db.audit_events.insert_one({
            "kind": "identity_confirmed", "sheet_id": sheet_id,
            "student_id": req.student_id, "actor": user.user_id,
            "at": datetime.utcnow()}, session=s)
    return {"status": "confirmed", "sheet_id": sheet_id}
```

Roll numbers are scoped by `exam_class` everywhere, so a roll number reused in another class
or year cannot cross-link records. OCR (Phase 1) sits *in front of* this endpoint and
auto-confirms only a unique exact scoped-roll match with compatible name evidence; everything
else lands in this same queue. OCR never creates a student and never issues an account.

### 4.6 Accounts via Keycloak

- Add `admin` and `student` realm roles; add a public browser client with Authorization Code
  + PKCE (the blueprint's §1.1 choice, and `cde/auth.py` already validates against JWKS).
- Admin provisions one Keycloak user per roster row and issues a temporary credential that
  Keycloak forces the student to replace on first login.
- Persist the mapping immutably: `{ "keycloak_sub": "...", "student_id": "...", "exam_class": "..." }`.
- **Enforce ownership server-side on every student endpoint**, not in the UI. Students must
  never reach the original class PDF, another student's evidence, review queues, or an
  arbitrary GridFS id — the current `GET /api/images/{file_id}` is an unscoped GridFS read and
  must be gated or removed before any student account exists.

### 4.7 Publication gate + student view

A report publishes only when: identity resolved **and** every bubble resolved **and** the
grade committed as a revision. (Diagnostics join this gate in Phase 1.)

```python
@student_router.get("/api/student/me/result")
def my_result(exam_id: str, student_id: str = Depends(current_student_id),
              db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    report = db_adapter.db.reports.find_one(
        {"exam_id": exam_id, "student_id": student_id, "state": "published"})
    if not report:
        return {"status": "processing", "can_upload_rough_work": True}
    return {"status": "ready", "score": report["score"], "max_score": report["max_score"],
            "answers": report["answers"], "revision": report["revision"]}
```

Note `can_upload_rough_work: True` during processing — per §1, students supply evidence
*before* results are visible, which is what unblocks Phase 1's diagnostics.

### Phase 0 gate

- A ~45-page PDF has **every page accounted for** — graded, rejected, or pending — with none
  dropped, merged, or overwritten.
- Unresolved sheets publish nothing.
- A confirmed student sees only their own finalized score.
- Duplicate uploads, a duplicate sheet for one student, and job retries cannot overwrite results.
- **Kill workers mid-batch and mid-review-resolution**; no work or decision is lost on restart.
- Page 1 and page 4 of the labeled batch both stay at low flag counts simultaneously.

---

## 5. Phase 1 — complete the diagnostic pilot

1. OCR behind manual matching; enable auto-accept only after evaluating labeled identities
   including conflicts and unknown students.
2. Admin-verified question map: question number → paper page/crop (diagrams and options
   included). Extend `cde/diagnostics.py` to receive those images alongside finalized choices
   and verified rough-work evidence — **preserving its existing provenance and abstention
   checks exactly**; do not loosen them to produce fuller-looking reports.
3. Route the existing rough-work UI through durable diagnostic jobs; retire any duplicate,
   more permissive inference path.
4. Publish complete diagnostic reports, finalized-grade cohort comparisons (disclosing
   coverage, e.g. `38/45 graded`), and PDF download.

**Gate:** absent / illegible / unmapped / contradictory rough work, provider failures, and
late or repeated uploads all behave correctly. Abstention survives. A provider outage is
**not** evidence-based abstention — retry, or hold an admin-visible failure state. Topic
insights and recommendations explicitly report *unavailable* rather than rendering empty
"personalization."

## 6. Phase 2 — content-dependent personalization

Blocked on content, not code. Admin validates a bounded topic taxonomy and tags the exam's
questions; curate a small practice bank with validated answers, solutions, topic tags, and
intended error targets; connect the preserved filters/ranking in `cde/retrieval.py` to
versioned embeddings, and wire `build_remediation` (currently a no-op stub in
`cde/activities.py`) to call `select_questions()`. Return "no suitable practice available"
when filters yield nothing — never relax relevance silently. In-memory ranking is fine for a
small curated bank; a vector index is a growth change, not a pilot dependency.

## 7. Release discipline

- Expand the 10-page set into labeled fixtures with held-out scans. Track **confidently
  wrong** separately from review rate. Block release on any known confidently-wrong case.
  Make no forward-looking zero-error claim.
- Test against real Mongo transactions, concurrent review claims, expired leases, answer-key
  revisions, and student-access isolation — not mocks. (The audit found the existing suites
  are mock-only and that Gamma never delivered test suites at all.)
- Restore from backup before real student use; document artifact access, retention, deletion.
- **One integration owner.** Components may be built separately, but "done" means the real
  vertical flow passes — not an activity returning `{"status": "ok"}`.
