# CDE App: Project Status & Handoff

This document outlines exactly what has been built in the `cde_app` directory so far, and the remaining tasks required to complete the Cognitive Diagnostic Engine.

## 1. What We Have Done (Completed)

### Core Architecture & Baseline
* **Baseline Secured:** The FastAPI backend and React frontend are wired together and running.
* **Database Patching:** The MongoDB adapter (`cde/db.py`) was patched to gracefully handle local standalone MongoDB instances by bypassing replica-set transactions.
* **Mock State Engine:** Built a time-aware offline mock engine in `cde/routes/beta.py` to simulate Temporal workflow state transitions (Processing -> Requires Admin Review -> Graded) for local UI testing.

### Rough Sheet Analytics (Formative Assessment)
* **Architectural Blueprint:** Finalized a 5-phase plan to shift from rigid summative grading (OpenCV bounding boxes) to unstructured formative grading using Gemini 1.5 Pro to diagnose *why* a student failed.
* **Frontend UI Built:** 
  * `RoughSheetDropzone.tsx`: Dropzone for students to upload full rough sheets.
  * `StudentExamView.tsx`: View tying the rough sheet upload to the specific exam submission.
  * `TeacherDashboard.tsx`: Dashboard containing the Class Insights view (aggregating dynamic organic errors like "Sign Error" or "Conceptual Deficit").
* **Backend Mocks:** Added the mock FastAPI endpoints (`/rough-sheets`, `/insights`, `/submissions`) to `beta.py` to power the React UI.

### AI Integration & Resilience
* **Gemini SDK Upgrade:** Updated the Python environment to `google-genai>=2.0.0` to support the new `client.interactions.create` API for both Gemini Vision (understanding) and Nano Banana (generation).
* **HITL Fallback Design:** Architected the Human-In-The-Loop fallback loop. If Gemini fails (e.g., 429 Quota Exceeded or illegible handwriting), the rough sheet enters a "Failed Diagnostics Queue" for manual admin override or retry.

---

## 2. What Is Left (Next Steps for the Target Model)

### Step 1: Real AI Workflow Integration
* Replace the mock implementation with a real Temporal workflow activity (`diagnose_rough_sheet_if_present`).
* Use the new `client.interactions.create` (google-genai v2) syntax to pass the raw rough sheet image to `gemini-3.1-pro-preview` or `gemini-3.8-flash`.

### Step 2: Admin Fallback Dashboard (HITL)
* **Backend:** Build the `POST /api/submissions/{id}/rough-sheets/retry` and `/override` endpoints.
* **Frontend:** Create an `AdminDiagnosticsQueue.tsx` view where teachers can manually view failed AI attempts, type in a custom error explanation, and save it directly to the database.

### Step 3: Production Database Aggregations
* Move the mock `/insights` endpoint into production by implementing the real MongoDB `$group` aggregation pipeline to dynamically cluster AI-generated `error_type` strings across the class.

### Step 4: Secure Object Storage
* Move the image storage layer from local disk saving (`mock_s3_storage`) to actual AWS S3 or Google Cloud Storage presigned URLs.

---

## 3. Cascade Pipeline Merge (Deterministic OMR)

The `MOCK_STATES` mock engine described above has been removed. `cde/routes/beta.py`
now does real, deterministic OMR grading instead of simulating workflow states.

* **`cde/omr_engine/`** (new) — the Adaptive Matrix-Crop bubble-detection logic
  from the standalone `biome_omr.py` research script, ported into a single
  async-callable function: `process_omr_sheet(image_bytes, exam_answer_key) -> OMRResult`.
  No disk I/O; runs the CPU-bound detection in a thread executor so it doesn't
  block the event loop. Geometry/thresholds are unchanged from the research
  script and are still provisional — see `OMRResult.limitations`.
* **`POST /api/omr/upload`** (new) — accepts `exam_id`, `student_id`,
  optional `submission_id`, and an image file. Saves the raw sheet to GridFS,
  runs `process_omr_sheet`, compares against `exam.answer_key`, and writes
  `score` / `max_score` / `answers[]` onto the `submissions` collection.
  Any bubble the detector can't confidently resolve (ambiguous / multiple /
  low-confidence) is cropped, saved to GridFS, and opens a document in
  `review_tasks` instead of being guessed.
* **HITL queue is now real.** `GET /api/review-tasks`, `POST
  /api/review-tasks/{id}/resolve`, `/claim`, `/renew`, and `GET
  /api/evidence/{crop_id}` all read/write the `review_tasks` collection and
  GridFS — matching the `ReviewTask` / `ResolutionCommand` contract already
  defined in `web/src/api/contracts.ts` and consumed by
  `features/admin/HitlQueue.tsx`. No frontend changes were needed.
* **Storage:** `cde/storage.py` gained `upload_named()` so each ambiguous
  crop gets its own GridFS file (a submission can have several). Still
  GridFS-only — no S3/disk.
* **Still a placeholder, as intended:** `build_remediation` in
  `cde/activities.py` (Phase 5 / Question Bank) is untouched — it still just
  returns `{"status": "ok"}`.
* **Not touched by this merge:** the existing fiducial-marker OMR pipeline in
  `cde/omr.py` / `cde/omr_adapter.py` (a separate, more rigorous multi-page
  PDF pipeline than the single-image BIOME layout this merge wires up), and
  the outbox/Temporal-replacement orchestration for `start_grading_workflow`
  (the `prepare_and_read` activity is still a stub — nothing currently
  consumes that outbox event end-to-end). If the two-step
  `/api/exams/{id}/uploads` → `mock-s3-upload` → `/api/uploads/{id}/complete`
  flow needs to produce a graded submission too, point its background/outbox
  handler at `cde.omr_engine.process_omr_sheet` the same way
  `POST /api/omr/upload` does.
