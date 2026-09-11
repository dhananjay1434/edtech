# Cognitive Diagnostic Engine — Agent Alpha Prompt
*(Adapted from the Tri-Agent Execution Pack)*

---

# 0. Read This Before Giving Any Agent Its Prompt

## 0.1 Product and boundaries

Build an institutional educator workspace that ingests roster-linked paper MCQ submissions, deterministically grades finalized answers, preserves durable human review, and optionally adds evidence-grounded diagnostics, approved remediation, reports, and controlled email delivery.

Target users:
- Assigned educators.
- Authorized reviewers.
- Exam publishers.
- Exam-scoped operators.
- Students initially receive verified email reports; they do not have browser accounts.

User flow:

Publish immutable exam revision → authorize and verify upload → confirm identity/template → align and read marks → resolve uncertainty → lock deterministic grade → inspect supported diagnostic evidence → retrieve approved practice → review PDF → explicitly release eligible delivery → reconcile delivery outcomes.

UI direction:
- Operational workspace, not a marketing landing page.
- Persistent exam, student/submission, and revision context.
- Evidence beside review controls.
- Keyboard-accessible controls and non-color-only status indicators.
- Separate grading, diagnostic availability, report readiness, acceptance, and delivery.
- Never describe a student as unintelligent, careless, dishonest, disabled, or low ability.

## 0.2 Source documents

Every agent receives this entire execution pack and both supplied documents:

1. `cognitive_diagnostic_engine_blueprint.md`
2. `cde_worker_prompts.md`

Supplied blueprint URL:

https://customer-assets-eiarnc6j.emergentagent.net/job_bd563d19-17de-47f2-acae-809ff4faff3c/artifacts/02uww3j7_cognitive_diagnostic_engine_blueprint.md

Supplied worker-pack URL:

https://customer-assets-eiarnc6j.emergentagent.net/job_bd563d19-17de-47f2-acae-809ff4faff3c/artifacts/6105ovxn_cde_worker_prompts.md

Source precedence:
1. Explicit operator-approved amendments recorded in the repository.
2. This pack for parallel ownership, interfaces, testing isolation, and integration.
3. The worker pack for the React/FastAPI/MongoDB adaptation and domain implementation contracts.
4. The blueprint for database-independent domain rules and protected reference blocks.

Never interpret this precedence as permission to weaken identity, grading, authorization, evidence, consent, or side-effect safeguards. Surface a safety conflict and block the affected operation.

### Important source corrections

- The worker pack's importer contains an older artifact URL. Alpha must freeze the supplied blueprint bytes and record their actual provenance before extraction. Do not silently download the older blueprint.
- The blueprint's PostgreSQL/pgvector implementation is not compatible application code for MongoDB. Replace database-specific behavior through named adapters.
- The orchestration brief mentions Atlas Vector Search, but the worker pack explicitly selects exact cosine ranking over MongoDB-filtered candidates. For this pack, follow that explicit worker-pack implementation initially. Keep retrieval behind a port. Atlas is an optional, separately approved adapter and qualification task, not an assumed available service or silent replacement.
- Missing work can justify evidence abstention. Provider refusal, exhausted transport retries, and malformed provider output are operational unavailability/failure, not evidence-based abstention about a student's work.

## 0.3 Fixed stack

- Frontend: React + TypeScript + Vite; follow the source UI libraries where useful.
- Backend: FastAPI, Python 3.12, Pydantic 2.
- Database: MongoDB replica set; use PyMongo and real multi-document transactions.
- Workflow engine: separately provisioned Temporal service with Python SDK.
- Authentication: institutional Keycloak/OIDC.
- Storage: private S3/object storage with immutable accepted objects and verified versions.
- Vision: source-specified OpenAI model, subject to actual account capability and approved policy.
- Embeddings: `text-embedding-3-small`, 1,536 finite dimensions.
- Reports: ReportLab with qualified, licensed fonts.
- Email: Resend with signed webhook verification.
- Telemetry: source-specified OpenTelemetry integration.

Do not introduce another application database, Celery, Redis, or a second queue to replace Temporal. Do not configure Temporal to persist into MongoDB. External Temporal/identity service internals are not the application database.

Resolve actual compatible dependency versions. Do not invent lockfile entries, provider methods, image digests, model access, prices, or credentials.

## 0.4 The necessary serial section

Do not have three agents invent the same contracts independently and hope Git resolves the disagreement.

The execution order is:

```text
Alpha creates a small shared seed and contract baseline
                    │
                    ▼
             operator freezes B0
                    │
         ┌──────────┼───────────┐
         ▼          ▼           ▼
       Alpha       Beta        Gamma
     data/auth   OMR/review   diagnostics/
      uploads    workflows   reports/email
         │          │           │
         └──────────┼───────────┘
                    ▼
             Merger integrates
                    ▼
         staging and external gates
```

The initial seed does not need a finished database layer, grading engine, or real provider integration. It needs stable contracts, shared dependencies, protected sources, isolated test tooling, and explicit unavailable stubs.

Before B0 exists, Beta and Gamma may inspect the documents and prepare change requests. They must not create competing production models, root configuration, migrations, or interface definitions.

Development can proceed with synthetic fixtures while external gates are pending. This permission does not authorize production use, automatic real-scan finalization, paid provider calls, or real delivery.

## 0.5 Ownership: one writer per path

Paths below are an explicit parallelization adaptation of the sequential worker pack.

| Surface | Owner during parallel work | Others' access |
|---|---|---|
| All dependency manifests and lockfiles, Python and frontend | Alpha | Read-only; submit requests |
| Root tooling, CI, lint/test configuration, shared test harness | Alpha | Read-only |
| `reference/**`, importer, copied-block manifest, protected imports | Alpha, importer only for protected content | Read-only |
| `contracts/**`, `cde/models/**`, `cde/ports/**`, shared frontend DTOs | Alpha | Read-only; conformance required |
| All executable database migrations and validator/index definitions | Alpha | Proposal files only |
| `cde/config.py`, `cde/db.py`, `cde/auth.py`, `cde/migrate.py` | Alpha | Public interfaces only |
| `cde/api.py`, shared API error mapping and dependency composition | Alpha | Export routers from owned modules |
| `web/src/main.tsx`, `App.tsx`, `api.ts`, `auth.ts`, shared UI | Alpha | Export owned pages |
| `infra/**`, Compose, Dockerfiles, CI, runtime configuration | Alpha | Requirements/proposals only |
| Data/auth/upload routes and services | Alpha | Read-only |
| OMR adapter, grading, HITL, stages, workflows, dispatcher, worker entrypoint | Beta | Public interfaces only |
| Diagnostic, retrieval, analytics, report, delivery services | Gamma | Public interfaces only |
| Alpha UI and tests | Alpha | Read-only |
| Beta UI and tests | Beta | Read-only |
| Gamma UI and tests | Gamma | Read-only |
| `handoff/alpha/**`, `change_requests/alpha/**` | Alpha | Read-only |
| `handoff/beta/**`, `change_requests/beta/**` | Beta | Read-only |
| `handoff/gamma/**`, `change_requests/gamma/**` | Gamma | Read-only |
| Final composition and migration execution after handoff | Merger, after explicit ownership transfer | Builders stop writing transferred paths |

### Runtime ownership is separate from file ownership

- Alpha owns schema definitions and reusable transactional primitives, not every domain mutation.
- Beta owns grading and review state transitions.
- Gamma owns diagnostic/report/delivery mutations in its collections.
- Shared stage and outbox behavior goes through the frozen ports implemented by the owning agent.
- Gamma cannot modify finalized answers or reset grading locks.
- Webhooks cannot change submission grading state.
- A shared-parent transaction guard must distinguish pre-grade writes from legitimate post-grade operations.

A file ownership table alone does not prevent unsafe concurrent database updates. Both forms of ownership must be enforced and tested.

## 0.6 Shared seed contract

Alpha prepares:

```text
contracts/
  version.json
  ownership.json
  interface-catalog.md
  source-precedence.md
  schemas/
  fixtures/
  feature-manifests/
  environment.md
  invariants.md
  migration-catalog.md
cde/
  models/
  ports/
  api.py
  config.py
reference/
  source.md
  worker-prompts.md
  source.lock.json
  inputs.lock.json
  copied-blocks.json
tools/
  import_reference.py
  verify_handoff.py
  verify_ownership.py
  verify_contracts.py
  run_tests.py
  verify_test_report.py
  make_bundle.py
  verify_bundle.py
tests/
  conftest.py
  contracts/
web/
  src/contracts/
  src/shared/
  src/App.tsx
  src/main.tsx
  src/api.ts
  src/auth.ts
```

These tool names are deliverables to implement, not claims that the tools already exist.

The seed must contain:
- Actual source hashes and exact extracted-reference hashes.
- Union dependency lock covering the planned three tracks.
- Importable DTOs and protocol definitions for the boundaries below.
- Shared errors and decimal/date serialization rules.
- Fake adapters confined to test namespaces.
- Explicit unavailable production adapters where implementations are not ready.
- A core startup path that does not require OpenAI or Resend.
- Test-isolation and destructive-cleanup guards.
- Ownership enforcement and contract fingerprint checks.
- Frontend shell with unavailable states, not fabricated successful data.

Do not make the seed an attempt to finish Alpha's complete implementation before parallel work starts.

## 0.7 Contract change protocol

A builder needing a shared change writes:

`change_requests/<agent>/CR-<unique-id>.md`

Include:
- Problem and affected invariant.
- Proposed DTO/schema/dependency/environment change.
- Exact consumers and affected paths.
- Backward-compatibility impact.
- Required migration and tests.
- Whether work can continue safely against the current contract.

Alpha implements an approved shared change in a spine-only commit on a contract-update branch descended from the common baseline. Do not include unrelated in-progress domain code.

All agents merge the same exact shared commit and acknowledge its fingerprint. Do not independently reproduce or cherry-pick differently edited versions of a shared contract.

Breaking interface changes require an explicit new contract version and consumer updates. No agent may silently add a field to work around validation.

The Merger rejects incompatible handoff fingerprints until the discrepancy is resolved.

## 0.8 Required interface boundaries

Alpha freezes the exact Python protocols, Pydantic models, JSON schemas, and corresponding frontend DTOs. Concrete implementations must pass the same contract tests as test fakes.

Required boundaries:

### AuthorizationPort
- Validate institutional identity and local enabled status.
- Apply exam assignment and action capability.
- Produce an authorized context; raw client IDs do not imply authorization.
- Handle revoked users and assignments.

### UnitOfWork / repository boundary
- Open a real MongoDB transaction using the source's transaction semantics.
- Perform all operations with the same session.
- Expose shared-parent conflict guards.
- Keep network/provider/Temporal calls outside retryable transaction callbacks.
- Distinguish `Conflict`, `NotFound`, `Forbidden`, `Unavailable`, and invariant failures.

### SubmissionReadPort
- Return submission metadata and immutable revision references.
- Return a transactionally consistent `GradedSubmissionV1` only when the grade is locked and complete.
- Never assemble a grade snapshot from unrelated reads of changing data.

### AnswerMutationPort
- Require the shared unlocked-submission guard before answer mutation.
- Reject locked, cancelled, or superseded submissions.
- Persist answer/task/audit/outbox changes in one transaction when applicable.

### DownstreamRevisionGuard
- Validate the exact locked grade and processing revision.
- Coordinate with cancellation, supersession, report release, and current-roster pointer changes using an appropriate shared conflict witness.
- Allow authorized downstream records without reopening answers.
- Do not reuse an unlocked-answer guard for diagnostics or delivery.

### StagePort
Operations include acquire, renew, read accepted result, commit, and fail.

Inputs identify submission, stage, input fingerprint, owner, and lease policy. Acquisitions return the monotonically increasing fence and lease expiry.

A commit requires the active owner/fence, valid lease, expected running state, and permitted aggregate revision. A lease timestamp without a fencing token is insufficient.

### OutboxPort
- Append an event inside the caller's transaction.
- Lease and dispatch outside that transaction.
- Acknowledge only under the active owner/fence.
- Validate event kind and typed payload.
- Preserve ambiguous dispatch for reconciliation.

### ReviewPort
- Claim, renew, and resolve versioned tasks.
- Enforce assignee, lease, expected version, authorized task kind, and idempotency.
- Support separately registered handlers for identity, alignment, bubble, work mapping, and diagnostic review.
- Commit human decision and wakeup intent atomically.

### QuestionBankPort / EvidencePort
- Return approved immutable question revisions and validated crop manifests.
- Expose no public object URLs.
- Preserve question-to-work mapping and identity exclusions.

### RetrievalPort
- Accept the immutable original-question snapshot, accepted error class, exclusions, and validated query embedding.
- Return approved candidate snapshots and explicit coverage/omission information.
- Never weaken policy filters because a provider or index is unavailable.

### ArtifactPort / provider adapters
- Store and read immutable bytes with checksums and version references.
- Keep provider calls injectable.
- Separate request execution from durable budget, stage, and result commits.

### Composition contract
- Alpha owns FastAPI application creation and shared dependencies.
- Beta exports its router bundle and workflow/activity registration bundle.
- Gamma exports its router bundle, task-handler extensions, and activity registration bundle.
- Beta owns workflow orchestration and the worker entrypoint.
- Gamma supplies activities, not another submission orchestrator or outbox daemon.
- Alpha owns frontend navigation; each builder exports its pages.
- Merger binds these bundles after ownership transfer.
- Required features with missing implementations fail readiness or remain explicitly disabled. Do not catch import errors and silently drop enabled routes or workers.

The catalog must freeze callable signatures, nullability, error mapping, activity names, task queues, input fingerprints, and result shapes before consumers implement them.

## 0.9 Shared fixtures: exact shape, synthetic values

These are authorized interface DTO examples, not MongoDB collection documents. They do not add persisted fields automatically. Alpha validates/finalizes these boundaries in B0.

### UnlockedSubmissionV1 — Beta's starting fixture

```json
{
  "schema_version": 1,
  "submission_id": "10000000-0000-4000-8000-000000000001",
  "exam_id": "20000000-0000-4000-8000-000000000001",
  "student_id": "30000000-0000-4000-8000-000000000001",
  "template_id": "40000000-0000-4000-8000-000000000001",
  "processing_revision": 1,
  "pipeline_target": 1,
  "version": 7,
  "state": "awaiting_review",
  "identity_confirmed": true,
  "alignment_confirmed": true,
  "answers_locked_at": null,
  "question_count": 2,
  "marking_policy": {
    "correct_marks": "1.000",
    "wrong_marks": "-0.250",
    "blank_marks": "0.000"
  },
  "answer_key": [
    {"question_number": 1, "correct_option": "A"},
    {"question_number": 2, "correct_option": "B"}
  ],
  "answers": [
    {
      "question_number": 1,
      "selected_option": "A",
      "finalized": true,
      "source": "machine"
    },
    {
      "question_number": 2,
      "selected_option": null,
      "finalized": false,
      "source": "machine"
    }
  ]
}
```

`null + finalized=false` is unresolved, not a blank. A reviewed blank is `null + finalized=true`.

### ReviewTaskV1

```json
{
  "schema_version": 1,
  "task_id": "50000000-0000-4000-8000-000000000001",
  "submission_id": "10000000-0000-4000-8000-000000000001",
  "exam_id": "20000000-0000-4000-8000-000000000001",
  "kind": "bubble",
  "question_number": 2,
  "state": "claimed",
  "version": 3,
  "claimed_by": "60000000-0000-4000-8000-000000000001",
  "lease_expires_at": "2026-01-01T10:05:00Z",
  "evidence_ref": "synthetic/review/q2.png"
}
```

The fake clock starts before expiry. Tests advance it deliberately; never depend on today's wall clock for this fixture.

### GradedSubmissionV1 — Gamma's starting fixture

```json
{
  "schema_version": 1,
  "submission_id": "10000000-0000-4000-8000-000000000001",
  "exam_id": "20000000-0000-4000-8000-000000000001",
  "student_id": "30000000-0000-4000-8000-000000000001",
  "template_id": "40000000-0000-4000-8000-000000000001",
  "exam_revision": 1,
  "processing_revision": 1,
  "version": 9,
  "answers_locked_at": "2026-01-01T10:10:00Z",
  "graded_at": "2026-01-01T10:10:00Z",
  "score": "0.750",
  "maximum_score": "2.000",
  "percentage": "37.500",
  "answers": [
    {
      "question_number": 1,
      "question_id": "70000000-0000-4000-8000-000000000001",
      "question_revision": 1,
      "selected_option": "A",
      "finalized": true,
      "state": "correct",
      "awarded_marks": "1.000"
    },
    {
      "question_number": 2,
      "question_id": "70000000-0000-4000-8000-000000000002",
      "question_revision": 1,
      "selected_option": "C",
      "finalized": true,
      "state": "incorrect",
      "awarded_marks": "-0.250"
    }
  ]
}
```

This DTO does not authorize a model call by itself. Gamma must also obtain approved question content, validated work mapping, usable evidence, and provider-policy authorization.

### Diagnostic candidate example

```json
{
  "status": "classified",
  "error_type": "Calculation Slip",
  "confidence": 0.72,
  "plain_language_summary": "The visible working uses the intended method but contains an arithmetic error.",
  "next_step": "Recheck the arithmetic in the highlighted step.",
  "abstention_reason": null,
  "evidence": [
    {
      "crop_id": "work-q2-1",
      "bbox": [0.1, 0.2, 0.8, 0.5],
      "transcription": "Synthetic arithmetic step",
      "supports": "Synthetic localized arithmetic error"
    }
  ]
}
```

This example is a semantic test case, not a replacement for the imported diagnostic JSON schema. Alpha/Gamma must map the fixture mechanically to the actual protected schema's exact field names before freezing the executable fixture. A mismatch is a contract issue, not permission to edit the protected schema silently.

The confidence value is synthetic and does not establish an acceptance threshold. Without an approved acceptance policy, this candidate goes to review rather than automatic acceptance.

### Fixture factories must also provide

- Approved two-question exam/key/template snapshots.
- Question-bank candidates for every retrieval class and each exclusion rule.
- Generated PNG crops with actual calculated hashes and dimensions.
- A work crop overlapping an identity region.
- Missing/unmapped/illegible work cases.
- Expired reviewer and expired stage leases.
- Provider timeout after possible acceptance.
- Reordered, duplicate, and conflicting signed-email-event fixtures.
- Cancellation and supersession during downstream work.

Do not invent file hashes or use illustrative object references as real storage evidence. Compute fixture artifact hashes from generated bytes.

## 0.10 Test-environment isolation

Each invocation has an agent and unique run ID.

Example:

```bash
export CDE_AGENT=beta
export CDE_TEST_RUN_ID="$(python -c 'import uuid; print(uuid.uuid4().hex[:12])')"
```

Alpha's harness derives:

```text
Mongo database:     cde_test_<agent>_<run-id>_<pytest-worker>
Temporal namespace: isolated per agent/run where supported
Temporal queues:   cde-test-<agent>-<run-id>-<queue>
Workflow ID prefix: cde-test/<agent>/<run-id>/
Object prefix:      cde-test/<agent>/<run-id>/
Compose project:    cde-<agent>-<run-id>
Local artifact dir: artifacts/<agent>/<run-id>/
```

Requirements:
- Distinct repositories/worktrees, virtual environments, `node_modules`, caches, temporary files, and output directories.
- An agent may share a MongoDB server only through a separately named database and appropriately scoped credentials.
- Include pytest-xdist worker identity when parallel tests create independent fixture lifecycles.
- Never drop a shared database or bucket, run `flushall`, or broadly terminate Temporal workflows.
- Unit/contract tests require no real provider credentials.
- Integration tests use an actual replica set; mongomock is not a transaction test.
- Refuse destructive cleanup unless the exact derived test database/prefix and run ownership match.
- Do not interpret a vaguely test-looking name as sufficient authorization.
- Never allocate or delete arbitrary Temporal namespaces without operator permission. Dedicated local test servers are acceptable for SDK tests, not production persistence qualification.
- Use dynamically allocated or explicitly reserved local ports; do not assume three Docker projects can bind the same host port.
- Live tests require explicit service configuration, approved accounts, and spending authorization.
- Sandbox email uses allowlisted synthetic/test recipients, never roster addresses by default.

### Required test-runner interface

Alpha implements:

```bash
python tools/run_tests.py --agent <alpha|beta|gamma|merger> --tier <unit|contract|integration|replay|live|gate> -- <pytest-paths-and-arguments>
```

The runner:
- Validates environment ownership and derives isolated resource names.
- Passes configuration to its child test process without logging secrets.
- Captures command, exit code, collection/pass/fail/skip counts, and output path.
- Fails a required suite with zero collected tests or unexpected skips.
- Does not convert missing live prerequisites into a green skip.
- Never loads production fake adapters to make an integration test pass.

`verify_test_report.py` checks required suite presence, exit codes, nonzero collection, unexpected skips, and gate evidence references.

Mocked success and live-service qualification must appear in separate report fields.

## 0.11 Handoff and communication

Each agent writes its own directory, never a shared phase report.

```text
handoff/<agent>/report.json
handoff/<agent>/README.md
handoff/<agent>/test-summary.json
handoff/<agent>/open-gaps.md
handoff/<agent>/logs/<command-id>.txt
```

Required report structure:

```json
{
  "agent": "alpha",
  "status": "blocked",
  "base_commit": null,
  "code_commit": null,
  "contract_version": null,
  "contract_sha256": null,
  "source_hashes": {},
  "owned_paths": [],
  "files": [],
  "commands": [],
  "migrations_required": [],
  "contracts_changed": [],
  "integration_exports": [],
  "external_gates": [],
  "open_gaps": [],
  "next_step": null
}
```

Allowed statuses:
- `complete`: assigned code and all required assigned gates have actual evidence.
- `code_ready_gate_blocked`: code checks passed; specified external qualification remains missing.
- `blocked`: code prerequisite, contract, or required internal test is unresolved.

Populate real commits, computed hashes, and actual outputs. The schema example's nulls are not a valid completed handoff.

Record the implementation commit before the reporting commit. Exclude the report from its own file-hash list. Do not create circular commit/hash requirements.

Test output committed to Git must be redacted. Raw provider responses, real scans, addresses, tokens, and presigned URLs belong in restricted storage, not handoff logs.

---

# 1. PROMPT FOR AGENT ALPHA
## Data Spine, Contracts, Authentication, and Infrastructure

### Your role

You are Agent Alpha. Own the shared foundation and invariant enforcement mechanisms for the Cognitive Diagnostic Engine.

Read Section 0 in full, both sources, and this prompt. The sequential phase ownership is superseded only where this pack explicitly reallocates work.

Your first deliverable is B0, not a completed product. After B0 is frozen, continue your data/auth/upload implementation in parallel with Beta and Gamma.

### A1. Exact responsibilities

You own:
- Shared Python and frontend dependencies and generated locks.
- Mechanical reference import and integrity verification for all phases.
- MongoDB connection, replica-set checks, transactions, validators, indexes, and migration runner.
- Pydantic persisted models, DTOs, ports, contract fixtures, and serializers.
- Institutional OIDC and exam-scoped authorization.
- Exam publication, membership, immutable revision, and reference-integrity guards.
- Safe upload registration, quarantine verification, and accepted-object registration.
- Shared API/frontend composition skeletons.
- Shared infrastructure and isolated test harness.
- Executable migrations for Gamma's later collections after contract review.

You do not implement:
- OMR algorithm adapters, scoring kernel, reviewer workflow, or Temporal orchestration.
- Vision diagnostics, retrieval ranking, analytics, reports, or email behavior.
- A substitute version of Beta/Gamma code merely because it is not merged yet.

### A2. Owned application paths

```text
pyproject.toml
requirements.in
requirements.lock
.gitignore
.env.example
.github/**
tools/**
reference/**
contracts/**
evaluation/acceptance-policy.json
cde/__init__.py
cde/config.py
cde/db.py
cde/auth.py
cde/migrate.py
cde/api.py
cde/uploads.py
cde/exams.py
cde/models/**
cde/ports/**
cde/repositories/**
cde/routes/alpha.py
migrations/**
infra/**
docker-compose.yml
web/package.json
web/package-lock.json
web/index.html
web/tsconfig.json
web/vite.config.ts
web/src/main.tsx
web/src/App.tsx
web/src/api.ts
web/src/auth.ts
web/src/contracts/**
web/src/shared/**
web/src/pages/ExamPage.tsx
web/src/pages/UploadPage.tsx
web/src/alpha/**
tests/conftest.py
tests/contracts/**
tests/alpha/**
docs/contracts.md
docs/alpha/**
handoff/alpha/**
change_requests/alpha/**
```

You also own extraction of all protected destinations listed in the source, including `cde/omr.py`, diagnostic prompt/schema/reference modules, embedding/report/email reference modules, and the template specimen. Those destinations are importer-only thereafter.

### A3. Preflight

1. Inspect the repository before changing it.
2. Report whether it is empty, an existing CDE implementation, or unrelated software.
3. Do not replace an unrelated app or delete existing migrations/data.
4. Confirm Python 3.12 and available terminal/network/container facilities.
5. Separate missing local tooling from missing live service credentials.
6. Create an inventory of existing files and migration history if a project already exists.
7. Establish canonical Git origin and actual default branch with the operator. Do not assume repositories created independently will merge cleanly.

### A4. Freeze source and protected references

1. Save the exact supplied blueprint to `reference/source.md` and worker pack to `reference/worker-prompts.md`.
2. Compute hashes from actual bytes; record both in `reference/inputs.lock.json`.
3. Correct the importer's acquisition/provenance handling explicitly. Preserve its deterministic block-selection and byte-preservation behavior.
4. Record the supplied URL or local input provenance honestly.
5. Extract phase 0, 2, 3, and 4 protected blocks now so later agents do not edit a common manifest concurrently.
6. If a section/fence is missing or ambiguous, stop. Do not select a similar-looking block.
7. If a reference has a defect, preserve it and document the narrow adapter correction needed.
8. Do not install an application SQL stack solely because an unused reference module imports one.

Commands after implementing the tools:

```bash
python tools/import_reference.py --phase 0
python tools/import_reference.py --phase 2
python tools/import_reference.py --phase 3
python tools/import_reference.py --phase 4
python -m compileall -q cde tools
```

Compilation is not proof that every reference module can be imported safely at runtime. Test only intentional runtime imports and route SQL-specific behavior through adapters.

### A5. Build the shared dependency spine

Collect the package families needed by all three agents from both sources.

Include actual requirements for FastAPI/Pydantic/PyMongo, OIDC, Temporal, OpenCV/PDFium, image validation, OpenAI, S3/HTTP, ReportLab, webhook verification, telemetry, and test tooling. Resolve compatibility rather than copying imaginary exact versions.

Generate and install the hash lock:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install pip-tools
pip-compile --generate-hashes --output-file=requirements.lock requirements.in
python -m pip install --require-hashes -r requirements.lock
python -m pip check
```

Create frontend scripts for:

```text
typecheck
lint
test
build
```

Only you run dependency additions and commit the resulting lock changes. Consumers run `npm ci`, never `npm install` to repair drift.

Ensure optional-provider configuration is not required just to import core grading dependencies or start the Phase-1 application.

### A6. Freeze B0 interfaces and tooling

Implement Section 0's shared DTOs, protocol methods, contract tests, environment rules, source checks, and path ownership validator.

Freeze:
- UUID string and API serialization rules.
- Decimal strings at API boundaries and Decimal128 in MongoDB.
- BSON UTC dates and timezone-aware Python representations.
- Submission `version`, stage `fence`, and immutable `pipeline_target` semantics.
- Workflow/activity names and input/output payloads with Beta's contract review.
- Diagnostic/report/delivery collection shapes with Gamma's contract review.
- Typed task-extension and outbox event catalogs.
- Explicit synthetic fixture semantics.
- Required test suites and their expected evidence class.

For the proposed diagnostic-candidate example, reconcile the exact imported schema before publishing an executable fixture. Preserve source field names and enum values.

Create unavailable production stubs that raise typed unavailability. Never return a synthetic grade, clean malware verdict, approved consent, or successful send in production.

Run:

```bash
python tools/verify_contracts.py
python tools/run_tests.py --agent alpha --tier contract -- tests/contracts
python tools/run_tests.py --agent alpha --tier unit -- tests/alpha/unit
(cd web && npm ci && npm run typecheck && npm test -- --run && npm run build)
```

Publish the seed commit and proposed B0 tag for operator approval. Record blockers independently of seed code readiness.

### A7. Implement MongoDB primitives and migrations

After B0, implement the production data layer while Beta/Gamma use the frozen fakes.

Required behavior:
- Fail replica-set/readiness checks on standalone MongoDB.
- Use source-compatible transaction concerns and bounded driver retry semantics.
- Make transaction callbacks replay-safe: no S3 upload, email, OpenAI, or Temporal calls inside them.
- Pass one transaction session to every operation in the transaction.
- Ensure synchronous PyMongo work does not block FastAPI's event loop; use sync routes or bounded offloading for the complete synchronous operation.
- Enforce cross-collection references through transactional services, not a claim that JSON validators provide foreign keys.
- Provide common conflict guards used by all answer writers and graders.
- Provide separate downstream guards for locked-grade consumers.
- Coordinate publication with question/key/template mutations through shared transactional conflict witnesses; read-only validation is not sufficient to prevent write skew.
- Coordinate current-submission pointer changes with downstream release checks.
- Keep published revisions immutable.
- Make audit writes append-only for normal service credentials.

Migration files:

```text
migrations/001_core.py
migrations/002_diagnostics.py
migrations/003_analytics_reports.py
migrations/004_delivery.py
```

Use source schemas plus explicitly recorded adaptation additions. Alpha owns all actual files; Gamma supplies specifications and tests.

Migration requirements:
- Checksum ledger in `schema_migrations`.
- Stable migration IDs; never edit applied migrations.
- Idempotent, resumable operations with postcondition verification.
- Read-only planning and drift checking.
- One operator-controlled migration job; API/worker replicas do not each run migrations on startup.
- Do not imply that index/validator DDL is rolled back by a multi-document transaction.
- Detect duplicate data before unique-index creation; block rather than delete duplicates.
- Use partial unique indexes for optional provider IDs and idempotency keys.
- Verify real MongoDB behavior when replacing current diagnostic records under partial unique indexes. If the intended atomic operation is unsupported, propose a versioned-head contract amendment; do not silently weaken uniqueness.
- No TTL deletion of review decisions, outbox events, submissions, audits, or delivery evidence.
- Expand/validate/backfill/contract changes are explicit; no hidden destructive migration.

Required migration CLI, implemented by you:

```bash
python -m cde.migrate --plan
python -m cde.migrate --check
python -m cde.migrate --apply
```

`--plan` is read-only. `--check` verifies applied checksums and schema/index expectations. `--apply` executes only against an explicitly configured target under the operator's migration procedure.

### A8. Authentication and authorization

Implement the source OIDC policy:
- Signature, approved algorithm, issuer, audience, expiry, and token type.
- Bounded JWKS caching and key rotation.
- Local enabled-user check and current exam assignments.
- Reviewer/publisher capabilities.
- Operators still need appropriate exam scope and an audit reason for sensitive actions.
- Apply authorization before pagination, aggregation, artifact access, and mutation.
- Return 404 for invisible resources and 403 for forbidden actions on visible resources.
- Never allow a request-supplied workflow ID to bypass resource authorization.

Frontend auth uses institutional OIDC Authorization Code + PKCE. Do not invent demo administrator accounts or ship secrets in the browser bundle.

### A9. Uploads and publication

Implement:

```text
GET  /api/health/live
GET  /api/health/ready
GET  /api/exams
GET  /api/exams/{exam_id}
POST /api/exams/{exam_id}/publish
POST /api/exams/{exam_id}/uploads
POST /api/uploads/{upload_id}/complete
```

Requirements:
- Publish only complete, approved, mutually consistent exam/key/question/template revisions.
- One uploaded PDF belongs to one roster student.
- Persist upload intent before issuing bounded quarantine credentials.
- Enforce source byte/page/pixel limits at the responsible boundary.
- Verify actual size, magic signature, checksum, object version, and malware result.
- No success-returning malware stub. Missing integration leaves the upload quarantined.
- Accepted objects are immutable and read by verified version.
- Upload completion creates submission, idempotent response, audit event, and workflow-start outbox intent in one MongoDB transaction.
- Object-store work happens outside retryable transaction callbacks; recoverable orphan artifacts are tracked or safely collected later.
- Same idempotency key/body returns the stored result; changed body conflicts.
- Identity conflict never becomes nearest-name matching.

### A10. Infrastructure

Provide an isolated local MongoDB replica-set environment or an explicit connection contract for an existing replica set.

Connect to separately provisioned Temporal and OIDC services. Do not pretend their production persistence is solved by the MongoDB container.

Own final Dockerfile/Compose changes requested by Beta/Gamma:
- Nonroot containers.
- Immutable dependencies and qualified native libraries.
- Separate worker capabilities and secret exposure.
- OMR process resource restrictions.
- Runtime nonsecret frontend configuration.
- Private storage and restricted ingress.
- Readiness checks for actual required core services.

Do not claim Kubernetes, managed backups, malware scanning, or real provider configuration exists unless actually provided and tested.

### A11. Required tests

Create meaningful tests under:

```text
tests/alpha/unit/
tests/alpha/contract/
tests/alpha/integration/
tests/alpha/authorization/
tests/alpha/failure_injection/
tests/alpha/gate/
```

Minimum cases:
- Protected source and extracted bytes unchanged.
- UUID/date/Decimal128/API round trips.
- Standalone MongoDB rejection.
- Transaction rollback and commit ambiguity handling.
- Published content mutation denied.
- Cross-exam/cross-student membership denied.
- Publication racing a content mutation.
- Duplicate upload completion and changed-body idempotency conflict.
- Corrupt, oversized, mismatched, and malware-unavailable uploads.
- Authorization revocation and 401/403/404 matrix.
- Optional-provider absence does not block core startup.
- Migration reapplication, checksum mismatch, partial operation recovery, and dirty-data rejection.
- Three concurrent harness runs cannot delete each other's sentinels.

Commands:

```bash
python tools/run_tests.py --agent alpha --tier unit -- tests/alpha/unit
python tools/run_tests.py --agent alpha --tier contract -- tests/contracts tests/alpha/contract
python tools/run_tests.py --agent alpha --tier integration -- tests/alpha/integration tests/alpha/authorization tests/alpha/failure_injection
python tools/run_tests.py --agent alpha --tier gate -- tests/alpha/gate
(cd web && npm run typecheck && npm run lint && npm test -- --run src/alpha && npm run build)
python tools/verify_test_report.py handoff/alpha/test-summary.json
```

A missing physical-template approval or real upload-security integration blocks its gate. Do not conceal it behind synthetic passes.

### A12. Handoff

Deliver:
- Source and contract hashes.
- Migration plan and schema/index catalog.
- Real repository adapter factories for the shared ports.
- Router/frontend composition instructions.
- Environment and secret requirements without secret values.
- Exact test evidence and unresolved service/approval blockers.
- Dependency/configuration change history.

Do not announce that Beta/Gamma are integrated before the Merger actually binds and tests them.
