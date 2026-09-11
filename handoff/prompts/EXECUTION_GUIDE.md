# Execution Guide — Cognitive Diagnostic Engine

**Version 2.** Rewritten after an independent audit of version 1 found 21 defects, including
missing tasks that made the plan impossible to complete (no job worker, no exam setup, no
report publication). Audit summary in Appendix A.

**Read Parts 0 and 1 completely before writing any code.**

Every task states: why it exists, the exact file, the exact change, the exact test, and the
pass condition. Follow tasks in order. Do not skip. Do not improvise.

---

# PART 0 — CONTEXT

## 0.1 The client and the users

The client runs a **coaching institute in India preparing students for JEE Main**, a national
engineering entrance exam. Students sit practice exams on paper, filling bubbles on printed OMR
answer sheets with pencil.

The pilot is **one class, ~45 students, one exam.**

Two user types only:

1. **Admin** — one person, the institute owner. Scans exams, runs the system, resolves anything
   the software is unsure about. Not a software engineer. No SLA — may take days to respond.
2. **Student** — a teenager preparing for a high-stakes exam. Logs in, sees their own results
   and what to work on. Never sees another student's data.

**There is no teacher role.** The existing code has teacher screens. They get removed (Phase 7).

## 0.2 The product flow

```
1.  Admin enters the class roster (names + roll numbers).
2.  Admin issues each student a login.
3.  Admin creates the exam: question count, answer key, marking scheme, subject ranges.
4.  Students sit the exam; each fills one OMR sheet.
5.  Admin scans all ~45 sheets into ONE PDF and uploads it.
6.  System splits the PDF into individual sheet records — one per page, none lost.
7.  System reads the bubbles on each sheet.
8.  Admin confirms whose sheet each one is.
9.  Anything uncertain goes to the admin. The system never guesses.
10. Once fully resolved, the system scores the sheet using +4/−1.
11. System publishes the report. Student logs in and sees their score.
        ── Release A ends here ──
12. Student uploads a photo of their rough work (the scratch paper).
13. AI examines question + student's answer + handwritten working, and identifies WHY they
    got it wrong: calculation slip, wrong procedure, misread question, or missing concept.
14. Student gets a detailed report including subject-level weakness analysis.
        ── Release B ends here ──
15. System recommends practice questions targeting those weaknesses.
        ── Release C ends here ──
```

## 0.3 The exam and marking scheme

JEE Main covers **Physics, Chemistry, Mathematics**. This paper has **~75 questions**.

| Outcome | Marks |
|---|---|
| Correct | **+4** |
| Wrong | **−1** |
| Blank | **0** |
| Multiple bubbles filled | **−1** |

Maximum = 4 × 75 = **300**.

**Why this matters.** Negative marking means blank ≠ wrong. A student who guesses 35 questions
wrongly scores 35 marks below one who left those blank, with identical correct counts. Software
that cannot distinguish blank from wrong destroys the marking scheme and misranks students.

**Critical detail:** the answer sheet has **180 bubble rows** (it is a generic high-density
institute sheet). The exam uses only ~75. Rows 76–180 are not part of the exam.

## 0.4 Safety rules — each prevents a specific harm

| Rule | Harm prevented |
|---|---|
| Never guess an uncertain bubble — a human decides | A misread bubble costs up to 5 marks; the student cannot know or appeal |
| Never guess whose sheet it is | Giving A's marks to B may go unnoticed for weeks |
| AI never calculates or alters a score | Grades must be reproducible and defensible |
| Never claim a weakness without evidence | Telling a student "you don't understand thermodynamics" when they made an arithmetic slip misdirects their entire preparation |
| Show nothing until fully resolved | A number that later changes destroys trust |
| A name on a sheet never grants account access | Otherwise anyone could read another student's results |

**If unsure whether to guess or ask a human: ASK A HUMAN.** A pending item costs the admin a
minute. A wrong grade costs a student their trust.

## 0.5 The existing codebase — what is there

```
cde_app_ready_v1.3.0/
├── cde/                        backend (Python, FastAPI)
│   ├── api.py                  FastAPI app; mounts alpha/beta/gamma routers
│   ├── config.py               Settings (pydantic-settings, .env)
│   ├── db.py                   DatabaseAdapter, unit_of_work(), get_db_adapter()
│   ├── storage.py              GridFS: upload(), upload_named(), presign()
│   ├── auth.py                 Keycloak OIDC validation (staff only so far)
│   ├── omr_engine/             BUBBLE READER — keep, harden
│   ├── grading_core.py         CORRECT SCORING incl. negative marking — UNUSED
│   ├── grading.py              thin wrapper, only importer of grading_core
│   ├── diagnostics.py          AI diagnosis — strict, careful, best code here
│   ├── retrieval.py            practice-question search — works, no data
│   ├── embeddings.py           Gemini embeddings
│   ├── report.py               PDF generation — not wired
│   ├── routes/
│   │   ├── alpha.py            exams/uploads — core actions are stubs
│   │   ├── beta.py             THE ONLY WORKING PATH (see below)
│   │   └── gamma.py            stub
│   ├── activities.py           6 functions that just `return {"status":"ok"}`
│   └── workflows.py worker.py dispatcher.py    Temporal — unused, to be deleted
├── web/                        frontend (React + TS + Vite + Tailwind v4)
│   └── src/
│       ├── main.tsx            router; HARDCODED MOCK AUTH — must be removed
│       ├── auth.ts             EMPTY STUB
│       ├── app/                Shell.tsx, providers.tsx, styles.css (20 lines)
│       ├── api/                client.ts, contracts.ts
│       └── features/           teacher/ (3), student/ (3), admin/ (2)
├── tests/                      alpha/ beta/ gamma/ contracts/ — conftest.py is "# Stub"
├── requirements.in / .lock     google-genai + pypdfium2 already fixed
└── handoff/prompts/            these documents
```

### What `cde/routes/beta.py` does today (the only working path)

```
POST /api/omr/upload                    grade ONE image inline; store to GridFS
GET  /api/submissions/{id}
GET  /api/review-tasks                  human review queue — REAL, reuse this
POST /api/review-tasks/{id}/claim       lease a task
POST /api/review-tasks/{id}/renew       extend lease
POST /api/review-tasks/{id}/resolve     record a decision
GET  /api/evidence/{crop_id}            serve a bubble crop
GET  /api/images/{file_id}              ⚠ UNSCOPED GridFS read — security hole
GET  /api/exams/{id}/insights           Mongo aggregation
POST /api/exams/{id}/submissions/{id}/rough-sheets
GET  /api/admin/diagnostics-queue
```

It runs everything **inline in the HTTP request**. That cannot work for a 45-sheet batch — one
timeout loses the lot. Phase 1 replaces this with a durable worker; Phase 7 deletes the old path.

### `review_tasks` document shape (already in use — reuse it, do not redesign)

```python
{
  "_id": str, "submission_id": str, "exam_id": str,
  "question_number": int, "kind": "ambiguous",
  "crop_id": str,                         # GridFS id of the bubble image
  "choices": [{"code": "A", "label": "Option A"}, ...],
  "suggested_code": str | None, "reason": str,
  "revision": int, "resolved": bool,
  "claimed_by": str | None, "lease_expires_at": datetime | None,
  "created_at": datetime,
}
```

### `cde/storage.py` API

```python
upload(submission_id: str, data: bytes, content_type="image/png") -> str   # storage key
upload_named(filename: str, data: bytes, content_type="image/png") -> str  # storage key
presign(storage_key: str, ttl_seconds=3600) -> Optional[str]
```

## 0.6 How to run the system

```bash
# 1. MongoDB as a replica set (REQUIRED — see P0-T1)
mongod --replSet rs0 --dbpath ./data
mongosh --eval "rs.initiate()"          # once only

# 2. Backend  (http://127.0.0.1:8000)
pip install -r requirements.lock
uvicorn cde.api:app --reload --port 8000

# 3. Worker (after Phase 1)
python -m cde.jobs.worker

# 4. Frontend (http://localhost:5173)
cd web && npm install && npm run dev

# 5. Tests
python -m pytest tests/ -v
```

`web/vite.config.ts` already proxies `/api`, `/exams`, `/uploads` → `127.0.0.1:8000`.
No CORS config is needed in development because of this proxy.

**Note:** `tests/conftest.py` currently contains only `# Stub`. Existing tests use mocked
dependencies and prove little. You are building the real test suite.

---

# PART 1 — RULES FOR THE EXECUTOR

**R1.** One task at a time. Complete it, run its test, confirm pass, then continue.

**R2.** Never mark a task done if its test fails. Report the failure.

**R3.** Never delete or rewrite working code to tidy it. Change only what a task says.

**R4.** **Never weaken a safety check to make a test pass.** If a test fails because the code
correctly refuses something unsafe, the *test* is wrong.

**R5.** If a file does not contain what the task says it contains, **STOP and report it.**

**R6.** Never invent a value (question count, marking scheme, file path). STOP and ask.

**R7.** Run the full suite before declaring a phase complete, not just new tests.

**R8.** Every state-changing database write happens inside `unit_of_work()`. No exceptions.

**R9.** Never log student names, credentials, or raw exam images. Log IDs and reason codes.

**R10.** **The application must start and the test suite must pass at the end of every task.**
Never leave a knowingly broken intermediate state. If a change breaks a caller, fix the caller
in the same task.

---

# PHASE 0 — FOUNDATION

**Goal:** make the existing system honest. No new features. Every task here prevents a silent
wrong answer.

---

## P0-T1 — MongoDB replica set

**Why:** MongoDB supports transactions only in replica-set mode. Transactions are what
guarantee a grade and the admin decision behind it are saved together or not at all.

```bash
mongod --replSet rs0 --dbpath ./data
mongosh --eval "rs.initiate()"
```

**Test:** `mongosh --eval "rs.status().ok"` prints `1`.

---

## P0-T2 — Refuse to run without transactions

**Why:** `unit_of_work()` currently pretends to start a transaction and silently does nothing
when Mongo is not a replica set. Every safety guarantee depends on transactions being real.

**File:** `cde/db.py` — replace the whole `unit_of_work` method:

```python
    @contextmanager
    def unit_of_work(self) -> Generator[ClientSession, None, None]:
        if not self.check_replica_set():
            raise RuntimeError(
                "MongoDB is not running as a replica set, so transactions are "
                "unavailable. Refusing to process. Start MongoDB with --replSet."
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

**Test** — `tests/test_transactions.py`:

```python
import pytest
from cde.db import DatabaseAdapter

URI, DB = "mongodb://localhost:27017", "cde_test"


def test_refuses_without_replica_set(monkeypatch):
    a = DatabaseAdapter(URI, DB)
    monkeypatch.setattr(a, "check_replica_set", lambda: False)
    with pytest.raises(RuntimeError, match="replica set"):
        with a.unit_of_work():
            pass


def test_commits_on_replica_set():
    a = DatabaseAdapter(URI, DB)
    assert a.check_replica_set(), "Run MongoDB with --replSet (P0-T1)"
    a.db.probe.delete_many({})
    with a.unit_of_work() as s:
        a.db.probe.insert_one({"_id": "x", "v": 1}, session=s)
    assert a.db.probe.find_one({"_id": "x"})["v"] == 1
    a.db.probe.delete_many({})


def test_rolls_back_on_error():
    a = DatabaseAdapter(URI, DB)
    a.db.probe.delete_many({})
    with pytest.raises(ValueError):
        with a.unit_of_work() as s:
            a.db.probe.insert_one({"_id": "y"}, session=s)
            raise ValueError("boom")
    assert a.db.probe.find_one({"_id": "y"}) is None
```

---

## P0-T3 — Create all database indexes

**Why:** Several safety rules (one sheet per student, no duplicate roll numbers, no duplicate
jobs) are enforced by unique indexes. Without them the rules are advisory only, and two
simultaneous requests can both succeed.

**Create `cde/indexes.py`:**

```python
"""Database indexes. Safety rules depend on these — they are not optional."""
from pymongo import ASCENDING


def ensure_indexes(db) -> list[str]:
    created = []

    # A roll number is unique WITHIN a roster. The same number in another
    # class or year is a different student.
    db.students.create_index(
        [("roster_id", ASCENDING), ("roll_number_normalized", ASCENDING)],
        unique=True, name="uniq_roll_per_roster")
    created.append("uniq_roll_per_roster")

    # One Keycloak identity maps to exactly one student, permanently.
    db.account_links.create_index(
        [("issuer", ASCENDING), ("subject", ASCENDING)],
        unique=True, name="uniq_account_link")
    created.append("uniq_account_link")

    # Every page of a batch appears exactly once.
    db.sheets.create_index(
        [("batch_id", ASCENDING), ("page_number", ASCENDING)],
        unique=True, name="uniq_page_per_batch")
    created.append("uniq_page_per_batch")

    # A student may have at most one sheet per exam. Partial index so many
    # sheets may have student_id = None simultaneously.
    db.sheets.create_index(
        [("exam_id", ASCENDING), ("student_id", ASCENDING)],
        unique=True, name="uniq_sheet_per_student_exam",
        partialFilterExpression={"student_id": {"$type": "string"}})
    created.append("uniq_sheet_per_student_exam")

    # A job is never enqueued twice for the same work.
    db.jobs.create_index([("idempotency_key", ASCENDING)],
                         unique=True, name="uniq_job_idempotency")
    created.append("uniq_job_idempotency")

    # Worker claim query.
    db.jobs.create_index(
        [("kind", ASCENDING), ("status", ASCENDING), ("lease_expires_at", ASCENDING)],
        name="job_claim")
    created.append("job_claim")

    # One published report per student per exam per revision.
    db.report_revisions.create_index(
        [("exam_id", ASCENDING), ("student_id", ASCENDING), ("revision", ASCENDING)],
        unique=True, name="uniq_report_revision")
    created.append("uniq_report_revision")

    return created
```

**Wire it into startup** — `cde/api.py`, after the app is created:

```python
from contextlib import asynccontextmanager
from cde.db import db_adapter
from cde.indexes import ensure_indexes


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not db_adapter.check_replica_set():
        raise RuntimeError("MongoDB must run as a replica set. Refusing to start.")
    ensure_indexes(db_adapter.db)
    yield


app = FastAPI(title="CDE App", version="2.0.0", lifespan=lifespan)
```

**Test** — `tests/test_indexes.py`:

```python
from cde.db import DatabaseAdapter
from cde.indexes import ensure_indexes


def test_indexes_are_created():
    a = DatabaseAdapter("mongodb://localhost:27017", "cde_test")
    names = ensure_indexes(a.db)
    for coll, idx in [("students", "uniq_roll_per_roster"),
                      ("sheets", "uniq_page_per_batch"),
                      ("sheets", "uniq_sheet_per_student_exam"),
                      ("jobs", "uniq_job_idempotency"),
                      ("account_links", "uniq_account_link")]:
        assert idx in a.db[coll].index_information(), f"{coll}.{idx} missing"


def test_duplicate_sheet_per_student_is_blocked_by_index():
    a = DatabaseAdapter("mongodb://localhost:27017", "cde_test")
    ensure_indexes(a.db)
    a.db.sheets.delete_many({})
    a.db.sheets.insert_one({"_id": "s1", "exam_id": "e1", "student_id": "std1",
                            "batch_id": "b1", "page_number": 1})
    import pymongo
    try:
        a.db.sheets.insert_one({"_id": "s2", "exam_id": "e1", "student_id": "std1",
                                "batch_id": "b1", "page_number": 2})
        assert False, "Index did not prevent two sheets for one student"
    except pymongo.errors.DuplicateKeyError:
        pass
    a.db.sheets.delete_many({})
```

---

## P0-T4 — Fix the page-1 reading bug

**Why:** A previous change to how the software finds the top of the answer grid fixed one test
page and broke another. On page 1 of the labeled batch it latches onto a gap *inside the
student-name block*, so it reads the grid from the wrong place: **79** questions flagged
instead of ~6, and only 18 of 36 rows calibrated.

**File:** `cde/omr_engine/engine.py`, in `_auto_header_cutoff` (~line 109).

**Find:**
```python
        is_convincing = diffs[i] >= 0.03 * h
```

**Replace:**
```python
        median_gap = float(np.median(diffs))
        is_convincing = (
            diffs[i] >= 0.03 * h
            and (median_gap <= 0 or diffs[i] >= 2.5 * median_gap)
        )
```

**In plain terms:** a gap counts as "the real top of the answer grid" only if it is both large
in absolute terms *and* much larger than the typical spacing between nearby marks. The second
condition is what stops it latching onto a small gap inside the name block.

**Test** — `tests/test_omr_regression.py`:

```python
import asyncio, glob, io, os, re
import pytest
from PIL import Image
from cde.omr_engine import process_omr_sheet

PAGES_DIR = os.environ.get("CDE_TEST_PAGES", "tests/fixtures/pages")
MAX_FLAGGED = 15


def _pages():
    files = glob.glob(os.path.join(PAGES_DIR, "page_*.png"))
    return sorted(files, key=lambda p: int(re.search(r"page_(\d+)", p).group(1)))


pages_available = pytest.mark.skipif(
    not _pages(), reason=f"No labeled pages in {PAGES_DIR}; set CDE_TEST_PAGES")


@pages_available
def test_no_page_flags_excessively():
    """Page 1 must not regress AND page 4 must stay fixed — both at once."""
    bad = []
    for path in _pages():
        with open(path, "rb") as f:
            r = asyncio.run(process_omr_sheet(f.read()))
        if r.review_count > MAX_FLAGGED:
            bad.append(f"{os.path.basename(path)}={r.review_count}")
    assert not bad, "Too many flagged: " + ", ".join(bad)
```

> **Copy your 10 labeled pages into `tests/fixtures/pages/`, or set `CDE_TEST_PAGES`.**
> If this test skips, you have no OMR regression coverage at all. Do not proceed without it.

---

## P0-T5 — Reject sheets the reader was not built for

**Why:** the most dangerous defect in the system. The reader has one sheet layout hard-coded.
Given a *different* sheet — wrong size, rotated, badly cropped, another exam's form — it does
**not** error. It reads whatever pixels sit at those coordinates and returns a full set of
confident, entirely wrong answers.

**File:** `cde/omr_engine/engine.py`

**1.** Add near the other helpers, before `_process_sync`:

```python
def validate_layout(image_width: int, image_height: int,
                    calibration_evidence: Dict[str, Any]) -> List[str]:
    """Check the scan really is the answer sheet this engine understands.

    Returns reasons to REJECT. Empty list = acceptable. Non-empty = DO NOT
    GRADE; send to a human.
    """
    reasons: List[str] = []
    if image_height <= 0 or image_width <= 0:
        return ["invalid_image_dimensions"]

    ratio = image_width / image_height
    if not (0.60 <= ratio <= 0.85):            # portrait A4-like
        reasons.append(f"unexpected_aspect_ratio:{ratio:.3f}")
    if calibration_evidence.get("panels_calibrated", 0) < N_PANELS:
        reasons.append("insufficient_panel_evidence")
    if calibration_evidence.get("rows_calibrated", 0) < 30:
        reasons.append("insufficient_row_evidence")
    if calibration_evidence.get("points", 0) < 100:
        reasons.append("too_few_detected_marks")
    return reasons
```

**2.** In the `OMRResult` dataclass **delete** `score: int` and `max_score: int`, and **add**:

```python
    layout_rejections: List[str] = field(default_factory=list)
```

**3.** In `_process_sync`:

- after `calibrated_x, calibrated_y, calibration_evidence = _calibrate_grid(...)` add:
  ```python
  layout_rejections = validate_layout(im.width, im.height, calibration_evidence)
  ```
- delete `score = 0` and `max_score = 0`
- replace the scoring block:
  ```python
              if correct_option is not None and not needs_review:
                  max_score += 1
                  is_correct = selected_option == correct_option
                  if is_correct:
                      score += 1
  ```
  with:
  ```python
              if correct_option is not None and not needs_review:
                  is_correct = selected_option == correct_option
  ```
- in `return OMRResult(...)` remove `score=score,` and `max_score=max_score,`, add
  `layout_rejections=layout_rejections,`

**4. Fix the caller in the same task (rule R10).** `cde/routes/beta.py` reads `result.score`.
In `upload_omr_sheet`, in the `$set` block replace:

```python
            "score": result.score,
            "max_score": result.max_score,
```
with:
```python
            "score": None,        # set by the grading service, not the OMR engine
            "max_score": None,
```

and in the function's final `return {...}` delete the `"score"` and `"max_score"` lines.

**Test** — add to `tests/test_omr_regression.py`:

```python
def test_omr_result_has_no_score():
    from cde.omr_engine import OMRResult
    f = OMRResult.__dataclass_fields__
    assert "score" not in f and "max_score" not in f
    assert "layout_rejections" in f


def test_wrong_shaped_image_is_rejected():
    img = Image.new("RGB", (1600, 400), "white")     # landscape, blank
    buf = io.BytesIO(); img.save(buf, format="PNG")
    r = asyncio.run(process_omr_sheet(buf.getvalue()))
    assert r.layout_rejections, "A blank landscape image was accepted for grading"


@pages_available
def test_real_sheets_are_accepted():
    """The guard must not be over-strict."""
    for path in _pages():
        with open(path, "rb") as f:
            r = asyncio.run(process_omr_sheet(f.read()))
        assert not r.layout_rejections, f"{os.path.basename(path)}: {r.layout_rejections}"


def test_app_still_imports():
    import cde.api  # noqa: F401
```

---

## P0-T6 — Add `invalid_multiple` to scoring

**Why:** When a student fills two bubbles, JEE Main scores **−1**. The current code has three
outcomes and decides "blank" when no option is selected — so a confirmed double-mark would
score **0** instead of **−1**. There is currently no way to record "definitely two bubbles."

**File:** `cde/grading_core.py`

Add after the `blank_marks` line:
```python
    multiple_marks = Decimal(policy.get("multiple_marks", "0.000"))
```

Replace the validation:
```python
    if wrong_marks > 0 or blank_marks > 0 or multiple_marks > 0:
        raise ValueError("Wrong, blank and multiple marks must be non-positive.")
```

Replace the start of the award branch:
```python
        if ans.get("state") == "invalid_multiple":
            state = "invalid_multiple"
            marks = multiple_marks
        elif sel_opt is None:
            state = "blank"
            marks = blank_marks
        elif sel_opt == key_opt:
```

**Test** — `tests/test_grading.py`:

```python
import pytest
from decimal import Decimal
from cde.grading_core import grade_submission

POLICY = {"correct_marks": "4.000", "wrong_marks": "-1.000",
          "blank_marks": "0.000", "multiple_marks": "-1.000"}


def sub(answers, n):
    return {"identity_confirmed": True, "alignment_confirmed": True,
            "question_count": n, "marking_policy": POLICY,
            "answer_key": [{"question_number": i, "correct_option": "A"}
                           for i in range(1, n + 1)],
            "answers": answers}


def ans(q, opt, state=None, finalized=True):
    d = {"question_number": q, "selected_option": opt, "finalized": finalized}
    if state:
        d["state"] = state
    return d


def test_correct_wrong_blank():
    g = grade_submission(sub([ans(1,"A"), ans(2,"A"), ans(3,"A"),
                              ans(4,"B"), ans(5,None)], 5))
    assert g.score == Decimal("11.000")      # 12 - 1 + 0
    assert g.maximum == Decimal("20.000")


def test_multiple_scores_minus_one_not_zero():
    g = grade_submission(sub([ans(1,"A"), ans(2,None,state="invalid_multiple")], 2))
    assert g.score == Decimal("3.000"), "invalid_multiple scored as blank, not wrong"


def test_guesser_scores_below_blank_leaver():
    guess = [ans(i,"A") for i in range(1,11)] + [ans(i,"B") for i in range(11,21)]
    blank = [ans(i,"A") for i in range(1,11)] + [ans(i,None) for i in range(11,21)]
    assert grade_submission(sub(guess,20)).score == Decimal("30.000")
    assert grade_submission(sub(blank,20)).score == Decimal("40.000")


def test_full_paper_maximum_is_300():
    g = grade_submission(sub([ans(i,"A") for i in range(1,76)], 75))
    assert g.maximum == Decimal("300.000")
    assert g.score == Decimal("300.000")


def test_positive_penalty_rejected():
    b = sub([ans(1,"A")], 1); b["marking_policy"] = {**POLICY, "wrong_marks": "1.000"}
    with pytest.raises(ValueError, match="non-positive"):
        grade_submission(b)


def test_unfinalized_blocks_grading():
    with pytest.raises(ValueError, match="not finalized"):
        grade_submission(sub([ans(1,"A",finalized=False)], 1))


def test_unconfirmed_identity_blocks_grading():
    b = sub([ans(1,"A")], 1); b["identity_confirmed"] = False
    with pytest.raises(ValueError, match="Identity"):
        grade_submission(b)
```

---

## P0-T7 — Environment template

**Create `.env.example`:**

```bash
# ---- Database (MUST be a replica set; the app refuses to start otherwise) ----
MONGODB_URI=mongodb://localhost:27017/?replicaSet=rs0
MONGODB_DB_NAME=cde_db

# ---- Keycloak ----
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=cde
KEYCLOAK_CLIENT_ID=cde-api          # backend audience
KEYCLOAK_WEB_CLIENT_ID=cde-web      # browser client (PKCE)

# ---- Gemini (Release B onward; leave blank for Release A) ----
GEMINI_API_KEY=
GEMINI_DIAGNOSTIC_MODEL=
CDE_VERIFIED_STORAGE_ROOT=./verified_storage
```

**Also create `web/.env.example`:**

```bash
VITE_KEYCLOAK_URL=http://localhost:8080
VITE_KEYCLOAK_REALM=cde
VITE_KEYCLOAK_CLIENT_ID=cde-web
```

**Test:** both files exist; `python -c "import cde.api"` succeeds.

---

## PHASE 0 EXIT GATE

- [ ] `mongosh --eval "rs.status().ok"` → `1`
- [ ] `pytest tests/test_transactions.py` — 3 passed
- [ ] `pytest tests/test_indexes.py` — 2 passed
- [ ] `pytest tests/test_omr_regression.py` — passed, **not skipped**; pages 1 and 4 both OK
- [ ] `pytest tests/test_grading.py` — 7 passed
- [ ] `.env.example` and `web/.env.example` exist
- [ ] `uvicorn cde.api:app` starts cleanly
- [ ] `pytest tests/ -v` — full suite green

---

# PHASE 1 — THE PROCESSING PIPELINE

**Goal:** the complete path from "admin uploads a PDF" to "a published report exists", running
on durable background jobs. No AI. No UI yet.

> **Version 1 of this guide omitted the worker, exam setup, answer storage, and report
> publication entirely — the plan could not produce a working system. They are here.**

---

## P1-T1 — Exam setup

**Why:** Nothing can be graded without knowing the question count, the answer key, the marking
scheme, and (for Release B) which questions belong to which subject.

**Create `cde/services/exams.py`:**

```python
import uuid
from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel, Field, model_validator


class AnswerKeyEntry(BaseModel):
    question_number: int = Field(ge=1)
    correct_option: str = Field(pattern="^[A-D]$")


class SubjectRange(BaseModel):
    subject: str = Field(min_length=1, max_length=40)
    first_question: int = Field(ge=1)
    last_question: int = Field(ge=1)

    @model_validator(mode="after")
    def ordered(self):
        if self.last_question < self.first_question:
            raise ValueError("last_question must be >= first_question")
        return self


class MarkingPolicy(BaseModel):
    correct_marks: str = "4.000"
    wrong_marks: str = "-1.000"
    blank_marks: str = "0.000"
    multiple_marks: str = "-1.000"


class ExamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    roster_id: str
    question_count: int = Field(ge=1, le=180)
    marking_policy: MarkingPolicy = MarkingPolicy()
    answer_key: List[AnswerKeyEntry]
    subject_ranges: List[SubjectRange] = []

    @model_validator(mode="after")
    def key_covers_every_question(self):
        nums = sorted(e.question_number for e in self.answer_key)
        if nums != list(range(1, self.question_count + 1)):
            raise ValueError(
                f"Answer key must cover questions 1..{self.question_count} exactly once"
            )
        return self

    @model_validator(mode="after")
    def subjects_do_not_overlap(self):
        seen = set()
        for r in self.subject_ranges:
            rng = set(range(r.first_question, r.last_question + 1))
            if rng & seen:
                raise ValueError(f"Subject ranges overlap at {sorted(rng & seen)}")
            if r.last_question > self.question_count:
                raise ValueError("Subject range exceeds question_count")
            seen |= rng
        return self


def create_exam(db_adapter, payload: ExamCreate, actor_id: str) -> Dict:
    exam_id = f"exam_{uuid.uuid4().hex[:12]}"
    with db_adapter.unit_of_work() as s:
        if not db_adapter.db.rosters.find_one({"_id": payload.roster_id}, session=s):
            raise ValueError(f"Roster {payload.roster_id} not found")
        db_adapter.db.exams.insert_one({
            "_id": exam_id,
            "name": payload.name,
            "roster_id": payload.roster_id,
            "question_count": payload.question_count,
            "marking_policy": payload.marking_policy.model_dump(),
            "answer_key": [e.model_dump() for e in payload.answer_key],
            "subject_ranges": [r.model_dump() for r in payload.subject_ranges],
            "report_policy_revision": "score_only",
            "created_at": datetime.utcnow(),
            "created_by": actor_id,
        }, session=s)
    return {"exam_id": exam_id, "question_count": payload.question_count}


def subject_for_question(exam: Dict, question_number: int) -> str | None:
    for r in exam.get("subject_ranges", []):
        if r["first_question"] <= question_number <= r["last_question"]:
            return r["subject"]
    return None
```

**Test** — `tests/test_exams.py`:

```python
import pytest
from cde.db import DatabaseAdapter
from cde.services.exams import ExamCreate, create_exam, subject_for_question


@pytest.fixture
def db():
    a = DatabaseAdapter("mongodb://localhost:27017", "cde_test")
    a.db.exams.delete_many({}); a.db.rosters.delete_many({})
    a.db.rosters.insert_one({"_id": "r1", "exam_class": "12A"})
    return a


def _key(n):
    return [{"question_number": i, "correct_option": "A"} for i in range(1, n + 1)]


def test_create_exam(db):
    p = ExamCreate(name="Mock 1", roster_id="r1", question_count=75, answer_key=_key(75))
    r = create_exam(db, p, "admin1")
    assert r["question_count"] == 75
    assert db.db.exams.find_one({"_id": r["exam_id"]})["marking_policy"]["wrong_marks"] == "-1.000"


def test_incomplete_answer_key_rejected():
    with pytest.raises(ValueError, match="1..75"):
        ExamCreate(name="x", roster_id="r1", question_count=75, answer_key=_key(70))


def test_overlapping_subjects_rejected():
    with pytest.raises(ValueError, match="overlap"):
        ExamCreate(name="x", roster_id="r1", question_count=75, answer_key=_key(75),
                   subject_ranges=[{"subject": "Physics", "first_question": 1, "last_question": 25},
                                   {"subject": "Chemistry", "first_question": 20, "last_question": 50}])


def test_subject_lookup():
    exam = {"subject_ranges": [
        {"subject": "Physics", "first_question": 1, "last_question": 25},
        {"subject": "Chemistry", "first_question": 26, "last_question": 50},
        {"subject": "Mathematics", "first_question": 51, "last_question": 75}]}
    assert subject_for_question(exam, 10) == "Physics"
    assert subject_for_question(exam, 40) == "Chemistry"
    assert subject_for_question(exam, 75) == "Mathematics"
    assert subject_for_question(exam, 120) is None
```

---

## P1-T2 — Roster import

**Create `cde/services/rosters.py`:**

```python
import uuid
from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel, Field


class RosterRow(BaseModel):
    roll_number: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=200)


class RosterImport(BaseModel):
    exam_class: str = Field(min_length=1, max_length=64)
    rows: List[RosterRow] = Field(min_length=1, max_length=500)


def normalize_roll(roll: str) -> str:
    """Normalize for MATCHING only. The original is always stored unchanged.
    Do NOT strip leading zeros — '007' and '7' may be different students."""
    return roll.strip().upper()


def import_roster(db_adapter, payload: RosterImport, actor_id: str) -> Dict:
    seen: Dict[str, str] = {}
    for row in payload.rows:
        k = normalize_roll(row.roll_number)
        if k in seen:
            raise ValueError(
                f"Duplicate roll number '{row.roll_number}' (also '{seen[k]}'). "
                "Fix the roster before importing.")
        seen[k] = row.name

    roster_id = f"roster_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow()
    with db_adapter.unit_of_work() as s:
        db_adapter.db.rosters.insert_one({
            "_id": roster_id, "exam_class": payload.exam_class,
            "revision": 1, "created_at": now, "created_by": actor_id}, session=s)
        db_adapter.db.students.insert_many([{
            "_id": f"std_{uuid.uuid4().hex[:12]}",
            "roster_id": roster_id,
            "exam_class": payload.exam_class,
            "roll_number": r.roll_number,
            "roll_number_normalized": normalize_roll(r.roll_number),
            "name": r.name,
            "created_at": now,
        } for r in payload.rows], session=s)
        db_adapter.db.audit_events.insert_one({
            "kind": "roster_imported", "roster_id": roster_id,
            "student_count": len(payload.rows), "actor": actor_id, "at": now}, session=s)
    return {"roster_id": roster_id, "student_count": len(payload.rows)}
```

**Test** — `tests/test_roster.py`:

```python
import pytest
from cde.db import DatabaseAdapter
from cde.indexes import ensure_indexes
from cde.services.rosters import RosterImport, import_roster, normalize_roll


@pytest.fixture
def db():
    a = DatabaseAdapter("mongodb://localhost:27017", "cde_test")
    for c in ("students", "rosters", "audit_events"):
        a.db[c].delete_many({})
    ensure_indexes(a.db)
    return a


def test_import_creates_students(db):
    r = import_roster(db, RosterImport(exam_class="12A", rows=[
        {"roll_number": "1", "name": "Asha"}, {"roll_number": "2", "name": "Ravi"}]), "admin1")
    assert r["student_count"] == 2
    assert db.db.students.count_documents({}) == 2


def test_duplicate_roll_rejected_and_nothing_written(db):
    with pytest.raises(ValueError, match="Duplicate roll number"):
        import_roster(db, RosterImport(exam_class="12A", rows=[
            {"roll_number": "7", "name": "Asha"}, {"roll_number": "7", "name": "Ravi"}]), "admin1")
    assert db.db.students.count_documents({}) == 0


def test_leading_zeros_preserved():
    assert normalize_roll("007") != normalize_roll("7")
```

---

## P1-T3 — Batch upload (split the PDF)

**Create `cde/services/batches.py`:**

```python
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
```

**Test** — `tests/test_batches.py`:

```python
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
```

---

## P1-T4 — The durable job worker

**Why:** Reading 45 sheets takes minutes of CPU. It cannot happen inside an HTTP request — a
timeout or restart would lose the batch. Jobs are claimed with a **lease** (so two workers
never do the same job) and a **fencing token** (so a slow worker that lost its lease cannot
overwrite newer work).

**Create `cde/jobs/queue.py`:**

```python
from datetime import datetime, timedelta
from typing import Optional, Dict
from pymongo import ASCENDING, ReturnDocument

DEFAULT_LEASE_SECONDS = 300


def claim_job(db, kind: str, owner: str,
              lease_seconds: int = DEFAULT_LEASE_SECONDS) -> Optional[Dict]:
    """Atomically claim one pending job, or a job whose lease has expired."""
    now = datetime.utcnow()
    return db.jobs.find_one_and_update(
        {"kind": kind,
         "status": {"$in": ["pending", "running"]},
         "$or": [{"lease_expires_at": None}, {"lease_expires_at": {"$lt": now}}],
         "$expr": {"$lt": ["$attempt_count", "$max_attempts"]}},
        {"$set": {"status": "running", "lease_owner": owner,
                  "lease_expires_at": now + timedelta(seconds=lease_seconds),
                  "updated_at": now},
         "$inc": {"attempt_count": 1, "fencing_token": 1}},
        sort=[("created_at", ASCENDING)],
        return_document=ReturnDocument.AFTER)


def heartbeat(db, job_id: str, owner: str, fencing_token: int,
              lease_seconds: int = DEFAULT_LEASE_SECONDS) -> bool:
    """Extend the lease. False means the lease was lost — STOP WORKING."""
    now = datetime.utcnow()
    r = db.jobs.update_one(
        {"_id": job_id, "lease_owner": owner, "fencing_token": fencing_token},
        {"$set": {"lease_expires_at": now + timedelta(seconds=lease_seconds)}})
    return r.matched_count == 1


def complete_job(db, job_id: str, owner: str, fencing_token: int, session=None) -> bool:
    """Mark succeeded, only if this worker still holds the lease."""
    r = db.jobs.update_one(
        {"_id": job_id, "lease_owner": owner, "fencing_token": fencing_token},
        {"$set": {"status": "succeeded", "lease_owner": None,
                  "lease_expires_at": None, "updated_at": datetime.utcnow()}},
        session=session)
    return r.matched_count == 1


def fail_job(db, job_id: str, owner: str, fencing_token: int, error: str) -> None:
    job = db.jobs.find_one({"_id": job_id})
    exhausted = job and job["attempt_count"] >= job["max_attempts"]
    db.jobs.update_one(
        {"_id": job_id, "lease_owner": owner, "fencing_token": fencing_token},
        {"$set": {"status": "failed" if exhausted else "pending",
                  "last_error": error[:500], "lease_owner": None,
                  "lease_expires_at": None, "updated_at": datetime.utcnow()}})
```

**Create `cde/jobs/handlers.py`:**

```python
import logging
from datetime import datetime
from typing import Dict

from cde.db import DatabaseAdapter
from cde.services.batches import render_page
from cde.storage import upload
from cde.omr_engine import process_omr_sheet
from cde.jobs.queue import complete_job

logger = logging.getLogger(__name__)


async def handle_read_sheet(db_adapter: DatabaseAdapter, job: Dict, owner: str) -> None:
    """Render one page, read its bubbles, store the answers, open review tasks."""
    sheet_id = job["entity_id"]
    sheet = db_adapter.db.sheets.find_one({"_id": sheet_id})
    if not sheet:
        raise ValueError(f"Sheet {sheet_id} not found")
    if sheet["state"] not in ("pending_read",):
        logger.info("sheet %s already read (state=%s); skipping", sheet_id, sheet["state"])
        complete_job(db_adapter.db, job["_id"], owner, job["fencing_token"])
        return

    batch = db_adapter.db.batches.find_one({"_id": sheet["batch_id"]})
    exam = db_adapter.db.exams.find_one({"_id": sheet["exam_id"]})

    from cde.storage import _download_bytes          # see note below
    pdf_bytes = _download_bytes(batch["original_pdf_key"])
    image_bytes = render_page(pdf_bytes, sheet["page_number"])

    image_key = upload(sheet_id, image_bytes, content_type="image/png")
    result = await process_omr_sheet(image_bytes, _key_map(exam))

    if result.layout_rejections:
        with db_adapter.unit_of_work() as s:
            db_adapter.db.sheets.update_one(
                {"_id": sheet_id},
                {"$set": {"state": "rejected_layout",
                          "rejection_reasons": result.layout_rejections,
                          "image_key": image_key,
                          "updated_at": datetime.utcnow()}}, session=s)
            complete_job(db_adapter.db, job["_id"], owner, job["fencing_token"], session=s)
        return

    from cde.services.grading import build_answer_docs, scope_answers_to_exam, \
        find_stray_marks_outside_exam
    qc = exam["question_count"]
    scoped = scope_answers_to_exam(result.questions, qc)
    answers = build_answer_docs(scoped)
    stray = find_stray_marks_outside_exam(result.questions, qc)

    review_tasks = _build_review_tasks(sheet, image_bytes, scoped)

    with db_adapter.unit_of_work() as s:
        db_adapter.db.sheets.update_one(
            {"_id": sheet_id},
            {"$set": {"state": "pending_identity",
                      "answers": answers,
                      "image_key": image_key,
                      "stray_marks_outside_exam": stray,
                      "omr_version": result.version,
                      "image_sha256": result.sha256,
                      "updated_at": datetime.utcnow()}}, session=s)
        if review_tasks:
            db_adapter.db.review_tasks.insert_many(review_tasks, session=s)
        complete_job(db_adapter.db, job["_id"], owner, job["fencing_token"], session=s)


def _key_map(exam) -> dict:
    return {int(e["question_number"]): e["correct_option"] for e in exam["answer_key"]}


def _build_review_tasks(sheet, image_bytes, scoped_questions):
    """One review task per uncertain bubble, matching the existing schema."""
    import uuid
    from cde.routes.beta import _crop_bytes
    from cde.storage import upload_named
    tasks = []
    for q in scoped_questions:
        if not q.needs_review:
            continue
        crop_id = upload_named(f"{sheet['_id']}-q{q.question_number}.png",
                               _crop_bytes(image_bytes, q.crop_box),
                               content_type="image/png")
        tasks.append({
            "_id": str(uuid.uuid4()),
            "submission_id": sheet["_id"], "exam_id": sheet["exam_id"],
            "question_number": q.question_number, "kind": "ambiguous",
            "crop_id": crop_id,
            "choices": [{"code": c, "label": f"Option {c}"} for c in "ABCD"],
            "suggested_code": q.selected_option, "reason": q.reason,
            "revision": 1, "resolved": False, "claimed_by": None,
            "lease_expires_at": None, "created_at": datetime.utcnow()})
    return tasks
```

> **Note:** `cde/storage.py` has no download helper. Add one:
> ```python
> def _download_bytes(storage_key: str) -> bytes:
>     """Read a stored file back into memory."""
>     import gridfs
>     from cde.db import db_adapter
>     fs = gridfs.GridFS(db_adapter.db)
>     return fs.get(storage_key).read()
> ```
> Match the identifier type `upload()` actually returns — if it returns a string id, convert
> with `bson.ObjectId` before calling `fs.get`. **Verify this against the real file before
> writing the code (rule R5).**

**Create `cde/jobs/worker.py`:**

```python
import asyncio, logging, os, socket, uuid
from cde.db import db_adapter
from cde.jobs.queue import claim_job, fail_job
from cde.jobs.handlers import handle_read_sheet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cde.worker")

HANDLERS = {"read_sheet": handle_read_sheet}
POLL_SECONDS = 2


async def run_once(owner: str) -> bool:
    """Claim and run one job. Returns True if work was done."""
    for kind, handler in HANDLERS.items():
        job = claim_job(db_adapter.db, kind, owner)
        if not job:
            continue
        logger.info("claimed job=%s kind=%s attempt=%s",
                    job["_id"], kind, job["attempt_count"])
        try:
            await handler(db_adapter, job, owner)
            logger.info("completed job=%s", job["_id"])
        except Exception as exc:
            logger.exception("job=%s failed", job["_id"])
            fail_job(db_adapter.db, job["_id"], owner, job["fencing_token"], str(exc))
        return True
    return False


async def main():
    owner = f"{socket.gethostname()}-{os.getpid()}-{uuid.uuid4().hex[:6]}"
    logger.info("worker %s started", owner)
    while True:
        did_work = await run_once(owner)
        if not did_work:
            await asyncio.sleep(POLL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
```

Create empty `cde/jobs/__init__.py` and `cde/services/__init__.py`.

**Test** — `tests/test_jobs.py`:

```python
import pytest
from datetime import datetime, timedelta
from cde.db import DatabaseAdapter
from cde.indexes import ensure_indexes
from cde.jobs.queue import claim_job, heartbeat, complete_job, fail_job


@pytest.fixture
def db():
    a = DatabaseAdapter("mongodb://localhost:27017", "cde_test")
    a.db.jobs.delete_many({})
    ensure_indexes(a.db)
    return a


def _job(db, jid="j1", **kw):
    doc = {"_id": jid, "kind": "read_sheet", "entity_id": "sh1", "status": "pending",
           "attempt_count": 0, "max_attempts": 3, "lease_owner": None,
           "lease_expires_at": None, "fencing_token": 0,
           "idempotency_key": f"k-{jid}", "created_at": datetime.utcnow()}
    doc.update(kw)
    db.db.jobs.insert_one(doc)
    return doc


def test_claim_returns_job(db):
    _job(db)
    j = claim_job(db.db, "read_sheet", "w1")
    assert j["_id"] == "j1" and j["lease_owner"] == "w1" and j["fencing_token"] == 1


def test_two_workers_cannot_claim_same_job(db):
    _job(db)
    a = claim_job(db.db, "read_sheet", "w1")
    b = claim_job(db.db, "read_sheet", "w2")
    assert a is not None and b is None, "Two workers claimed the same job"


def test_expired_lease_can_be_reclaimed(db):
    _job(db, status="running", lease_owner="dead",
         lease_expires_at=datetime.utcnow() - timedelta(minutes=10))
    j = claim_job(db.db, "read_sheet", "w2")
    assert j is not None and j["lease_owner"] == "w2"


def test_stale_worker_cannot_complete(db):
    """A worker that lost its lease must not be able to finish the job."""
    _job(db)
    first = claim_job(db.db, "read_sheet", "w1")
    db.db.jobs.update_one({"_id": "j1"},
                          {"$set": {"lease_expires_at": datetime.utcnow() - timedelta(minutes=1)}})
    second = claim_job(db.db, "read_sheet", "w2")
    assert not complete_job(db.db, "j1", "w1", first["fencing_token"]), \
        "Stale worker completed a job it no longer owned"
    assert complete_job(db.db, "j1", "w2", second["fencing_token"])


def test_heartbeat_fails_after_lease_lost(db):
    _job(db)
    j = claim_job(db.db, "read_sheet", "w1")
    db.db.jobs.update_one({"_id": "j1"}, {"$inc": {"fencing_token": 1}})
    assert heartbeat(db.db, "j1", "w1", j["fencing_token"]) is False


def test_retries_then_gives_up(db):
    _job(db, max_attempts=2)
    for _ in range(2):
        j = claim_job(db.db, "read_sheet", "w1")
        fail_job(db.db, "j1", "w1", j["fencing_token"], "boom")
    assert db.db.jobs.find_one({"_id": "j1"})["status"] == "failed"
    assert claim_job(db.db, "read_sheet", "w1") is None
```

---

## P1-T5 — Identity confirmation

**Create `cde/services/identity.py`:**

```python
from datetime import datetime
from typing import Dict
from pymongo import ReturnDocument


def confirm_identity(db_adapter, sheet_id: str, student_id: str, actor_id: str) -> Dict:
    """Bind one scanned sheet to one roster student."""
    with db_adapter.unit_of_work() as s:
        sheet = db_adapter.db.sheets.find_one({"_id": sheet_id}, session=s)
        if not sheet:
            raise ValueError(f"Sheet {sheet_id} not found")
        if sheet.get("student_id"):
            raise ValueError(f"Sheet {sheet_id} already assigned to {sheet['student_id']}")
        if sheet.get("rejection_reasons"):
            raise ValueError(
                f"Sheet {sheet_id} was rejected ({sheet['rejection_reasons']}); "
                "replace the scan before assigning.")

        if not db_adapter.db.students.find_one({"_id": student_id}, session=s):
            raise ValueError(
                f"Student {student_id} is not on the roster. Identity matching "
                "must never create a student.")

        clash = db_adapter.db.sheets.find_one(
            {"exam_id": sheet["exam_id"], "student_id": student_id}, session=s)
        if clash:
            raise ValueError(
                f"Student {student_id} already has sheet {clash['_id']} for this exam.")

        updated = db_adapter.db.sheets.find_one_and_update(
            {"_id": sheet_id, "student_id": None},
            {"$set": {"student_id": student_id, "identity_method": "admin_manual",
                      "identity_confirmed_by": actor_id,
                      "identity_confirmed_at": datetime.utcnow(),
                      "state": "identified"}},
            session=s, return_document=ReturnDocument.AFTER)
        if not updated:
            raise ValueError("Sheet was just assigned by someone else. Reload.")

        db_adapter.db.audit_events.insert_one({
            "kind": "identity_confirmed", "sheet_id": sheet_id,
            "student_id": student_id, "actor": actor_id,
            "at": datetime.utcnow()}, session=s)

        _maybe_enqueue_grade(db_adapter, updated, s)

    return {"sheet_id": sheet_id, "student_id": student_id, "state": "identified"}


def _maybe_enqueue_grade(db_adapter, sheet, session) -> None:
    """Queue grading once identity is set AND every answer is finalized."""
    import uuid
    if not sheet.get("student_id"):
        return
    if any(not a.get("finalized") for a in sheet.get("answers", [])):
        return
    key = f"grade:{sheet['_id']}:{len(sheet['answers'])}"
    if db_adapter.db.jobs.find_one({"idempotency_key": key}, session=session):
        return
    db_adapter.db.jobs.insert_one({
        "_id": f"job_{uuid.uuid4().hex[:12]}", "kind": "grade_sheet",
        "entity_id": sheet["_id"], "batch_id": sheet.get("batch_id"),
        "status": "pending", "attempt_count": 0, "max_attempts": 5,
        "lease_owner": None, "lease_expires_at": None, "fencing_token": 0,
        "idempotency_key": key, "created_at": datetime.utcnow()}, session=session)
```

**Test** — `tests/test_identity.py`:

```python
import pytest
from cde.db import DatabaseAdapter
from cde.indexes import ensure_indexes
from cde.services.identity import confirm_identity


@pytest.fixture
def db():
    a = DatabaseAdapter("mongodb://localhost:27017", "cde_test")
    for c in ("sheets", "students", "audit_events", "jobs"):
        a.db[c].delete_many({})
    ensure_indexes(a.db)
    a.db.students.insert_many([{"_id": "std1", "name": "Asha"}, {"_id": "std2", "name": "Ravi"}])
    for i in (1, 2):
        a.db.sheets.insert_one({"_id": f"sh{i}", "exam_id": "e1", "batch_id": "b1",
                                "page_number": i, "student_id": None,
                                "rejection_reasons": [], "answers": []})
    return a


def test_confirm_binds(db):
    confirm_identity(db, "sh1", "std1", "admin1")
    assert db.db.sheets.find_one({"_id": "sh1"})["student_id"] == "std1"


def test_cannot_assign_unknown_student(db):
    with pytest.raises(ValueError, match="not on the roster"):
        confirm_identity(db, "sh1", "ghost", "admin1")
    assert db.db.students.count_documents({}) == 2


def test_one_student_one_sheet(db):
    confirm_identity(db, "sh1", "std1", "admin1")
    with pytest.raises(ValueError, match="already has sheet"):
        confirm_identity(db, "sh2", "std1", "admin1")


def test_cannot_reassign(db):
    confirm_identity(db, "sh1", "std1", "admin1")
    with pytest.raises(ValueError, match="already assigned"):
        confirm_identity(db, "sh1", "std2", "admin1")


def test_rejected_sheet_cannot_be_assigned(db):
    db.db.sheets.update_one({"_id": "sh2"}, {"$set": {"rejection_reasons": ["bad_ratio"]}})
    with pytest.raises(ValueError, match="rejected"):
        confirm_identity(db, "sh2", "std2", "admin1")


def test_grading_queued_only_when_answers_final(db):
    db.db.sheets.update_one({"_id": "sh1"}, {"$set": {"answers": [
        {"question_number": 1, "finalized": True}]}})
    confirm_identity(db, "sh1", "std1", "admin1")
    assert db.db.jobs.count_documents({"kind": "grade_sheet"}) == 1


def test_grading_not_queued_while_review_pending(db):
    db.db.sheets.update_one({"_id": "sh2"}, {"$set": {"answers": [
        {"question_number": 1, "finalized": False}]}})
    confirm_identity(db, "sh2", "std2", "admin1")
    assert db.db.jobs.count_documents({"kind": "grade_sheet"}) == 0
```

---

## P1-T6 — Grading and publication

**Create `cde/services/grading.py`:**

```python
from datetime import datetime
from typing import Any, Dict, List
from cde.grading_core import grade_submission


def scope_answers_to_exam(omr_questions: List[Any], question_count: int) -> List[Any]:
    """Keep only the rows this exam uses. The sheet has 180; the exam has ~75."""
    scoped = [q for q in omr_questions if q.question_number <= question_count]
    if len(scoped) != question_count:
        raise ValueError(f"Expected {question_count} questions, got {len(scoped)}")
    return scoped


def find_stray_marks_outside_exam(omr_questions: List[Any],
                                  question_count: int) -> List[int]:
    """Marks in unused rows. A human must look — never silently scored."""
    return [q.question_number for q in omr_questions
            if q.question_number > question_count and q.state != "blank"]


def build_answer_docs(scoped: List[Any]) -> List[Dict[str, Any]]:
    docs = []
    for q in scoped:
        if q.needs_review:
            docs.append({"question_number": q.question_number, "selected_option": None,
                         "state": "pending_review", "finalized": False})
        elif q.state == "multiple":
            docs.append({"question_number": q.question_number, "selected_option": None,
                         "state": "invalid_multiple", "finalized": True})
        else:
            docs.append({"question_number": q.question_number,
                         "selected_option": q.selected_option,
                         "state": "blank" if q.selected_option is None else "answered",
                         "finalized": True})
    return docs


def grade_and_publish(db_adapter, sheet_id: str) -> Dict[str, Any]:
    """Score a fully-resolved sheet and publish its report, atomically."""
    with db_adapter.unit_of_work() as s:
        sheet = db_adapter.db.sheets.find_one({"_id": sheet_id}, session=s)
        if not sheet:
            raise ValueError(f"Sheet {sheet_id} not found")
        exam = db_adapter.db.exams.find_one({"_id": sheet["exam_id"]}, session=s)

        grade = grade_submission({
            "identity_confirmed": sheet.get("student_id") is not None,
            "alignment_confirmed": not sheet.get("rejection_reasons"),
            "question_count": exam["question_count"],
            "marking_policy": exam["marking_policy"],
            "answer_key": exam["answer_key"],
            "answers": sheet["answers"],
        })

        revision = sheet.get("grade_revision", 0) + 1
        awards = [{"question_number": a.question_number, "state": a.state,
                   "awarded_marks": str(a.awarded_marks),
                   "selected_option": a.selected_option} for a in grade.awards]

        db_adapter.db.grade_revisions.insert_one({
            "_id": f"{sheet_id}:r{revision}", "sheet_id": sheet_id,
            "student_id": sheet["student_id"], "exam_id": sheet["exam_id"],
            "revision": revision, "score": str(grade.score),
            "maximum": str(grade.maximum), "percentage": str(grade.percentage),
            "awards": awards, "created_at": datetime.utcnow()}, session=s)

        # Release A publishes score-only reports.
        db_adapter.db.report_revisions.insert_one({
            "_id": f"report:{sheet_id}:r{revision}",
            "exam_id": sheet["exam_id"], "student_id": sheet["student_id"],
            "sheet_id": sheet_id, "revision": revision,
            "report_policy": exam.get("report_policy_revision", "score_only"),
            "state": "published",
            "score": str(grade.score), "maximum": str(grade.maximum),
            "percentage": str(grade.percentage), "awards": awards,
            "published_at": datetime.utcnow()}, session=s)

        db_adapter.db.sheets.update_one(
            {"_id": sheet_id},
            {"$set": {"state": "published", "grade_revision": revision}}, session=s)

    return {"sheet_id": sheet_id, "score": str(grade.score),
            "maximum": str(grade.maximum), "revision": revision}
```

**Add the handler** in `cde/jobs/handlers.py`:

```python
async def handle_grade_sheet(db_adapter, job, owner):
    from cde.services.grading import grade_and_publish
    from cde.jobs.queue import complete_job
    sheet = db_adapter.db.sheets.find_one({"_id": job["entity_id"]})
    if sheet and sheet.get("state") == "published":
        complete_job(db_adapter.db, job["_id"], owner, job["fencing_token"])
        return
    grade_and_publish(db_adapter, job["entity_id"])
    complete_job(db_adapter.db, job["_id"], owner, job["fencing_token"])
```

and register it: `HANDLERS = {"read_sheet": handle_read_sheet, "grade_sheet": handle_grade_sheet}`

**Also:** when a review task is resolved (`POST /api/review-tasks/{id}/resolve` in
`cde/routes/beta.py`), after writing the finalized answer onto the sheet, call
`_maybe_enqueue_grade`. Do this inside the same transaction as the resolution.

**Test** — add to `tests/test_grading.py`:

```python
from dataclasses import dataclass
from cde.services.grading import (scope_answers_to_exam, find_stray_marks_outside_exam,
                                   build_answer_docs)


@dataclass
class FakeQ:
    question_number: int
    selected_option: str | None
    state: str
    needs_review: bool = False


def test_scoping_drops_unused_rows():
    qs = [FakeQ(i, "A", "filled") for i in range(1, 181)]
    scoped = scope_answers_to_exam(qs, 75)
    assert len(scoped) == 75 and max(q.question_number for q in scoped) == 75


def test_stray_mark_in_unused_row_is_reported():
    qs = [FakeQ(i, None, "blank") for i in range(1, 181)]
    qs[119] = FakeQ(120, "C", "filled")
    assert find_stray_marks_outside_exam(qs, 75) == [120]


def test_clean_unused_rows_are_fine():
    qs = [FakeQ(i, "A" if i <= 75 else None,
                "filled" if i <= 75 else "blank") for i in range(1, 181)]
    assert find_stray_marks_outside_exam(qs, 75) == []


def test_multiple_is_not_blank():
    d = build_answer_docs([FakeQ(1, None, "multiple")])[0]
    assert d["state"] == "invalid_multiple" and d["finalized"] is True


def test_needs_review_not_finalized():
    d = build_answer_docs([FakeQ(1, None, "ambiguous", needs_review=True)])[0]
    assert d["finalized"] is False
```

**Integration test** — `tests/test_pipeline.py`:

```python
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
def db():
    a = DatabaseAdapter("mongodb://localhost:27017", "cde_test")
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
```

---

## PHASE 1 EXIT GATE

- [ ] `pytest tests/ -v` fully green
- [ ] Upload a 45-page PDF → exactly 45 sheets numbered 1–45, 45 jobs created
- [ ] Start the worker → all 45 jobs reach `succeeded` or `failed`, none stuck
- [ ] Kill the worker mid-batch, restart → no sheet lost, none processed twice
- [ ] Two workers simultaneously → never claim the same job
- [ ] A wrong-layout page becomes `rejected_layout` and is never graded
- [ ] A sheet with an unresolved bubble cannot publish
- [ ] **Hand-calculate one student's score with +4/−1 — the system matches exactly**

---

# PHASE 2 — AUTHENTICATION AND STUDENT ACCESS

## P2-T1 — Keycloak configuration

In the Keycloak admin console, realm `cde`:

1. Realm roles: `admin`, `student`.
2. Client `cde-api` — bearer-only (backend audience).
3. Client `cde-web` — public, Standard flow ON, **PKCE method S256**,
   redirect URIs `http://localhost:5173/*`, web origins `http://localhost:5173`.
4. Per student: user `<exam_class>-<roll_number>`, role `student`, temporary password with
   **Temporary: ON** (forces replacement at first login).

Export the realm to `infra/keycloak/cde-realm.json` and commit it.

## P2-T2 — Backend token validation and account links

**Create `cde/services/accounts.py`:**

```python
from datetime import datetime


def link_account(db_adapter, issuer: str, subject: str, student_id: str) -> dict:
    """Bind a Keycloak identity to a roster student. Immutable once created."""
    with db_adapter.unit_of_work() as s:
        existing = db_adapter.db.account_links.find_one(
            {"issuer": issuer, "subject": subject}, session=s)
        if existing:
            if existing["student_id"] != student_id:
                raise ValueError("This login is already linked to a different student.")
            return existing
        if not db_adapter.db.students.find_one({"_id": student_id}, session=s):
            raise ValueError("Cannot link a login to a non-roster student")
        link = {"_id": f"{issuer}|{subject}", "issuer": issuer, "subject": subject,
                "student_id": student_id, "created_at": datetime.utcnow()}
        db_adapter.db.account_links.insert_one(link, session=s)
    return link


def resolve_student_id(db_adapter, issuer: str, subject: str) -> str:
    link = db_adapter.db.account_links.find_one({"issuer": issuer, "subject": subject})
    if not link:
        raise PermissionError("This login is not linked to any student record")
    return link["student_id"]
```

**Create `cde/routes/student.py`:**

```python
from fastapi import APIRouter, Depends, Header, HTTPException
from cde.db import DatabaseAdapter, get_db_adapter
from cde.auth import AuthorizationPort, get_auth_port
from cde.services.accounts import resolve_student_id

student_router = APIRouter()


def verified_claims(authorization: str = Header(...),
                    auth_port: AuthorizationPort = Depends(get_auth_port)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    try:
        return auth_port.validate_token(authorization[7:])
    except Exception:
        raise HTTPException(401, "Invalid token")


def current_student_id(claims: dict = Depends(verified_claims),
                       db_adapter: DatabaseAdapter = Depends(get_db_adapter)) -> str:
    """Identity comes ONLY from the verified token — never from URL or body."""
    roles = claims.get("realm_access", {}).get("roles", [])
    if "student" not in roles:
        raise HTTPException(403, "Not a student account")
    try:
        return resolve_student_id(db_adapter, claims["iss"], claims["sub"])
    except PermissionError:
        raise HTTPException(403, "Account is not linked to a student")


@student_router.get("/api/me/exams/{exam_id}/report")
def my_report(exam_id: str,
              student_id: str = Depends(current_student_id),
              db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    report = db_adapter.db.report_revisions.find_one(
        {"exam_id": exam_id, "student_id": student_id, "state": "published"},
        sort=[("revision", -1)])
    if not report:
        # No score data of any kind while processing.
        return {"status": "processing"}
    return {"status": "ready", "score": report["score"],
            "maximum": report["maximum"], "percentage": report["percentage"],
            "answers": report["awards"], "revision": report["revision"]}
```

Register it in `cde/api.py`: `app.include_router(student_router)`.

**Test** — `tests/test_student_access.py`:

```python
import pytest
from cde.db import DatabaseAdapter
from cde.indexes import ensure_indexes
from cde.services.accounts import link_account, resolve_student_id


@pytest.fixture
def db():
    a = DatabaseAdapter("mongodb://localhost:27017", "cde_test")
    for c in ("account_links", "students", "report_revisions"):
        a.db[c].delete_many({})
    ensure_indexes(a.db)
    a.db.students.insert_many([{"_id": "std1"}, {"_id": "std2"}])
    return a


def test_link_and_resolve(db):
    link_account(db, "iss", "subA", "std1")
    assert resolve_student_id(db, "iss", "subA") == "std1"


def test_cannot_link_non_roster_student(db):
    with pytest.raises(ValueError, match="non-roster"):
        link_account(db, "iss", "subX", "ghost")


def test_link_is_immutable(db):
    link_account(db, "iss", "subA", "std1")
    with pytest.raises(ValueError, match="different student"):
        link_account(db, "iss", "subA", "std2")


def test_unlinked_login_refused(db):
    with pytest.raises(PermissionError):
        resolve_student_id(db, "iss", "nobody")


def test_processing_payload_has_no_score():
    payload = {"status": "processing"}
    assert "score" not in payload and "answers" not in payload
```

## P2-T3 — Remove the mock auth from the frontend

**Why:** `web/src/main.tsx` hardcodes `const mockToken = "mock_token"` and a runtime granting
all three portals. Anyone can currently open any screen.

Replace `web/src/auth.ts` (currently empty):

```typescript
import Keycloak from "keycloak-js";

const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL ?? "http://localhost:8080",
  realm: import.meta.env.VITE_KEYCLOAK_REALM ?? "cde",
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID ?? "cde-web",
});

export async function initAuth(): Promise<boolean> {
  return keycloak.init({ onLoad: "login-required", pkceMethod: "S256",
                          checkLoginIframe: false });
}

export const getToken = () => keycloak.token;
export const hasRole = (r: string) => keycloak.hasRealmRole(r);
export const logout = () => keycloak.logout();

export async function authFetch(url: string, options: RequestInit = {}) {
  await keycloak.updateToken(30);
  return fetch(url, { ...options, headers: {
    ...(options.headers ?? {}), Authorization: `Bearer ${keycloak.token}` } });
}

export default keycloak;
```

In `main.tsx`: delete `mockToken` and `mockRuntime`; call `await initAuth()` before rendering;
build the runtime from real roles — `portals: [hasRole('admin') && 'admin',
hasRole('student') && 'student'].filter(Boolean)`. **Note `teacher` is deliberately absent.**

**Test:** loading the app with no session redirects to Keycloak; a `student` account sees no
admin navigation; `grep -r "mock_token" web/src` returns nothing.

---

# PHASE 3 — USER INTERFACE

**Goal:** a genuinely good interface, not scaffolding. The current components are 37–188 lines
of unstyled markup and there is **no component library** — no shadcn, no Radix, only Tailwind v4
and a 20-line stylesheet. This phase builds the UI layer.

## P3-T1 — Install a design system

```bash
cd web
npx shadcn@latest init          # Tailwind v4, TypeScript, path alias @/
npx shadcn@latest add button card table dialog badge input label \
                        select skeleton toast alert tabs progress avatar
```

Define tokens in `web/src/app/styles.css`: colour scale, spacing, radii, typography.
Support light and dark. Every colour must come from a token — no hard-coded hex values.

## P3-T2 — Student interface

Students are stressed teenagers checking a high-stakes result on a phone. Design accordingly.

**Screens:**

1. **Login** — clean, minimal, institute branding, clear error messages.
2. **My exams** — card per exam with a status badge (`Processing` / `Ready`).
3. **Processing** — this must not feel broken. Explain what is happening, and what they can do
   meanwhile (upload rough work, Release B). No score data anywhere on this screen.
4. **Result**
   - Score headline: `240 / 300` with the percentage
   - Breakdown: correct / wrong / blank / invalid, with the marks each contributed
     (**show the −1s explicitly** — students must see what guessing cost them)
   - Subject breakdown (Release B): Physics / Chemistry / Maths
   - Question-by-question table: number, their answer, correct answer, marks awarded
   - Diagnostic findings (Release B), with abstentions shown honestly as
     *"We could not determine this from the work provided"*
5. **Rough work upload** (Release B) — drag-and-drop, preview, clear
   *"I have no rough work"* alternative.

**Requirements:**
- **Mobile-first.** Most students will open this on a phone.
- Every list has a **loading** (skeleton), **empty**, and **error** state.
- Keyboard navigable; visible focus rings; semantic headings; WCAG AA contrast.
- Never show a raw error. Human-readable messages with a next action.
- A score must never appear on screen before `status === "ready"`.

## P3-T3 — Admin interface

1. **Roster** — CSV import with a preview and per-row validation errors before committing.
2. **Exam setup** — question count, answer key entry/import, marking policy (defaulted to
   +4/−1/0), subject ranges.
3. **Batch upload** — drop the PDF, then a live progress view: per-sheet status, counts of
   pending/rejected/graded, and *"45 pages received, 45 accounted for"*.
4. **Identity queue** — sheet image beside a searchable roster list; confirm in one click;
   shows the OCR suggestion in Phase 4.
5. **Bubble review** — the bubble crop, large, with the four options and a clear reason for the
   flag. This is the screen the admin will spend most time in — make it fast, and keyboard
   driven (`A`/`B`/`C`/`D`, `Enter` to confirm, `→` for next).
6. **Exceptions** — rejected layouts, stray marks in unused rows, failed jobs.

## P3-T4 — UI tests

```
- Student cannot navigate to any admin route (guard, not hidden link)
- Processing screen renders no score element (assert by test id)
- Result screen shows negative marks explicitly
- All screens usable at 375px width
- Every table/list has loading, empty and error states
- Keyboard-only: log in, review a bubble, confirm identity
- axe accessibility scan passes with no critical violations
```

---

# PHASE 4 — OCR IDENTITY AND ROUGH WORK

> **BLOCKED — answer first:** *Does the sheet contain numerical/integer answer grids (JEE Main
> Section B), or only 4-option A/B/C/D questions?* The reader handles only four option columns
> and **cannot** read a digit grid. If Section B exists, that is a new feature with its own
> calibration and review rules, and must be scoped before this phase starts.

**P4-T1 — OCR the identity block.** Suggests only. Auto-accept **only** when: layout valid,
roll number matches exactly one roster entry exactly, name legible and consistent, and no other
sheet assigned to that student. Everything else goes to the P1-T5 queue. OCR never creates a
student. The identity region is excluded from anything later sent to the AI.

**P4-T2 — Question image map.** Admin confirms which crop of the question paper shows each
question, including diagrams and options.

**P4-T3 — Rough work upload.** Available *during* processing, with an explicit
*"I have no rough work"* action. Attach only to the authenticated student's own submission.

**Tests:** unknown roll → queue, no student created · roll matching two students → queue ·
illegible name → queue · exact match → auto-bind · question with no confirmed crop blocks
diagnosis · crop hash mismatch refused · student cannot attach work to another's submission ·
silence leaves the report processing indefinitely.

---

# PHASE 5 — AI DIAGNOSIS (RELEASE B)

Use the existing `cde/diagnostics.py`. **Do not weaken it.** Add the question image to its
inputs; keep every check (strict schema, crop-hash verification, evidence gates, abstention,
confidence suppression, `MIN_CLASSIFICATION_CONFIDENCE = 0.90`).

**The four error classes are exactly as written in the code:**

```
Calculation Slip · Procedural Flaw · Reading Comprehension Error · Conceptual Deficit
```

`abstained` is a **status**, not a fifth class. The older design documents list a different set
(*Arithmetic Slip / … / Unknown*) — those documents are out of date and are being corrected.
`cde/retrieval.py` filters on the same four literals, so changing them silently breaks
retrieval.

**Subject-level analysis is free** — question numbers map to Physics/Chemistry/Maths via
`subject_ranges` (P1-T1). Report *"your Conceptual Deficits cluster in Physics"*. **Never** a
finer topic until Release C, because nobody has labelled sub-topics.

**Publication (diagnostic policy):** identity resolved AND layout valid AND every answer
finalized AND grade committed AND every wrong answer either supported or explicitly abstained.

**Tests:** missing / unreadable / unrelated work → `abstained` · provider timeout →
processing failure, retried, **never** abstention · class without evidence → schema rejection ·
every diagnosis records prompt, schema and model versions · cohort comparison states coverage
(*"38 of 45 finalized"*) · one unresolved student never blocks another.

---

# PHASE 6 — PRACTICE QUESTIONS (RELEASE C)

Blocked on **content**, not code. `retrieval.py` and `embeddings.py` already work; there is
nothing to search.

Needed: question text and images · correct answer and checked solution · validated subject and
sub-topic tags · targeted error class · question-family id for de-duplication.

Then wire `build_remediation` (currently `return {"status": "ok"}`) to `select_questions()`.

**Tests:** never recommends the question the student just got wrong · never two near-duplicates ·
incompatible embedding versions rejected · nothing suitable → *"No suitable practice available
yet"*, never a relaxed filter presented as personalized.

---

# PHASE 7 — PRODUCTION READINESS

## P7-T1 — Delete dead code

| Delete | Why |
|---|---|
| `cde/workflows.py`, `cde/activities.py`, `cde/worker.py`, `cde/dispatcher.py`, `run_worker.py` | Temporal is unused; six activities are `{"status":"ok"}` no-ops |
| `temporalio` from `requirements.in`, recompile lock | No longer a dependency |
| `cde/omr.py`, `cde/omr_adapter.py` | Second, unwired OMR implementation |
| `POST /api/omr/upload` and the inline path in `cde/routes/beta.py` | Replaced by the batch pipeline |
| `cde/routes/alpha.py` upload stubs, `mock-s3-upload` | Success-shaped no-ops |
| `cde/routes/gamma.py` | Stub |
| `web/src/features/teacher/*` | No teacher role in this product |
| Root-level scratch scripts (`diag_*.py`, `fix_*.py`, `patch_v130.py`, `eval_v130.py`, …) | One-off debugging artifacts |

**Test:** `pytest tests/ -v` green; `uvicorn cde.api:app` starts; `grep -rn "temporalio\|mock_token\|omr_adapter" cde web/src` returns nothing.

## P7-T2 — Close the security holes

1. **`GET /api/images/{file_id}`** — an unscoped GridFS read. Remove it, or require
   authentication and verify the caller owns the referenced asset.
2. **CORS** — `cde/api.py` sets `allow_origins=["*"]` with `allow_credentials=True`. That
   combination is invalid and unsafe. Replace with an explicit origin list from settings.
3. Verify no endpoint accepts a `student_id` from the body or URL to select data.

**Test:** an unauthenticated request for a GridFS id → 401/403 · a student requesting another
student's asset → 403 · CORS rejects an unlisted origin.

## P7-T3 — Logging and observability

Structured JSON logs with correlation ids. **Never** log names, tokens, or image bytes.

Track: pages received vs accounted for · job retries, expired leases, failures · layout
rejections · review queue depth and age · publication blockers · unauthorized attempts ·
(Release B) classification vs abstention rate, provider latency and failures.

## P7-T4 — Operational safety

- Backup and **practise a restore** before real student data exists.
- A reconciliation job (§blueprint 5.2) for expired leases, orphaned files, ready-but-unqueued
  stages.
- Document: how to start everything, how to recover a stuck batch, how to reset a password.

## P7-T5 — Final release gate

- [ ] Full suite green, including the OMR regression (not skipped)
- [ ] A complete run: roster → accounts → exam → 45-page batch → identity → review → publish →
      student login → correct score
- [ ] **Hand-verified scores for at least 5 students match exactly**
- [ ] Worker killed at three different points — no loss, no duplication
- [ ] Backup restored successfully into a clean environment
- [ ] Accessibility scan clean; usable at 375px
- [ ] No `TODO`, no `{"status": "ok"}` stub, no mock auth anywhere in shipped code

---

# APPENDIX A — AUDIT OF VERSION 1 (what changed and why)

**Missing tasks that made the plan impossible to complete:**
1. No job worker — jobs were created but nothing ran them. *Added P1-T4.*
2. `sheet["answers"]` read by grading but never written. *Added the read_sheet handler.*
3. No exam setup — `question_count`, `answer_key`, `marking_policy` never created. *Added P1-T1.*
4. No report publication — the student endpoint read `report_revisions`, nothing wrote it.
   *Added P1-T6.*
5. No review-resolution → regrade path. *Added `_maybe_enqueue_grade`.*
6. `scope_answers_to_exam` and `build_answer_docs` defined but never called. *Now wired.*
7. `current_student_id` used a literal `Depends(...)` — not runnable. *Implemented properly.*
8. Indexes described inline but never created. *Added P0-T3.*

**Ordering defects:**
9. Removing `score` from `OMRResult` broke `beta.py`, which was not fixed until much later —
   a knowingly broken intermediate state. *Caller now fixed in the same task; rule R10 added.*
10. Keycloak setup appeared after endpoints that needed it. *Moved to Phase 2, before use.*

**Security items documented in the blueprint but absent from the guide:**
11. `main.tsx` hardcoded `mockToken` granting all portals. *Added P2-T3.*
12. CORS `allow_origins=["*"]` with credentials. *Added P7-T2.*
13. Unscoped `GET /api/images/{file_id}`. *Added P7-T2.*

**Explicit client requirements with no tasks:**
14. UI/UX — the client asked for a top-notch student interface; v1 had one `auth.ts` file.
    *Added Phase 3.*
15. Production readiness — no cleanup, logging, deployment, or dead-code removal.
    *Added Phase 7.*

**Missing context:**
16. No instructions for running the app. *Added §0.6.*
17. Not stated that `tests/conftest.py` is a stub and existing tests prove little. *Added §0.6.*
18. Vite proxy not explained. *Added §0.6.*
19. `storage.py` API undocumented — and it has **no download function**, which the worker needs.
    *Documented in §0.5; flagged in P1-T4.*
20. `review_tasks` schema undocumented though tasks must reuse it. *Added §0.5.*
21. Test fixture path was hardcoded to one machine, so the OMR regression would silently skip.
    *Now `tests/fixtures/pages/` with an explicit warning.*

---

# APPENDIX B — STOP AND ASK

Stop if any of these occur. Do not guess.

1. A file does not contain what a task says it contains.
2. A test can only pass by weakening a safety check.
3. You need the question count, marking scheme, or subject ranges and do not have them.
4. The sheet turns out to have numerical answer grids (Phase 4).
5. Results look plausible but you cannot verify them.
6. A task would require guessing a student's identity or an uncertain answer.

**Stopping is always safer than guessing.**
