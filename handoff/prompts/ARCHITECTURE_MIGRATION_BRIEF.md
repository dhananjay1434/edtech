# Cognitive Diagnostic Engine — Architecture Audit & Migration Brief

**Purpose of this document:** this is a handoff prompt for a larger-parameter model. It contains (1) what the product is supposed to be, in the owner's own words, (2) what the original written blueprint specified, (3) what actually exists in the codebase today, verified by reading the code directly, and (4) every place those three disagree. Your job, as the receiving model, is to produce a **new, restructured architecture and migration plan** — not a rewrite of this document — that reconciles all three and gets the project back on a coherent path to the owner's actual target, in priority order. Do not assume the original blueprint is correct where it conflicts with the owner's stated intent below; the owner's intent in Section 1 is the source of truth for product decisions. Do not assume the codebase is correct just because it exists; a lot of it was produced by a multi-agent swarm that partially failed (see Section 4).

---

## 1. The product, in the owner's own words (verbatim intent — source of truth)

This is a direct transcription of what the owner described wanting, unedited in substance:

- MVP has a **student portal** (individual student logins/accounts) and an **admin portal**. **No teacher portal in MVP.**
- Admin uploads **one PDF containing ~45 scanned OMR answer sheets** (a whole class's exam batch in one file), each sheet carrying the student's name, roll number, and other identifying info printed/handwritten on it.
- The system must **extract each student's name and roll number from their sheet** and match/create the corresponding student record — this is required, not optional, and it's a batch of 45 sheets per PDF, not one sheet per upload.
- The system performs **OMR** on each sheet to determine which option the student marked for each question.
- The system then produces **detailed performance analysis** for each student: how they did relative to the class, and specifically **what *types* of questions/topics they are making mistakes on** — this is meant to feed personalization.
- Separately, the **student** (via their portal) uploads their **raw rough work** (scratch paper / working) for the exam.
- That rough work, together with **the original question paper** and **the student's answer/option choices**, is sent to a **multimodal model** capable of analyzing images. The model must look at (a) the question, (b) the student's chosen answer, and (c) the actual handwritten working, and diagnose **how** the student approached the question and **why** they went wrong — e.g. conceptual error (wrong formula/concept applied), arithmetic/calculation error, procedural/approach error.
- This produces a **more detailed, personalized diagnostic** beyond the class-level analysis: e.g. "you have a conceptual gap — go learn formula X" vs. "you have a calculation-accuracy problem — here's practice for that."
- The student receives a **detailed report**: personalized attention, overall performance, and the specific diagnostic breakdown above.
- Finally, there is a **question bank** with **semantic search**: based on the student's diagnosed weaknesses (topic + error type), the system selects and serves **personalized practice questions** targeting exactly what they're getting wrong.

This is the target. Everything below is measured against it.

---

## 2. The originally written blueprint (what the project's own design docs specify)

The repository ships a ~2,700-line design document (`docs/cognitive_diagnostic_engine_blueprint.md`, duplicated as `reference/source.md`) plus a large multi-agent execution pack (`docs/tri_agent_execution_pack.md`, `docs/agent_alpha_prompt.md`, `docs/agent_beta_prompt.md`, `docs/agent_gamma_prompt.md`, `docs/cde_worker_prompts.md`). Key specified decisions:

### 2.1 Stack (as specified)
| Layer | Specified choice |
|---|---|
| Workflow engine | Temporal (Python SDK) |
| Backend | Python 3.12 + FastAPI + Pydantic 2 |
| Database | **PostgreSQL 16 + pgvector** (explicitly: *"PostgreSQL is intentional... this document does not retrofit the surrounding editor's starter application or its database"*) |
| DB driver | psycopg 3 + psycopg_pool |
| Migrations | Alembic |
| PDF rasterization | pypdfium2 |
| Computer vision | OpenCV headless + NumPy |
| Vision-language model | **OpenAI `gpt-5.4`**, Structured Outputs |
| Embeddings | **OpenAI `text-embedding-3-small`** |
| Vector store | **pgvector inside Postgres** |
| Object storage | Private Amazon S3 |
| Email | Resend |
| PDF generation | ReportLab Platypus |
| Frontend | React + TS + Vite + shadcn/ui + TanStack Query |
| Auth | **Keycloak via OIDC** (institutional identity) |
| Telemetry | OpenTelemetry → Grafana Cloud |

### 2.2 Non-negotiable invariants (§2.2 of the blueprint — these are good and should likely survive any rewrite)
- **Scores never depend on AI.** Grading uses only finalized answers + a versioned answer key.
- **No uncertain answer is guessed.** Ambiguous bubble density, bad alignment, or unresolved identity blocks grading for that sheet and routes to human review.
- **No implied cognition without evidence.** The diagnostic model must abstain (not classify) when rough work is absent, illegible, unmapped to a question, or contradictory.
- **No lost sheet / no lost human decision** — submission creation and workflow-start commit in one transaction; review resolutions commit atomically with the resulting state change.
- **Every AI classification is inspectable** — crop coordinates, hashes, prompt/schema/model version, and the raw model response are all persisted.
- **Safe reprocessing** — re-running a stage creates a new revision; it never silently overwrites a published report or re-sends an email.
- Four fixed error classes for diagnostics: **Arithmetic Slip, Procedural Flaw, Conceptual Deficit, Unknown** — plus `abstained`, which the doc is explicit is a *decision status, not a fifth error class*.

### 2.3 Explicit assumptions that conflict with the owner's MVP (§2.1) — **flag these for reconciliation, don't silently keep or drop them**
1. *"Every uploaded file is one student's submission... every page must belong to the same identified student."* — **This directly contradicts the 45-sheets-per-PDF requirement in Section 1.** The blueprint has no concept of a batch/multi-student upload.
2. *"A manifest or a validated printed barcode maps the sheet to an enrolled student. Handwritten identity or a conflicting barcode requires human identity review. Never select the nearest matching name automatically."* — the owner wants automatic name/roll extraction; the blueprint wants barcode-first identity with mandatory human review on anything else. These need to be reconciled (see Section 5, Gap A).
3. *"Students are initially verified email recipients, not browser users. Adding a student portal... requires a separate authorization migration, not merely a new UI filter."* — the owner's MVP requires a full student portal with individual logins on day one. The blueprint's auth model (Keycloak OIDC) was designed only for institutional staff (educators/reviewers/operators), not students.
4. The blueprint's pipeline has **no node at all** for "ingest the original question paper as an image input to the multimodal diagnostic call" — it only ever sends rough-work crops + the student's finalized answer + question *text/context*, not a rendered image of the question paper page. The owner's requirement to feed the question paper image itself into the multimodal model is new.

### 2.4 Phased roadmap (§18, as specified)
```
Phase 0  paper contract, template, identity protocol           1-2 wk
Phase 1  deterministic grading + durable review (Temporal)     2-3 wk   <- "first useful product milestone"
Phase 2  evidence-grounded diagnostics (vision model)           2-3 wk
Phase 3  cohort insight + targeted practice (retrieval)         2 wk
Phase 4  delivery + operational hardening (email, PDF, backups) 1-2 wk
Phase 5  controlled institutional pilot                         2-4 wk
```
Explicit instruction: *"Do not block grading on AI or email integrations."*

### 2.5 Multi-agent build split (as specified in the execution pack)
The build was divided across three agents with disjoint file ownership (`contracts/ownership.json`):
- **alpha**: `cde/api.py`, `cde/config.py`, `cde/db.py`, `cde/auth.py`, `cde/migrate.py`, `contracts/**`, `infra/**`
- **beta**: `cde/omr.py`, `workflows/**`
- **gamma**: `cde/diagnostics.py`, `cde/reports.py`

Source precedence for resolving conflicts (`contracts/source-precedence.md`): operator amendments > execution pack > worker pack > blueprint.

---

## 3. What is actually in the codebase (verified by direct inspection, not inferred)

### 3.1 Stack actually used (diverges from §2.1 in three major ways)
| Layer | Blueprint said | Code actually has |
|---|---|---|
| Database | PostgreSQL 16 + pgvector | **MongoDB** (`pymongo`) + **GridFS** for blob storage. `cde/db.py` wraps sessions in `unit_of_work()`, but falls back to *no transaction at all* when the Mongo instance isn't a replica set (`check_replica_set()` → non-replica-set path just `yield session` with no `start_transaction`). Locally this means **the transactional invariants in §2.2 are not actually enforced** unless deployed against a real replica set. |
| Diagnostic vision model | OpenAI `gpt-5.4` | **Google Gemini**, via `google-genai`. Model id read from `GEMINI_DIAGNOSTIC_MODEL` env var. `cde/diagnostics.py` is otherwise a faithful, well-built implementation of the blueprint's evidence/abstention contract (see 3.5). |
| Embeddings | OpenAI `text-embedding-3-small` | **Gemini `text-embedding-004`** (`cde/embeddings.py`, `cde/retrieval.py`). |
| Auth | Keycloak OIDC for everyone | `cde/auth.py` **is** real Keycloak OIDC (JWT validation via `PyJWKClient`, role/assignment model) — but it is wired for institutional staff only. `web/src/auth.ts` is a **literal empty stub**: `export const auth = { /* Institutional OIDC client skeleton */ }`. There is no student-facing auth of any kind. |
| Object storage | Private S3 | GridFS only. `s3_*` settings exist in `cde/config.py` but nothing reads/writes S3. |
| Workflow engine | Temporal, fully orchestrating every stage | Temporal scaffolding exists (`cde/workflows.py`, `cde/activities.py`, `cde/worker.py`, `cde/dispatcher.py`) but the **live/working code path bypasses it entirely** (see 3.3). |
| Email (Resend) | Required for Phase 4 | Not integrated at all. `cde/email.py` exists but nothing calls it from a live route. |
| PDF report generation | ReportLab | `cde/report.py` exists but is not wired to any route that a user can trigger. |

### 3.2 Multi-agent handoff outcome (verified from the agents' own handoff notes)
`handoff/beta/open-gaps.md`:
> "1. Alpha DB Adapters: Waiting for Alpha to provide real UnitOfWork and MongoDB implementations. 2. Gamma Integration: Waiting for Gamma to supply post-grade review handlers and its required Temporal child workflows (`diagnose_question`, `build_remediation`). 3. Integration Tests: Due to missing Alpha dependencies, real replica-set tests are blocked. Mocked unit tests were used instead."

`handoff/merger/open-gaps.md`:
> "1. Gamma failed to implement test suites. 2. Gamma failed to implement activity bundles and review handlers, which the Merger had to stub."

Consequence, verified directly in `cde/activities.py`: **six activity functions are literal no-ops**, each body is exactly:
```python
return {"status": "ok"}
```
This includes `build_remediation` (the question-bank/remediation step) and the diagnose-related child-workflow activities gamma was supposed to deliver. The durable-workflow spine that is supposed to hold the whole pipeline together (per §6 and §13 of the blueprint) is a shell with no real logic behind most of its nodes. There are also **no test suites** at all for OMR, diagnostics, or workflows — searching for `*test*omr*` returns nothing; `tests/` exists (`tests/alpha`, `tests/beta`, `tests/gamma`, `tests/contracts`) but per the handoff notes these are mocked-dependency unit tests, not the golden-dataset/integration suites §17 of the blueprint requires.

### 3.3 What is actually live and working end-to-end (verified against `cde/routes/beta.py`)
A **separate, inline, non-Temporal path** was built later (per `PROJECT_STATUS.md`, described as "Cascade Pipeline Merge") that replaced an earlier pure-mock engine:

```
POST /api/omr/upload                                real: grades one image inline, writes to Mongo/GridFS
GET  /api/review-tasks                               real HITL queue
POST /api/review-tasks/{id}/claim|renew|resolve      real, with lease semantics
GET  /api/evidence/{crop_id}                         real crop serving from GridFS
POST /api/exams/{id}/submissions/{id}/rough-sheets   real upload endpoint
GET  /api/admin/diagnostics-queue                    real
POST /api/submissions/{id}/rough-sheets/retry|override  real, admin fallback for failed AI diagnosis
GET  /api/exams/{id}/insights                        real Mongo $group aggregation by error_type
GET  /api/exams/{id}/submissions                     real
GET  /api/images/{file_id}                           real GridFS image serving
```

This path **does not go through Temporal at all** — it calls `cde/omr_engine/engine.py`'s `process_omr_sheet()` directly from the FastAPI route handler, in a thread executor. It is the only part of the system that a real user flow can currently exercise end-to-end (upload one sheet → get graded → ambiguous bubbles queue for human review → resolve → see the score).

Meanwhile `cde/routes/alpha.py` — which is supposed to own the exam/upload lifecycle per `contracts/ownership.json` (`POST /exams/{id}/uploads`, `/uploads/{id}/complete`, `/mock-s3-upload/...`) — still just returns `{"status": "ok"}` for its core actions and does not connect to `omr_engine`. **There are two disconnected upload paths in the codebase and neither is the batch/PDF path the owner needs.**

### 3.4 The OMR engine itself — two implementations, verified by reading both files
- **`cde/omr.py`** — the blueprint's §5 reference implementation. Template-driven (JSON spec, `load_template()`, `validate_template()`), uses **4 fiducial corner markers + 1 asymmetric orientation marker** for perspective alignment (`align_page()`, `corner_centers()`), and has an explicit `identity_cut()` function that **deliberately strips the top 15% of the sheet (the name/ID block) before any image reaches an LLM**, per `docs/deep_business_logic_patch.md` Patch 2's PII requirement. `render_pages()` hard-caps at `max_pages=10` and requires `1 <= page_count <= max_pages` — **this alone makes a 45-sheet single PDF impossible to ingest through this module as written.** This module is layout-agnostic (works for any exam whose template is registered) but is **not wired to any live route** — it is dead code from the current API's point of view.
- **`cde/omr_engine/`** — a ported research script (originally `biome_omr.py`), self-calibrating against the marks a student actually made rather than a fixed template. This is what `POST /api/omr/upload` actually calls. It has hardcoded layout constants for one specific answer-sheet design:
  ```python
  W_REF, H_REF = 992.0, 1347.0
  PANEL_LEFTS = [70, 237, 405, 578, 756]      # exactly 5 panels
  OPTION_OFFSETS = [49, 83, 117, 151]         # exactly 4 options
  N_ROWS, N_PANELS = 36, 5                    # exactly 180 questions
  ```
  It has **no concept of student identity, name, or roll number at all** — it is called with a `student_id` already known and supplied by the caller. It has no fiducial/orientation-marker recovery and no PII-stripping step (there is no PII step needed because it never looks at an identity region — the caller is assumed to already know whose sheet this is).

  **Recent verified accuracy work on this engine** (done in this session, against a real labeled 10-page test batch): four calibration bugs were found and fixed — (1) independent per-row clustering that could cascade-shift and drop the last row, fixed with a global evenly-spaced line fit; (2) a whole-panel horizontal shift collapsing one option column onto another, fixed the same way on the x-axis; (3) panel rotation/skew (15-20px drift top-to-bottom), fixed with `_fit_skewed_options()`; (4) a stray handwritten digit in an "Exam Date" box below the grid being misdetected as a filled bubble and dragging an entire panel's row-fit off by ~180px, fixed with a footer cutoff mirroring the existing header cutoff. Result on the labeled page: **175/180 correct (97.2%), 0 wrong answers, 5 correctly flagged for human review.** Across a 10-page batch, 9 of 10 pages sit around ~2-3% flagged-for-review; **one known, diagnosed, not-yet-fixed regression**: page 1 of that batch regressed to 79/180 flagged after a header-cutoff threshold was loosened (from a density-relative check `diffs[i] >= max(4.0*median_gap, 0.01*h)` to a bare absolute `diffs[i] >= 0.03*h`) to fix the page-4 footer bug — the fix that solved page 4 broke page 1's header detection because it removed the density-relative guard against latching onto the wrong internal gap inside the identity/info block. The fix is understood (restore the density check alongside the absolute one, e.g. `diffs[i] >= 0.03*h and diffs[i] >= 2.5*median_gap`) but not yet applied/re-verified.

  **Critical limitation to carry into the redesign:** because everything is compiled into module-level constants for one exact layout, feeding this engine a differently-shaped sheet (different question count, different option count, different panel count, different aspect ratio) will **not error out** — it will silently sample the wrong pixels and confidently return a full set of wrong answers. There is no layout-mismatch detection at all in this path.

### 3.5 Diagnostics module — the strongest, most faithful piece of the codebase
`cde/diagnostics.py` is a genuinely solid implementation of the blueprint's evidence-and-abstention contract, just on Gemini instead of OpenAI:
- Strict Pydantic models with `model_config = ConfigDict(extra="forbid", allow_inf_nan=False)`.
- Verifies rough-work crop hashes against what's stored before trusting them (`_load_verified_crops`).
- `_supported_evidence()` gates whether a classification is allowed to stand.
- `_abstain(reason, evidence)` is a first-class return path, not an afterthought.
- Confidence is zeroed (`model_copy(update={"confidence": 0.0})`) when evidence support fails, rather than trusting the model's self-reported confidence.
- Records `returned_model` (the actual model version string the provider returned) for provenance, separate from the requested `model_id`.

**However**, per the owner's Section 1 requirement, this module currently does **not** ingest an image of the original question paper — only `question_context` (implied to be text) plus rough-work crops plus the student's finalized answer. This is a real gap against the owner's target, not just against the original blueprint.

### 3.6 Retrieval / semantic search — algorithm exists, bank and wiring do not
`cde/retrieval.py` and `cde/embeddings.py` contain a real, reasonably careful implementation:
```python
MODEL = "text-embedding-004"
def cosine_distance(a, b): ...
def eligible(candidate, original, error_class, ...)   # hard policy filters — rejects mismatched embedding model, wrong error class, etc.
def select_questions(..., query_vector, ...)          # ranked, deduplicated by question family
```
This is close to what Section 1's "semantic search over the question bank, filtered by diagnosed weakness" needs conceptually. What's missing: (a) there is no actual populated question bank with embedded content anywhere in the repo, (b) `cosine_distance` runs in-memory over whatever candidates are passed in — there is no vector index (fine at small scale, will not scale to a real bank), (c) nothing calls this from a live route — `build_remediation` (the activity meant to trigger it) is one of the six no-op stubs in `cde/activities.py`.

### 3.7 Rough-sheet / formative-diagnostics feature — built ahead of its dependencies
There is a fully-fleshed-out formative-assessment feature (`docs/rough_sheet_diagnostics_blueprint.md`, `cde/routes/beta.py` rough-sheet endpoints, `web/src/features/student/RoughSheetDropzone.tsx`, `web/src/features/admin/RoughSheetAdminQueue.tsx`) that is architecturally very close to what Section 1 describes for the rough-work diagnostic step — upload rough sheet → send whole page + wrong-answer list + question context to Gemini in one pass → structured `DiagnosticResult` per question → Mongo aggregation for class-wide insight. This is good, real work. But it was built **on top of a student-identity and batch-upload foundation that does not exist yet** (see 3.3/3.4) — right now every rough-sheet upload has to be pointed at a `submission_id` that some other, currently-nonexistent flow would have had to create first via the 45-sheet batch + identity-extraction path.

### 3.8 Frontend — built for the wrong role split relative to the MVP
```
web/src/features/teacher/   TeacherDashboard.tsx  TeacherUploadBay.tsx  SubmissionStatus.tsx
web/src/features/student/   StudentExamView.tsx  StudentDiagnosticView.tsx  RoughSheetDropzone.tsx
web/src/features/admin/     HitlQueue.tsx  RoughSheetAdminQueue.tsx
web/src/pages/              OperatorPage.tsx  ReviewPage.tsx  SubmissionPage.tsx
web/src/auth.ts              <- empty stub, no real auth client for anyone
```
Per Section 1, MVP should have **student + admin only, no teacher**. `TeacherUploadBay.tsx` in particular is likely where the 45-sheet batch upload was meant to eventually live conceptually — it may be salvageable as the *admin* upload surface rather than thrown away, but the role boundary needs to be redrawn. `OperatorPage.tsx` is the closest existing thing to an admin home but is not confirmed to cover the identity-review queue this design needs (Gap A below).

---

## 4. Summary: how far off is the codebase from the owner's stated MVP?

| Owner requirement (Section 1) | Status | Evidence |
|---|---|---|
| Individual student login/accounts | **Not built** | `web/src/auth.ts` is an empty stub; `cde/auth.py` is staff-only Keycloak |
| Admin portal | **Partially built** | `OperatorPage.tsx` exists; scope vs. admin needs unconfirmed |
| No teacher access in MVP | **Contradicted by current build** | 3 teacher-specific components exist and appear to own the upload flow |
| Upload one PDF with ~45 OMR sheets | **Not possible today** | `cde/omr.py`'s `render_pages()` hard-fails past `max_pages=10`; live path (`cde/omr_engine`) takes one image + a pre-known `student_id`, no batch concept anywhere |
| Extract name/roll number per sheet | **Not built at all** | `cde/omr.py` has `identity_cut()` which *strips* the identity region rather than reading it; `cde/omr_engine` has no identity logic whatsoever |
| OMR grading (marked options) | **Working, verified accurate** | 97.2% exact, 0 wrong-answers on labeled test page; one known regression to fix; single-layout limitation |
| Per-student + class + by-topic/question-type analysis | **Partially built** | Class-level `$group` aggregation by error_type works (`/api/exams/{id}/insights`); no confirmed per-student report; no explicit "topic" taxonomy tying questions to subject-matter tags beyond the 4-class error taxonomy |
| Student uploads rough work | **Built** | Dropzone + upload endpoint + admin retry/override flow all real |
| Multimodal analysis: question + answer + rough work → diagnosis | **Partially built** | Model call + strict schema + abstention logic all real and solid; question-paper *image* is not currently part of the payload — only rough-work crops + finalized answer + (text) question context |
| Personalized report to student | **Not built** | `cde/report.py` exists but is not wired to any callable route; no student-facing report UI confirmed beyond `StudentDiagnosticView.tsx` |
| Question bank + semantic search + personalized practice questions | **Algorithm built, everything else missing** | `retrieval.py`/`embeddings.py` are real and reasonably careful; no populated bank; not wired — `build_remediation` activity is a no-op stub |

**Root cause pattern:** the project has meaningfully over-invested in Phase 2/3-equivalent work (Gemini diagnostics, class insights, retrieval math — all genuinely good code) while the Phase-0/Phase-1-equivalent foundation the owner's MVP actually opens on — **batch PDF ingestion, per-sheet student identity extraction, and student-facing auth** — is either unbuilt or actively designed against (the PII-stripping `identity_cut()` and the one-file-one-student assumption both work *against* what the owner wants, not merely absent). Every downstream feature (analysis, rough-work diagnosis, reports, question recommendations) is keyed to a student identity that no current code path produces from a batch upload.

---

## 5. Specific gaps and internal contradictions to resolve (not an exhaustive fix list — a reconciliation checklist)

**Gap A — Identity extraction vs. the blueprint's anti-automation stance.** The owner wants automatic name/roll extraction from each of the 45 sheets. The original blueprint explicitly forbids "select the nearest matching name automatically" and wants barcode-first identity. These are not actually incompatible if separated correctly: OCR/read the identity region locally (never send it to the multimodal model — keep the PII-stripping instinct from `identity_cut()`, just repurpose it as "read-then-strip" instead of "strip-and-discard"), match against an enrolled roster, auto-accept only above a high-confidence exact/near-exact threshold, and route everything else (no match, multiple matches, illegible) to an admin identity-resolution queue before grading proceeds for that sheet. Design this explicitly rather than picking one side.

**Gap B — Batch upload has no home.** Neither `cde/routes/alpha.py` (owns uploads per `contracts/ownership.json`, but is stubbed) nor `cde/routes/beta.py` (has the only working OMR call, but takes one image + known `student_id`) can accept a 45-page PDF today. A new ingestion stage is needed: PDF → page-render → per-page segmentation into individual sheet images → per-sheet identity resolution (Gap A) → per-sheet OMR grading, with the batch as a whole tracked as one job with N sub-results (some sheets may need identity review, some may need bubble review, independently of each other).

**Gap C — Which OMR engine is the real one going forward.** `cde/omr.py` (template-driven, fiducial-marker based, general across layouts, currently unwired) vs. `cde/omr_engine/` (self-calibrating, high verified accuracy, currently live, hardcoded to one layout, no identity awareness). A decision is needed: extend `omr_engine`'s self-calibration approach into a template-parameterized form (best of both), or invest in wiring up `omr.py` properly and porting the accuracy fixes over. Recommend evaluating which approach handles Gap A/B's per-sheet segmentation more naturally.

**Gap D — Two disconnected upload paths already exist** (`alpha.py`'s stubbed exam/upload lifecycle vs. `beta.py`'s working inline grading). Any redesign should collapse these into one real path rather than adding a third.

**Gap E — Temporal workflow layer is currently decorative.** Six activities are literal `{"status": "ok"}` stubs, including the one meant to trigger remediation/question-bank selection. Decide deliberately whether Temporal is still the right orchestration choice given the live system currently works by bypassing it entirely, or whether a lighter-weight job/queue model better fits an MVP-stage batch-processing product (45-sheet PDF jobs, each with N independent sub-tasks that can independently need human review) — this is a real architectural decision, not just "finish implementing the stubs."

**Gap F — Student auth is a bigger lift than a UI change.** The blueprint itself warns this: *"requires a separate authorization migration, not merely a new UI filter."* `cde/auth.py`'s Keycloak/role/assignment model was built for staff. Decide whether students get their own Keycloak realm/client, a separate lightweight auth system, or an extension of the existing one — and how student accounts get created in the first place (self-registration? admin-provisioned alongside the roster used for Gap A's identity matching? likely the latter, since the roster already needs to exist for name/roll matching).

**Gap G — Question paper is not part of the multimodal diagnostic payload.** `cde/diagnostics.py` needs to also receive a rendered image (or page crop) of the actual question, not just text context, to match the owner's stated requirement of the model reasoning over "the question, the answer, and the rough work" together as images.

**Gap H — Question bank does not exist.** Semantic search and retrieval-filtering code is ready and waiting for data; there is no question authoring/ingestion/embedding pipeline populating it, and no confirmed taxonomy connecting bank questions to topics/subtopics (needed for the "types of questions they're making mistakes on" analysis, not just the 4-class error taxonomy).

**Gap I — Reports and remediation delivery are unwired dead code**, not missing code — `report.py` and the remediation-selection path both exist in some form but aren't reachable by any live route.

**Gap J — Role/scope mismatch in the frontend** — teacher-specific UI was built for a role explicitly excluded from MVP; decide what to keep (likely repurpose as admin surfaces) vs. defer.

**Gap K — Mongo transactions are not actually enforced locally.** `unit_of_work()` silently no-ops the transaction wrapper when not connected to a replica set. If the blueprint's "no lost sheet / no lost human decision" invariants matter for the MVP (they should, especially once 45 sheets are batched per job), this needs either a guaranteed replica-set deployment or a different consistency strategy that doesn't silently degrade.

---

## 6. What is asked of you (the receiving model)

Using everything above:

1. Propose a **restructured architecture** that satisfies the owner's Section 1 intent as the primary requirement, keeping the blueprint's good invariants (§2.2) and the well-built existing pieces (diagnostics module, retrieval algorithm, HITL review queue, the now-97%-accurate OMR core) rather than discarding working code, while explicitly resolving Gaps A–K above with a stated decision for each (don't leave any of them open-ended).
2. Produce a **concrete migration plan**, in priority/dependency order, that gets from the current codebase state to that architecture — identify what to keep as-is, what to modify, what to remove, and what to build new, and be explicit about *why* something in the current build should or shouldn't survive.
3. State a **feature/growth phasing** appropriate to an actual MVP-then-grow trajectory (not necessarily the original blueprint's 5-phase plan, which was written before the owner's specific batch-upload/identity/student-portal requirements were known) — the target ratio should reflect getting the owner's full described flow (batch upload → identity → OMR → analysis → rough-work diagnosis → report → personalized question recommendations) working end-to-end for a small pilot as fast as responsibly possible, without violating the "no uncertain answer is guessed" / "no implied cognition without evidence" invariants.
4. Output your result as a **single, well-structured Markdown file**, written to be handed to an implementation team (or further agents) directly — not another audit, an actual forward-looking plan and architecture spec.
