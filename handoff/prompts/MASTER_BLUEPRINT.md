# Cognitive Diagnostic Engine — Master Implementation Blueprint

**Status:** Authoritative. Supersedes `IMPLEMENTATION_PLAN.md`, the earlier hardened plan, and
any conflicting statement in `docs/cognitive_diagnostic_engine_blueprint.md`.
**Scope:** One class, one JEE Main exam, ~45 students. Admin + student portals. No teacher role.
**Audience:** Implementers starting execution immediately.

**Source documents folded into this one:**
- `ARCHITECTURE_MIGRATION_BRIEF.md` — the code audit
- `ANSWERS_TO_CLARIFYING_QUESTIONS.md` — owner's confirmed constraints
- The detailed migration plan (received truncated at §18.2 — see §16 for what is missing)
- `PLAN_CORRECTIONS_VERIFIED.md` — four code-verified corrections, integrated below

---

## 0. The four corrections that change execution

These were found by reading the running code, not by reasoning from documents. Each one
invalidates a task in the earlier plans. **Read these before scheduling anything.**

### 0.1 The error taxonomy on paper is not the taxonomy in the code

Every design document says the four classes are *Arithmetic Slip / Procedural Flaw /
Conceptual Deficit / Unknown*. The running code (`cde/diagnostics.py:20-23`) says:

```python
ErrorClass = Literal[
    "Calculation Slip", "Procedural Flaw",
    "Reading Comprehension Error", "Conceptual Deficit",
]
```

`Reading Comprehension Error` exists in no design document. There is no `Unknown` class.
`cde/retrieval.py:9` filters on the **same four literals**, and the diagnostic prompt
(`cde/diagnostics.py:115-202`) carries worked few-shot examples per class.

**Decision: the code's four are canonical.** They are the only set with a validated prompt,
few-shot examples, and matching retrieval filters. Update
`docs/cognitive_diagnostic_engine_blueprint.md` §2.1 and
`docs/rough_sheet_diagnostics_blueprint.md` to match, in one edit. Divergence here guarantees
the model returns classes that retrieval silently rejects.

### 0.2 Abstention is already solved — do not migrate it

`Diagnostic` already separates decision status from error class, and enforces it with a
validator rather than convention:

```python
status: Literal["classified", "abstained"]
error_class: ErrorClass | None = None
abstention_reason: str | None = None
# validator: classified => class AND evidence AND no reason
#            abstained  => no class AND a reason
```

The invalid combinations are unrepresentable. Also already present and uncredited:
`MIN_CLASSIFICATION_CONFIDENCE = 0.90`, `PRIVACY_POLICY = "page1-top15-black-v1"` (the identity
redaction), and `Evidence.bbox` validated as normalized finite coords `0 <= x0 < x1 <= 1`.

**Action: delete any abstention-migration task.** Extend only the module's *inputs*.

### 0.3 Correct grading exists, is unwired, and the live path is wrong

`cde/grading_core.py` implements `marking_policy` (`correct_marks`/`wrong_marks`/`blank_marks`),
Decimal arithmetic with `ROUND_HALF_UP`, validates penalties are non-positive, refuses to grade
unless `identity_confirmed` **and** `alignment_confirmed`, refuses non-finalized answers, and
requires exact contiguous question coverage. That is negative-marking support plus most of the
publication predicate — already written.

**Nothing calls it.** Only `cde/grading.py` imports it; no route uses either. The live path
scores at `cde/omr_engine/engine.py:392-394` with `score += 1` per correct answer.

**Confirmed marking scheme: +4 correct / −1 wrong / 0 blank.** Consequences in §8.

### 0.4 The exam is JEE Main (~75 questions), not a 180-question paper

Every prior document mistook the BIOME sheet's 180-row *capacity* for the exam's question
count. It is a high-density institute sheet; this paper uses ~75 rows.

This creates a **hard incompatibility**: the engine unconditionally emits 180 results
(`TOTAL_QUESTIONS = N_PANELS * N_ROWS`, no question-count parameter), while `grading_core`
raises `ValueError` unless answers are exactly `1..question_count`. Neither module is wrong;
they were designed against different assumptions. See §8.2 for the fix.

**Open blocker:** JEE Main Section B is numerical/integer answer entry. The engine reads
exactly four option columns and cannot read a digit grid. **See §16.1 — this must be answered
before Phase 2 is scheduled.**

---

## 1. Confirmed constraints (owner)

| Area | Confirmed |
|---|---|
| Roles | Admin + student only. No teacher portal. |
| Paper | One page per student, one fixed layout (BIOME 5-panel). |
| Exam | JEE Main format, ~75 questions, **+4 / −1 / 0**. Max = 300. |
| Batch | One PDF containing the class's ~45 scanned pages. |
| Identity | Admin-preloaded roster is authoritative. OCR never creates students. |
| Access | Admin-issued credentials tied to roster records, independent of OCR. |
| Scale | One class, one exam. |
| Review | One admin, best-effort, **no SLA** — queues may sit indefinitely. |
| Hosting | No data-residency constraints. |
| Student UX | **No partial results.** Processing state until fully finalized. |
| Topic tags | Not authored. But subject ranges are free — see §10.3. |
| Practice bank | Does not exist. Blocked on content, not code. |

---

## 2. Release boundaries

### Release A — score-only walking skeleton
Roster import, admin-issued student accounts, batch PDF ingestion with full page accounting,
manual admin identity matching, fixed-layout OMR, bubble review, finalized **score-only**
reports under the real +4/−1 policy.

Excludes: OCR auto-accept, diagnostics, subject/topic analysis, practice.

### Release B — diagnostic pilot
Adds validated identity OCR (manual retained as fallback), admin-verified question-image
mapping, student rough-work upload before results are visible, evidence-grounded diagnosis or
explicit abstention, detailed reports, cohort comparison with disclosed coverage, **and
subject-level analysis** (§10.3).

Sub-topic analysis and practice remain visibly unavailable.

### Release C — content-enabled personalization
Admin-validated sub-topic tags, curated practice bank, versioned embeddings, targeted
retrieval, student practice delivery.

### 2.1 Version the publication policy

Persist `report_policy_revision` per exam: `score_only` | `diagnostic` |
`diagnostic_with_validated_content`. Enabling diagnostics later must not silently treat an old
score report as a completed diagnostic report. A policy change creates a new target report
revision; published artifacts stay immutable. The student endpoint serves only the current
target policy's finalized report — it never substitutes an older score report while a required
diagnostic report is pending.

---

## 3. Architecture

```text
React + TypeScript (Vite, Tailwind v4, keycloak-js)
├── Admin
│   ├── Roster + account issuance
│   ├── Exam / answer-key / marking-policy / question-map setup
│   ├── Batch upload + processing dashboard
│   ├── Review queues: layout, identity, bubble, diagnostic
│   └── Reports + cohort insight
└── Student
    ├── Keycloak login
    ├── Processing state + rough-work upload / "none available" declaration
    └── Finalized report (+ practice, Release C)

FastAPI  — thin routes: authn, authz, validation, service invocation only
Services — rosters, exams, batches, identity, grading, reviews, evidence, publication
Repositories — Mongo queries, indexes, transaction boundaries
Adapters — omr, identity_ocr, keycloak_accounts, files, diagnostics, embeddings, report
Workers  — claim durable jobs, invoke services, idempotent commits

MongoDB replica set (mandatory) — domain records, immutable revisions, jobs,
                                  review_tasks, audit_events, GridFS
Keycloak — admin + student realms/roles, Authorization Code + PKCE
Gemini   — diagnostics (google-genai), embeddings (text-embedding-004)
```

**Rule:** routes never run OMR or model inference inline. Workers may execute a job more than
once, so every committing operation is idempotent. Do not rewrite files merely to achieve this
layering — extract working logic incrementally, preserving behavior with tests.

### 3.1 Module boundaries

```text
cde/
  routes/          admin.py, student.py        # thin
  services/        rosters exams batches identity grading reviews evidence publication
  repositories/    transactions, indexes, revisions
  jobs/            queue.py worker.py handlers.py reconciliation.py
  adapters/        identity_ocr.py keycloak_accounts.py files.py
  omr_engine/      KEEP — harden, do not generalize
  grading_core.py  KEEP — wire it (§0.3)
  diagnostics.py   KEEP contract — extend inputs only (§0.2)
  retrieval.py     KEEP — inactive until Release C
  embeddings.py    KEEP behind versioned adapter
  report.py        wire through report service
```

---

## 4. Domain model

| Record | Responsibility |
|---|---|
| `students` | Internal identity. Created **only** by an admin roster operation. |
| `rosters` / `roster_entries` | Class membership, roll numbers scoped to the roster instance. |
| `account_links` | Immutable Keycloak `(issuer, subject)` → `student_id`. |
| `exams` | Roster assignment, template version, **`question_count`**, **`marking_policy`**, **`subject_ranges`**, `report_policy_revision`. |
| `answer_key_revisions` | Immutable key + scoring rules. |
| `question_revisions` | Question number, verified paper crops, subject, later sub-topic tags. |
| `batches` | PDF, expected counts, manifest state, aggregate progress. |
| `sheets` | One source page; layout + identity state; provenance. |
| `submissions` | One resolved student's attempt; current target revisions. |
| `omr_revisions` | Extracted mark states, confidence, flags, engine version, image hash. |
| `grade_revisions` | Finalized answers, key revision, policy, totals. |
| `rough_work_revisions` | Evidence, privacy clearance, availability declaration. |
| `diagnostic_revisions` | Per-question evidence, mapping, status, model provenance. |
| `report_revisions` | Immutable assembled report + referenced input revisions. |
| `review_tasks` | Durable human decisions, leases, scope, history. |
| `jobs` | Durable async work + execution leases. |
| `audit_events` | Append-only domain/security decisions. |
| `file_assets` | Verified refs, hashes, access scope, staging lifecycle. |

### 4.1 Required unique indexes

- roll number within a roster instance
- Keycloak `(issuer, subject)` account link
- batch page `(batch_id, page_number)`
- at most one accepted sheet per `(student, exam)`
- job idempotency key
- revision number within each revisioned entity
- review resolution operation id
- current report publication per target revision

A reused roll number in another class or year is **not** the same identity. Never match
globally by roll number or name.

### 4.2 Transactions are mandatory

Delete the silent non-transactional path in `cde/db.py`:

```python
@contextmanager
def unit_of_work(self):
    if not self.check_replica_set():
        raise RuntimeError(
            "MongoDB is not a replica set; transactional writes unavailable. "
            "Refusing to process."
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

`GET /health/ready` in `cde/routes/alpha.py` already 503s on non-replica-set — now consistent
with the write path. At startup also verify required indexes exist and a transaction commits.

Transaction boundaries: domain state + next job insertion · identity binding + submission
creation · review resolution + revision transition + audit event · grade finalization +
downstream scheduling · report publication + current-report pointer.

### 4.3 Files stage outside domain transactions

1. Allocate durable staging record → 2. write GridFS → 3. verify completeness + hash →
4. commit file ref + domain transition + job **in one Mongo transaction** → 5. reconcile
interrupted uploads and orphans after a retention window.

Never delete files under active upload leases or referenced by revisions. A job must never
consume an unverified file.

### 4.4 No cross-system transactions

Keycloak provisioning and Gemini calls cannot join a Mongo transaction. Use durable intent
records, retry-safe adapters, reconciliation. A model response may arrive twice after retry —
only one result per expected input revision becomes current. Guarantee **idempotent domain
effects**, not exactly-once external execution.

---

## 5. Durable jobs

```text
id · kind · entity_id · input_revision · idempotency_key
status: pending | running | succeeded | failed | superseded
attempt_count · next_attempt_at
lease_owner · lease_expires_at · fencing_token
last_error_code · created_at · updated_at
```

Claim atomically; increment `fencing_token` on every new lease; heartbeat long work; require
current lease token **and** input revision at commit; bounded backoff; exhausted retries surface
to the admin queue; mark stale jobs `superseded` when inputs are no longer current.

**Never hold a Mongo transaction open while running OpenCV, rendering PDFs, or calling Gemini.**

### 5.1 Human waiting is not worker execution

On review need: persist blocked state + review task → **finish the job** → wait with no lease
and no polling loop. On resolution, atomically persist the decision and enqueue the next job.
Admin claim leases may expire and be reclaimed; the task and its history never expire.

### 5.2 Reconciliation job

Detect expired worker leases · verified uploads with no job · completed manifests missing page
records · ready stages lacking jobs · incomplete account provisioning · staged files eligible
for cleanup · failed/superseded work still referenced as current. Use the same idempotency keys
as normal scheduling.

---

## 6. Roster, accounts, authorization

### 6.1 Roster lifecycle
Admin creates roster → imports names + roll numbers → resolves duplicates/invalid rows →
confirms the roster revision assigned to the exam → issues accounts against those records.

Preserve original identity values alongside normalized matching values; normalization must not
erase meaningful distinctions (leading zeros in roll numbers). OCR can never alter roster
records — a genuinely missing student requires a separate audited roster correction.

### 6.2 Keycloak
Extend the existing installation: `admin` + `student` roles; browser client with Authorization
Code + PKCE; FastAPI audience config; admin-provisioned student accounts; temporary credentials
requiring replacement on first use; admin-assisted reset with no email dependency.

Prefer strong temporary credentials over short reusable PINs. **Never** use roll number, date
of birth, or OCR-extracted identity as an authentication secret. Provisioning must be
retry-safe via a stable reference. Never log temporary credentials or place them in audit
payloads.

`web/src/auth.ts` is currently `export const auth = {}` — implement it properly with
`keycloak-js` (already a dependency).

### 6.3 Request authorization
Validate signature, issuer, audience, expiry → resolve subject to account link → enforce role →
enforce ownership or admin scope. **Student identity comes from the session, never the request
body.**

### 6.4 Protected resources
Students must never reach: the class PDF · another student's score/report/rough work · identity
crops or candidate lists · admin diagnostic responses · arbitrary GridFS files.

`GET /api/images/{file_id}` in `cde/routes/beta.py` is currently an unscoped GridFS read.
**Gate or remove it before any student account exists.** GridFS IDs are not authorization
tokens.

---

## 7. Batch ingestion

### 7.1 Canonical path
Authorize admin + verify exam readiness → create batch record → persist and verify PDF →
record page count and expected count → schedule rendering → create **exactly one sheet record
per source page**. Return a durable batch id. Do not wait for OMR inside the HTTP request.

Support ~45 pages via configured, tested limits. The old `max_pages=10` cap in `cde/omr.py` is
not the constraint (that module is retired — §14). Apply explicit limits on file size, page
count, raster dimensions, processing time, worker concurrency.

**Use `pypdfium2`** (pinned). The `fitz`/PyMuPDF import has been removed — see §15.

### 7.2 Page accounting
The manifest includes every page, even failures. Each page terminates in exactly one of:
processing · awaiting layout review · awaiting identity review · awaiting bubble review ·
graded/downstream · rejected with reason.

A page-count discrepancy is an admin exception — never silently drop pages or infer absent
students.

### 7.3 Layout validation (before identity or grading)
Expected aspect ratio within tested tolerance · detectable panel/grid arrangement · expected row
and option geometry · calibration residuals and sampling bounds · usable orientation and full
answer region.

Failure routes to layout review/rejection. Resolution normally means a corrected scan.
**An admin cannot bypass a failed geometry check by clicking "grade anyway."**

This closes the audit's most dangerous finding: a mismatched layout currently returns confident
garbage rather than erroring.

### 7.4 Duplicates
Request idempotency (network retry) · file hashes (exact duplicate pages) · `(student, exam)`
uniqueness (second sheet, different bytes) → held for admin reconciliation, never overwritten.
General perceptual duplicate detection is out of scope.

---

## 8. OMR extraction and grading

### 8.1 Keep the tuned engine
Retain `cde/omr_engine/` for the fixed BIOME layout. Do **not** switch to `cde/omr.py` or
generalize its constants into a multi-template framework.

**Outstanding regression, unfixed:** loosening `_auto_header_cutoff` (`engine.py:109`) from a
density-relative test to a bare absolute one fixed page 4 (19→5 flagged) but regressed page 1
(→79 flagged, `rows_calibrated` 18/36; header cutoff lands at y=721 vs reference 1298 — it
latches onto a gap inside the student-info block). Candidate fix:

```python
median_gap = float(np.median(diffs))
is_convincing = (
    diffs[i] >= 0.03 * h
    and (median_gap <= 0 or diffs[i] >= 2.5 * median_gap)
)
```

This is a **candidate**, not an accepted fix. Apply only after comparing all labeled regression
pages and held-out scans. Page 1 and page 4 must come down together — that pair is the test.

### 8.2 Scope extraction to the exam's question range  ← CORRECTION 0.4

The engine emits 180 results; `grading_core` requires exactly `1..question_count`.

Add `question_count` (and, if the live rows are not `1..N`, an explicit live row range) to the
exam record. The grading service filters `OMRResult.questions` to the live range and asserts
the remaining rows are genuinely unused. **Do not relax `grading_core`'s contiguity check** —
it is correct and it is what caught this.

Stray marks in unused rows 76–180 must raise a **review exception**, not a silent −1.

### 8.3 Separate extraction from scoring
The engine returns per-question mark state, candidate option where unambiguous, calibration
signals, review reason and crop coords where uncertain, engine/template version, image hash.

**`OMRResult` must stop reporting `score`/`max_score` entirely** (`engine.py:392-394`). The
grading service owns scoring and consumes only finalized answers + an immutable key + policy.

### 8.4 Marking policy — +4 / −1 / 0  ← CORRECTION 0.3

```json
{ "correct_marks": "4.000", "wrong_marks": "-1.000",
  "blank_marks": "0.000", "multiple_marks": "-1.000" }
```

`maximum = correct_marks × question_count` = 4 × 75 = **300**.

**(a) Flat scoring erases ranking — not just scale.** Over 75 questions:

| | Correct | Wrong | Blank | Flat (current) | +4/−1 (real) |
|---|---:|---:|---:|---:|---:|
| Student A | 40 | 35 | 0 | 40/75 = **53.3%** | 160−35 = 125/300 = **41.7%** |
| Student B | 40 | 0 | 35 | 40/75 = **53.3%** | 160−0 = 160/300 = **53.3%** |

Identical today; **35 marks apart** in reality. Separating a guesser from a blank-leaver is the
entire purpose of negative marking. Any cohort statistic built on current scores inherits this
distortion.

**(b) `grading_core` cannot represent a confirmed multiple-mark — and now it must.**
Its award logic is a three-way branch (`None`→blank, `==key`→correct, `else`→incorrect), but
`_classify()` emits five states (`blank`, `ambiguous`, `multiple`, `review_low_resolution`,
`filled`). Under +4/−1 a double-marked bubble scores **−1**, not 0. A reviewer confirming
"student marked both B and C" can currently only pick one option (possibly awarding +4) or
leave it null (scored 0). **Add a finalized `invalid_multiple` state and the `multiple_marks`
policy entry, and extend the award branch.** Do not encode it as `None`.

**(c) The blank threshold is now worth up to 5 marks, and is self-described as provisional.**
`_classify()` calls blank at `best < 0.18`; the reason strings read
`all_options_below_provisional_floor` and `single_candidate_passed_provisional_gate`. Under
+4/−1: a faint **correct** mark read as blank loses the student **4**; a faint **wrong** mark
read as blank gains them **1**. A 5-mark swing from one threshold, **asymmetric in favour of
faint markers**. Re-validate these thresholds against labeled scans under the real scheme
before unattended grading, and report confidently-wrong cases **weighted by marks at stake**
(§17.1), not as a flat count.

### 8.5 Answer finalization
Distinguish: confirmed selected option · confirmed blank · confirmed `invalid_multiple`.
Ambiguous extraction is **not** a finalized blank. It stays pending until reviewed.

### 8.6 Bubble review
Reuse existing claim/renew/resolve. Resolution atomically records question + evidence revision
reviewed, finalized state, admin identity, timestamp, reason, updated sheet revision, and the
next grading job if all answers are now final. A stale review cannot overwrite a newer
extraction or key revision.

### 8.7 AI never touches scores
AI never determines a score, resolves an ambiguous bubble, or changes a finalized answer.

---

## 9. Exam content and question images

Admin verifies, per scored question: correct paper page(s), crop coordinates, all necessary
diagrams/tables/options, and the matching key entry. Do not assume PDF extraction preserves
mathematical notation, numbering, or diagrams.

For one exam, prefer a simple admin crop/mapping editor over automated document understanding.
Render the paper, propose crops if useful, require admin confirmation. A question spanning
pages may reference multiple crops. Text context is optional support; **the question image is
part of every diagnostic payload.**

---

## 10. Diagnostics

### 10.1 Avoid the upload/publication deadlock
The processing screen may contain rough-work upload controls, receipt/status, and an explicit
**"I have no rough work available"** action. It must **not** contain partial scores, wrong-answer
lists, or incomplete findings.

Associate uploads with the authenticated student's assigned exam record. If the sheet is not
yet identity-resolved, hold the evidence and attach it once binding completes.

### 10.2 Evidence intake and mapping
Validate type/size/page count/decoded dimensions · preserve original private evidence · create
normalized redacted derivatives · record hashes and page coordinates · strip names/roll numbers
before provider submission · **require admin privacy clearance of prepared payloads for the
first diagnostic pilot**, automating only after validation.

Two-step bounded pipeline: **(1) mapping** — sanitized rough-work pages against the verified
question catalogue, returning candidate question IDs + evidence coordinates; **(2) diagnosis** —
per eligible wrong answer, with question images, finalized answer, key context, mapped evidence.
Chunk where necessary and reconcile across chunks — **never resolve collisions by highest
self-reported confidence.** Ambiguous or contradictory mapping abstains or goes to admin review.

Treat text inside uploaded documents as evidence, never as instructions. The model receives no
credentials and no ability to modify records.

### 10.3 Subjects are free; sub-topics are not  ← CORRECTION 0.4(d)

Both prior plans said topic analysis is blocked until an admin authors a taxonomy. That is
**too strict for JEE Main**: question numbers map deterministically to **Physics / Chemistry /
Mathematics** by range. That is ground-truth subject labelling with zero authoring.

Add `subject_ranges` to the exam record in Phase 1. **Release B can honestly report
subject-level findings** — *"your Conceptual Deficits cluster in Physics"* — without waiting for
Release C.

Sub-topic labels (kinematics, thermodynamics…) still require admin authoring and stay
unavailable until Release C. Never present `Conceptual Deficit` as a subject, and never ask the
model to invent topic labels and display them as validated exam metadata.

### 10.4 Preserve the existing contract — extend inputs only
Keep: strict Pydantic `extra="forbid"` · crop-hash verification · evidence support gates ·
explicit abstention · confidence suppression on unsupported evidence · requested **and**
returned model identifiers · raw response persistence · `MIN_CLASSIFICATION_CONFIDENCE = 0.90`.

Validate the configured model's availability, image handling, and schema behavior before
release — do not assume `GEMINI_DIAGNOSTIC_MODEL` still names a suitable model.

### 10.5 Operational failure is not abstention
Timeout, outage, malformed response, or hash mismatch = **processing failure**. Retry transient
errors; surface exhausted retries to the admin; keep the stage pending/failed until repaired.
Never manufacture an evidence-based abstention to make a report look complete.

### 10.6 Admin intervention
The admin may correct a mapping with evidence, replace a crop, approve a redacted payload,
retry a failed job, or confirm that available evidence is unusable and record an abstention
reason. **The override endpoint must not permit unsupported classifications or score changes.**

---

## 11. Reports

### 11.1 Publication predicate

```text
publishable =
    identity resolved
    AND sheet passed layout validation
    AND all answer states finalized
    AND grade revision committed
    AND all stages required by report_policy_revision are terminal and valid
```

Under `diagnostic` policy, every required wrong-answer result must be either a supported
classification or an explicit evidence-based abstention. No wrong answers ⇒ no required
diagnoses.

### 11.2 No rough work
An explicit student declaration permits terminal abstentions with a clear reason. **Silence is
not that declaration** — the report stays processing until the student uploads, declares
unavailability, or the admin records a legitimate availability decision. Under the no-SLA
policy this may persist indefinitely; the admin must see the blocking reason while the student
sees no partial results.

### 11.3 Content
**Score-only:** identity, final score + scheme, correct/incorrect/blank totals, explicit
score-only label.
**Diagnostic:** the above plus cohort comparison with denominator, per-question supported
findings, abstention reasons, error-class summary with diagnosed/abstained coverage,
**subject-level breakdown** (§10.3), cautious guidance grounded in validated question context,
explicit sub-topic/practice availability status.

Never name a formula or concept as the student's weakness unless evidence and question context
support it. Never present generated advice as an official worked solution.

### 11.4 Cohort comparisons
Use only finalized grades. Disclose coverage: *"Compared with 38 finalized submissions out of
45 rostered students."* Do not wait for the whole class to publish a complete report — an
unresolved classmate must not block anyone else. Diagnostic percentages use supported
classifications as denominator and show abstention coverage separately. Persist the cohort
snapshot revision; updating comparisons creates a new report revision.

### 11.5 Portal and PDF
Portal is primary. Reuse `cde/report.py` after verifying its input contract. PDF failure does
not invalidate a complete portal report — show download unavailable and retry. Email is
deferred and **never** part of the publication predicate.

---

## 12. Question bank and practice (Release C)

Do not wire `build_remediation` to return an empty success and call it done. Before activation
the bank needs: content + images · correct answer + validated solution · validated
subject/sub-topic/question-type tags · intended error targets · difficulty metadata ·
source/provenance/permission · question-family ids for dedup.

Workflow: admin imports/authors → validates answers, solutions, tags → approves bank revision →
worker creates versioned embeddings → eligibility/ranking tests pass → feature enabled.
Assistance may draft tags; unvalidated suggestions never become authoritative automatically.

Retrieval: preserve existing hard eligibility filters and family dedup. Select by validated
topic/error-target policy → exclude source question and disallowed duplicates → require
compatible embedding model/version/dimension → rank with existing similarity logic → persist
selected IDs and inputs. Linear in-memory ranking is fine at this scale; a vector index is a
growth change.

Put the embedding provider behind a versioned adapter — do not assume `text-embedding-004`
remains available. If it changes, re-embed a complete bank revision; never compare vectors from
incompatible spaces.

Empty state: *"No suitable practice is available for this diagnosed weakness yet."* Never relax
filters silently or label random questions as personalized.

---

## 13. Canonical API

### Admin
```
POST /api/rosters                              create/import roster
POST /api/rosters/{id}/accounts/issue          schedule account provisioning
POST /api/exams                                create exam + marking_policy + question_count
                                               + subject_ranges + report policy
POST /api/exams/{id}/answer-key-revisions      validate + version key/scoring
POST /api/exams/{id}/question-paper            upload source paper
PUT  /api/exams/{id}/question-map              confirm question image mappings
POST /api/exams/{id}/batches                   upload batch PDF, return durable id
GET  /api/batches/{id}                         page counts, progress, blocking reasons
GET  /api/review-tasks                         filter layout/identity/bubble/diagnostic
POST /api/review-tasks/{id}/claim|renew|resolve
GET  /api/exams/{id}/insights                  finalized-grade + supported-diagnostic aggregates
```

### Student
```
GET  /api/me                                   account + role
GET  /api/me/exams                             assigned exams (never via sheet OCR)
GET  /api/me/exams/{id}/status                 processing/published + evidence controls only
POST /api/me/exams/{id}/rough-work             upload evidence
POST /api/me/exams/{id}/rough-work/unavailable explicit declaration
GET  /api/me/exams/{id}/report                 current finalized report or minimal processing
GET  /api/me/exams/{id}/report.pdf             authorized download when ready
GET  /api/me/exams/{id}/practice               Release C only
```

**Processing responses must not include hidden grade or diagnostic objects for the frontend to
suppress.**

### 13.1 Frontend
Replace `web/src/auth.ts` (empty stub) with real `keycloak-js` integration · repurpose
`TeacherUploadBay` + dashboard elements as admin surfaces · remove teacher routes/menus/
permissions · extend admin review surfaces to identity + layout exceptions · reuse student
rough-work components behind the new authz/publication contract · show per-sheet batch progress ·
make blocking reasons actionable for admin without exposing classmates to students.

**Note:** there is no component library installed — no shadcn `components.json`, no Radix, no
`class-variance-authority`. Just Tailwind v4 and a 20-line stylesheet. Existing components
(44–188 lines) are functional scaffolding, not UI. A "clean, professional" interface means
installing a design system and building the UI layer for the first time — budget for it.

---

## 14. Existing-code disposition

| Component | Action | Reason |
|---|---|---|
| `cde/omr_engine/` | **Keep + harden** | Best evidence of useful OMR for the confirmed layout. Fix regression, add layout guards, remove scoring, scope to `question_count`. |
| `cde/grading_core.py` | **Keep + WIRE** | Already correct incl. negative marking. Currently unreachable. Add `invalid_multiple`. |
| `cde/grading.py` | Keep as service seam | Only importer of `grading_core`. |
| `cde/diagnostics.py` | **Keep contract, extend inputs** | Strongest module in the repo. Do not migrate abstention. |
| `cde/retrieval.py` | Keep + test, inactive till Release C | Filters/ranking useful; no bank yet. Shares the canonical taxonomy. |
| `cde/embeddings.py` | Keep behind versioned adapter | Avoid hardcoded model assumptions. |
| Review queue (`beta.py`) | Preserve leases; make transitions transactional + revision-checked | Durable human decisions are central. |
| `cde/routes/beta.py` | Extract logic into services; keep thin endpoints | Inline execution unsuitable for durable batches. |
| `cde/routes/alpha.py` | Replace upload stubs with canonical batch lifecycle, or remove | Success-shaped no-ops must not remain reachable. |
| `cde/omr.py` | **Retire as an active engine**; salvage rendering/identity-crop helpers | Avoid two scoring implementations; multi-template not needed. |
| Temporal (`workflows/activities/dispatcher/worker`) | **Retire** after durable-job parity tests | Six activities are `return {"status":"ok"}` no-ops. |
| `cde/auth.py` | Extend roles/ownership | Real token validation — do not add a second auth system. |
| `web/src/auth.ts` | **Implement** | Currently an empty stub. |
| `cde/report.py` | Wire through report service | Reuse, don't rewrite. |
| Email | Defer | Portal delivery suffices; must not gate publication. |
| GridFS | Retain, scoped access + staging reconciliation | S3 is not a pilot dependency. |
| `contracts/ownership.json` | Replace with service ownership + integration gates | Historical file ownership preserved disconnected paths. |

Archive obsolete design docs and link them to this blueprint. Do not leave multiple documents
claiming to define the active database, role model, taxonomy, or upload architecture.

---

## 15. Already applied

1. `cde/routes/beta.py` imported `fitz`/PyMuPDF — pinned in neither `requirements.in` nor
   `.lock`; every PDF upload raised `ImportError`. Replaced with `pypdfium2` (already pinned).
   Syntax-checked; no `fitz` references remain under `cde/`.
2. `google-genai` — required by `diagnostics.py` and `embeddings.py` — was pinned nowhere;
   `requirements.in` still listed `openai`. Swapped and recompiled with `uv pip compile`;
   resolved clean, `google-genai==2.22.0` verified importable.

---

## 16. Open blockers — resolve before scheduling

### 16.1 Does the sheet contain numerical (Section B) answers?  ← BLOCKING

JEE Main is 3 subjects × 25, split into **Section A (MCQ, 4 options)** and **Section B
(numerical/integer entry)**. The engine reads exactly four option columns
(`OPTION_LETTERS = "ABCD"`, `OPTION_OFFSETS` has 4 entries) and **cannot read a digit grid**.

If Section B appears on this sheet, grading it is a **missing feature** — a multi-column
digit-grid reader with its own calibration, ambiguity rules, and review flow — not a tuning
task. This may add substantial scope to Release A.

**Answer required before Phase 2 is scheduled.**

### 16.2 Missing artifacts
- **No Keycloak realm config** anywhere (`infra/keycloak/` absent). Needed before `cde/auth.py`
  can validate a real `student` role: realm name, client IDs, redirect URIs, roles, token
  lifetimes, first-login credential-replacement mechanics.
- **No `.env.example`.** `cde/config.py` has silent defaults masking required settings
  (`GEMINI_API_KEY`, `GEMINI_DIAGNOSTIC_MODEL`, Keycloak realm/client, replica-set Mongo URI).
  Add fail-fast validation for anything without a safe default.
- **No roster CSV or question-map format** specified.

### 16.3 Undetermined
- Exact question count (72 vs 75) and the live row range on the sheet.
- Whether cancelled questions or partial-credit rules apply.
- OCR name-match policy: exact vs fuzzy, threshold, and what it is validated against (no
  labeled identity dataset exists — same unvalidated-threshold trap as the OMR accuracy claim).

### 16.4 Document completeness
The detailed migration plan was received **truncated mid-§18.2** (Minimum observability).
§18.3 onward and any §19+ are not reflected here. Reconcile when supplied.

---

## 17. Execution order

### Phase 0 — safety baseline
1. Verify this blueprint against the repo.
2. Capture existing OMR/review behavior in regression fixtures.
3. Label available scans to measure wrong reads separately from review flags.
4. Fix the header/footer regression (§8.1); add layout guards (§7.3).
5. Deploy replica-set Mongo locally + in CI.
6. Delete the silent non-transactional path (§4.2).
7. Establish revisions, indexes, job contract.

**Gate:** regressions reproduced and repaired on labeled fixtures · wrong-layout inputs held,
never force-graded · transaction-dependent code refuses unsupported deployment · one integration
owner, one live path.

### Phase 1 — score-only skeleton (Release A)
1. Roster import + validation.
2. Keycloak issuance + account-link reconciliation.
3. Real frontend login + server-side ownership checks.
4. Durable batch upload, rendering, page manifest.
5. Manual identity review + submission binding.
6. **Wire `grading_core`**: scope extraction to `question_count` (§8.2), remove scoring from
   `OMRResult` (§8.3), add `invalid_multiple` (§8.4b), apply +4/−1 policy.
7. Bubble review resolutions → durable continuation jobs.
8. Versioned score-only portal reports.
9. Repurpose admin frontend; remove competing upload paths.

**Gate:** a ~45-page PDF yields exactly one tracked result per page · identity admin-confirmed ·
every uncertain bubble unpublished until resolved · student sees only their own finalized score ·
an unresolved page blocks nobody else · worker restarts and duplicate requests neither lose nor
duplicate domain effects · **scores match hand-computed +4/−1 on a sample**.

### Phase 2 — identity automation + evidence intake
Requires §16.1 answered. OCR behind manual matching · evaluate exact-match auto-accept on
labeled identities incl. conflicts · keep auto-accept disabled until validated · question-map
editor + admin verification · authenticated rough-work intake + unavailable declaration ·
evidence normalization, privacy clearance, immutable revisions.

**Gate:** unknown/conflicting identity cannot auto-bind · OCR creates no students and grants no
access · each scored question has correct image context · rough work received pre-publication
without leaking partial results.

### Phase 3 — diagnostic pilot (Release B)
Bounded evidence mapping + collision handling · extend diagnostics with question images · all
diagnostics via durable jobs · retire permissive inference paths and unrestricted overrides ·
implement the diagnostic publication predicate · assemble reports, cohort snapshots, PDF ·
**enable subject-level analysis (§10.3)** · admin retries and evidence-based abstentions.

**Gate:** missing/illegible/unmapped/contradictory evidence produces correct abstention ·
provider failures stay processing failures · every published diagnosis traceable to evidence and
model/schema/prompt versions · results hidden until policy satisfied · sub-topics and practice
explicitly unavailable rather than faked.

### Phase 4 — content personalization (Release C)
Approve sub-topic taxonomy + tag questions · populate validated practice bank · versioned
embedding ingestion · connect eligibility/ranking to real candidates · persist recommendation
provenance · student practice delivery.

**Gate:** every recommendation has validated content and an appropriate weakness target ·
source questions and duplicate families excluded · embedding compatibility enforced · no
eligible content yields an honest unavailable state.

### Growth backlog
Multiple classes/exams · multi-template OMR · scan recovery · vector indexing · S3 · email ·
practice history and adaptive progression · additional roles only after a new product decision.

---

## 18. Acceptance tests

Run against a **real replica-set MongoDB**, not mocks. (Existing suites are mock-only; Gamma
never delivered test suites at all.)

| Scenario | Required result |
|---|---|
| Valid ~45-page PDF | Every page appears exactly once in manifest and results |
| Request repeated after timeout | Existing batch/job reused; no duplicate submission |
| Wrong-layout / badly cropped page | Layout review or rejection; no grade |
| **75-question exam, 180-row sheet** | Grading scoped to live range; unused rows not scored |
| **Stray mark in unused row** | Review exception, not a silent −1 |
| Known header/footer regression | No recurrence on the full labeled set; pages 1 and 4 both low |
| Blank or sparse sheet | Correct extraction or conservative review; never confident wrong-grid sampling |
| **Confirmed multiple-mark** | Finalized `invalid_multiple`, scored −1, not 0 and not +4 |
| **Hand-computed +4/−1 sample** | System total matches exactly |
| Unknown or conflicting identity | Admin review; no new student, no publication |
| Duplicate roll within roster | Roster validation fails before matching |
| Same roll in different class/year | No cross-roster match |
| Second sheet for same student/exam | Duplicate review; no overwrite |
| Ambiguous bubble | No finalized grade until resolved |
| Worker dies after file write | Reconciliation recovers a verified ref or cleans a true orphan |
| Worker dies after domain commit | Retry cannot duplicate the committed revision |
| Lease expires while old worker runs | Fencing prevents stale completion winning |
| Two admins resolve the same review | One revision-valid resolution wins; other gets conflict |
| Review untouched for weeks | State recoverable; other sheets proceed |
| Keycloak succeeds, DB link fails | Reconciliation links intended account, no duplicates |
| Student alters URL/resource id | No access to another student or arbitrary file |
| Wrong token issuer/audience | Rejected |
| No rough work declared | Evidence-based abstentions permit a complete report |
| No upload and no declaration | Report remains processing |
| Illegible/unmapped/contradictory work | Abstention, not inferred cognition |
| Provider timeout or invalid schema | Retry/exception state; no fabricated abstention |
| Question image omitted or mismatched | Diagnosis blocked |
| Evidence hash mismatch | Fails securely; evidence not trusted |
| Key or evidence changed post-publication | New target revisions; no silent overwrite |
| Sub-topic tags or bank absent | Explicit unavailable state |
| Retrieval has no eligible candidates | No weak fallback labeled "personalized" |
| Backup restoration | DB, referenced files, account links all recover |

### 18.1 OMR evaluation policy
Report: correct automatic reads · **confidently wrong automatic reads, weighted by marks at
stake (§8.4c)** · review rate · layout rejection rate · final accuracy after review.

Use held-out scans as well as existing regression pages. **Block release on any known
confidently-wrong case.** Passing a finite set establishes no universal guarantee — the current
evidence is one labeled page (175/180, 0 errors), which is a promising signal and nothing more.

For the first real batch, the admin compares finalized results against independently checked
paper outcomes before publication. If that cannot be staffed, the batch is a supervised test,
not an unattended release.

### 18.2 Diagnostic evaluation policy
Build a small labeled set covering the four canonical classes plus abstention cases. Inspect
mapping correctness, evidence support, unsupported-classification rate, abstention behavior, and
explanation consistency with cited work. **Model self-confidence is not an acceptance metric.**

---

## 19. Operations

Deploy: React static frontend · FastAPI · worker with conservative rendering/inference
concurrency · MongoDB replica set with private GridFS · Keycloak. No Redis, second database, new
orchestrator, or S3 needed for the pilot.

Track: pages received vs accounted for · job retries, expired leases, failures · layout
rejection and review counts · confidently-wrong OMR cases found in validation · classification
vs abstention coverage · provider latency/failures · publication blockers · unauthorized access
attempts.

Log correlation IDs and reason codes — never student names, credentials, or raw evidence.

---

## 20. Release discipline

- One integration owner. Components may be built separately, but "done" means the real vertical
  flow passes — not an activity returning `{"status": "ok"}`.
- No accuracy claim beyond what labeled evidence supports.
- No feature described as ready while its content dependency is missing.
- Test backup restoration before real student use.
- If a gate fails, demonstrate with synthetic or explicitly approved test records. Do not
  describe an incomplete implementation as a ready student pilot.
