# Cognitive Diagnostic Engine — Detailed Worker Prompt Pack

**Save this Markdown content as `cde_worker_prompts.md`.**

**Deliverable:** execution instructions for a smaller coding model, not a claim that the application has already been implemented or tested.

**Application type:** web-based application.

**Target users:** institutional educators, assigned reviewers, publishers, and operators. Students initially receive verified email deliveries; they do not have application accounts.

## Important implementation decisions

Your permission to choose the best approach is being used for these explicit adaptations:

1. **Use React + TypeScript, FastAPI, and MongoDB.** The attached blueprint's PostgreSQL/pgvector implementation cannot be copied into that stack unchanged. Database-specific code must be replaced, not disguised as compatible.
2. **Use a MongoDB replica set with transactions.** A standalone MongoDB server is not sufficient. Application-level transactional guards do not magically provide PostgreSQL foreign keys or triggers; the implementation must explicitly enforce the corresponding invariants.
3. **Preserve database-independent reference code mechanically.** A small importer below downloads the supplied Markdown once, freezes its hash, and copies selected fenced blocks without asking another model to regenerate them. This intentionally replaces the original requirement to repeat every reference module inline. It reduces both transcription mistakes and worker-context usage.
4. **Keep Temporal for durable workflows.** Connect to a separately provisioned Temporal service. Do not attempt to configure Temporal to use MongoDB as its persistence backend. Local SDK test environments are for tests, not production persistence.
5. **Keep institutional Keycloak/OIDC, private S3, OpenAI, Resend, and ReportLab.** Provisioned external services remain prerequisites where they are actually needed. Do not invent credentials, regions, account capabilities, or successful integration results.
6. **Use exact cosine ranking over MongoDB-filtered question candidates initially.** This is the explicit replacement for pgvector. Do not add a second vector database. Qualify performance against the actual bank before release.
7. **Keep grading independent from diagnostics and delivery.** Phase 1 must provide a useful product without OpenAI or Resend being configured.
8. **Do not manufacture acceptance thresholds.** Missing physical scans, educator approvals, provider credentials, or restore evidence remain visible gate blockers.

**Source attribution convention:** quoted exit gates below reproduce Section 18. Newly supplied Python, file paths, supporting collections, and API contracts are adaptation specifications—not claims of verbatim blueprint code. The importer is the authority for byte-preserved source blocks.

**Verification status:** the code in this document has not been executed in your repository. The worker must execute the supplied verification steps and report actual results.

---

# A. Global Worker-Model Preamble

Paste this preamble before the selected phase prompt.

```text
ROLE
You are implementing one phase of a specified web application.
Follow instructions literally. Do not redesign, rename, reorganize, or add features.
The application stack is React + TypeScript, FastAPI, and MongoDB.
You have no reliable memory of another phase. The repository and verified handoff
report are your only sources of prior implementation state.

SOURCE AND COPY RULES
1. Files produced by tools/import_reference.py are protected reference files.
2. Do not regenerate, reformat, optimize, or silently repair those files.
3. Put database adaptation and integration behavior in the explicitly named adapters.
4. If a reference file is defective, preserve it and report the exact failing test.
   Make the narrowest documented adapter correction when possible.
5. Never claim newly written adaptation code was copied from the blueprint.

DO NOT INVENT
- Do not invent schema fields, enum values, routes, environment variables, libraries,
  provider method names, retries, thresholds, or business rules outside this prompt.
- Do not add a different application database or queue.
- Do not infer student identity from a similar name.
- Do not infer an answer from uncertain marks.
- Do not infer a cognitive error from a wrong option alone.
- Do not convert a provider failure into a student diagnostic classification.
- Do not claim that a mock establishes live-service correctness.
- Do not turn skipped tests, missing data, or an unimplemented stub into success.

GAPS
For a genuinely unspecified requirement:
  # TODO(gap): <specific missing contract and affected behavior>
Write the narrowest fail-closed stub. Raise an explicit error or return an explicitly
unavailable state. Do not return fabricated successful data.
List the gap in the completion report.
If the gap affects identity, grading, authorization, publication, consent, or external
side effects, block that operation until the gap is resolved.

PRIOR STATE
Read the required handoff report and verify its listed file hashes before editing.
If a required file or migration is missing, stop and report it.
Do not recreate a prior-phase file from memory.
Never reset, force-push, or delete unrelated work.

ATOMIC EXECUTION
Work on one numbered step at a time.
After each step, run its specified tests plus affected existing tests.
A failing command must be fixed and rerun, or reported as BLOCKED.
Do not continue past a broken prerequisite.
Never weaken an assertion simply to obtain a green result.

TESTING HONESTY
Paste actual command output. Do not predict or fabricate it.
Distinguish:
- code checks passed;
- live integration checks passed;
- the literal phase exit gate satisfied.
These are not interchangeable.
A required suite with zero collected tests, unexpected skips, or missing external
prerequisites is not a passing gate.

SECRETS AND PRIVACY
Use synthetic data until institution-approved staging is available.
Never commit .env, tokens, real scans, names, email addresses, presigned URLs,
student work, or raw provider responses to the repository.
Never put provider credentials in the React bundle or OMR container.

CONTEXT LIMIT
If the prompt or output will exceed your context budget, stop at the last verified
atomic step. Write the completion report with next_step. Do not compress, truncate,
or invent the remaining code. Resume using this same phase prompt and that report.

COMPLETION REPORT
Write handoff/phase-N.json with this exact top-level structure:
{
  "phase": N,
  "status": "complete | code_ready_gate_blocked | blocked",
  "code_commit": "actual git commit or null",
  "source_sha256": "actual frozen source digest",
  "files": [{"path": "relative/path", "sha256": "actual digest"}],
  "commands": [{"command": "actual command", "exit_code": 0,
                "output_file": "relative/path/to/captured/output"}],
  "migrations": [],
  "contracts_changed": [],
  "exit_gate": {"satisfied": false, "evidence": [], "blockers": []},
  "open_gaps": [],
  "next_step": null
}
Use one actual status value, not the descriptive alternatives shown above.
Record the code commit before creating the report; do not create a circular hash
requirement by including the report in its own files array.
Also print a short human-readable "Phase N Completion Report" and "Open Gaps".
```

## Product and interface direction

- Operational educator workspace, not a promotional landing page.
- Clear exam and submission context on every screen.
- Persistent status labels for uploaded, awaiting review, graded, diagnostic unavailable, report ready, and delivery unknown.
- Review screens show the evidence crop next to the decision controls.
- Show task version and lease expiry; reject stale saves instead of overwriting another reviewer.
- Distinguish score, diagnostic interpretation, report publication, provider acceptance, and actual delivery.
- Use accessible labels, keyboard-operable forms, visible focus, and non-color-only status indicators.
- Never label a student as unintelligent, careless, dishonest, disabled, or low ability.

## Overall user flow

Publish an approved exam revision → register a roster-linked upload → verify and retain the scan → align and read marks → resolve uncertainty → lock a deterministic grade → diagnose only supported wrong-answer evidence → show cohort insights → retrieve approved practice → render and review a report → explicitly release eligible delivery → reconcile the delivery outcome.

---

# B. Phase Dependency & File Map

All paths are relative to the repository root. The outer `cde/` directory in the source's repository illustration is the root, not an instruction to create `cde/cde/cde`.

Files marked **adaptation** are newly specified here. Existing source paths are retained where practical. Tests are created in the source's test-directory families.

| Phase | Files created or first owned | MongoDB collections first created | API surface first implemented |
|---|---|---|---|
| 0 | `pyproject.toml`, `requirements.in`, `requirements.lock`, `.gitignore`, `cde/__init__.py`, `tools/import_reference.py`, `tools/verify_handoff.py`, `reference/source.md`, `reference/source.lock.json`, `reference/copied-blocks.json`, `cde/omr.py`, `templates/a4-demo-v1.json`, `docs/contracts.md`, `evaluation/acceptance-policy.json`, `tests/unit/test_reference_integrity.py`, `tests/unit/test_template_contract.py`, `tests/omr_golden/test_phase0_gate.py` | None | None; template preview is a local specimen artifact |
| 1 | `cde/config.py`, `cde/db.py`, `cde/migrate.py`, `migrations/001_core.py`, `cde/auth.py`, `cde/uploads.py`, `cde/omr_adapter.py`, `cde/grading_core.py`, `cde/grading.py`, `cde/review.py`, `cde/stages.py`, `cde/dispatcher.py`, `cde/workflows.py`, `cde/activities.py`, `cde/worker.py`, `cde/api.py`, `web/`, `infra/keycloak/cde-realm.json`, `tests/unit/test_grading_core.py`, Phase 1 integration/access/recovery tests | `schema_migrations`, `users`, `students`, `sheet_templates`, `questions`, `exams`, `exam_questions`, `answer_keys`, `exam_roster`, `exam_access`, `uploads`, `submissions`, `sheet_pages`, `student_answers`, `hitl_tasks`, `idempotency_records`, `stage_runs`, `outbox_events`, `audit_events` | Health, exams/publication, uploads/completion, submission status, review queue/claim/renew/resolve, operator retry |
| 2 | `prompts/diagnose-v1.txt`, `schemas/diagnostic-v1.json`, `cde/diagnostics_reference.py`, `cde/diagnostics.py`, `cde/evidence.py`, `cde/provider_budget.py`, `migrations/002_diagnostics.py`, diagnostic review UI/tests | `error_taxonomy_results`, `provider_budget_windows`, `provider_reservations` | Diagnostic reads, work-mapping resolution, diagnostic override |
| 3 | `cde/embeddings_reference.py`, `cde/embeddings.py`, `cde/retrieval.py`, `cde/analytics.py`, `cde/report_reference.py`, `cde/report.py`, `migrations/003_analytics_reports.py`, `fonts/manifest.json`, analytics/report UI/tests | `cohort_analytics`, `remediation_jobs`, `remediation_items` | Analytics snapshots, remediation generation, report status/download |
| 4 | `cde/email_reference.py`, `cde/email_policy.py`, `cde/email.py`, `cde/email_event_applier.py`, `cde/telemetry.py`, `migrations/004_delivery.py`, `infra/Dockerfile.api`, `infra/Dockerfile.worker`, `infra/Dockerfile.web`, `infra/Caddyfile`, `docker-compose.yml`, release/delivery UI, recovery runbook/tests | `email_events`; delivery fields/indexes added to `remediation_jobs` | Report release, delivery status, signed Resend webhook, operator reconciliation |

### Protected reference ownership

| Source section | Destination | Created in |
|---|---|---|
| 5.1 | `cde/omr.py` | Phase 0 |
| 5.2 | `templates/a4-demo-v1.json` | Phase 0 |
| 8.2 | `prompts/diagnose-v1.txt` | Phase 2 |
| 8.4 | `schemas/diagnostic-v1.json` | Phase 2 |
| 8.5 | `cde/diagnostics_reference.py` | Phase 2 |
| 10.3 | `cde/embeddings_reference.py` | Phase 3 |
| 10.7 | `cde/report_reference.py` | Phase 3 |
| 11.3 | `cde/email_reference.py` | Phase 4 |

The importer must stop if a requested section does not contain exactly one fence in the specified language. It must not choose a vaguely similar block.

### Frozen adaptation rules

- UUID identifiers are canonical lowercase UUID strings in MongoDB.
- An entity's source `id` becomes MongoDB `_id`; do not store two competing identities.
- All persisted timestamps are BSON UTC dates.
- Decimal marks, scores, and percentages use BSON `Decimal128`; API representations are decimal strings.
- References remain explicit ID fields; embedding an entire mutable student record in every submission is prohibited.
- `version` is added to submissions and mutable publication aggregates for compare-and-set fencing.
- Stage `fence` is an explicit monotonically increasing integer.
- Do not set TTL indexes on submissions, tasks, outbox events, audit events, idempotency decisions, or delivery evidence.
- Collection validators reject unknown top-level fields. Deliberately extensible objects such as evidence and provider usage must still be validated at their application boundary.
- MongoDB validators cannot enforce cross-collection membership or historical immutability. Those checks require transactional services, controlled write credentials, and adversarial integration tests.

---

# C. One Execution Prompt per Phase

## Clarifications Needed Before Phase 0

**Decision adopted:** preserve reference code using a mechanical importer rather than putting a potentially transformed copy of a very large module into a small model's context.

**Still external:** representative physical scans and educator approval. The worker may prepare code and synthetic fixtures, but must not manufacture this evidence.

````markdown
# PHASE 0 PROMPT — Data and paper contract

## 1. Objective

Establish the approved sheet-template, identity, question/work mapping, grading, and evaluation contracts. Produce template-preview/specimen artifacts and executable reference checks; do not make automated cognitive claims.

This is a React + TypeScript, FastAPI, MongoDB web application. This phase has no application database or live AI requirement.

## 2. In scope / Out of scope

IN SCOPE
- Freeze the supplied reference document and extract its OMR/template code mechanically.
- Validate template structure and approved physical assumptions.
- Prepare synthetic geometry tests and the real-scan evaluation manifest contract.
- Record unresolved institutional acceptance thresholds explicitly.

OUT OF SCOPE
- Upload API, authentication, database, grading persistence, review workflow.
- AI, analytics, retrieval, report delivery.
- SKIP — out of scope for this build: student portal, rich formula rendering,
  broader language support, scanner calibration UI, SIS sync,
  multi-institution controls, longitudinal learning progress.

## 3. Prerequisites

- An empty or explicitly approved working directory.
- Python 3.12 and a terminal.
- Network access to the exact supplied artifact URL, or an unmodified local copy
  placed at reference/source.md.
- Do not assume Docker, real scans, provider credentials, or institutional approval.

If the directory contains an unrelated application, stop instead of replacing it.

## 4. Deliverables

Create exactly:
- pyproject.toml
- requirements.in
- requirements.lock, generated by the dependency resolver
- .gitignore
- cde/__init__.py
- tools/import_reference.py
- tools/verify_handoff.py
- reference/source.md
- reference/source.lock.json
- reference/copied-blocks.json
- cde/omr.py, through the importer only
- templates/a4-demo-v1.json, through the importer only
- docs/contracts.md
- evaluation/acceptance-policy.json
- tests/unit/test_reference_integrity.py
- tests/unit/test_template_contract.py
- tests/omr_golden/test_phase0_gate.py
- handoff/phase-0.json

## 5. Steps

### Step 1 — Create the minimal project configuration

Write pyproject.toml:

```toml
[project]
name = "cognitive-diagnostic-engine"
version = "0.1.0"
requires-python = ">=3.12,<3.13"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
addopts = "-ra --strict-markers"
markers = [
  "live: requires explicitly configured real services",
  "gate: requires external acceptance evidence",
]
```

Write requirements.in:

```text
numpy>=1.26,<3
opencv-python-headless>=4.10,<5
pypdfium2>=4.30,<6
Pillow>=10,<13
pytest
```

The numerical-library ranges come from the source's standalone OMR installation
instructions. The resulting lockfile must contain resolved versions and hashes;
do not type imaginary lock entries.

Write .gitignore:

```gitignore
.venv/
__pycache__/
.pytest_cache/
.env
.env.*
!.env.example
node_modules/
web/dist/
artifacts/
private-data/
*.log
```

Create an empty cde/__init__.py.

Run:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install pip-tools
pip-compile --generate-hashes --output-file=requirements.lock requirements.in
python -m pip install --require-hashes -r requirements.lock
python -m pip check
```

Expected: dependency resolution, installation, and pip check succeed. Network or
resolution failure is a blocker, not permission to invent versions.

### Step 2 — Create the exact-source importer

Write tools/import_reference.py with this complete content:

```python
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
URL = (
    "https://customer-assets-4nw71qhi.emergentagent.net/"
    "job_daab7c77-d9c1-4db4-b0b0-73550965f901/artifacts/"
    "43u04b5g_cognitive_diagnostic_engine_blueprint.md"
)
SOURCE = ROOT / "reference/source.md"
LOCK = ROOT / "reference/source.lock.json"
MANIFEST = ROOT / "reference/copied-blocks.json"
MAX_SOURCE_BYTES = 4 * 1024 * 1024

TARGETS = {
    0: [
        ("5.1", "python", "cde/omr.py"),
        ("5.2", "json", "templates/a4-demo-v1.json"),
    ],
    2: [
        ("8.2", "text", "prompts/diagnose-v1.txt"),
        ("8.4", "json", "schemas/diagnostic-v1.json"),
        ("8.5", "python", "cde/diagnostics_reference.py"),
    ],
    3: [
        ("10.3", "python", "cde/embeddings_reference.py"),
        ("10.7", "python", "cde/report_reference.py"),
    ],
    4: [("11.3", "python", "cde/email_reference.py")],
}

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def frozen_source() -> bytes:
    SOURCE.parent.mkdir(parents=True, exist_ok=True)
    if not SOURCE.exists():
        if LOCK.exists():
            raise SystemExit("Frozen source missing; restore it, do not replace it")
        with urlopen(URL, timeout=60) as response:
            data = response.read(MAX_SOURCE_BYTES + 1)
        if len(data) > MAX_SOURCE_BYTES:
            raise SystemExit("Source exceeds the importer limit")
        if b"# Cognitive Diagnostic Engine" not in data[:4096]:
            raise SystemExit("Unexpected source content")
        SOURCE.write_bytes(data)
    data = SOURCE.read_bytes()
    if len(data) > MAX_SOURCE_BYTES:
        raise SystemExit("Source exceeds the importer limit")
    current = digest(data)
    if LOCK.exists():
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        if lock["sha256"] != current:
            raise SystemExit("Frozen source hash mismatch")
    else:
        LOCK.write_text(
            json.dumps({"url": URL, "sha256": current}, indent=2) + "\n",
            encoding="utf-8",
        )
    return data

def blocks(data: bytes) -> list[dict]:
    text = data.decode("utf-8")
    result = []
    section = None
    opened = None
    language = None
    collected = []
    block_section = None
    for line in text.splitlines(keepends=True):
        stripped = line.rstrip("\r\n")
        if opened is not None:
            closing = re.fullmatch(
                re.escape(opened[0]) + "{" + str(len(opened)) + ",}" + r"\s*",
                stripped,
            )
            if closing:
                result.append({
                    "section": block_section,
                    "language": language,
                    "data": "".join(collected).encode("utf-8"),
                })
                opened = None
                collected = []
            else:
                collected.append(line)
            continue
        heading = re.match(r"^#{1,6}\s+(\d+(?:\.\d+)*)(?:\s|$)", stripped)
        if heading:
            section = heading.group(1)
        opening = re.fullmatch(r"(`{3,}|~{3,})([^\r\n]*)", stripped)
        if opening:
            opened = opening.group(1)
            info = opening.group(2).strip().split()
            language = info[0] if info else ""
            block_section = section
            collected = []
    if opened is not None:
        raise SystemExit("Unclosed source fence")
    return result

def import_phase(phase: int) -> None:
    data = frozen_source()
    candidates = blocks(data)
    manifest = (
        json.loads(MANIFEST.read_text(encoding="utf-8"))
        if MANIFEST.exists() else {}
    )
    for section, language, relative in TARGETS[phase]:
        matches = [b for b in candidates
                   if b["section"] == section and b["language"] == language]
        if len(matches) != 1:
            raise SystemExit(
                f"Expected one {language} block in section {section}; "
                f"found {len(matches)}. Stop; do not select a substitute."
            )
        content = matches[0]["data"]
        target = ROOT / relative
        if target.exists() and target.read_bytes() != content:
            raise SystemExit(f"Protected destination differs: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        manifest[relative] = {
            "section": section,
            "language": language,
            "sha256": digest(content),
            "source_sha256": digest(data),
        }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"phase": phase, "source_sha256": digest(data),
                      "files": [x[2] for x in TARGETS[phase]]}, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", type=int, choices=sorted(TARGETS), required=True)
    import_phase(parser.parse_args().phase)
```

Run:

```bash
python tools/import_reference.py --phase 0
python -m compileall -q cde/omr.py tools/import_reference.py
python -m cde.omr --help
python tools/import_reference.py --phase 0
```

Expected:
- Source and extracted file digests are printed.
- Compilation succeeds.
- OMR help displays successfully.
- Second import changes no protected code bytes.

Do not claim the fetched source digest was known before running this command.

### Step 3 — Create the prior-state verifier

Write tools/verify_handoff.py:

```python
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report")
    parser.add_argument("--allow-gate-pending", action="store_true")
    args = parser.parse_args()
    report_path = ROOT / args.report
    report = json.loads(report_path.read_text(encoding="utf-8"))
    permitted = {"complete"}
    if args.allow_gate_pending:
        permitted.add("code_ready_gate_blocked")
    if report["status"] not in permitted:
        raise SystemExit("Prior phase is not in an allowed state")
    if not report["files"]:
        raise SystemExit("Handoff has no verified files")
    lock = json.loads((ROOT / "reference/source.lock.json").read_text())
    if report["source_sha256"] != lock["sha256"]:
        raise SystemExit("Source version differs from prior phase")
    for item in report["files"]:
        path = (ROOT / item["path"]).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise SystemExit(f"Missing or invalid handoff path: {item['path']}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != item["sha256"]:
            raise SystemExit(f"Handoff hash mismatch: {item['path']}")
    print(f"Verified phase {report['phase']} handoff")

if __name__ == "__main__":
    main()
```

The optional flag is not permission to waive a gate. Use it only when the human
explicitly authorizes further non-production development despite a pending gate.
Record that authorization in the next report.

Run:

```bash
python -m compileall -q tools/verify_handoff.py
```

Expected: compilation succeeds.

### Step 4 — Freeze the paper and identity contracts

Write docs/contracts.md with these exact decisions, using headings and checklists:

- One uploaded PDF belongs to one roster student.
- A file may contain at most ten pages, all from the approved template manifest.
- Canonical reference page: 2480 × 3508 pixels at 300 DPI.
- Four ordered corner markers plus the asymmetric orientation marker are required.
- A missing marker, mirrored sheet, ambiguous orientation, unexpected page,
  missing page, or wrong template must not silently yield a grade.
- Student identity comes from a validated roster-linked manifest or validated
  printed identifier. Similar-name matching is prohibited.
- An identity conflict creates human review and blocks grading.
- Question numbers are unique, positive, and exactly match the published exam.
- Answer options for the reference template are A, B, C, D, E.
- Work regions must be explicitly associated with questions.
- Missing or uncertain work mapping causes diagnostic abstention, not score changes.
- The two-question demo template is a specimen, not approval for every exam layout.
- A homography supports the declared flat-sheet geometry, not arbitrary curled paper.
- No synthetic test result is a physical-scan accuracy claim.

Run:

```bash
python -m json.tool templates/a4-demo-v1.json > /dev/null
```

Expected: valid JSON.

### Step 5 — Record acceptance requirements without inventing values

Write evaluation/acceptance-policy.json:

```json
{
  "schema_version": 1,
  "approved_by": null,
  "approved_at": null,
  "omr": {
    "dataset_manifest": null,
    "maximum_false_finalization_rate": null,
    "minimum_evaluation_cases": null,
    "approved_template_hashes": []
  },
  "diagnostics": {
    "dataset_manifest": null,
    "minimum_precision_by_class": {
      "Calculation Slip": null,
      "Procedural Flaw": null,
      "Reading Comprehension Error": null,
      "Conceptual Deficit": null
    },
    "minimum_evidence_localization_score": null,
    "acceptance_policy_version": null
  }
}
```

Null means NOT APPROVED. Do not substitute zero, 0.9, 95%, or an assumed sample size.

The physical-scan manifest must identify de-identified student/scanner groups,
source hashes, template hashes, expected answers, ambiguity labels, reviewer
labels, and train/validation/held-out assignment. Do not put real scans in git.

Run:

```bash
python -m json.tool evaluation/acceptance-policy.json > /dev/null
```

Expected: valid JSON, with unresolved values remaining null.

### Step 6 — Write reference-integrity tests

Write tests/unit/test_reference_integrity.py:

```python
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_frozen_source_hash():
    lock = json.loads((ROOT / "reference/source.lock.json").read_text())
    source = (ROOT / "reference/source.md").read_bytes()
    assert hashlib.sha256(source).hexdigest() == lock["sha256"]

def test_copied_blocks_are_unchanged():
    manifest = json.loads((ROOT / "reference/copied-blocks.json").read_text())
    assert manifest
    for relative, record in manifest.items():
        content = (ROOT / relative).read_bytes()
        assert hashlib.sha256(content).hexdigest() == record["sha256"], relative
```

Run:

```bash
python -m pytest -q tests/unit/test_reference_integrity.py
```

Expected: both tests pass.

### Step 7 — Write template and geometry tests

Create tests/unit/test_template_contract.py.

Use the imported module's actual function signatures. Inspect that file; do not
invent another OMR API. Required cases:

1. The imported template loads with canonical dimensions and A–E options.
2. Duplicate question numbers are rejected or caught by the adapter contract.
3. An out-of-bounds bubble or work box is rejected.
4. A generated specimen aligns at rotations 0, 90, 180, and 270 degrees.
5. Missing fiducial produces explicit rejection.
6. Mirrored specimen produces explicit rejection or an objectively verified mapping;
   never silently assume its answer labels are correct.
7. Wrong/extra/missing page mapping cannot become a finalized answer set.

Generate synthetic pixel fixtures from the actual template coordinates.
Do not alter the template to make these tests pass.
Do not add a handwritten-identity recognizer.

Run:

```bash
python -m pytest -q tests/unit/test_template_contract.py
```

Expected: all cases pass, or a precise reference defect is reported and phase
status remains blocked. If a boundary check belongs in an adapter, specify it
without editing the protected module.

### Step 8 — Implement the real Phase 0 gate test

Create tests/omr_golden/test_phase0_gate.py, marked gate.

It must fail with an actionable message if approved physical fixtures or educator
sign-off are absent. It must not skip or accept synthetic fixtures as substitutes.
When supplied, it verifies:
- representative physical scans align to correct mappings or explicitly fail;
- template/question/key revisions are approved;
- educators have approved the exact taxonomy and abstention rules.

Run:

```bash
python -m pytest -q tests/omr_golden/test_phase0_gate.py
```

Expected when evidence is supplied: pass.
Expected without evidence: a clear gate failure and code_ready_gate_blocked status.

## 6. DO NOT INVENT

- Do not change OMR thresholds to reduce the review queue.
- Do not claim the demo template is institution-approved.
- Do not create artificial educator approval or physical scans.
- Do not add database or provider configuration to this phase.
- Do not edit imported source code to hide a failing case.

## 7. Final verification

```bash
python tools/import_reference.py --phase 0
python -m compileall -q cde tools
python -m pytest -q tests/unit/test_reference_integrity.py tests/unit/test_template_contract.py
python -m pytest -q tests/omr_golden/test_phase0_gate.py
```

Paste actual output. A pending physical gate is not phase completion.

## 8. Definition of Done / Exit Gate

Literal source Section 18 exit gate:

**Exit gate:** representative scans align correctly or fail explicitly; educators agree on question IDs, key revisions, and the four-class taxonomy/abstention rules.

In addition, all executable checks above must have actual successful output before
status can be complete. This is proof of the gate, not a replacement for its wording.

## 9. Phase 0 Completion Report

Write handoff/phase-0.json using the global report schema.
Include protected-source hashes, test outputs, external gate evidence, and every gap.
Print:
- Phase 0 Completion Report
- Files created
- Tests actually passing
- Gate satisfied or blocked
- Exact code commit or null
- Open Gaps
- Next atomic step, if incomplete
````

## Clarifications Needed Before Phase 1

**Decision adopted:** MongoDB transactions plus shared-parent writes replace SQL row-locking in application services. This is not equivalent to installing the source's SQL triggers.

**Additional contracts fixed here:** UUID-string identifiers, Decimal128 values, stage fencing, explicit idempotency records, and an immutable workflow `pipeline_target`.

**External blockers:** a usable replica set, institutional OIDC configuration, S3 configuration, an approved malware-verification adapter, and held-out physical scans. Malware verification must fail closed until a real adapter is selected.

````markdown
# PHASE 1 PROMPT — Deterministic grading + durable review

## 1. Objective

Implement safe ingestion, durable review, institutional authorization, and locked
deterministic grading. An educator must be able to recover from worker crashes and
resolve uncertain answers without losing tasks or changing an already locked grade.

Stack: React + TypeScript, FastAPI/Python 3.12, MongoDB replica-set transactions,
Temporal, private S3, and institutional Keycloak/OIDC.

Do not require OpenAI or Resend for Phase 1 startup or grading.

## 2. In scope / Out of scope

IN SCOPE — mandatory P0
- Database validators/index migrations and publication/membership checks.
- Institutional authorization and assigned-exam queries.
- Quarantine upload, integrity checks, immutable accepted source.
- Isolated OMR, durable tasks, claim/renew/resolve UI.
- Transactional outbox, stage fencing, durable workflow, locked grading.
- Operator-visible failures and the prescribed crash tests.

OUT OF SCOPE
- Diagnostic calls, embeddings, cohort analytics, PDFs, email.
- SKIP — out of scope for this build: student portal, rich formula rendering,
  broader language support, scanner calibration UI, SIS sync,
  multi-institution controls, longitudinal learning progress.

## 3. Prerequisites check

Run:

```bash
python tools/verify_handoff.py handoff/phase-0.json
python -m pytest -q tests/unit/test_reference_integrity.py tests/unit/test_template_contract.py
```

Required files:
- cde/omr.py and templates/a4-demo-v1.json
- docs/contracts.md
- evaluation/acceptance-policy.json
- reference/source.lock.json
- requirements.lock

Missing or changed prior files: stop, report, do not recreate.

Required for live integration:
- MONGODB_URI and MONGODB_DATABASE
- OIDC_ISSUER, OIDC_AUDIENCE, OIDC_JWKS_URL, OIDC_WEB_CLIENT_ID
- WEB_ORIGIN
- S3_BUCKET, AWS_REGION
- TEMPORAL_ADDRESS, TEMPORAL_NAMESPACE and service-auth material supplied securely

Do not invent credentials. Use an explicitly isolated synthetic integration database.

## 4. Exact files to create/edit

Create:
- cde/config.py, cde/db.py, cde/migrate.py
- migrations/001_core.py
- cde/auth.py, cde/uploads.py, cde/omr_adapter.py
- cde/grading_core.py, cde/grading.py, cde/review.py, cde/stages.py
- cde/dispatcher.py, cde/workflows.py, cde/activities.py, cde/worker.py
- cde/api.py
- web/package.json, web/package-lock.json, web/index.html
- web/tsconfig.json, web/vite.config.ts
- web/src/main.tsx, web/src/App.tsx, web/src/api.ts, web/src/auth.ts
- web/src/pages/ExamPage.tsx, SubmissionPage.tsx, ReviewPage.tsx, OperatorPage.tsx
- infra/keycloak/cde-realm.json
- tests/unit/test_grading_core.py
- tests/integration/test_phase1.py
- tests/authorization/test_phase1_access.py
- tests/failure_injection/test_phase1_recovery.py
- tests/omr_golden/test_phase1_gate.py

Edit requirements.in and regenerate requirements.lock.
Do not edit cde/omr.py.

## 5. Frozen database contract

Create only the collections needed by this phase.
Source field names are preserved except id → _id and the explicit additions below.

Common entity IDs: canonical UUID strings.
Common timestamps: BSON UTC dates.
Nullable fields must be explicitly nullable; do not confuse absent with null.

Collections and essential fields:

- users:
  _id, oidc_subject, display_name, enabled, is_operator, created_at.
- students:
  _id, roll_number, display_name, email, email_verified_at, email_consent_at,
  preferred_language, active, created_at, updated_at.
- sheet_templates:
  _id, name, version, specification, sha256, approved_by, approved_at.
- questions:
  _id, family_id, revision, stem, options, correct_option, explanation,
  distractor_explanations, subject, topic_code, concept_code, procedure_code,
  difficulty, target_skill, language, phrasing_variant, approved, active,
  embedding, embedding_model, embedding_input_sha256, created_at.
  embedding is null in this phase.
- exams:
  _id, series_id, revision, title, subject, state, template_id, question_count,
  correct_marks, wrong_marks, blank_marks, omr_threshold, trap_threshold,
  created_by, created_at, published_at, version.
- exam_questions:
  _id, exam_id, question_number, question_id.
- answer_keys:
  _id, exam_id, question_number, correct_option, approved_by, approved_at.
- exam_roster:
  _id, exam_id, student_id, current_submission_id, excluded_reason.
- exam_access:
  _id, exam_id, user_id, can_review, can_publish.
- submissions:
  _id, exam_id, student_id, revision, original_object_key, original_version_id,
  original_sha256, template_id, workflow_id, state, identity_confirmed,
  alignment_confirmed, answers_locked_at, graded_at, score, maximum_score,
  percentage, failure_code, failure_detail, created_at, updated_at, version,
  pipeline_target.
- sheet_pages:
  _id, submission_id, page_index, aligned_object_key, aligned_sha256,
  width_px, height_px, homography, clockwise_rotation, quality_metrics.
- student_answers:
  _id, submission_id, exam_id, question_number, machine_option,
  machine_confidence, density_metrics, selected_option, finalized, source,
  state, awarded_marks, reviewed_by, finalized_at.
- hitl_tasks:
  _id, submission_id, kind, question_number, dedup_key, state,
  evidence_object_key, machine_suggestion, decision, claimed_by,
  lease_expires_at, resolved_by, resolved_at, version, created_at, updated_at.
- stage_runs:
  _id, submission_id, stage, input_fingerprint, state, attempt, fence,
  lease_owner, lease_expires_at, result, error_code, started_at, finished_at.
- outbox_events:
  _id, kind, dedup_key, aggregate_id, payload, attempts, available_at,
  lease_owner, lease_expires_at, fence, dispatched_at, last_error, created_at.
- audit_events:
  _id, actor_user_id, actor_service, action, resource_type, resource_id,
  correlation_id, details, created_at.

New supporting collections, explicitly authorized adaptation:

- uploads:
  _id, exam_id, student_id, created_by, mime_type, expected_size,
  expected_sha256, quarantine_key, quarantine_version_id, accepted_object_key,
  accepted_version_id, state, malware_verdict, submission_id, created_at,
  expires_at, version.
  states: registered, verifying, accepted, rejected.
  malware_verdict: null, clean, infected, unavailable.
- idempotency_records:
  _id, actor_id, operation, resource_id, key, request_sha256,
  response_status, response_body, created_at.
- schema_migrations:
  _id, checksum, applied_at.

Exact enums:
- answer option: A, B, C, D, E.
- answer state: pending, correct, incorrect, blank.
- answer source: machine, reviewer.
- exam state: draft, published, closed, archived.
- task kind: identity, alignment, bubble, work_mapping, diagnostic.
- task state: open, claimed, resolved, superseded, cancelled.
- submission state: uploaded, validating, preparing, reading, awaiting_identity,
  awaiting_alignment, awaiting_review, grading, diagnosing, remediating, ready,
  delivery_pending, completed, needs_operator, cancelled, superseded.
- run state: pending, running, succeeded, retrying, failed, cancelled.
- practice skill: accuracy, procedure, reading, foundation.

Required unique indexes:
- users(oidc_subject)
- students(roll_number)
- sheet_templates(name, version), sheet_templates(sha256)
- questions(family_id, revision)
- exams(series_id, revision)
- exam_questions(exam_id, question_number), exam_questions(exam_id, question_id)
- answer_keys(exam_id, question_number)
- exam_roster(exam_id, student_id)
- exam_access(exam_id, user_id)
- submissions(exam_id, student_id, revision), submissions(workflow_id)
- sheet_pages(submission_id, page_index)
- student_answers(submission_id, question_number)
- hitl_tasks(submission_id, dedup_key)
- stage_runs(submission_id, stage, input_fingerprint)
- outbox_events(dedup_key)
- idempotency_records(actor_id, operation, resource_id, key)

Also index the actual queue/query predicates:
- submissions(exam_id, state)
- hitl_tasks(state, kind, created_at), hitl_tasks(submission_id, state)
- stage_runs(state, lease_expires_at)
- outbox_events(dispatched_at, available_at)
- exam_access(user_id, exam_id)
- exam_roster(current_submission_id)
- student_answers(exam_id, question_number, selected_option)

No TTL cleanup of durable work.
No production migration may silently drop a collection or index.

## 6. Atomic implementation steps

### Step 1 — Dependencies and typed configuration

Add these approved dependency families to requirements.in:

```text
fastapi
uvicorn[standard]
pydantic>=2,<3
pydantic-settings
pymongo
boto3
temporalio
PyJWT[crypto]
httpx
```

Regenerate the hash lock and install it:

```bash
pip-compile --generate-hashes --output-file=requirements.lock requirements.in
python -m pip install --require-hashes -r requirements.lock
python -m pip check
```

Implement config.py using typed settings with no secret defaults.
Phase 1 must not validate OPENAI_API_KEY or RESEND_API_KEY.
Use fixed application contracts for ports/paths, and typed environment variables
only for actual deployment configuration.

An unavailable live service makes readiness false; it must not prevent pure
unit-test imports of grading_core.py.

Run:

```bash
python -m compileall -q cde/config.py
```

### Step 2 — MongoDB transaction boundary

Write cde/db.py with this core. Extend only with explicitly required lifecycle
wiring; do not change transaction semantics.

```python
from __future__ import annotations

from typing import Callable, TypeVar

from pymongo import MongoClient, ReturnDocument
from pymongo.read_concern import ReadConcern
from pymongo.read_preferences import ReadPreference
from pymongo.write_concern import WriteConcern

T = TypeVar("T")

class InvariantViolation(RuntimeError):
    pass

class Conflict(RuntimeError):
    pass

def connect(uri: str) -> MongoClient:
    return MongoClient(
        uri,
        tz_aware=True,
        serverSelectionTimeoutMS=5000,
        retryWrites=True,
    )

def require_replica_set(client: MongoClient) -> None:
    hello = client.admin.command("hello")
    if not hello.get("setName"):
        raise InvariantViolation("MONGODB_REPLICA_SET_REQUIRED")

def transact(client: MongoClient, callback: Callable) -> T:
    with client.start_session() as session:
        return session.with_transaction(
            callback,
            read_concern=ReadConcern("snapshot"),
            write_concern=WriteConcern("majority"),
            read_preference=ReadPreference.PRIMARY,
            max_commit_time_ms=10000,
        )

def touch_unlocked_submission(db, session, submission_id: str) -> dict:
    document = db.submissions.find_one_and_update(
        {
            "_id": submission_id,
            "answers_locked_at": None,
            "state": {"$nin": ["cancelled", "superseded"]},
        },
        {"$inc": {"version": 1}},
        session=session,
        return_document=ReturnDocument.AFTER,
    )
    if document is None:
        raise Conflict("SUBMISSION_MISSING_LOCKED_OR_TERMINAL")
    return document
```

Important:
- with_transaction may rerun its callback.
- Never call S3, Temporal, email, or AI inside that callback.
- Every answer writer and grader must write the same parent submission before
  touching answer rows. A read-only parent check is not enough to prevent write skew.
- Synchronous PyMongo calls must not block the FastAPI event loop. Use synchronous
  route/service execution or an explicitly managed executor at the async boundary.

Run:

```bash
python -m compileall -q cde/db.py
```

### Step 3 — Validators and idempotent migrations

Implement migrations/001_core.py using the collection contract above.

Use MongoDB $jsonSchema validators with:
- required identifiers and invariant-bearing fields;
- additionalProperties: false at document top level;
- BSON date types for timestamps;
- BSON decimal for marks/scores;
- explicit enum lists;
- positive question/revision numbers;
- difficulty between 1 and 5;
- confidence between 0 and 1;
- source reviewer implies a non-null reviewed_by, checked in the service;
- finalized answers require finalized_at, checked in the service;
- stored correct/incorrect/blank states require finalized answers.

Implement cde/migrate.py:
- command: python -m cde.migrate;
- verify replica-set support;
- apply migrations in numerical order;
- record migration ID and actual file checksum;
- stop if an applied migration's checksum changed;
- create/update validators and indexes idempotently;
- mark applied only after every migration action succeeds;
- serialize migration execution as a deployment job, not on every API replica.

Cross-collection publication, membership, and immutability are transaction-service
requirements, not capabilities supplied by $jsonSchema.

Run twice:

```bash
python -m cde.migrate
python -m cde.migrate
```

Expected: both succeed; second run applies nothing new and preserves all data.

### Step 4 — Deterministic grading kernel

Write cde/grading_core.py:

```python
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Mapping, Sequence

OPTIONS = frozenset("ABCDE")
THREE_PLACES = Decimal("0.001")

@dataclass(frozen=True)
class FinalAnswer:
    question_number: int
    selected_option: str | None
    finalized: bool

@dataclass(frozen=True)
class GradePolicy:
    correct_marks: Decimal
    wrong_marks: Decimal
    blank_marks: Decimal

@dataclass(frozen=True)
class AnswerAward:
    question_number: int
    state: str
    awarded_marks: Decimal

@dataclass(frozen=True)
class Grade:
    awards: tuple[AnswerAward, ...]
    score: Decimal
    maximum_score: Decimal
    percentage: Decimal

def exact_decimal(value: Decimal) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError("Marks must be finite Decimal values")
    if value != value.quantize(THREE_PLACES):
        raise ValueError("Marks may have at most three decimal places")
    return value

def calculate_grade(
    question_count: int,
    answer_key: Mapping[int, str],
    answers: Sequence[FinalAnswer],
    policy: GradePolicy,
) -> Grade:
    if type(question_count) is not int or question_count <= 0:
        raise ValueError("Invalid question count")
    correct = exact_decimal(policy.correct_marks)
    wrong = exact_decimal(policy.wrong_marks)
    blank = exact_decimal(policy.blank_marks)
    if correct <= 0 or wrong > 0 or blank > 0:
        raise ValueError("Invalid grading policy")
    expected = set(range(1, question_count + 1))
    if set(answer_key) != expected or any(type(k) is not int for k in answer_key):
        raise ValueError("Incomplete or invalid answer-key coverage")
    if any(option not in OPTIONS for option in answer_key.values()):
        raise ValueError("Invalid answer-key option")
    by_number = {}
    for answer in answers:
        if type(answer.question_number) is not int:
            raise ValueError("Invalid answer number")
        if answer.question_number in by_number:
            raise ValueError("Duplicate answer")
        if answer.finalized is not True:
            raise ValueError("Unfinalized answer")
        if answer.selected_option is not None and answer.selected_option not in OPTIONS:
            raise ValueError("Invalid selected option")
        by_number[answer.question_number] = answer
    if set(by_number) != expected:
        raise ValueError("Incomplete answer coverage")
    awards = []
    for number in range(1, question_count + 1):
        selected = by_number[number].selected_option
        if selected is None:
            state, marks = "blank", blank
        elif selected == answer_key[number]:
            state, marks = "correct", correct
        else:
            state, marks = "incorrect", wrong
        awards.append(AnswerAward(number, state, marks))
    score = sum((a.awarded_marks for a in awards), Decimal("0"))
    maximum = correct * question_count
    percentage = (score * Decimal("100") / maximum).quantize(
        THREE_PLACES, rounding=ROUND_HALF_UP
    )
    return Grade(tuple(awards), score, maximum, percentage)
```

ROUND_HALF_UP and three-place percentage serialization are explicit adaptation
choices. Do not use binary floats or clamp a legitimate negative score to zero.

Write tests/unit/test_grading_core.py:

```python
from decimal import Decimal

import pytest

from cde.grading_core import FinalAnswer, GradePolicy, calculate_grade

def test_correct_wrong_blank_with_negative_marking():
    grade = calculate_grade(
        3,
        {1: "A", 2: "B", 3: "C"},
        [FinalAnswer(1, "A", True), FinalAnswer(2, "D", True),
         FinalAnswer(3, None, True)],
        GradePolicy(Decimal("4"), Decimal("-1"), Decimal("0")),
    )
    assert grade.score == Decimal("3")
    assert grade.maximum_score == Decimal("12")
    assert grade.percentage == Decimal("25.000")
    assert [a.state for a in grade.awards] == ["correct", "incorrect", "blank"]

def test_negative_percentage_is_not_clamped():
    grade = calculate_grade(
        1, {1: "A"}, [FinalAnswer(1, "B", True)],
        GradePolicy(Decimal("1"), Decimal("-1"), Decimal("0")),
    )
    assert grade.percentage == Decimal("-100.000")

def test_missing_answer_is_not_a_blank():
    with pytest.raises(ValueError, match="coverage"):
        calculate_grade(1, {1: "A"}, [],
                        GradePolicy(Decimal("1"), Decimal("0"), Decimal("0")))

def test_unfinalized_answer_is_rejected():
    with pytest.raises(ValueError, match="Unfinalized"):
        calculate_grade(1, {1: "A"}, [FinalAnswer(1, "A", False)],
                        GradePolicy(Decimal("1"), Decimal("0"), Decimal("0")))

def test_duplicate_answer_is_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        calculate_grade(1, {1: "A"},
                        [FinalAnswer(1, "A", True), FinalAnswer(1, "A", True)],
                        GradePolicy(Decimal("1"), Decimal("0"), Decimal("0")))
```

Run:

```bash
python -m pytest -q tests/unit/test_grading_core.py
```

Expected: five tests pass.

### Step 5 — Transactional grade adapter

Implement cde/grading.py with a grade_submission(client, db, submission_id) service.

The transaction callback must perform these exact operations in order:
1. Read the submission. Missing submission is an invariant error.
2. If answers_locked_at is set, verify stored grade fields exist and return them.
   Do not recalculate or update answers on this retry path.
3. Touch the unlocked parent using touch_unlocked_submission.
4. Verify identity_confirmed and alignment_confirmed.
5. Load the exact referenced exam revision; require published/closed immutable content.
6. Verify submission.template_id equals exam.template_id.
7. Verify roster membership. Do not automatically repoint current_submission_id.
8. Verify no unresolved identity, alignment, or bubble tasks remain.
9. Read answer-key and answer rows using the same MongoDB session.
10. Convert stored Decimal128 policy values to Decimal.
11. Call calculate_grade with complete coverage.
12. Update every answer's state and awarded_marks using this session.
13. Set score, maximum_score, percentage, graded_at, answers_locked_at last.
14. Set state=ready for pipeline_target=1. Later targets advance through explicitly
    implemented later-stage orchestration, never guessed activities.
15. Insert a grade.locked audit event in the same transaction.
16. Commit and return the stored grade shape.

If any update matches fewer rows than expected, abort the transaction.
Return decimal strings at the API boundary, not JSON floats.

Add integration cases in tests/integration/test_phase1.py for a concurrent reviewer
versus grader, repeated grading, missing identity, incomplete key, and partial
answer coverage.

Run the grading subset:

```bash
python -m pytest -q tests/integration/test_phase1.py -k grading
```

Expected: exactly one committed locked grade; no post-lock answer mutation.

### Step 6 — Central authorization and exam publication

Implement cde/auth.py and the relevant routes in cde/api.py.

Token checks: trusted signature, explicit algorithm allowlist, exact issuer,
audience, expiry, and access-token type. Reject ID tokens where access tokens are
required. Bound JWKS cache lifetime and support key rotation.

After token validation:
- locate users.oidc_subject;
- require enabled=true;
- apply exam_access predicates to queries before pagination or aggregation;
- require can_review/can_publish for those actions;
- is_operator does not bypass student-work authorization.

Responses:
- 401: unauthenticated/invalid token;
- 404: resource outside the user's visible exam assignments;
- 403: visible resource, missing requested capability.

Publication transaction:
- touch the draft exam's version;
- require contiguous question numbers 1..question_count;
- require an approved question revision and matching answer key for every number;
- require approved template coverage;
- reject inconsistent bank/key answers;
- freeze content through all authorized mutation services;
- create new revisions for corrections.

Provision Keycloak realm cde, public client cde-web, code flow + PKCE S256,
exact callback origin, API audience cde-api, no password/implicit flows,
no wildcard redirect and no demo credentials. Use the configured institution's
issuer. Verify the realm import against its actual Keycloak version; do not guess
unsupported JSON keys.

Run:

```bash
python -m pytest -q tests/authorization/test_phase1_access.py
```

Expected: the 401/403/404 matrix passes for anonymous, assigned viewer, reviewer,
publisher, unassigned, revoked, and scoped worker identities.

### Step 7 — Quarantine uploads and idempotent acceptance

Implement cde/uploads.py and these exact routes:

- POST /api/exams/{exam_id}/uploads
- POST /api/uploads/{upload_id}/complete
- GET /api/submissions/{submission_id}

Registration body:

```json
{
  "student_id": "UUID string",
  "mime_type": "application/pdf",
  "size_bytes": 12345,
  "sha256": "64 lowercase hexadecimal characters"
}
```

Registration:
- authorize the exam and roster student before signing;
- persist uploads before issuing credentials;
- use a random quarantine object key, never a filename;
- return a bounded S3 presigned POST;
- enforce exact key/MIME constraints and size at most 25 MiB;
- retain intent across interrupted transfers.

Completion:
- authorize again;
- verify the actual object version, byte count, magic signature, SHA-256 and
  malware verdict;
- do not trust ETag or the client's Content-Type/hash;
- unavailable malware verification must not return clean;
- publish an immutable accepted object and verify its version/checksum;
- transactionally create submission + workflow.start outbox + idempotency result;
- preserve the accepted object if the database commit fails; reconcile it, do not
  create another logical submission blindly.

Exact successful completion response, HTTP 202:

```json
{
  "submission_id": "UUID string",
  "status_url": "/api/submissions/UUID string",
  "state": "uploaded"
}
```

Idempotency-Key is bound to actor, operation, resource and canonical request hash.
Same key/body returns the stored logical response. Same key/different body is 409.
A new upload does not silently supersede a locked or published processing revision.

Run:

```bash
python -m pytest -q tests/integration/test_phase1.py -k upload
```

Expected: duplicate completion yields one submission and one start intent;
invalid or unverified source cannot be accepted.

### Step 8 — OMR adapter and durable review

Implement cde/omr_adapter.py without modifying cde/omr.py.

- Call the imported reference through its real function/CLI contract.
- One document per isolated PDFium process.
- Enforce 25 MiB, ten pages, 20 million pixels/page, 120-second OMR stage budget,
  and a 1 GiB OMR container memory limit.
- A PDFium crash gets at most one clean-process retry within that budget.
- Validate exact expected question coverage before persisting finalized answers.
- Partial OMR results never become a complete graded submission.
- Persist review tasks for identity/alignment/bubble uncertainty.
- A machine suggestion is not a finalized answer when review is required.
- Preserve crops, page coordinates, hashes, orientation and alignment metadata.

Implement cde/review.py and routes:
- GET /api/exams/{exam_id}/review-tasks
- POST /api/review-tasks/{task_id}/claim
- POST /api/review-tasks/{task_id}/renew
- POST /api/review-tasks/{task_id}/resolve

Claim body: {"expected_version": integer}.
Renew body: {"expected_version": integer}.
Bubble resolve body:

```json
{
  "expected_version": 2,
  "decision": {"selected_option": "A"}
}
```

selected_option=null means an explicitly reviewed blank.
Use an Idempotency-Key for claim/renew/resolve mutations.

Lease duration is an explicitly recorded deployment policy, not an invisible magic
number. If not configured, claim writes fail with configuration unavailable.

Resolution order inside one transaction:
1. Authorize the actor for the task's actual exam.
2. Check an existing matching idempotency record before checking lease expiry;
   a valid replay after resolution must return its stored result.
3. Touch the parent submission to serialize answer writers and grading.
4. Check task kind, expected version, claimant, unexpired lease and unresolved state.
5. Validate the decision against the task kind and question options.
6. Finalize the answer and record reviewer/source/timestamp.
7. Resolve the task and increment its version.
8. Insert audit event, resume outbox intent, and idempotency result.
9. Commit everything together.

An expired lease or stale browser gets 409 and must refetch.
Resolved tasks are immutable; no overwrite API.
A different idempotency key cannot be used to silently change a resolved decision.

Identity/alignment resolutions must store approved corrected mappings and trigger
safe re-evaluation before grading; a generic "accept anyway" button is prohibited.

Run:

```bash
python -m pytest -q tests/integration/test_phase1.py -k 'review or omr'
```

Expected: one decision wins concurrent resolution; expired/stale requests fail;
all uncertain states remain visible and recoverable.

### Step 9 — Stage fencing, outbox and Temporal

Implement cde/stages.py:
- logical stage identity is (submission_id, stage, input_fingerprint);
- lease acquisition atomically increments fence;
- a worker's result commit must match its fence, owner, running state and valid lease;
- result, domain writes, audit and stage success commit together;
- a stale worker cannot commit after another worker acquired the stage;
- an already succeeded fingerprint returns its stored result;
- never hold a database transaction open during rendering or provider calls.

Use attempt-specific temporary S3 keys. Only the winning fenced transaction may
publish a verified object reference as the accepted stage artifact. A stale process
must not overwrite the current artifact at a shared mutable key.

Implement cde/dispatcher.py:
- lease an undispatched event with a fencing token;
- perform the external dispatch outside the database transaction;
- mark dispatched only under the same fence;
- leave the event pending if the process dies after dispatch;
- duplicate start/signal must be logically safe.

Workflow ID: submission/{submission_uuid}/r{revision}.
Reject duplicate workflow-ID reuse. Treat a matching already-started workflow as
success only after confirming its intended submission/revision.

Implement cde/workflows.py with immutable workflow input:

```json
{
  "submission_id": "UUID string",
  "processing_revision": 1,
  "pipeline_target": 1
}
```

pipeline_target is server-selected and frozen; the browser cannot set it.
Phase 1 accepts target=1 only. Keep the workflow name and input contract stable.
Later phases add branches only for newly supported targets and must replay the
existing target=1 histories before deployment.

Activity contracts:
- validate_and_prepare_identity(submission_id)
- prepare_and_read(submission_id)
- review_gate(submission_id, gate)
- grade(submission_id)
- mark_failed(submission_id, failed_stage)

Read authoritative state inside activities, not inside workflow code.
Never use nondeterministic database/network/time calls inside the workflow.

Avoid lost wakeups:
- snapshot a signal sequence counter before awaiting review_gate;
- if gate is ready, continue;
- otherwise wait until the sequence differs, then check the database gate again.
A signal is a wakeup, not the authoritative review decision.

Register actual SDK activities/workflows in cde/worker.py.
Use cde-omr, cde-ai, cde-io task queues; do not start an AI worker in Phase 1.
Register only implemented activities. Do not create fake successful future stages.

Transport retry configuration must be explicit and bounded. Preserve the source's
failure classes: deterministic invalid inputs are not retried; human waits are not
polling retry loops; provider retry policy is deferred to Phase 2.
Do not add another queue library.

Run:

```bash
python -m pytest -q tests/failure_injection/test_phase1_recovery.py
```

Required checkpoints:
- after S3 write before database commit;
- after review commit before workflow signal;
- after grade commit before activity acknowledgement;
- duplicate workflow start and duplicate signal;
- Temporal outage and eventual outbox recovery;
- stale fenced worker attempting to commit.

Expected: no lost tasks, one logical grade, persisted output reuse, no discarded intent.

### Step 10 — React workspace

Use React + TypeScript + Vite and TanStack Query. Use shadcn/ui components only
through actual installed exports; do not invent component APIs.

Implement only:
- exam/roster/submission list;
- bounded direct-to-S3 upload progress;
- durable submission status and score;
- review queue with evidence crop, task version, claimant and lease expiry;
- bubble decision with explicit blank option;
- visible 409 conflict recovery;
- operator failure/checkpoint view.

Authorization is enforced in the API regardless of hidden UI controls.
Do not store tokens in query-string URLs. Use Authorization Code + PKCE and a
reviewed token lifecycle. Runtime configuration contains only public values.

Frozen API additions:
- GET /api/health/live → 200 {"status":"alive"}
- GET /api/health/ready → 200 when Phase 1 dependencies are usable, otherwise 503
- GET /api/exams
- GET /api/exams/{exam_id}
- POST /api/exams/{exam_id}/publish
- POST /api/submissions/{submission_id}/retry, operator action with audit reason

The mutation services for exam/bank/template import must validate the frozen
contracts; do not add a general unauthenticated JSON database editor.

Run:

```bash
cd web
npm ci
npm run typecheck
npm test -- --run
npm run build
cd ..
```

Expected: typecheck, actual UI tests and production build succeed.
If package scripts are missing, implement the named scripts rather than claiming
these commands passed.

## 7. Tests and verification

```bash
python -m cde.migrate
python -m pytest -q tests/unit/test_grading_core.py
python -m pytest -q tests/integration/test_phase1.py
python -m pytest -q tests/authorization/test_phase1_access.py
python -m pytest -q tests/failure_injection/test_phase1_recovery.py
python -m pytest -q tests/omr_golden/test_phase1_gate.py
```

The physical OMR gate must use held-out scans split by student/scanner, report
false finalization, false blanks, accuracy, review rate and input-condition results.
An absent approved bound or insufficient dataset fails the gate.

## 8. DO NOT INVENT

- No standalone-Mongo transaction fallback.
- No claim that validators enforce cross-collection foreign keys or immutable history.
- No success-returning malware stub.
- No nearest-name identity matching.
- No missing-answer zero fill.
- No answer mutation after locking.
- No unbounded lease/outbox retry behavior.
- No AI/email startup dependency.
- No new workflow/activity names beyond those explicitly implemented and tested.

## 9. Definition of Done / Exit Gate

Literal source Section 18 exit gate:

**Exit gate:** worker-crash and duplicate-request tests pass; no lost tasks; OMR false-finalization target met on held-out physical scans.

All required command outputs must be attached. Green unit tests alone do not meet
this exit gate.

## 10. Phase 1 Completion Report

Write handoff/phase-1.json using the global schema.
Include migration checksums, actual API contract changes, UI test output, workflow
history/recovery evidence, physical scan qualification and unresolved adapters.
Print "Phase 1 Completion Report" and "Open Gaps" before stopping.
````

## Clarifications Needed Before Phase 2

**Decision adopted:** a structurally valid model response is a candidate interpretation, not automatic proof of educational correctness. Acceptance requires the versioned educator-approved policy; missing policy holds the candidate for review.

**External blockers:** approved de-identified evidence, per-class thresholds, provider model access, and institution-approved provider budget/processing terms.

````markdown
# PHASE 2 PROMPT — Evidence-grounded diagnostics

## 1. Objective

Add evidence-grounded diagnostics for finalized incorrect answers only. Preserve
locked grades, record complete provenance, abstain when evidence is insufficient,
and recover child-workflow failures without calling them student deficits.

Stack: React + TypeScript, FastAPI, MongoDB replica set, Temporal, private S3,
OpenAI strict structured output. Grading must remain usable when AI is unavailable.

## 2. In scope / Out of scope

IN SCOPE
- Verified question-specific work crops.
- Protected source prompt/schema/provider module.
- Strict response validation and provenance.
- Diagnostic review/override and explicit abstention.
- Shared provider-budget enforcement and child-workflow recovery.
- Per-class educator evaluation.

OUT OF SCOPE
- Embeddings, analytics, report assembly, email delivery.
- SKIP — out of scope for this build: student portal, rich formula rendering,
  broader language support, scanner calibration UI, SIS sync,
  multi-institution controls, longitudinal learning progress.

## 3. Prerequisites check

```bash
python tools/verify_handoff.py handoff/phase-1.json
python -m pytest -q tests/unit/test_reference_integrity.py tests/unit/test_grading_core.py
```

Required interfaces:
- cde.db.transact(client, callback)
- finalized, locked submissions and student_answers
- cde/stages.py fenced stage acquisition/result commit
- existing authorization and durable task resolution
- SubmissionWorkflow input: submission_id, processing_revision, pipeline_target
- private immutable S3 artifact access

Required Phase 2 live variables:
- OPENAI_API_KEY
- OPENAI_VISION_MODEL
- approved provider budget configuration

Use the source-requested gpt-5.4 only if the account actually supports it; store
requested and returned identifiers. Do not substitute a different model silently.
Missing live credentials blocks live AI tests, not existing grading endpoints.

## 4. Deliverables

Create:
- prompts/diagnose-v1.txt
- schemas/diagnostic-v1.json
- cde/diagnostics_reference.py
- cde/diagnostics.py
- cde/evidence.py
- cde/provider_budget.py
- migrations/002_diagnostics.py
- web/src/pages/DiagnosticsPage.tsx
- tests/unit/test_evidence.py
- tests/unit/test_diagnostic_schema.py
- tests/integration/test_phase2.py
- tests/authorization/test_phase2_access.py
- tests/failure_injection/test_phase2_recovery.py
- tests/diagnostic_evaluation/test_phase2_gate.py

Edit cde/workflows.py, cde/activities.py, cde/worker.py, cde/api.py, web routing,
requirements.in and its regenerated lockfile.
Do not edit protected reference files or grading semantics.

## 5. New database contract

error_taxonomy_results fields:
- _id, submission_id, question_number, analysis_revision, is_current, state,
  error_type, confidence, plain_language_summary, next_step, abstention_reason,
  concept_code, procedure_code, evidence, crop_object_keys, input_fingerprint,
  requested_model, returned_model, prompt_version, schema_version,
  raw_response_object_key, provider_request_id, provider_usage,
  overridden_by, override_reason, acceptance_policy_version, created_at.

next_step and acceptance_policy_version are explicit adaptation additions.

Unique indexes:
- (submission_id, question_number, analysis_revision)
- (submission_id, question_number, input_fingerprint)
- partial unique (submission_id, question_number) where is_current=true

States: classified, abstained, overridden.
error_type is exactly one of:
- Calculation Slip
- Procedural Flaw
- Reading Comprehension Error
- Conceptual Deficit

abstained is not a fifth class.

Classified/overridden results require nonempty evidence and a class.
Abstained results require null class and a nonempty reason.
Overrides require actor, reason, provenance, and a new analysis revision.

Raw candidates that fail acceptance policy are retained as restricted stage
artifacts and a durable diagnostic task, not falsely published as accepted results.

Budget supporting collections:
- provider_budget_windows:
  _id, provider, window_start, window_end, limit_units, reserved_units,
  consumed_units, version.
- provider_reservations:
  _id, stage_run_id, attempt, provider, window_id, reserved_units,
  consumed_units, state, created_at, updated_at.
  states: reserved, settled, uncertain, released.
  unique(stage_run_id, attempt, provider).

Units and limits must come from approved provider-budget configuration.
An unresolved billable request retains a conservative reservation; a crash must
not automatically refund a request that may already have been charged.

## 6. Atomic steps

### Step 1 — Import the exact source artifacts

```bash
python tools/import_reference.py --phase 2
```

This copies:
- source 8.2 → prompts/diagnose-v1.txt
- source 8.4 → schemas/diagnostic-v1.json
- source 8.5 → cde/diagnostics_reference.py

Add openai, pytest-asyncio and jsonschema to requirements.in; resolve and reinstall
the hash lock. Do not invent SDK versions.

```bash
pip-compile --generate-hashes --output-file=requirements.lock requirements.in
python -m pip install --require-hashes -r requirements.lock
python -m compileall -q cde/diagnostics_reference.py
python -m json.tool schemas/diagnostic-v1.json > /dev/null
python -m pytest -q tests/unit/test_reference_integrity.py
```

Expected: immutable-source checks, compilation and schema parsing pass.

Inspect the imported function signatures before writing the adapter. Use the actual
provider calls in that file; do not replace them with remembered SDK APIs.

### Step 2 — Validate evidence before any provider request

Write cde/evidence.py:

```python
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

@dataclass(frozen=True)
class Crop:
    id: str
    path: Path
    sha256: str
    question_number: int
    page_index: int
    box: tuple[int, int, int, int]
    mapping_verified: bool

def overlaps(a: tuple[int, int, int, int],
             b: tuple[int, int, int, int]) -> bool:
    return max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])

def validate_crops(
    question_number: int,
    crops: list[Crop],
    page_dimensions: dict[int, tuple[int, int]],
    identity_boxes: dict[int, list[tuple[int, int, int, int]]],
) -> None:
    if len(crops) > 3 or len({c.id for c in crops}) != len(crops):
        raise ValueError("Invalid crop count or duplicate crop ID")
    for crop in crops:
        if not crop.id or crop.question_number != question_number:
            raise ValueError("Wrong crop identity or question")
        if not crop.mapping_verified:
            raise ValueError("Work mapping is not verified")
        if crop.page_index not in page_dimensions or crop.page_index not in identity_boxes:
            raise ValueError("Missing page or identity-region contract")
        width, height = page_dimensions[crop.page_index]
        x0, y0, x1, y1 = crop.box
        if any(type(v) is not int for v in crop.box):
            raise ValueError("Crop coordinates must be integer pixels")
        if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
            raise ValueError("Crop outside aligned page")
        if (x1 - x0) * (y1 - y0) > 2_000_000:
            raise ValueError("Crop pixel limit exceeded")
        if any(overlaps(crop.box, box) for box in identity_boxes[crop.page_index]):
            raise ValueError("Crop overlaps a known identity region")
        data = crop.path.read_bytes()
        if len(data) > 8 * 1024 * 1024:
            raise ValueError("Crop byte limit exceeded")
        if hashlib.sha256(data).hexdigest() != crop.sha256:
            raise ValueError("Crop digest mismatch")
        with Image.open(crop.path) as image:
            if image.format != "PNG" or image.size != (x1 - x0, y1 - y0):
                raise ValueError("Crop encoding or dimensions mismatch")
            image.verify()

def validate_evidence_box(box: list[float]) -> None:
    if len(box) != 4:
        raise ValueError("Evidence box needs four coordinates")
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in box):
        raise ValueError("Evidence coordinates must be finite numbers")
    x0, y0, x1, y1 = box
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        raise ValueError("Evidence box must be ordered and normalized")
```

This check prevents known identity-region overlap. It does not prove that a student
has not written their name inside a work box. The data-preparation/review policy
must address incidental identity within pixels; do not advertise full de-identification
based on bounding boxes alone.

Write tests/unit/test_evidence.py for:
- valid crop;
- unknown page;
- unverified/wrong-question mapping;
- duplicate ID and more than three crops;
- wrong SHA or image dimensions;
- overlap with identity region;
- NaN/infinity/reversed/zero-area evidence boxes.

Run:

```bash
python -m pytest -q tests/unit/test_evidence.py
```

Expected: all validation cases pass; invalid inputs cannot reach the provider.

### Step 3 — Build the diagnostic adapter

Implement cde/diagnostics.py around the protected reference function.

Before calling it:
1. Authorize the service/exam scope.
2. Verify the submission is graded and locked.
3. Verify the answer is finalized and incorrect.
4. Resolve immutable question/key revisions.
5. Verify work mapping and crop bytes/coordinates/hashes.
6. Build a de-identified context containing only:
   language, question_number, question_revision_id, subject, topic_code,
   concept_code, procedure_code, question_text, options, correct_option,
   correct_reasoning, selected_option, crop_manifest.
7. Include crop IDs, page indices, canonical boxes and hashes in crop_manifest.
8. Acquire a fenced stage and shared budget reservation before calling OpenAI.

Fingerprint input includes:
- source/template/exam/processing revisions;
- finalized selected option;
- ordered crop IDs and hashes;
- question revision;
- prompt/schema hashes and versions;
- requested model;
- acceptance-policy version;
- code/configuration version.

No crops or no reliable mapping:
- produce explicit missing_or_unmapped_work abstention;
- do not call the provider;
- do not alter the grade.

After a provider response:
- enforce the exact strict schema and Pydantic semantic checks;
- reject unknown fields/enums/crop IDs and invalid boxes;
- store raw structured response only in restricted encrypted object storage;
- preserve request ID, returned model, usage and all input provenance;
- publish at most the first accepted result for this fingerprint;
- retain subsequent computation as attempts, not overwrites.

Model confidence is not a calibrated probability. A candidate below an approved
acceptance policy becomes diagnostic review; missing approval also becomes review.
Do not invent a universal 0.9 acceptance threshold.

Write tests/unit/test_diagnostic_schema.py for invalid JSON, extra fields,
invalid enum, unsupported box, unknown crop ID, classified without evidence,
abstained with a class, provider refusal, and truncated/incomplete output.

Run:

```bash
python -m pytest -q tests/unit/test_diagnostic_schema.py
```

Expected: no malformed accepted diagnosis.

### Step 4 — Provider budgets and failure classes

Implement cde/provider_budget.py using MongoDB transactions and the collections
specified above. The limit is global to the deployment, not a per-process semaphore.

Requirements:
- reserve against an explicit approved window before dispatch;
- reject work that would exceed the limit;
- settle actual usage when known;
- preserve uncertain reservation after a possible billable success;
- reconcile uncertain attempts before reuse;
- apply bounded concurrency independently of monetary/token budget;
- never release a reservation merely because a worker process disappeared.

Keep SDK automatic retries disabled if the protected reference delegates retries
to Temporal. Do not multiply nested retry counts.

Failure classification:
- transport 429/5xx/timeout: bounded provider-aware retry;
- 401/403/unavailable model: configuration incident and pause affected work;
- malformed schema: at most two separate schema-repair calls;
- refusal: explicitly unavailable, no evasive prompting;
- absent/illegible/unmapped/insufficient work: valid evidence abstention;
- exhausted transport or malformed output: operational failure, not Conceptual Deficit.

Any concrete retry schedule not already present in the protected/reference
contracts must be recorded as an adaptation policy and covered by tests.
Do not allow an unbounded default SDK policy.

Run:

```bash
python -m pytest -q tests/integration/test_phase2.py -k 'budget or failure'
```

Expected: concurrent workers cannot overspend the configured reservation bound;
uncertain billable attempts are visible and retained.

### Step 5 — Diagnostic tasks, overrides and child recovery

Add migration 002 and these routes:
- GET /api/submissions/{submission_id}/diagnostics
- POST /api/diagnostics/{diagnostic_id}/override

Reuse task claim/renew/resolve for work_mapping and diagnostic task kinds, adding
explicit kind-specific decision schemas. Do not accept untyped arbitrary decisions.

Override body:

```json
{
  "expected_analysis_revision": 1,
  "error_type": "Procedural Flaw",
  "reason": "Educator explanation grounded in the visible step",
  "evidence": [
    {
      "crop_id": "known crop ID",
      "bbox": [0.1, 0.1, 0.5, 0.4],
      "observation": "Short visible observation",
      "transcription": null
    }
  ]
}
```

Override transaction:
- authorize reviewer;
- validate prior current revision and evidence;
- create a new revision with overridden actor/reason;
- atomically switch the current pointer and audit;
- preserve the original interpretation;
- do not modify student_answers or grades.

Workflow target=2:
- grade first using existing behavior;
- diagnostic_plan returns ordered finalized incorrect question numbers;
- zero incorrect questions returns an empty list, not an error;
- run child diagnostic workflows with stable question-specific logical IDs;
- await children and catch child failures;
- persist needs_operator and failed checkpoint;
- wait for authorized retry/deferral rather than losing the parent;
- reuse successful child results on resume.

Do not read deployment environment variables from workflow code.
Replay Phase 1 histories before accepting the new worker version.

Run:

```bash
python -m cde.migrate
python -m pytest -q tests/integration/test_phase2.py
python -m pytest -q tests/authorization/test_phase2_access.py
python -m pytest -q tests/failure_injection/test_phase2_recovery.py
python -m pytest -q tests/workflow_replay
```

Expected: child crash is recoverable, successful results are reused, and existing
grading histories remain replayable.

### Step 6 — Diagnostic review UI and educator evaluation

Build DiagnosticsPage.tsx:
- wrong-answer context and finalized selected option;
- exact source crop and overlay evidence boxes;
- accepted hypothesis, explicit abstention, pending review, or unavailable state;
- model/prompt/schema/revision provenance;
- reviewer correction with reason;
- no clinical or enduring-trait labels.

Create tests/diagnostic_evaluation/test_phase2_gate.py.
Require at least two subject educators' independent labels and adjudicated held-out
cases. Allow disagreement and abstention.
Report per-class precision/recall, procedural-vs-conceptual confusion, evidence
localization validity, hallucinated-transcription rate, abstention coverage and
override rate. Use the approved acceptance policy, not invented numerical targets.

Run:

```bash
cd web
npm run typecheck
npm test -- --run
npm run build
cd ..
python -m pytest -q tests/diagnostic_evaluation/test_phase2_gate.py
```

Expected: UI checks pass; the educational gate passes only with real approved evidence.

## 7. DO NOT INVENT

- No fifth error class.
- No AI changes to grades, recipients, permissions or publication.
- No diagnosis of a correct or unfinalized answer.
- No distractor-only cognitive inference.
- No provider error relabeled as abstention about the student's working.
- No unknown crop IDs or invented handwritten steps.
- No fake model availability or budget approvals.
- No automatically accepted diagnostic merely because JSON validation passed.

## 8. Final verification

```bash
python tools/import_reference.py --phase 2
python -m cde.migrate
python -m pytest -q tests/unit/test_reference_integrity.py tests/unit/test_evidence.py tests/unit/test_diagnostic_schema.py
python -m pytest -q tests/integration/test_phase2.py tests/authorization/test_phase2_access.py
python -m pytest -q tests/failure_injection/test_phase2_recovery.py tests/workflow_replay
python -m pytest -q tests/diagnostic_evaluation/test_phase2_gate.py
```

Paste actual output, including live-provider qualification separately from mock tests.

## 9. Definition of Done / Exit Gate

Literal source Section 18 exit gate:

**Exit gate:** agreed precision/evidence thresholds met; child-workflow failure recovery implemented; no model failure is mislabeled as a student deficit.

## 10. Phase 2 Completion Report

Write handoff/phase-2.json using the global schema.
Include copied-block hashes, actual model identifiers tested, policy version,
evaluation evidence, child-recovery/replay results and provider-budget gaps.
Print "Phase 2 Completion Report" and "Open Gaps".
````

## Clarifications Needed Before Phase 3

**Decision adopted:** deterministic exact cosine ranking over the fully eligible MongoDB candidate stream. This is appropriate to qualify for a curriculum-sized bank, not a promise about arbitrary bank size.

**Decision adopted:** provisional analytics always expose denominators, unresolved counts, exclusions, and the exact current-revision population. Report snapshots remain immutable.

**Still external:** bank coverage, approved fonts/licenses, representative report content, and human visual inspection.

````markdown
# PHASE 3 PROMPT — Cohort insight and targeted practice

## 1. Objective

Build revision-correct cohort analytics, approved-question retrieval, explicit
coverage reporting, and verified PDF downloads. No automatic email delivery.

Stack: React + TypeScript, FastAPI, MongoDB transactions, Temporal, OpenAI embeddings,
private S3 and ReportLab. Do not introduce pgvector or a second vector database.

## 2. In scope / Out of scope

IN SCOPE
- Snapshot analytics and distractor distributions.
- Repeated observed concept-gap groups, not enduring student labels.
- Approved 1536-dimensional embeddings and hard-filter retrieval.
- Two questions per distinct diagnosed gap, at most ten overall.
- Immutable report manifest, PDF render/visual verification and download.

OUT OF SCOPE
- Automatic email release/send/webhooks.
- SKIP — out of scope for this build: student portal, rich formula rendering,
  broader language support, scanner calibration UI, SIS sync,
  multi-institution controls, longitudinal learning progress.

## 3. Prerequisites

```bash
python tools/verify_handoff.py handoff/phase-2.json
python -m pytest -q tests/unit/test_reference_integrity.py tests/unit/test_grading_core.py tests/unit/test_diagnostic_schema.py
```

Required existing contracts:
- exam_roster.current_submission_id selects the current processing revision;
- exclusions are explicit excluded_reason values;
- locked grades and current accepted diagnostic revisions;
- questions have versioned curriculum metadata and family IDs;
- fenced stage commits and private immutable artifacts;
- assigned-exam authorization for every read/list/aggregate/download.

Live prerequisites:
- approved bank content;
- OPENAI_API_KEY and supported text-embedding-3-small access;
- licensed approved font files and their actual hashes;
- representative report fixtures for visual review.

## 4. Deliverables

Create:
- cde/embeddings_reference.py, cde/embeddings.py
- cde/retrieval.py, cde/analytics.py
- cde/report_reference.py, cde/report.py
- migrations/003_analytics_reports.py
- fonts/manifest.json
- web/src/pages/AnalyticsPage.tsx, ReportsPage.tsx
- tests/unit/test_retrieval.py
- tests/integration/test_phase3_analytics.py
- tests/integration/test_phase3_reports.py
- tests/authorization/test_phase3_access.py
- tests/report_visual/test_phase3_gate.py

Edit workflow/activity/API registrations, web routing and dependency locks.

## 5. Database additions

cohort_analytics:
- _id, exam_id, snapshot_revision, input_fingerprint, enrolled_count, graded_count,
  diagnostic_count, unresolved_count, excluded_count, metrics, created_at.
- unique(exam_id, snapshot_revision)
- unique(exam_id, input_fingerprint)

remediation_jobs:
- _id, submission_id, report_revision, input_fingerprint, state,
  report_object_key, report_sha256, manifest_object_key, created_at, updated_at,
  failure_code.
- unique(submission_id, report_revision)
- unique(submission_id, input_fingerprint)

remediation_items:
- _id, remediation_job_id, ordinal, question_id, diagnostic_id,
  retrieval_distance, selection_reason, question_snapshot.
- unique(remediation_job_id, ordinal)
- unique(remediation_job_id, question_id)

Phase 3 remediation states:
- pending, retrieving, insufficient_bank, rendering, ready, failed.

Do not introduce sending/delivery behavior until Phase 4.
Question embedding values are finite numeric arrays of exactly 1536 values,
embedding_model=text-embedding-3-small, with embedding_input_sha256.

## 6. Atomic steps

### Step 1 — Import protected reference modules

```bash
python tools/import_reference.py --phase 3
```

Copies source 10.3 and 10.7 into the reference destinations.
Add reportlab to requirements.in and regenerate/install the hash lock.

```bash
pip-compile --generate-hashes --output-file=requirements.lock requirements.in
python -m pip install --require-hashes -r requirements.lock
python -m compileall -q cde/embeddings_reference.py cde/report_reference.py
python -m pytest -q tests/unit/test_reference_integrity.py
```

Inspect imported dependencies before importing a reference module at runtime.
If it includes a database-specific operation, preserve the file but implement that
operation in the named MongoDB adapter. Do not install a prohibited application
SQL stack merely to satisfy an unused reference import.

### Step 2 — Embedding adapter

Implement cde/embeddings.py around the actual provider call supplied in the
protected reference. Persist through PyMongo, not source SQL.

- Embed approved question revisions only.
- Preserve original question metadata and content hash.
- Require model text-embedding-3-small and exactly 1536 finite values.
- Reject a zero-norm vector before cosine ranking.
- Reuse a stored embedding when model/input hash matches.
- Never publish a new vector onto a different question revision by accident.
- Use the shared provider budget and failure handling already implemented.
- A returned vector of another dimension/model is an ingestion failure.

Run the embedding cases in the report integration suite:

```bash
python -m pytest -q tests/integration/test_phase3_reports.py -k embedding
```

Expected: wrong model/dimensions are rejected; matching work is reused.

### Step 3 — Implement deterministic retrieval policy

Write cde/retrieval.py with this complete policy kernel:

```python
from __future__ import annotations

import math
from typing import Iterable

MODEL = "text-embedding-3-small"
DIMENSIONS = 1536
CLASSES = {
    "Calculation Slip", "Procedural Flaw",
    "Reading Comprehension Error", "Conceptual Deficit",
}

class InsufficientBank(RuntimeError):
    pass

def cosine_distance(a: list[float], b: list[float]) -> float:
    if len(a) != DIMENSIONS or len(b) != DIMENSIONS:
        raise ValueError("Embedding dimension mismatch")
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in a + b):
        raise ValueError("Embedding contains a non-finite or invalid value")
    an = math.sqrt(sum(x * x for x in a))
    bn = math.sqrt(sum(x * x for x in b))
    if an == 0 or bn == 0:
        raise ValueError("Zero-norm embedding")
    similarity = sum(x * y for x, y in zip(a, b)) / (an * bn)
    return 1.0 - max(-1.0, min(1.0, similarity))

def eligible(candidate: dict, original: dict, error_class: str,
             excluded_families: set[str]) -> bool:
    if error_class not in CLASSES:
        raise ValueError("Unsupported error class")
    if not candidate["approved"] or not candidate["active"]:
        return False
    if candidate["family_id"] in excluded_families:
        return False
    if candidate.get("embedding_model") != MODEL or candidate.get("embedding") is None:
        return False
    for field in ("subject", "topic_code", "language"):
        if candidate[field] != original[field]:
            return False
    difficulty = original["difficulty"]
    if error_class == "Calculation Slip":
        return (candidate["target_skill"] == "accuracy"
                and candidate["difficulty"] == difficulty)
    if error_class == "Procedural Flaw":
        procedure = original.get("procedure_code")
        return (procedure is not None
                and candidate["target_skill"] == "procedure"
                and candidate.get("procedure_code") == procedure
                and candidate["difficulty"] <= difficulty)
    if error_class == "Reading Comprehension Error":
        return (candidate["target_skill"] == "reading"
                and candidate["phrasing_variant"] != original["phrasing_variant"]
                and candidate["difficulty"] <= difficulty)
    return (candidate["target_skill"] == "foundation"
            and candidate["concept_code"] == original["concept_code"]
            and candidate["difficulty"] <= max(1, difficulty - 1))

def select_questions(
    original: dict,
    error_class: str,
    query_vector: list[float],
    candidates: Iterable[dict],
    excluded_families: set[str],
    limit: int = 2,
) -> list[tuple[dict, float]]:
    if type(limit) is not int or not 1 <= limit <= 2:
        raise ValueError("Per-gap selection limit must be one or two")
    # Validate query even when the eligible bank is empty.
    cosine_distance(query_vector, query_vector)
    if error_class == "Procedural Flaw" and not original.get("procedure_code"):
        raise InsufficientBank("MISSING_PROCEDURE_CODE")
    excluded = set(excluded_families)
    excluded.add(original["family_id"])
    best_per_family = {}
    for candidate in candidates:
        if not eligible(candidate, original, error_class, excluded):
            continue
        distance = cosine_distance(query_vector, candidate["embedding"])
        ordering = (distance, candidate["family_id"], candidate["_id"])
        previous = best_per_family.get(candidate["family_id"])
        if previous is None or ordering < previous[0]:
            best_per_family[candidate["family_id"]] = (ordering, candidate)
    ranked = sorted(best_per_family.values(), key=lambda entry: entry[0])
    return [(candidate, ordering[0]) for ordering, candidate in ranked[:limit]]
```

This is newly supplied adaptation code based on the source's hard-filter intent,
not verbatim retrieval SQL. The declared tie-break order is deterministic.

MongoDB query adapter requirements:
- apply approved/active/model/subject/topic/language and class-specific predicates
  before iterating candidates;
- exclude the original exam's families and families already assigned in this package;
- recheck eligibility in the kernel;
- do not arbitrarily truncate the candidate cursor before exact ranking;
- use a consistent question-bank view or immutable versioned input manifest;
- no unapproved question generation or filter relaxation.

Group distinct gaps by (error_class, concept_code, procedure_code).
This grouping key is an explicit adaptation decision.
Order gaps deterministically by the earliest affected question number, then the key.
Select at most two per gap and ten total. Explain cap-related omissions separately
from insufficient-bank omissions. Do not count an intentional cap as full coverage.

A result with fewer than the requested eligible questions records the actual
coverage and insufficient_bank. Do not fabricate replacements.

Write tests/unit/test_retrieval.py for:
- all four classes;
- missing procedure code;
- level-1 conceptual deficit;
- wrong subject/topic/language;
- wrong embedding model/dimension/zero vector;
- same original family and duplicate families;
- sparse bank;
- deterministic ties;
- global family deduplication and ten-question cap.

Run:

```bash
python -m pytest -q tests/unit/test_retrieval.py
```

Expected: all hard filters remain intact; insufficient coverage is explicit.

### Step 4 — Snapshot analytics

Implement cde/analytics.py with these explicit denominator contracts:

- enrolled_count: all roster memberships for the exam revision.
- excluded_count: roster memberships with a non-null excluded_reason.
- eligible_count: enrolled_count - excluded_count, stored inside metrics.
- graded_count: eligible students whose referenced current_submission_id points
  to a matching, locked, graded submission revision.
- unresolved_count: eligible_count - graded_count.
- diagnostic_count: eligible graded students whose incorrect answers all have a
  current accepted classified/overridden/abstained outcome; zero incorrect answers
  is complete without provider calls.
- pending provider failures are not accepted diagnostic outcomes.

Per-question answer percentages:
- denominator is graded_count for that exact current population;
- blank is reported separately from incorrect options;
- unresolved and excluded students do not appear as guessed blanks;
- empty denominator produces null percentage, not division by zero or 0% certainty.

Diagnostic distribution:
- class shares use accepted classified/overridden wrong answers as denominator;
- abstained and unavailable counts are displayed separately;
- label whether a count is students, answers, or observations;
- repeated concept cohorts count distinct current students, not duplicate revisions.

These are frozen MongoDB-adaptation metric definitions. Do not claim an SQL query
was copied unchanged.

Read roster pointers, grades, diagnostic-current pointers and exclusions from one
consistent transactional snapshot. Build the fingerprint from the ordered input
revision IDs and policy/version identifiers. Persist the snapshot under unique
exam/fingerprint identity. Concurrent recomputes either reuse the same logical
snapshot or allocate a new snapshot revision transactionally.

Do not overwrite a prior snapshot during a race. Keep creation time and provisional
coverage visible. Updating current_submission_id must never mutate old reports.

Create tests/integration/test_phase3_analytics.py for:
- excluded/unresolved students;
- a superseded processing revision;
- corrected key represented by a different exam revision;
- zero students and zero wrong answers;
- abstained versus failed diagnostics;
- duplicate answers/current pointers rejected by prior invariants;
- concurrent recomputation and pointer changes;
- unassigned user aggregate access.

Run:

```bash
python -m pytest -q tests/integration/test_phase3_analytics.py
```

Expected: correct denominators, explicit partial coverage and stable revision fingerprints.

### Step 5 — Immutable report manifest and safe renderer adapter

Implement cde/report.py around the imported ReportLab reference API.
Inspect its real function signature and required fonts; do not invent a call.

The report manifest must snapshot:
- submission/exam/key/report revisions;
- grade and answer summary;
- accepted diagnostic IDs and evidence references;
- selected practice question IDs, family/revision IDs and full approved content;
- retrieval policy version, selection reasons and distances;
- insufficient coverage and intentional cap omissions;
- template/prompt/schema/model versions needed for provenance;
- font identifiers/checksums and renderer code version.

Persist the manifest before accepting the PDF stage result.
Never rebuild a previously published revision from mutable current question text.

Renderer requirements:
- escape all student, question and model text passed to ReportLab markup;
- never execute HTML/JavaScript supplied by a model;
- use approved font files with verified checksums and licenses;
- support only the qualified language/script/math subset;
- preserve long-text wrapping, pagination, answer explanations and footer identity;
- missing fonts or unsupported rendering blocks publication; no silent font fallback;
- verify uploaded PDF bytes and hash before state=ready;
- reuse the first accepted artifact for the same fingerprint.

fonts/manifest.json must contain actual supplied files, hashes and license references.
Do not write invented hashes or download unlicensed assets.

Routes:
- GET /api/exams/{exam_id}/analytics
- POST /api/submissions/{submission_id}/remediation
- GET /api/reports/{report_id}
- GET /api/reports/{report_id}/download

Downloads require assigned-exam authorization and return short-lived private-object
access or an authorized streamed response. No public bucket/object ACL.

Workflow target=3 adds build_remediation and refresh_analytics only after the prior
stage results are available. The source grade remains independently usable.
A missing bank holds remediation, not grading.

Run:

```bash
python -m cde.migrate
python -m pytest -q tests/integration/test_phase3_reports.py
python -m pytest -q tests/authorization/test_phase3_access.py
python -m pytest -q tests/workflow_replay
```

Expected: immutable artifacts, private downloads, correct holds and replay compatibility.

### Step 6 — Analytics and report UI

Build AnalyticsPage.tsx and ReportsPage.tsx:
- show exam revision/snapshot timestamp;
- show enrolled/graded/unresolved/excluded/diagnostic coverage together;
- show distractor and observed concept-gap distributions with labeled denominators;
- show insufficient bank coverage and explicit cap omissions;
- show report revision, rendering status and authorized download;
- no email send button in this phase.

Run:

```bash
cd web
npm run typecheck
npm test -- --run
npm run build
cd ..
```

Expected: all commands succeed.

### Step 7 — Visual qualification

Create tests/report_visual/test_phase3_gate.py.
Required fixtures from the source verification contract:
- long names;
- long stems;
- many options;
- multi-page breaks;
- supported math/script;
- injection-like text rendered harmlessly.

Render every resulting PDF page to PNG in an isolated PDFium process.
Store the rendered-page hashes in a review manifest. Require actual human visual
approval identifying those exact hashes. A nonempty PDF or OCR text is not proof
of no clipping/blank pages.

Run:

```bash
python -m pytest -q tests/report_visual/test_phase3_gate.py
```

Expected: all representative pages rendered and visually approved.
Missing fonts or approvals: code_ready_gate_blocked, not complete.

## 7. DO NOT INVENT

- No unapproved generated practice questions.
- No relaxed language, concept, procedure, difficulty or family filters.
- No silent candidate truncation before exact ranking.
- No analytics from superseded revisions or guessed missing answers.
- No class distribution that silently includes abstentions as deficits.
- No fabricated visual approval or font license/hash.
- No public PDF links or automatic email sending.

## 8. Final verification

```bash
python tools/import_reference.py --phase 3
python -m cde.migrate
python -m pytest -q tests/unit/test_reference_integrity.py tests/unit/test_retrieval.py
python -m pytest -q tests/integration/test_phase3_analytics.py tests/integration/test_phase3_reports.py
python -m pytest -q tests/authorization/test_phase3_access.py tests/workflow_replay
python -m pytest -q tests/report_visual/test_phase3_gate.py
```

Paste actual outputs and the actual visual-review evidence identifiers.

## 9. Definition of Done / Exit Gate

Literal source Section 18 exit gate:

**Exit gate:** analytics denominators/revisions correct; retrieval constraints and deduplication pass; every representative PDF page visually verified.

## 10. Phase 3 Completion Report

Write handoff/phase-3.json using the global schema.
Include input/snapshot fingerprints, bank/model qualification, retrieval tests,
report/font hashes, visual approvals and any measured performance limitation.
Print "Phase 3 Completion Report" and "Open Gaps".
````

## Clarifications Needed Before Phase 4

**Decision adopted:** uncertainty after possible provider acceptance is reconciled, not solved by blind resending. A conservative retry cutoff is a configurable, recorded policy no longer than the source's 24-hour provider window.

**Still external:** verified sender/domain, reachable signed webhook, institution-approved recipient/consent policy, deployment images, secrets, and a real cross-system recovery procedure. A Temporal history export alone must not be represented as a complete workflow-service backup.

````markdown
# PHASE 4 PROMPT — Delivery and operational hardening

## 1. Objective

Release approved reports to verified, eligible recipients with immutable email
payloads, traceable outcomes, ambiguity reconciliation, operational monitoring,
and a proven recovery drill.

Stack: React + TypeScript, FastAPI, MongoDB replica set, Temporal, private S3,
Resend, signed webhooks, OpenTelemetry. Keep scoring independent from delivery.

## 2. In scope / Out of scope

IN SCOPE
- Publisher release and consent/current-revision checks.
- Frozen email bytes/hash/key and fenced send attempts.
- Signed durable webhook ingestion and monotonic projection.
- Delivery-unknown and bounce reconciliation.
- Deployment images, least-privilege service separation, alerts and restore drills.

OUT OF SCOPE
- The organizational Phase 5 institutional pilot.
- SKIP — out of scope for this build: student portal, rich formula rendering,
  broader language support, scanner calibration UI, SIS sync,
  multi-institution controls, longitudinal learning progress.

## 3. Prerequisites

```bash
python tools/verify_handoff.py handoff/phase-3.json
python -m pytest -q tests/unit/test_reference_integrity.py tests/unit/test_retrieval.py
```

Required existing contracts:
- immutable ready report manifest/PDF with verified hashes;
- current submission revision and explicit report revision;
- student email, email_verified_at and email_consent_at;
- can_publish exam authorization;
- transactional outbox, idempotency records and fenced stages;
- controlled private S3 access and MongoDB transactions.

Live variables:
- RESEND_API_BASE, RESEND_API_KEY, RESEND_WEBHOOK_SECRET, EMAIL_FROM
- EMAIL_RETRY_CUTOFF_SECONDS, positive and at most 86400
- OTEL_EXPORTER_OTLP_ENDPOINT and approved credentials through secret injection
- build image identifiers/digests and exact public origins

Do not put Resend credentials in API routes that do not need them, the React bundle,
or the OMR worker. The local convenience environment must not become a production
shared-secret design.

## 4. Deliverables

Create:
- cde/email_reference.py, cde/email_policy.py, cde/email.py
- cde/email_event_applier.py, cde/telemetry.py
- migrations/004_delivery.py
- web/src/pages/DeliveryPage.tsx
- infra/Dockerfile.api, infra/Dockerfile.worker, infra/Dockerfile.web
- infra/Caddyfile, docker-compose.yml
- docs/recovery-runbook.md
- tests/unit/test_email_policy.py
- tests/integration/test_phase4_email.py
- tests/authorization/test_phase4_access.py
- tests/failure_injection/test_phase4_delivery.py
- tests/integration/test_phase4_recovery.py

Edit existing API/workflow/worker/web registration and dependency locks.

## 5. Database changes

Add to remediation_jobs:
- recipient_email, consent_checked_at, released_by, released_at,
  email_payload_object_key, email_payload_sha256, email_idempotency_key,
  first_send_attempt_at, provider_email_id, accepted_at, delivered_at,
  bounced_at, attempts, release_version.

released_by/released_at/bounced_at/release_version are explicit adaptation additions.

Add delivery states:
- sending, accepted, delivered, bounced, delivery_unknown, suppressed.
Retain existing pending/retrieving/insufficient_bank/rendering/ready/failed states.

Indexes:
- unique email_idempotency_key when its BSON type is string;
- unique provider_email_id when its BSON type is string;
- dispatch query index on state, updated_at.

Do not use a naive unique nullable index that permits only one null document.

email_events:
- _id = verified provider event ID;
- provider_email_id, event_type, occurred_at, received_at,
  payload, payload_sha256, applied_at.
- index(provider_email_id, occurred_at)
- index(applied_at, received_at)

Do not delete unmatched events just because the send response was lost.

## 6. Atomic steps

### Step 1 — Import email reference and add dependencies

```bash
python tools/import_reference.py --phase 4
```

Add svix and the approved OpenTelemetry package families to requirements.in,
regenerate/install the hash lock, and verify protected files.

```bash
pip-compile --generate-hashes --output-file=requirements.lock requirements.in
python -m pip install --require-hashes -r requirements.lock
python -m compileall -q cde/email_reference.py
python -m pytest -q tests/unit/test_reference_integrity.py
```

Use the actual HTTP/provider contract in the imported source. Database adaptation
belongs in cde/email.py, not edits to the protected reference.

### Step 2 — Implement the pure send-decision kernel

Write cde/email_policy.py:

```python
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

Decision = Literal["send", "retry_same_payload", "reconcile", "do_not_send", "suppress"]

@dataclass(frozen=True)
class SendFacts:
    eligible: bool
    provider_email_id: str | None
    first_attempt_at: datetime | None
    expected_payload_sha256: str
    terminal_failure: bool

def aware(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Timezone-aware timestamp required")

def decide_send(
    facts: SendFacts,
    payload_bytes: bytes,
    now: datetime,
    retry_cutoff_seconds: int,
) -> Decision:
    aware(now)
    if type(retry_cutoff_seconds) is not int or not 0 < retry_cutoff_seconds <= 86400:
        raise ValueError("Invalid retry cutoff")
    actual = hashlib.sha256(payload_bytes).hexdigest()
    if actual != facts.expected_payload_sha256:
        raise ValueError("Frozen email payload hash mismatch")
    if facts.provider_email_id is not None or facts.terminal_failure:
        return "do_not_send"
    if facts.first_attempt_at is None:
        return "send" if facts.eligible else "suppress"
    aware(facts.first_attempt_at)
    if now < facts.first_attempt_at:
        return "reconcile"
    if not facts.eligible:
        # Eligibility withdrawal does not prove that an earlier request was unsent.
        return "reconcile"
    deadline = facts.first_attempt_at + timedelta(seconds=retry_cutoff_seconds)
    if now >= deadline:
        return "reconcile"
    return "retry_same_payload"
```

The caller must also reserve enough time for the actual request to finish before
the allowed provider window. This function alone is not permission to launch a
request seconds before a deduplication deadline. Persist and test a conservative
cutoff appropriate to the real HTTP timeout and deployment clock policy.

Write tests/unit/test_email_policy.py:

```python
import hashlib
from datetime import datetime, timedelta, timezone

import pytest

from cde.email_policy import SendFacts, decide_send

PAYLOAD = b'{"to":["synthetic@example.invalid"],"subject":"Test"}'
HASH = hashlib.sha256(PAYLOAD).hexdigest()
NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)

def facts(**changes):
    values = dict(eligible=True, provider_email_id=None, first_attempt_at=None,
                  expected_payload_sha256=HASH, terminal_failure=False)
    values.update(changes)
    return SendFacts(**values)

def test_new_eligible_send():
    assert decide_send(facts(), PAYLOAD, NOW, 86000) == "send"

def test_missing_eligibility_suppresses_unattempted_send():
    assert decide_send(facts(eligible=False), PAYLOAD, NOW, 86000) == "suppress"

def test_known_provider_acceptance_is_not_resent():
    assert decide_send(facts(provider_email_id="provider-id"), PAYLOAD, NOW, 86000) == "do_not_send"

def test_same_payload_retry_inside_window():
    assert decide_send(facts(first_attempt_at=NOW), PAYLOAD,
                       NOW + timedelta(hours=1), 86000) == "retry_same_payload"

def test_expired_window_requires_reconciliation():
    assert decide_send(facts(first_attempt_at=NOW), PAYLOAD,
                       NOW + timedelta(hours=24), 86000) == "reconcile"

def test_changed_payload_is_rejected():
    with pytest.raises(ValueError, match="hash mismatch"):
        decide_send(facts(), PAYLOAD + b" ", NOW, 86000)

def test_consent_withdrawal_after_attempt_keeps_uncertainty():
    assert decide_send(facts(eligible=False, first_attempt_at=NOW), PAYLOAD,
                       NOW + timedelta(minutes=1), 86000) == "reconcile"
```

The test cutoff is fixture data, not an institution-approved production default.

Run:

```bash
python -m pytest -q tests/unit/test_email_policy.py
```

Expected: seven tests pass.

### Step 3 — Release transaction and immutable payload

Implement route:
- POST /api/reports/{report_id}/release

Require publisher capability, Idempotency-Key, expected report/release version,
and an explicit release action. The model cannot release a report.

Recheck:
- report is ready with verified manifest/PDF;
- no unresolved publication hold;
- submission/report not cancelled or superseded;
- recipient comes from the authorized student record, never model output;
- current verified address and institution-approved consent policy;
- the released report revision matches the intended student/exam revision.

Freeze exact serialized UTF-8 email payload bytes in private S3.
Include the exact attachment bytes or immutable verified references required by
the provider API. Do not regenerate JSON or PDF on retry.

Stable logical key:
- cde/report/{report_uuid}/revision/{report_revision}

Transactionally persist:
- release actor/version/time;
- frozen recipient and consent check;
- payload object/hash and stable key;
- delivery outbox intent and audit record;
- idempotency response.

Different payload with the same key is a conflict. A corrected recipient/content
requires a deliberate new report/delivery revision and release; not a hidden retry.

Run:

```bash
python -m pytest -q tests/integration/test_phase4_email.py -k release
python -m pytest -q tests/authorization/test_phase4_access.py
```

Expected: unauthorized/unverified/superseded reports cannot be queued for sending.

### Step 4 — Fenced send and ambiguity handling

Implement cde/email.py:
1. Acquire the fenced send stage.
2. Read the immutable payload bytes and verify their hash.
3. Recheck current eligibility immediately before dispatch.
4. Persist first_send_attempt_at before the first external request; never reset it.
5. Increment the persisted attempt count under the fence.
6. Call decide_send and enforce the conservative transport deadline.
7. Send the exact bytes with the stable provider Idempotency-Key.
8. On accepted response, persist provider ID and accepted_at.
9. Do not set delivered_at from an HTTP success response.
10. On uncertain response, keep the same key/bytes; retry only inside the allowed window.
11. Beyond that window, set delivery_unknown and require reconciliation.

Do not call the provider within a MongoDB transaction callback.
A database retry must not automatically resend email.
A fenced result commit prevents stale logical commits, but does not undo an
external email already accepted. Preserve that uncertainty honestly.

Permanent payload/credential errors are not unbounded retries.
Cancellation after dispatch is best effort; do not claim the recipient cannot
receive an already accepted email.

Run:

```bash
python -m pytest -q tests/failure_injection/test_phase4_delivery.py
```

Required case: kill the sender after provider acceptance but before storing its ID.
Expected: same-key recovery inside the window, delivery_unknown outside it, never
a new key invented by retry code.

### Step 5 — Signed durable webhook ingestion

Implement:
- POST /api/webhooks/resend

Requirements:
- verify signature and timestamp using the actual installed Svix verification API
  shown in the source reference contract;
- verify the original raw body bytes, not a reserialized JSON object;
- use the verified delivery/event ID as the unique event identity;
- only acknowledge after durable insert or verified idempotent duplicate handling;
- reject an invalid signature without mutating report state;
- never trust a client-supplied email address to link a report;
- retain unknown provider_email_id events unapplied until reconciliation links them.

Duplicate verified event ID with the same bytes is safe.
Same event ID with different payload hash is a visible integrity incident, not an
instruction to overwrite the previous event.

Run:

```bash
python -m pytest -q tests/integration/test_phase4_email.py -k webhook
```

Expected: signed events are durable; forged, expired or conflicting events cannot
change delivery state.

### Step 6 — Event projection and reconciliation

Implement cde/email_event_applier.py as a separate durable consumer.

- Read unapplied events.
- Link using provider_email_id.
- In one transaction, apply event facts and mark that event applied.
- Preserve accepted, delivered and bounced timestamps independently.
- An older accepted/sent event must not downgrade delivered/bounced state.
- Handle event-before-send-response by retaining the event and retrying linkage.
- Preserve provider timestamps and distinguish occurrence from receipt time.
- Contradictory terminal events require visible reconciliation; do not invent a
  universal event precedence unsupported by the provider contract.
- Bounces do not trigger repeated automatic resends.

Operator reconciliation must show:
- report/revision/key;
- first attempt and retry deadline;
- frozen payload hash;
- known provider IDs and verified event history;
- exact ambiguity or bounce reason;
- audited action taken.

Routes:
- GET /api/reports/{report_id}/delivery
- POST /api/reports/{report_id}/reconcile

The reconcile mutation is operator-authorized plus exam-scoped and requires an
audit reason. Do not expose an arbitrary "mark delivered" endpoint without external
proof. Unknown acceptance remains unknown until reconciled.

Run:

```bash
python -m pytest -q tests/integration/test_phase4_email.py
```

Expected: no regressions from duplicate/reordered events, no lost unmatched event,
and no blind duplicate sends.

### Step 7 — Deployment images and runtime configuration

Build separate API, worker and React images.

API/worker:
- Python 3.12 slim base pinned to a qualified digest at release;
- install the actual hash-locked dependencies with pip --require-hashes;
- nonroot user;
- PYTHONDONTWRITEBYTECODE=1;
- immutable source/prompts/schemas/templates;
- no dependency downloads on startup;
- approved runtime native libraries and licensed fonts;
- read-only filesystem with bounded temporary storage.

React image:
- npm ci from committed lock;
- production build;
- static server with SPA fallback;
- generate nonsecret /runtime-config.json from PUBLIC_* values before serving;
- do not assume environment variables modify an already bundled Vite build.

docker-compose.yml is an application integration manifest, not a replacement
production deployment for institutional identity or Temporal.
Connect to the explicitly provisioned MongoDB replica set, Temporal and OIDC service.
Do not guess unsupported persistence backends or silently introduce another app DB.

Expose only ingress. Direct browser uploads go to bounded S3 quarantine credentials.
The API ingress body limit is 1 MiB for normal JSON routes; do not route large PDFs
through an unbounded API body.

Workers:
- OMR: one document per process, 1 GiB memory, no provider secrets/general internet;
- AI: budget/concurrency limited;
- IO: database/storage budget limited;
- separate email and other service credentials by least privilege.

Image tags, native package lists and infrastructure endpoint values must be
resolved/tested in the actual build environment. Never invent a successful image
digest or assume an unverified native package exists.

Run:

```bash
docker compose --env-file .env config --quiet
docker compose --env-file .env build
docker compose --env-file .env run --rm migrate
docker compose --env-file .env up -d
```

Expected: actual configuration/build/migration/startup success with supplied services.
Readiness remains false until MongoDB, required object storage and the configured
Temporal namespace are usable. Compose ordering alone is not readiness.

### Step 8 — Telemetry, alerts and delivery UI

Implement cde/telemetry.py and DeliveryPage.tsx.

Log only operational identifiers:
- correlation ID, submission/exam UUID, stage/fingerprint, attempt/fence,
  workflow/run ID, provider request ID, duration, stable status/error code.

Never log names, addresses, JWTs, presigned URLs, raw scans, handwriting,
provider keys or complete model transcripts.

Alerts from the source contract:
- outbox age >60 seconds warning, >5 minutes critical;
- no non-human stage progress >10 minutes warning;
- human task age according to institution-approved SLA;
- schema-failure rate >1% over representative rolling volume;
- any confirmed false-finalized OMR mark triggers calibration review;
- email acceptance unknown alerts immediately;
- checksum mismatch and workflow nondeterminism alert immediately;
- overdue restore test is a release blocker.

Show provider acceptance, delivery, bounce, suppression and unknown separately.
A green "sent" label must not collapse all those states.

Run:

```bash
cd web
npm run typecheck
npm test -- --run
npm run build
cd ..
python -m pytest -q tests/authorization/test_phase4_access.py
```

Expected: accessible delivery controls, correct authorization and no secrets in bundles.

### Step 9 — Recovery drill

Write docs/recovery-runbook.md for the actually provisioned services.
It must cover:
- MongoDB backup/point-in-time recovery and immutable revisions;
- Temporal persistence recovery or the managed service's verified recovery procedure;
- S3 object versions and report/source checksums;
- institutional identity recovery/configuration;
- restoration ordering and the reconciliation admission barrier;
- pending outbox events, stage leases, child workflows and delivery_unknown records.

Do not equate an exported workflow history with a complete service backup.
Do not restore over production to run a test. Use an isolated recovery environment.

Create tests/integration/test_phase4_recovery.py to verify restored invariants and
capture actual RPO/RTO measurements. Source design targets are RPO <=15 minutes and
RTO <=4 hours; they are not guarantees until demonstrated by the provisioned setup.

Before admitting new jobs after restoration:
- reconcile current roster pointers and published revisions;
- verify source/report objects and hashes;
- reconcile outbox dispatch versus actual workflow state;
- reject expired/stale stage owners;
- preserve uncertain email acceptance and unmatched signed events;
- verify enabled users/exam permissions.

Run:

```bash
python -m pytest -q tests/integration/test_phase4_recovery.py
```

Expected: actual restored services pass invariant reconciliation and produce a
recovery evidence record. A mocked database restore is not this gate.

## 7. DO NOT INVENT

- No automatic resend with a fresh key after uncertainty.
- No changed recipient/body/attachment under an existing idempotency key.
- No provider acceptance reported as recipient delivery.
- No webhook acknowledgement before durable storage.
- No unverified "mark delivered" operator shortcut.
- No inferred consent or invented lawful-basis approval.
- No fabricated restore drill, image digest, availability or compliance claim.
- No Phase 5 pilot presented as completed by these code prompts.

## 8. Final verification

```bash
python tools/import_reference.py --phase 4
python -m cde.migrate
python -m pytest -q tests/unit/test_reference_integrity.py tests/unit/test_email_policy.py
python -m pytest -q tests/integration/test_phase4_email.py tests/authorization/test_phase4_access.py
python -m pytest -q tests/failure_injection/test_phase4_delivery.py
python -m pytest -q tests/workflow_replay
python -m pytest -q tests/integration/test_phase4_recovery.py
```

Also attach actual Compose build/readiness output and live staging email/webhook
qualification, distinct from mocked transport tests.

## 9. Definition of Done / Exit Gate

Literal source Section 18 exit gate:

**Exit gate:** timeout-after-acceptance test, 24-hour ambiguity path, bounce handling, and recovery drill pass.

## 10. Phase 4 Completion Report

Write handoff/phase-4.json using the global schema.
Include release/consent evidence, immutable payload/key tests, signed-webhook tests,
ambiguity and bounce evidence, deployment digests, alerts, restore measurements
and any remaining production/pilot blockers.
Print "Phase 4 Completion Report" and "Open Gaps".
````

---

# D. Clarifications Needed

The following remain human/environmental inputs, not permission for the worker to invent values:

| Decision or evidence | Needed by | Required behavior while missing |
|---|---|---|
| Worker context limit, repository persistence, terminal/network access | Before execution | Use atomic steps and verified handoff; stop before context truncation |
| Representative scans, approved template and identity/work mapping policy | Phase 0 | Prepare synthetic checks, but do not claim the physical gate passed |
| OMR false-finalization bound and minimum evaluation size | Phase 1 | Do not qualify automatic finalization on real scans |
| MongoDB replica set and controlled service credentials | Phase 1 | Fail readiness/integration checks; no standalone fallback |
| Institution OIDC configuration and review-lease policy | Phase 1 | Fail protected mutations/configuration checks explicitly |
| Actual malware-verification integration | Phase 1 | Keep uploads quarantined; never assume clean |
| Per-class diagnostic quality/evidence policy and educator gold set | Phase 2 | Hold candidate interpretations for review; no fabricated threshold |
| Provider access, approved processing terms and shared budget limits | Phase 2 | Disable affected live calls, preserve grading |
| Question-bank coverage and approved rendering fonts | Phase 3 | Explicit insufficient-bank/rendering hold |
| Human inspection of every representative PDF page | Phase 3 | Do not mark visual qualification complete |
| Verified email sender, recipients, consent/release policy and retry cutoff | Phase 4 | Suppress unattempted sends or preserve uncertainty after an attempt |
| Actual service backup/recovery procedures and isolated restore environment | Phase 4 | Do not claim production readiness or a passed recovery drill |

## Explicit deviations from the original meta-prompt

- This is an **authorized MongoDB adaptation**, not a verbatim implementation of the source's SQL architecture.
- Reference modules are copied by a **byte-preserving importer**, rather than regenerated or repeated in every prompt. The worker can execute without reading the full blueprint as conversational context.
- Complete code is provided for the importer, handoff verifier, grading kernel, MongoDB transaction boundary, evidence validation, retrieval policy and email send-decision policy. The remaining named adapters are implementation work with frozen contracts and tests—not a claim that an entire repository is already supplied.
- A missing safety-critical contract or external gate may block completion. The worker is not instructed to conceal that blocker behind a passing stub.
- **Phase 5 is out of scope for these code-generation prompts.** It remains a controlled institutional pilot requiring educational, privacy, operational and cost/latency approval.

## Recommended execution order

1. Save this document as `cde_worker_prompts.md`.
2. Give the worker Section A plus **only Phase 0**.
3. Review the actual command output and completion report.
4. Resolve the phase's blocking gaps and approvals.
5. Give the worker Section A, the next phase prompt, and the verified prior report.
6. Never treat an unverified report, synthetic fixture, or mocked integration as evidence that the next production gate has been met.

**First useful milestone:** Phase 1—safe uploads, durable human review, and correct locked grades. AI and email must not delay or undermine that milestone.
