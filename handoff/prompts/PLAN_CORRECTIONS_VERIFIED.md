# Corrections to the Implementation Plan — verified against the code

The detailed implementation plan is adopted. These are three factual corrections found by
reading the actual source, plus two fixes already applied. Each one changes a task in the
plan, so apply them before Phase 0 scheduling.

---

## Correction 1 — the error taxonomy in §11.6 is not the taxonomy in the code

**Plan §11.6 states:** "There are exactly four error classes: 1. Arithmetic Slip.
2. Procedural Flaw. 3. Conceptual Deficit. 4. Unknown."

**The code has a different four** (`cde/diagnostics.py:20-23`):

```python
ErrorClass = Literal[
    "Calculation Slip", "Procedural Flaw",
    "Reading Comprehension Error", "Conceptual Deficit",
]
```

Differences that matter:
- `Calculation Slip`, not `Arithmetic Slip`.
- **`Reading Comprehension Error` is a real fourth class** that appears in neither the original
  blueprint nor either migration plan.
- **There is no `Unknown` class at all.**

This is not a loose string constant. It is load-bearing in three places:
- `cde/retrieval.py:9` keys its eligibility filters off the **same four literals** — changing
  the taxonomy silently breaks practice-question retrieval.
- The diagnostic prompt in `cde/diagnostics.py:115-202` is built around these four names, with
  worked few-shot examples per class.
- Any persisted diagnostic revisions already use them.

**Three competing taxonomies currently exist in the repository:**

| Source | Classes |
|---|---|
| Blueprint §2.1 assumption 7, and `docs/rough_sheet_diagnostics_blueprint.md` | Arithmetic Slip / Procedural Flaw / Conceptual Deficit / **Unknown** |
| `cde/diagnostics.py` + `cde/retrieval.py` (**the working code**) | Calculation Slip / Procedural Flaw / **Reading Comprehension Error** / Conceptual Deficit |
| Both migration plans | Assumed the blueprint's set |

**Decision required.** Recommend adopting the code's four as canonical — it is the only set
with a validated prompt, few-shot examples and matching retrieval filters behind it — and
updating the blueprint and rough-sheet doc to match, rather than migrating working code to a
taxonomy that exists only on paper. Whichever is chosen, all three sources must be reconciled
in one edit; leaving them divergent guarantees a silent mismatch between what the model
returns and what retrieval filters accept.

---

## Correction 2 — §11.6's abstention concern is already solved, more cleanly than proposed

**Plan §11.6 says:** "If an existing schema requires `Unknown` for unavailable work, migrate or
adapt it so analytics still distinguish abstention from an evidence-supported Unknown
classification."

**No migration is needed.** `cde/diagnostics.py` already implements exactly the separation the
plan is asking for, and enforces it structurally:

```python
class Diagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    status: Literal["classified", "abstained"]
    error_class: ErrorClass | None = None
    abstention_reason: str | None = None
    evidence: list[Evidence]

    @model_validator(mode="after")
    def decision_is_valid(self):
        if self.status == "classified":
            if self.error_class is None or not self.evidence or self.abstention_reason is not None:
                raise ValueError("Classification requires evidence and a class")
        elif self.error_class is not None or not self.abstention_reason:
            raise ValueError("Abstention requires null class and a reason")
        return self
```

Abstention is a `status`, orthogonal to `error_class` — it is impossible to represent an
abstention as a class, or a classification without evidence. This is stronger than the
plan's proposed `status | error_class | reason_code` contract because a validator rejects the
invalid combinations rather than relying on convention.

Also already present and not credited in the plan:
- `MIN_CLASSIFICATION_CONFIDENCE = 0.90`
- `PRIVACY_POLICY = "page1-top15-black-v1"` — the identity redaction §8.4 asks for is
  implemented and versioned.
- `Evidence.bbox` validated as normalized finite coordinates with `0 <= x0 < x1 <= 1`.

**Action:** delete the §11.6 migration task. Keep the contract as-is and extend only its
*inputs* (question images, mapping evidence) as §11.4 describes.

---

## Correction 3 — scoring policy already exists, is correct, and is not wired

**Plan §9.3 says:** "The admin must explicitly configure scoring rules before grading...
Do not silently assume a marking scheme because the sheet contains 180 questions." Correct —
but this is already implemented in `cde/grading_core.py`, which neither plan mentions and
which §15's disposition table omits entirely.

`grade_submission()` already enforces:

```python
policy = submission.get("marking_policy", {})
correct_marks = Decimal(policy.get("correct_marks", "1.000"))
wrong_marks   = Decimal(policy.get("wrong_marks",   "0.000"))
blank_marks   = Decimal(policy.get("blank_marks",   "0.000"))

if wrong_marks > 0 or blank_marks > 0:
    raise ValueError("Wrong and blank marks must be non-positive.")
if correct_marks <= 0:
    raise ValueError("Correct marks must be positive.")
```

Plus, before computing anything:
- refuses to grade unless `identity_confirmed` **and** `alignment_confirmed`
- refuses any answer where `finalized` is false
- requires exact contiguous question coverage `1..question_count`
- rejects duplicate question numbers
- uses `Decimal` with `ROUND_HALF_UP`, not float

That is **negative marking support plus most of the publication predicate from §12.1**,
already written.

**The problem:** it is unreachable. Only `cde/grading.py` imports it; nothing under
`cde/routes/` calls either. The live path scores in `cde/omr_engine/engine.py:392-394`:

```python
max_score += 1
if is_correct: score += 1
```

Flat +1 per correct answer, no marking policy, no penalty, no blank handling — and `beta.py`
writes that number straight onto the submission.

For a 180-question five-panel sheet of this type, flat +1/0 scoring is very likely the wrong
marking scheme, and it is currently the only scheme the running system can produce.

**Action:** add `cde/grading_core.py` to the §15 disposition table as **keep and wire** (not
rewrite). In Phase 1 task 6 ("move OMR and deterministic grading into worker-invoked
services"), the grading service must call `grade_submission()` rather than consume
`OMRResult.score`. `OMRResult` should stop reporting a score at all — per the plan's own §9.2,
extraction returns mark states and the grading service owns scoring.

### 3a. Marking scheme confirmed: **+4 correct / −1 wrong / 0 blank**

`marking_policy` for this exam is therefore:

```json
{ "correct_marks": "4.000", "wrong_marks": "-1.000", "blank_marks": "0.000" }
```

`grading_core` accepts this (it validates `wrong_marks <= 0`) and computes
`maximum = correct_marks × question_count` = **720**, not 180. Three consequences, all of
which raise the priority of wiring it:

**(a) The live path's scores are not merely mis-scaled — they erase student ranking.**
Flat `+1/0` cannot distinguish a guesser from a blank-leaver. Over 180 questions:

| | Correct | Wrong | Blank | Flat (current) | +4/−1 (actual) |
|---|---:|---:|---:|---:|---:|
| Student A | 100 | 80 | 0 | 100/180 = **55.6%** | 400 − 80 = 320/720 = **44.4%** |
| Student B | 100 | 0 | 80 | 100/180 = **55.6%** | 400 − 0 = 400/720 = **55.6%** |

Identical under the current system; **80 marks apart** under the real scheme. Distinguishing
those two students is the entire purpose of negative marking, and the running system currently
erases it. Any diagnostic or cohort analysis built on the current scores inherits this.

**(b) `grading_core` cannot represent a confirmed multiple-mark — and now it must.**
Its award logic is a three-way branch (`cde/grading_core.py`):

```python
if sel_opt is None:        state, marks = "blank",     blank_marks
elif sel_opt == key_opt:   state, marks = "correct",   correct_marks
else:                      state, marks = "incorrect", wrong_marks
```

But `_classify()` in `cde/omr_engine/engine.py` emits **five** states — `blank`, `ambiguous`,
`multiple`, `review_low_resolution`, `filled`. Under +4/−1, a student who marks two bubbles is
normally scored **−1 (invalid)**, not 0. There is currently no way to express that: a reviewer
resolving "the student clearly marked both B and C" must either pick one option
(misrepresenting the sheet, and possibly awarding +4) or leave it null (scored as blank, 0 —
when the policy says −1).

This is exactly the gap the plan flags in §9.3 ("a confirmed multiple-mark/invalid response,
**if the exam policy defines its scoring**"). The policy now does define it. Add an explicit
finalized `invalid_multiple` answer state and a `multiple_marks` entry to `marking_policy`,
and extend the award branch. Do not encode it as `None`.

**(c) The blank/filled threshold is now worth up to 5 marks per question, and is provisional.**
`_classify()` calls blank at `best < 0.18`, with reason strings that say so outright —
`all_options_below_provisional_floor`, `single_candidate_passed_provisional_gate`. Under flat
`+1/0`, misreading a faint real mark as blank cost at most the 1 mark at stake. Under +4/−1:

- a faint **correct** mark read as blank → student loses **4** marks they earned
- a faint **wrong** mark read as blank → student gains **1** mark they should have lost

Same threshold error, now up to a **5-mark swing**, and **asymmetric** — it systematically
favours students whose marking is faint. These thresholds were tuned when a misread was worth
1 mark. They must be re-validated against labeled scans under the real marking scheme before
unattended grading, and the plan's §17.1 OMR evaluation policy should report
confidently-wrong cases **weighted by marks at stake**, not just as a count.

Confirm with the owner whether unattempted-and-cancelled questions, or any partial-credit
rules, also apply before the first real batch.

---

## Correction 4 — the exam is JEE Main (~75 questions), not a 180-question paper

Confirmed by the owner: the pilot exam is **JEE Main format, approximately 75 questions**,
marked **+4 / −1**. Every prior document assumed the sheet's 180-row capacity *was* the exam.
It is not — the BIOME sheet is a high-density institute answer sheet whose row capacity
exceeds this paper's question count.

**(a) Hard incompatibility: the engine and the grader cannot both be right.**

`cde/omr_engine/engine.py` unconditionally emits `TOTAL_QUESTIONS = N_PANELS * N_ROWS = 180`
question results — there is no question-count parameter. `cde/grading_core.py` requires:

```python
expected_numbers = set(range(1, question_count + 1))
actual_numbers   = {a["question_number"] for a in answers}
if actual_numbers != expected_numbers:
    raise ValueError("Missing or unexpected answers. Contiguous coverage required.")
```

With `question_count = 75` and 180 emitted answers, this raises immediately. The two modules
are incompatible for this exam as written. **Neither plan caught this**, because both assumed
a 180-question exam.

Fix: the extraction result must be scoped to the exam's live question range before grading.
Add an explicit `question_count` (or live row range) to the exam record; the grading service
truncates/filters `OMRResult.questions` to `1..question_count` and asserts the remaining rows
are genuinely unused. Do **not** relax `grading_core`'s contiguity check — it is correct, and
it is what caught this.

Also: unused rows 76–180 will be read as `blank`, which is harmless for scoring only if the
answer key covers exactly 1–75 and the grader ignores the rest. If a student stray-marks in
an unused row, that must be a review exception, not a silent −1.

**(b) Maximum marks is 300, not 720.** `maximum = correct_marks × question_count`
= 4 × 75 = **300**. Any UI, report or cohort statistic assuming 180 or 720 is wrong.

**(c) BLOCKING QUESTION — numerical (Section B) answers cannot be read by this engine.**

Current JEE Main structure is 3 subjects × 25 questions, split into **Section A (MCQ, 4
options)** and **Section B (numerical/integer answer)**. The OMR engine reads exactly four
option columns per row (`OPTION_LETTERS = "ABCD"`, `OPTION_OFFSETS` has 4 entries) and has no
capability to read a digit grid.

If this paper includes Section B numerical questions, **the engine structurally cannot grade
them** — this is not a tuning problem, it is a missing feature (a multi-column digit-grid
reader, with its own calibration and its own ambiguity rules). This must be resolved before
Phase 1 scheduling, because it may add substantial scope.

Confirm: does the pilot answer sheet contain only 4-option MCQ rows, or does it also have
numerical/integer grids?

**(d) Good news — a partial topic taxonomy already exists for free.**

Correction/relaxation of the plan's §10.3 and §13.1 ("topics unavailable until an admin
validates a taxonomy"): JEE Main question numbers map deterministically to **Physics /
Chemistry / Mathematics** by range. That is a genuine, ground-truth, zero-authoring subject
label — no model inference and no admin tagging required, just the exam's own structure
recorded on the exam record.

This does **not** provide sub-topic labels (kinematics, thermodynamics, etc.), which still
require admin authoring. But it means Release B can honestly report *"you are weakest in
Chemistry"* and *"your Conceptual Deficits cluster in Physics"* without waiting for Release C
content work. Recommend adding a `subject_ranges` field to the exam record in Phase 1 and
enabling subject-level (not topic-level) analysis in Release B.

---

## Already applied (no action needed)

Two integration breakages from the earlier audit were fixed and verified:

1. `cde/routes/beta.py` imported `fitz`/PyMuPDF, which was pinned in neither `requirements.in`
   nor `requirements.lock` — every PDF upload raised `ImportError`. Replaced with `pypdfium2`
   (already pinned; the blueprint's original choice). Syntax-checked, no `fitz` references
   remain under `cde/`.
2. `google-genai` — required by `cde/diagnostics.py` and `cde/embeddings.py` — was pinned
   nowhere; `requirements.in` still listed `openai`. Swapped and recompiled the lock with
   `uv pip compile`; resolved clean, `google-genai==2.22.0` verified importable.

---

## Note on completeness

The plan text received here is **truncated mid-§18.2** (Minimum observability), so §18.3
onward and any §19+ are missing. The three corrections above cover only what was received.
Send the remainder if there are further sections to reconcile.
