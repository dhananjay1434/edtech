# Answers to the Clarifying Questions (for the migration plan)

These are the owner's confirmed answers to the four clarifying questions raised against
`ARCHITECTURE_MIGRATION_BRIEF.md`. Treat every answer below as a **fixed constraint** for
the architecture and migration plan — not a default to reconsider.

---

## 1. Paper contract

- **One page per student, one fixed layout.** Every submission in the pilot is exactly one
  scanned page, using the same OMR template already tuned in this codebase (the 180-question,
  5-panel BIOME layout in `cde/omr_engine/engine.py`).
- **No stated messy-scan cases for the pilot** (no confirmed rotated pages, duplicate scans,
  missing pages, or mixed exam types in one batch). Do not build heavy tolerance for those
  cases into the pilot critical path — but do not let them fail silently either: any page
  that doesn't match the expected single template (wrong aspect ratio, wrong page count
  signature, etc.) must be routed to an admin review/rejection queue, not force-graded.
- Multi-template support (different layouts per exam) is **out of scope for the pilot**,
  confirmed not needed right now.

## 2. Identity source and account access

- **Authoritative roster is admin-provided, before grading starts.** Admin enters/uploads
  the class roster (name, roll number, class/section) ahead of the exam batch.
- **OCR/identity extraction only matches against this existing roster. It must never create
  a new student record on its own.** Any sheet whose read name/roll number doesn't match a
  roster entry with high confidence — no match, ambiguous match, multiple candidates,
  illegible — goes to an **admin identity-resolution queue**. Grading for that sheet is
  blocked until the admin confirms which roster entry it belongs to (or flags it as
  unresolvable).
- **Account access is decoupled from what OCR reads off a sheet.** The admin issues
  credentials (e.g. a one-time login/PIN per roster entry) directly tied to the roster
  record, independent of the sheet-matching pipeline. Reading a name off a sheet is never,
  by itself, sufficient to grant portal access to that student's data — the roster + admin
  issuance is the actual authorization boundary.

## 3. Content readiness

- **Question papers and answer keys already exist** for the pilot exam. Use these as-is.
- **Topic/question-type tags do NOT exist yet.** There is no current mapping from a question
  number to a subject/topic label beyond the question paper itself. The "what type of
  questions is this student weak on" analysis therefore has **no ground-truth taxonomy to
  draw on today** — do not have the AI invent topic labels ad hoc and present them as
  validated. Either (a) require an admin to tag each question with a topic before the first
  report is generated, or (b) report only at the granularity the current 4-class error
  taxonomy already supports (arithmetic/procedural/conceptual/unknown) and label topic-level
  insight explicitly as unavailable for this pilot.
- **A separate practice-question bank does NOT exist yet.** Semantic-search-based
  personalized practice recommendations (the last stage of the owner's flow) have no content
  to draw from right now. This stage cannot go live for the pilot without content being
  authored/collected first — treat it as blocked on content, not on code.
- Rough-work-to-question mapping is **not pre-established**; per the existing
  `rough_sheet_diagnostics_blueprint.md` design, the diagnostic model itself is expected to
  identify which question each part of the rough work belongs to, abstaining
  (`found_on_rough_sheet: false` / `Unknown`) where it cannot.

## 4. Operational boundaries

- **Scale: one class, one exam, to start** (~45 students). Design for this scale first;
  do not over-build for multi-class throughput yet.
- **Review staffing: the admin/owner only, best-effort, no SLA.** There is no dedicated
  reviewer team and no same-day guarantee. The system must tolerate a review queue sitting
  unresolved for an indefinite period without corrupting state or blocking unrelated work.
- **Hosting/data: no constraints.** Any reasonable cloud host is acceptable; no data
  residency or on-prem requirement for the pilot.
- **Deadline: stated as "today."** See the concern below — this is flagged, not silently
  accepted at face value.
- **Unresolved-result UX: show nothing until fully resolved.** A student's portal shows a
  simple "processing" state until their entire sheet (identity + all bubbles + any
  diagnostics tied to their wrong answers) is finalized — no partial/pending-flagged results
  in the MVP UI.

---

## Concern: the "today" deadline

The requested deadline for a *working pilot* — batch PDF ingestion, admin-verified identity
matching, admin-issued student accounts, wiring the existing diagnostics/retrieval code into
one live flow, and a report a student can actually see — is not something that can be built,
tested, and made safe in the remainder of today. This isn't a matter of typing faster: the
invariants this project has correctly insisted on throughout (`no uncertain answer is
guessed`, `no implied cognition without evidence`, identity resolution requiring admin
confirmation rather than auto-matching) are precisely the kind of safeguards that get quietly
dropped under emergency-speed pressure, and dropping them here means either misgrading real
students or handing out account access on unverified identity — not acceptable trade-offs for
a shortcut.

**What is realistic today:** a thin, honest walking skeleton — one class, one exam, uploaded
as a single 45-page PDF, split into individual sheets, graded by the existing OMR engine
(promising on one labeled page — 175/180, 0 errors — but **not** production-validated; see
`IMPLEMENTATION_PLAN.md` §1), with identity done via **admin-confirmed manual matching for this
first batch** (not full OCR-based auto-matching, which needs more validation than a few
hours allows) and admin-issued logins so students can log in and see only their own finalized
score. That is a real, demoable, non-fake version of the flow — it just defers OCR-based
auto-identity, rough-work diagnostics, topic tagging, and question-bank recommendations to
the days immediately following, in the order laid out in `IMPLEMENTATION_PLAN.md`.

The plan below is written in exactly that shape: **Day 0 (today)** gets a real thin path
end-to-end; the phases after it build out identity automation, diagnostics wiring, and content
in dependency order.
