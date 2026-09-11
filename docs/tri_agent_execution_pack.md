# Cognitive Diagnostic Engine — Parallel Execution Pack
## Three implementation agents + one merger/migration agent

**Save as:** `tri_agent_execution_pack.md`

**Deliverable:** detailed execution prompts, not application code or a claim that tests have passed.

**Application:** React + TypeScript web application, FastAPI backend, MongoDB application database.

**Team arrangement:** three people run Alpha, Beta, and Gamma in separate repositories or worktrees. After their handoffs, one person runs the Merger prompt. The merger is a fourth execution role, not necessarily a fourth person.

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

---

# 2. PROMPT FOR AGENT BETA
## Deterministic OMR, Grading, Durable Review, and Temporal

### Your role

You are Agent Beta. Make grading deterministic, human decisions durable, and workflows recoverable.

Read Section 0, the sources, and this prompt. Your production code depends on Alpha's frozen interfaces, not on Alpha finishing its database implementation first.

### B1. Owned paths

```text
cde/omr_adapter.py
cde/grading_core.py
cde/grading.py
cde/review.py
cde/stages.py
cde/dispatcher.py
cde/workflows.py
cde/activities.py
cde/worker.py
cde/beta/**
cde/routes/beta.py
web/src/pages/SubmissionPage.tsx
web/src/pages/ReviewPage.tsx
web/src/pages/OperatorPage.tsx
web/src/beta/**
tests/beta/**
docs/beta/**
handoff/beta/**
change_requests/beta/**
```

`cde/omr.py` is protected and read-only. All shared manifests, models, ports, migrations, API composition, and frontend navigation are Alpha-owned.

### B2. Forbidden scope

Do not:
- Implement alternative auth, MongoDB setup, or data models.
- Change imported OMR reference bytes.
- Add provider calls to grading.
- Implement Gamma's diagnostics, report generation, or email.
- Add a second job queue or substitute background-task framework.
- Modify shared `package.json`, locks, `conftest.py`, API entrypoint, or navigation.
- Add a whole-file formatter pass across the repository.

### B3. Start from B0 and verify

```bash
python tools/verify_contracts.py
python tools/run_tests.py --agent beta --tier contract -- tests/contracts
python -m pip install --require-hashes -r requirements.lock
(cd web && npm ci)
```

Read `contracts/interface-catalog.md` and implement against its exact signatures. An upstream implementation gap is handled by test injection, not by editing a shared model.

### B4. Mock strategy before Alpha is ready

Create only test adapters under:

```text
tests/beta/fakes/
tests/beta/fixtures/
```

Required fakes:
- Transaction/repository adapter with explicit commit and rollback behavior.
- Fake clock.
- Immutable artifact store.
- Submission/answer/task repository.
- Outbox sink.
- Authorization context fixture.
- Stage lease state machine.

Use the `UnlockedSubmissionV1` and `ReviewTaskV1` structures from Section 0.

Fake behavior must cover:
- Shared-parent version conflict.
- Expired claim and stale expected version.
- Duplicate decision returning its stored response.
- Changed-body idempotency conflict.
- Locked-answer denial.
- Losing stage fence.
- Failure before and after an intended commit.

Do not monkey-patch `sys.modules`, shadow `cde.models`, or create fake production packages. Inject adapters through explicit factories or service constructors.

A simulated transaction test proves your domain behavior only. Real MongoDB race tests remain required after Alpha's adapter is available.

### B5. OMR adapter

Inspect the protected module's actual signatures and reuse it mechanically through `cde/omr_adapter.py`.

Implement boundary checks for:
- Approved template manifest and exact page coverage.
- Correct orientation at 0/90/180/270 degrees or explicit rejection.
- Missing fiducials, mirroring, unknown template, skew, and unsupported non-flat distortion.
- Duplicate, missing, or unexpected pages/questions.
- Identity conflicts.
- Faint, erased, double-filled, stained, shadowed, and ambiguous marks.
- Correct distinction between unresolved and finalized blank.
- Valid question-specific rough-work regions.

Resource limits from the source include:
- 25 MiB uploaded document.
- At most 10 pages.
- 300 DPI reference rendering and 20 million pixels per page.
- Isolated PDFium process; one concurrent document per OMR process.
- 1 GiB OMR worker memory limit.
- Supported maximum document OMR budget of 120 seconds.

No provider secrets or general internet access in the OMR worker.

Store attempt-specific outputs safely. A stale worker must not overwrite the accepted aligned page or crop via a mutable shared object key.

Do not tune thresholds to hide a large review queue. Real-scan false-finalization approval remains external.

### B6. Pure deterministic grading

Implement the source grading kernel in `cde/grading_core.py` without database or provider imports.

Rules:
- Exact contiguous question/key/answer coverage.
- Reject duplicate, missing, invalid, or unfinalized answers.
- Decimal arithmetic only, no binary floating-point scoring.
- Respect positive correct marks and non-positive wrong/blank marks.
- Preserve negative scores and percentages where the source policy permits them.
- Percentage rounding follows the worker pack's exact rule.
- Repeated evaluation of identical finalized inputs yields the same grade.

Persist grading in one transaction:
1. Obtain the shared parent conflict guard.
2. Verify identity, alignment, key revision, coverage, and blocking reviews.
3. Calculate grade from finalized answers.
4. Persist answer awards and grade.
5. Set `answers_locked_at` last in that transaction.
6. Persist audit/stage outcome/outbox intent as specified by the frozen contracts.

On retry of an already committed grade, return the stored grade without rewriting locked answers.

### B7. HITL claim, renew, and resolve

Implement:

```text
GET  /api/submissions/{submission_id}
GET  /api/exams/{exam_id}/review-tasks
POST /api/review-tasks/{task_id}/claim
POST /api/review-tasks/{task_id}/renew
POST /api/review-tasks/{task_id}/resolve
POST /api/submissions/{submission_id}/retry
```

Require the source's authorization, expected versions, lease policy, and idempotency headers.

Bubble resolution transaction:
- Verify visible exam and review capability.
- Return an existing identical idempotent response when appropriate.
- Reject changed-body reuse.
- Verify active claimant, expected task version, and unexpired lease.
- Obtain the unlocked submission guard before answer mutation.
- Persist the immutable decision and finalized answer.
- Persist audit and resume outbox event.
- Persist the idempotency response.
- Commit all together.

A double-click after successful resolution must return its stored result, not create a second decision. Revoked authorization must still be enforced.

Different review kinds have different guarded mutations:
- Identity/alignment/bubble may affect pre-grade processing.
- Work mapping and diagnostic review may occur after grading but cannot alter answers.

Implement a typed handler registry so Gamma can supply post-grade task handlers without editing `cde/review.py`. Dispatch one transaction through the matching handler; do not split task resolution and its domain mutation into separate commits.

Lease expiry makes a task reclaimable. It does not erase a human decision or automatically guess the answer.

### B8. Stage fencing and outbox

Implement the shared StagePort and OutboxPort.

Stage identity:

```text
(submission_id, stage, input_fingerprint)
```

Stage acquisition:
- Atomically acquire/reclaim the lease and increment the fence.
- Return stored accepted results for completed identical fingerprints.
- Persist attempt identity.

Stage completion:
- Check owner, fence, running state, expiry, and eligible revision in the result transaction.
- Accept only verified artifact references.
- Persist the first accepted logical result.
- Reject stale result publication, including an older worker finishing after lease takeover.

Outbox:
- Domain intent is committed with the domain mutation.
- Dispatch to Temporal or a registered external handler outside the database transaction.
- Acknowledge under the same event owner/fence.
- Treat matching duplicate workflow starts as idempotent success only after checking the intended aggregate/revision.
- A crash after dispatch but before acknowledgement leaves recoverable ambiguity, not lost intent.
- Unsupported event kinds become visible incidents, not discarded rows.

Gamma supplies delivery handlers to this dispatcher through the contract. Gamma must not run a competing general outbox implementation.

### B9. Temporal orchestration

Use the immutable source input:

```json
{
  "submission_id": "10000000-0000-4000-8000-000000000001",
  "processing_revision": 1,
  "pipeline_target": 1
}
```

Production workflow identity:

```text
submission/{submission_uuid}/r{processing_revision}
```

Test runs additionally use their isolated prefix/namespace.

Responsibilities:
- Preserve one submission orchestrator.
- Use deterministic workflow code only.
- Keep database/network/provider operations inside activities.
- Freeze activity names and versioning behavior in B0.
- Target 1 supports useful grading without Gamma or provider credentials.
- Targets 2–4 are selected for new workflows only when implementations and feature gates permit them.
- Do not mutate an in-flight workflow's target by reading a changed environment variable.
- Add later behavior through replay-compatible branching/patching/versioning.

Review wakeup algorithm:
1. Snapshot the signal sequence before the authoritative gate activity.
2. Query the persisted review gate.
3. Continue if ready.
4. Otherwise wait for a different signal sequence, then query again.

Signals are wakeups, not trusted decisions. This must survive a signal arriving during the gate check.

Diagnostics:
- Launch stable question-specific child workflows under the frozen contract.
- Reuse successful accepted results.
- Catch child failures.
- Persist failed checkpoint/needs-operator state.
- Wait for authorized retry/deferral rather than abandoning the parent.
- Zero wrong answers completes the diagnostic plan without provider calls.

Keep pipeline status separate from email-delivery facts. A delayed webhook must never reopen grading or overwrite a submission's newer processing revision.

### B10. Worker registration and frontend

Own `cde/worker.py` and publish the exact bundle Gamma must export for its activities.

Avoid importing heavyweight AI/PDF/email implementations into Temporal workflow definitions. Keep workflow-safe DTO imports separate from concrete activity modules.

Queue/worker behavior:
- OMR process concurrency matches source restrictions.
- AI provider concurrency is enforced through Gamma's shared budget controls, not only a per-process semaphore.
- IO concurrency respects configured database/storage capacity.
- Readiness detects enabled features with missing registrations.

Frontend:
- Submission page: truthful durable state, grade, blocked reason, revision.
- Review page: crop, option/blank controls, claimant, expiry, version, conflict refresh.
- Operator page: failed stage/checkpoint, audit-reason retry, no arbitrary workflow signalling.
- Do not add editable grade fields or ambiguous green success labels.

Export pages; do not modify Alpha's app navigation.

### B11. Required tests and commands

Create:

```text
tests/beta/unit/
tests/beta/contract/
tests/beta/integration/
tests/beta/authorization/
tests/beta/failure_injection/
tests/beta/workflow_replay/
tests/beta/gate/
```

Mandatory races/failures:
- Two reviewers claim the same task.
- Expired lease and stale tab.
- Duplicate resolve after successful commit.
- Changed request under the same idempotency key.
- Reviewer resolve versus grader.
- Two graders.
- Cancellation/supersession versus result commit.
- Worker death after object write, before DB commit.
- Worker death after grade commit, before activity acknowledgement.
- Review commit before Temporal signal delivery.
- Signal before/during gate evaluation.
- Outbox dispatch before acknowledgement.
- Lease expiry followed by stale worker commit.
- Child diagnostic failure and operator recovery.
- Old target-1 histories replay with later-feature worker versions.
- Missing page/answer never treated as blank.

Commands:

```bash
python tools/run_tests.py --agent beta --tier unit -- tests/beta/unit
python tools/run_tests.py --agent beta --tier contract -- tests/contracts tests/beta/contract
python tools/run_tests.py --agent beta --tier integration -- tests/beta/integration tests/beta/authorization tests/beta/failure_injection
python tools/run_tests.py --agent beta --tier replay -- tests/beta/workflow_replay
python tools/run_tests.py --agent beta --tier gate -- tests/beta/gate
(cd web && npm run typecheck && npm run lint && npm test -- --run src/beta && npm run build)
python tools/verify_test_report.py handoff/beta/test-summary.json
```

Run real replica-set races against Alpha's adapters when available. Record fake-only suites separately until then.

### B12. Handoff

Provide:
- Router export and worker/activity bundles.
- Accepted workflow/activity catalog and replay evidence.
- Stage/outbox/ReviewPort implementation factories.
- Gamma's integration contract for child workflows and post-grade review handlers.
- Exact concurrency and fault-injection results.
- OMR calibration/real-scan blockers.
- Required infrastructure/package requests already accepted or still outstanding.

Do not claim an OMR accuracy bound from synthetic forms alone.

---

# 3. PROMPT FOR AGENT GAMMA
## Evidence-Grounded Diagnostics, Retrieval, Reports, and Delivery

### Your role

You are Agent Gamma. Implement the external-facing and cognitive stages without compromising locked deterministic grading.

Your work is the largest track. Deliver it in independently testable slices: diagnostics, then retrieval/analytics/reports, then delivery. Do not wait until all three slices are complete to publish integration contracts and testable exports.

Read Section 0, both sources, and this prompt.

### G1. Owned paths

```text
cde/diagnostics.py
cde/evidence.py
cde/provider_budget.py
cde/embeddings.py
cde/retrieval.py
cde/analytics.py
cde/report.py
cde/email_policy.py
cde/email.py
cde/email_event_applier.py
cde/telemetry.py
cde/gamma/**
cde/routes/gamma.py
cde/gamma/activity_bundle.py
cde/gamma/review_handlers.py
fonts/manifest.json
fonts/approved-assets/**
web/src/pages/DiagnosticsPage.tsx
web/src/pages/AnalyticsPage.tsx
web/src/pages/ReportsPage.tsx
web/src/pages/DeliveryPage.tsx
web/src/gamma/**
tests/gamma/**
docs/gamma/**
handoff/gamma/**
change_requests/gamma/**
```

Protected prompt/schema/reference modules remain read-only. Alpha owns migrations, shared models, dependencies, infrastructure, API composition, and frontend navigation. Beta owns workflows, general outbox dispatch, review routing, stage fencing, and worker entrypoint.

### G2. Non-negotiable prohibitions

Do not:
- Read an unlocked answer and call it a graded submission.
- Alter selected options, awarded marks, grade totals, or grading locks.
- Infer an error from a wrong distractor alone.
- Convert model/provider failures into a student deficit or evidence abstention.
- Let model output choose recipients, release reports, change permissions, or execute tools.
- Auto-generate unapproved practice questions.
- Silently add Atlas, a second vector database, or another workflow engine.
- Create an alternate outbox dispatcher or submission workflow.
- Introduce duplicate API paths already owned by Beta.

### G3. Start and mocks

```bash
python tools/verify_contracts.py
python tools/run_tests.py --agent gamma --tier contract -- tests/contracts
python -m pip install --require-hashes -r requirements.lock
(cd web && npm ci)
```

Create fakes only in:

```text
tests/gamma/fakes/
tests/gamma/fixtures/
```

Inject:
- SubmissionReadPort returning Section 0's `GradedSubmissionV1`.
- Immutable approved QuestionBankPort snapshots.
- EvidencePort with real generated PNG bytes and hashes.
- StagePort with explicit fence loss and duplicate-result behavior.
- OutboxPort recording typed intents.
- ArtifactPort verifying immutable bytes.
- Vision/embedding/email transport fakes.
- Fake clock and deterministic request IDs.
- Budget reservation adapter with shared-state concurrency simulation.

Use the same frozen contract suite with fakes and real implementations. Do not invent upstream model fields or install a fake Alpha/Beta module under a production import path.

A fake OpenAI response is a contract test, not evidence of live model access or diagnostic quality.

### G4. Database changes through Alpha

Submit complete validator/index/migration specifications for:

```text
error_taxonomy_results
provider_budget_windows
provider_reservations
cohort_analytics
remediation_jobs
remediation_items
email_events
```

Preserve source field names, declared adaptations, exact enums, dates, UUIDs, Decimal128 rules, and unknown-field rejection.

Include:
- Uniqueness and current-result semantics.
- Nullable provider ID/key partial indexes.
- Analysis/report revision allocation.
- Acceptance-policy and provenance fields.
- Consent/release/delivery version fields.
- Any additional concurrency-control records that are genuinely required, with explicit contract approval before implementation.

You do not edit executable migration files. Alpha publishes the reviewed migration commit; you integrate it exactly.

### G5. Diagnostics

Use the actual imported vision reference and strict JSON schema through adapters.

Eligibility:
- Exact processing/exam/question revision.
- Locked grade.
- Finalized incorrect answer only.
- Verified work mapping and approved evidence-processing policy.

Evidence checks:
- At most three crops per wrong answer, each within the source pixel limits.
- Verified bytes/hash/media type/dimensions.
- Crop lies inside its declared page and approved question work region.
- No overlap with identity regions.
- Unique crop IDs.
- Evidence references only supplied crop IDs.
- Finite normalized bounding boxes with ordered coordinates.
- Prompt text and image content are untrusted data.

Exactly four classes:

```text
Calculation Slip
Procedural Flaw
Reading Comprehension Error
Conceptual Deficit
```

Outcomes:
- Absent, unmapped, illegible, contradictory, or insufficient work: valid evidence abstention, no invented diagnosis.
- Strict-schema-valid candidate: still requires evidence validation and approved acceptance policy.
- Missing acceptance policy or insufficient policy confidence: durable educator review; retain restricted candidate artifact.
- Provider refusal: diagnostic unavailable; no evasive prompting.
- Exhausted transport/schema errors: operational failure; grade stays valid.

Preserve provenance:
- Original and crop hashes/coordinates.
- Exact answer/key/question/processing revisions.
- Prompt/schema/model identifiers.
- Requested and returned model when available.
- Provider request ID and usage.
- Restricted raw response object.
- Acceptance-policy version.
- Immutable reviewer override history.

Persist the first accepted result for an input fingerprint. Retrying does not promise identical model text. Reprocessing/override creates a deliberate revision and never silently edits a published report.

### G6. Provider budgets and external-call boundaries

Before any billable dispatch:
1. Verify configured provider access and approved data-processing policy.
2. Calculate a conservative reservation in approved units.
3. Atomically reserve capacity against shared limits.
4. Acquire required shared concurrency capacity.
5. Persist attempt identity.
6. Dispatch outside any MongoDB transaction callback.
7. Settle actual usage when known.
8. Preserve uncertain reservations after possible billable success.
9. Reconcile uncertainty before reusing that capacity.

Cover all AI workers, embeddings, and schema-repair calls. Per-worker semaphores alone do not enforce a global budget.

Do not invent prices, rate limits, institution spending caps, or confidence thresholds. Missing required values disable the affected live calls.

Retry policy:
- Provider-aware bounded handling of 429/5xx/timeouts.
- Configuration failures pause affected work instead of repeating across the batch.
- At most the source's two separate schema-repair calls.
- Avoid multiplicative SDK × activity × workflow retries.
- Reserve budget for every real outbound attempt.
- Crash after a possible provider success remains potentially billable.

### G7. Diagnostic review and APIs

Implement/export:

```text
GET  /api/submissions/{submission_id}/diagnostics
POST /api/diagnostics/{diagnostic_id}/override
```

Overrides require authorization, expected analysis revision, idempotency, reason, and valid evidence. Preserve the old interpretation and create the new analysis revision transactionally.

Supply work-mapping and diagnostic-task handlers through Beta's ReviewPort registry. Do not create a competing `/review-tasks/{id}/resolve` endpoint.

The handler transaction coordinates the task decision, accepted/revised result, audit, idempotency response, and wakeup intent. It must use a downstream guard, not Beta's unlocked-answer guard.

UI shows evidence, uncertainty, abstention, unavailable-provider state, and educator overrides separately.

### G8. Embeddings and retrieval

Embedding adapter:
- Approved immutable question revisions only.
- Exact model and 1,536 finite values.
- Reject wrong dimensions, wrong model, zero norm, NaN, and infinity.
- Reuse matching input/model hashes.
- Do not attach an embedding to a changed question revision.
- Use shared budgets.

Default retrieval:
- MongoDB hard filters first.
- Exact cosine ranking over the entire qualified candidate set.
- No arbitrary candidate truncation before exact ranking.
- Deterministic tie-breaking as specified by the worker pack.
- Consistent question-bank snapshot or immutable input manifest.

Policies:
- Common: approved, active, correct embedding model, subject/topic/language, original-exam family exclusion, package-wide family deduplication.
- Calculation Slip: accuracy skill at the same difficulty.
- Procedural Flaw: matching non-null procedure and allowed difficulty.
- Reading Comprehension Error: reading skill, different phrasing variant, allowed difficulty.
- Conceptual Deficit: foundation skill, same concept, source-defined lower-difficulty rule including level 1.

Group distinct gaps by the worker pack's exact grouping key. Select at most two questions per gap and ten total.

Record insufficient eligible bank coverage separately from deliberate package-cap omissions. Do not relax language/concept/procedure/family constraints or fabricate replacements.

Atlas decision:
- Keep an adapter boundary and document bank-size/performance measurements.
- Do not implement or enable an Atlas path without an approved contract amendment and available service/index configuration.
- If later approved, test hard filters, index readiness, index freshness, revision/approval revalidation, and ranking semantics separately; approximate search must not be presented as exact ranking.

### G9. Snapshot analytics

Implement the worker pack's frozen denominators:
- Enrolled: all roster memberships for the exam revision.
- Excluded: memberships with an exclusion reason.
- Eligible: enrolled minus excluded.
- Graded: eligible students whose current pointer identifies a matching locked grade.
- Unresolved: eligible minus graded.
- Diagnostic complete: eligible graded students whose incorrect answers have accepted classified/overridden/abstained outcomes; zero incorrect answers needs no provider call.
- Provider failure is not diagnostic completion.

Per-question percentages use the current graded population. Report blank separately. Empty denominator gives null, not fabricated 0% certainty.

Class shares exclude abstentions and unavailable outcomes from the classified/overridden denominator. Label students versus answers versus observations.

Read roster pointers, grades, diagnostic-current records, and exclusions from one consistent transactional snapshot. Fingerprint ordered input revisions and policy versions. Concurrent recomputes reuse the same logical snapshot or allocate revisions safely.

Do not overwrite old analytics or published reports when a current-submission pointer changes.

### G10. Reports

Implement/export:

```text
GET  /api/exams/{exam_id}/analytics
POST /api/submissions/{submission_id}/remediation
GET  /api/reports/{report_id}
GET  /api/reports/{report_id}/download
```

Persist the immutable manifest before accepting the PDF result. Include:
- Exam/key/submission/report revisions.
- Grade summary.
- Accepted diagnostic IDs/evidence references.
- Approved practice content snapshots and family/revision IDs.
- Retrieval rules/reasons/distances and omissions.
- Prompt/schema/model/template versions.
- Font identifiers, verified checksums/licenses, and renderer version.

Renderer:
- Adapt the protected ReportLab API rather than guessing its signature.
- Escape student, question, and model text.
- Do not execute model-authored HTML/JS.
- Block unsupported fonts/scripts/math rather than silently rendering broken output.
- Verify stored PDF bytes/hash before ready.
- Download requires current exam authorization and private short-lived access.
- Missing bank/rendering holds reports, not grading.

Visual gate:
- Render every representative PDF page to PNG in isolated PDFium processes.
- Include long names/stems, many options, page breaks, supported script/math, and injection-like text.
- Require actual human approval linked to exact rendered-page hashes.
- Nonempty PDF bytes or OCR text do not prove visual correctness.

### G11. Explicit report release

Implement/export:

```text
POST /api/reports/{report_id}/release
GET  /api/reports/{report_id}/delivery
POST /api/reports/{report_id}/reconcile
POST /api/webhooks/resend
```

Release requires:
- Publisher capability and current local authorization.
- Explicit action, expected report/release version, and idempotency key.
- Verified ready manifest/PDF and no publication hold.
- Non-cancelled, non-superseded intended revision.
- Verified authorized recipient and institution-approved consent/release policy.
- Frozen payload bytes, checksum, recipient, report revision, and stable provider key.

Use the source logical email key:

```text
cde/report/{report_uuid}/revision/{report_revision}
```

Store immutable payload bytes before committing the send intent. Handle orphan storage artifacts explicitly. Do not perform external sends in a transaction callback.

Changed recipient/body/attachment requires a deliberate new revision and release, not mutation under the old key.

### G12. Sending and ambiguity

Use Beta's StagePort and shared dispatcher contract.

- Recheck eligibility immediately before dispatch.
- Persist first attempt time before the first external call; never reset it.
- Send the identical payload bytes under the same provider key.
- Preserve provider acceptance separately from delivery.
- Retry only inside a conservative approved cutoff within the provider's verified deduplication window.
- Budget enough time for the complete HTTP request before the deadline.
- Verify current provider behavior during live qualification; the source's 24-hour window is not an eternal assumption.
- Outside the permitted window, mark `delivery_unknown` and reconcile.
- Never invent a fresh key to resolve unknown acceptance.

A stage fence prevents stale database commits. It cannot undo an email accepted by the provider. If a stale/in-flight attempt later produces valid acceptance evidence, retain that evidence through an audited reconciliation path rather than silently discarding it.

Consent withdrawal before an unattempted send suppresses it. Withdrawal after possible dispatch does not prove nothing was sent. Cancellation cannot retract an already accepted email by assertion.

### G13. Signed webhooks and projection

Webhook ingestion:
- Verify original raw body bytes and actual signature/timestamp contract.
- Use verified provider event/delivery identity.
- Persist durably before acknowledging.
- Same event ID/same hash is an idempotent duplicate.
- Same event ID/different hash is an integrity incident.
- Unknown provider email IDs remain stored and unapplied.
- Never link by client-supplied recipient email.

Projection:
- Separate durable event consumer.
- Transactionally apply event facts and mark the event applied.
- Preserve occurrence versus receipt times.
- Preserve accepted/delivered/bounced facts independently.
- Older accepted events cannot downgrade later delivery/bounce facts.
- Contradictory terminal facts require visible reconciliation.
- Bounces do not cause automatic repeated sends.
- Neither ingestion nor projection touches answers, grade totals, grading locks, or Beta's state machine directly.

Reconciliation requires operator authorization, exam scope, an audit reason, and verifiable external evidence. Do not provide an arbitrary mark-delivered shortcut.

### G14. Telemetry and frontend

Implement redacted telemetry in your owned module and provide Alpha/Beta an instrumentation integration manifest.

No names, email addresses, JWTs, signed URLs, raw student writing, or full model transcripts in ordinary logs.

Pages:
- Diagnostics: evidence, accepted interpretation, abstained/unavailable distinction, override history.
- Analytics: exact denominators, revision/time, unresolved/excluded coverage.
- Reports: manifest/revision, insufficient-bank and rendering holds, private download.
- Delivery: explicit release, accepted/delivered/bounced/suppressed/unknown, reconciliation trail.

Export pages and routers without editing shared composition files.

### G15. Required tests and commands

Create:

```text
tests/gamma/unit/
tests/gamma/contract/
tests/gamma/integration/
tests/gamma/authorization/
tests/gamma/failure_injection/
tests/gamma/live/
tests/gamma/gate/
```

Required cases:
- Correct/unfinalized/unlocked answers denied for diagnosis.
- Missing work produces evidence abstention without a provider call.
- Refusal/timeout/malformed output produces operational unavailability, not a fifth class or student deficit.
- Unknown crop ID, out-of-bounds box, identity overlap, prompt injection.
- Strict-schema candidate without acceptance approval goes to review.
- Concurrent provider reservations and uncertain billable attempts.
- Schema repair consumes budget and respects total retry limits.
- Two accepted-result commits for one fingerprint.
- Diagnostic override racing another override and cancellation/supersession.
- All retrieval hard filters, family deduplication, sparse bank, tie ordering, and cap accounting.
- Zero-student/zero-wrong-answer analytics and current-pointer races.
- Immutable PDF/manifest retries and stale artifact publication.
- Release versus recipient/consent/current-revision change.
- Crash after send acceptance before provider-ID persistence.
- Same-key retry inside the allowed window and unknown outside it.
- Webhook before response, duplicates, reordering, invalid signature, conflicting event hash.
- Webhook/diagnostic writes cannot mutate locked answers.

Commands:

```bash
python tools/run_tests.py --agent gamma --tier unit -- tests/gamma/unit
python tools/run_tests.py --agent gamma --tier contract -- tests/contracts tests/gamma/contract
python tools/run_tests.py --agent gamma --tier integration -- tests/gamma/integration tests/gamma/authorization tests/gamma/failure_injection
python tools/run_tests.py --agent gamma --tier live -- tests/gamma/live
python tools/run_tests.py --agent gamma --tier gate -- tests/gamma/gate
(cd web && npm run typecheck && npm run lint && npm test -- --run src/gamma && npm run build)
python tools/verify_test_report.py handoff/gamma/test-summary.json
```

Live/gate commands require actual prerequisites. Missing provider approval, fonts, educator labels, PDF visual approval, or sender configuration remains a reported blocker.

### G16. Handoff

Deliver separately testable slices:
1. Diagnostic activities, review handlers, schemas/adapters, budget controls.
2. Retrieval/analytics/report services and PDF qualification evidence.
3. Release/send/webhook/reconciliation services and delivery evidence.

For each, provide router/activity/page exports, migration requirements already accepted by Alpha, exact feature prerequisites, test outputs, and external gate blockers.

Do not describe all of Gamma as complete because mocked email transport passed.

---

# 4. PROMPT FOR THE MERGER / INTEGRATION / MIGRATION AGENT
## Controlled Assembly, Real Adapter Wiring, Database Migration, and Release Qualification

### Your role

You are the Merger. Assemble the three independently produced implementations into one coherent, tested application.

Your job is not to paste folders together, choose one side of every Git conflict, rewrite all three agents' code, or claim production readiness from a successful build.

Read the full execution pack, both sources, all three handoffs, accepted change requests, and actual Git diffs before changing anything.

### M1. Your authority and limits

After the operator freezes builder handoffs:
- You become the sole writer for shared composition/configuration paths during integration.
- Builders stop editing those transferred paths.
- You may bind adapters, routers, task handlers, worker bundles, frontend pages, and final infrastructure settings.
- Narrow cross-module fixes must have an integration issue, rationale, and regression test.
- Substantial domain defects go back to the owning builder for a focused patch.
- You do not weaken tests, remove migrations, edit protected reference bytes, or fabricate missing approvals.
- You do not send real email, run paid provider tests, delete data, or migrate production without explicit authorization.

Owned integration outputs:

```text
docs/integration/merge-plan.md
docs/integration/source-and-contract-audit.md
docs/integration/migration-plan.md
docs/integration/release-checklist.md
docs/integration/recovery-runbook.md
tests/merger/**
handoff/merger/**
```

Shared spine changes must be explicit integration commits, not mixed into unexplained conflict resolutions.

### M2. Git topology and handoff transport

Preferred setup: one canonical repository, common B0 ancestry, three feature branches.

Operator-approved seed:

```bash
git tag -a cde-contracts-v1 <actual-seed-commit> -m "CDE shared contract baseline"
git push origin cde-contracts-v1
```

Each builder uses its own clone/worktree and branch from that actual tag:

```bash
git fetch origin --tags
git switch -c cde/alpha cde-contracts-v1
# Beta uses cde/beta; Gamma uses cde/gamma in their own workspaces.
```

These are templates. Substitute actual reviewed refs; do not run them blindly in a dirty or unrelated repository.

If network Git access is unavailable:
- Each agent exports a Git bundle plus report and checksum manifest using the seed's bundle tool.
- Bundle metadata names the baseline, implementation commit, report commit, and contract fingerprint.
- Verify with `git bundle verify` and the custom manifest verifier before fetching.
- Import bundles into the integration repository without copying folders over existing files.

If agents already initialized unrelated Git histories:
- Do not use `--allow-unrelated-histories` as a substitute for review.
- Inventory their changes against the approved B0 file set.
- Produce path-scoped patches containing only each owner's authorized changes.
- Apply those patches to B0-derived branches and rerun source/contract/ownership tests.
- Preserve original commit IDs and patch provenance in the handoff.

### M3. Intake audit: stop before merging if unsafe

For every agent:
1. Verify common source hashes and B0 ancestry.
2. Verify implementation commit and handoff file hashes.
3. Check contract version/fingerprint compatibility.
4. Check owned-path diffs against `contracts/ownership.json`.
5. Verify test outputs are actual, nonempty, and collected the required tests.
6. Separate fake, real-integration, live-provider, and external-gate evidence.
7. Inspect all TODO/gap/unavailable stubs and feature flags.
8. Reject hidden fake production adapters or success-returning security stubs.
9. Confirm no real student data, secrets, or private responses entered Git.
10. Check for duplicate routes, workflow names, migrations, collection models, or competing outbox implementations.
11. Confirm Beta/Gamma did not edit manifests or regenerate protected reference files.
12. Confirm every required contract update was merged from the same reviewed commit.

Use Alpha's implemented tools:

```bash
python tools/verify_handoff.py handoff/alpha/report.json --allow-gate-pending
python tools/verify_handoff.py handoff/beta/report.json --allow-gate-pending
python tools/verify_handoff.py handoff/gamma/report.json --allow-gate-pending
python tools/verify_contracts.py
```

The gate-pending flag permits non-production integration of code-ready work only. It does not waive any release gate.

Verify handoff file hashes at the handoff's own commit. After integration changes, create a new merger manifest; do not rewrite builder evidence to match new files.

### M4. Create the integration branch

Start from the approved baseline or the agreed current mainline containing it. Record the exact merge base.

Example sequence:

```bash
git status --short
git fetch origin --tags
git switch -c integration/cde-v1 <approved-integration-base>
git merge --no-ff origin/cde/alpha
# Verify source, ownership, migrations, and Alpha tests.
git merge --no-ff origin/cde/beta
# Verify contracts, deterministic grading, review, and replay.
git merge --no-ff origin/cde/gamma
# Verify contracts and downstream suites.
```

Before each merge, inspect:

```bash
git diff --name-status <recorded-base>...<incoming-ref>
git log --oneline <recorded-base>..<incoming-ref>
```

Rules:
- Alpha → Beta → Gamma is the normal merge order because foundation and workflow interfaces are upstream.
- Run verification after every merge, not only after all three.
- Never use repository-wide `ours`/`theirs` conflict resolution.
- A shared-lockfile conflict is an ownership/process violation; reconstruct the approved manifest and regenerate one lock as sole owner.
- A shared DTO conflict requires a versioned contract decision and consumer updates, not a union of arbitrary fields.
- A migration-number conflict requires catalog review; do not renumber already applied migrations.
- Unexpected edits to another agent's domain are rejected or reviewed as explicit patches.

Record every conflict and its resolution in `docs/integration/merge-plan.md`.

### M5. Wire real adapters; remove false integration

Explicitly compose:

```text
Alpha auth/context/repositories/transaction helpers
             │
             ├── Beta grading/review/stages/outbox
             │           │
             │           └── Beta workflow and worker entrypoints
             │                          │
             └── Gamma diagnostics/retrieval/report/delivery activities
                                        │
                         signed event ingestion and projection
```

Verify:
- One FastAPI app and one centralized authorization policy.
- One production model/DTO definition per contract.
- One generic stage implementation and one generic outbox dispatcher.
- One submission workflow family with replay-compatible evolution.
- One owner for each route path and HTTP method.
- One post-grade handler registration per review task kind.
- Real adapters injected in production and staging.
- Fakes importable only from test paths.
- Required enabled bundles missing from an installation fail readiness.
- Core grading runs when diagnostics/email are disabled.
- Frontend route/page exports are registered once.
- Optional features show unavailable states, not invented data.

Document the exact factory bindings in the merger report.

### M6. Database migration assessment

First determine the real starting point:
- Fresh MongoDB database.
- Existing CDE MongoDB schema/version.
- Unknown or unrelated database.
- A separately identified legacy application/data store.

Do not assume a PostgreSQL database exists merely because the theoretical blueprint contains SQL.

For unknown/unrelated data: stop migration and produce an inventory/report. Do not overwrite it.

For a fresh MongoDB database:
- Provision/verify replica-set transaction support.
- Apply the reviewed migrations once.
- Verify validators, indexes, credentials, and runtime compatibility.

For existing CDE MongoDB:
1. Inventory migration ledger/checksums, collection validators, indexes, counts, and data-shape deviations.
2. Detect duplicate identifiers, dangling references, invalid decimals/dates, duplicate current records, and inconsistent roster pointers.
3. Produce a read-only migration plan with estimated affected records and irreversible operations.
4. Capture an actual restorable backup/snapshot and object/workflow recovery references.
5. Rehearse migration on an isolated restored copy.
6. Pause admission/mutations as required by the reviewed compatibility plan; drain or route workers safely.
7. Run one deployment-controlled migration job.
8. Verify each migration's postconditions before recording success.
9. Reconcile app/workflow/object state before reopening admission.

DDL cautions:
- Do not assume index creation, validator changes, and data backfills form one transactional rollback unit.
- An interrupted migration must be safely resumable based on observed state and checksums.
- Do not automatically start a second migration runner while the previous runner may still execute DDL.
- Do not blindly remove duplicates to make unique indexes build.
- Use expand/validate/backfill/contract for incompatible schema changes.
- Existing applications may need a maintenance window; do not promise zero downtime without an actual compatibility test.

Commands, only after target and approvals are verified:

```bash
python -m cde.migrate --plan
python -m cde.migrate --check
python -m cde.migrate --apply
python -m cde.migrate --check
```

Record the target's nonsecret identity, backup reference, migration IDs/checksums, start/end times, counts, validation output, and operator approval.

### M7. If a real legacy SQL migration is requested

This is not automatic scope. Do not create another application database or infer that data must be migrated from the reference schema.

If the operator confirms an actual legacy dataset:
- Inventory/export its schema and data read-only.
- Produce an approved field-by-field migration map before importing.
- Preserve canonical UUIDs and revision relationships.
- Convert decimal values losslessly to Decimal128 and timestamps to UTC.
- Translate SQL-only constraints into explicit MongoDB validation and transactional guard tests.
- Validate every reference, current-submission pointer, grading lock, report revision, and delivery idempotency key.
- Preserve original immutable source/report object hashes and versions.
- Preserve unknown email acceptance; never re-enqueue all historical deliveries.
- Reconcile counts, hashes, and sampled domain invariants before cutover.
- Do not synthesize grades, consent, identities, provider IDs, or approvals for missing legacy fields.
- Keep import tooling separate from the application's fixed MongoDB runtime stack.

Missing migration mapping or provenance blocks cutover. A data import is not permission to resend reports.

### M8. End-to-end test environment

Use an isolated merger run:

```bash
export CDE_AGENT=merger
export CDE_TEST_RUN_ID="$(python -c 'import uuid; print(uuid.uuid4().hex[:12])')"
```

Use the shared harness for all backend suites. Do not point it at developer or production databases.

Create merger tests under:

```text
tests/merger/contract/
tests/merger/integration/
tests/merger/failure_injection/
tests/merger/migration/
tests/merger/recovery/
tests/merger/live/
tests/merger/gate/
```

At minimum, execute these complete paths:

1. **Core grading:** authorized upload → verified quarantine/acceptance → outbox start → OMR → review → locked grade, with AI/email disabled.
2. **No wrong answers:** diagnostic plan empty; no billable diagnostic calls.
3. **Missing work:** valid grade plus evidence abstention; no inferred deficit.
4. **Supported work:** strict validated candidate → policy/review → accepted diagnostic → approved retrieval → immutable report.
5. **Insufficient bank:** explicit coverage hold; grade remains usable.
6. **Controlled delivery:** explicit release → frozen payload → acceptance → signed event → delivery projection.
7. **Revoked permission:** access denied across API, evidence, reports, analytics, review, release, and reconcile.
8. **Reprocessing:** new revision/current pointer does not mutate old grades, snapshots, reports, or silently re-email.

### M9. Cross-agent race and crash matrix

These must use the integrated real implementations, not three isolated mocks.

| Race/failure | Required outcome |
|---|---|
| Two reviewers resolve one task | One immutable decision; other request conflicts or returns identical idempotent response |
| Reviewer versus grader | Shared-parent conflict prevents answer change after lock |
| Two graders | One accepted deterministic grade per revision |
| Stage lease takeover versus old worker | Old fence cannot publish accepted result |
| Review committed, process dies before signal | Durable outbox resumes correct workflow |
| Signal arrives during review gate | No lost wakeup |
| Grade committed, activity acknowledgement lost | Stored grade reused; no answer rewrite |
| Diagnostic commit versus supersession | Correct revision provenance; no publication as the new current revision |
| Concurrent diagnostic overrides | Versioned history and one valid current result |
| Provider call succeeds, response/commit lost | Uncertainty retained; no false free-budget reclamation |
| Gamma activity imported by target-1 worker | Core workflow remains independent of unavailable providers |
| Webhook while another sheet is grading | Delivery update cannot touch answers or grading locks |
| Webhook before provider ID recorded | Event durable and unapplied until verified linkage |
| Contradictory terminal email events | Visible reconciliation; no invented precedence |
| Report release versus recipient/consent change | Authorized eligibility rechecked; in-flight uncertainty preserved |
| Email accepted, sender dies before persistence | Same-key recovery within verified window; unknown/reconcile outside it |
| Current pointer changes during analytics | Consistent snapshot or explicit retry, never mixed denominator |
| Migration interrupted midway | Safe resumption with verified schema/index state |
| Three test runs execute cleanup concurrently | Each run's sentinels survive other runs' cleanup |
| Worker version changed with active histories | Replay passes or deployment is blocked |
| Restore app DB without matching workflow/object state | Admission remains blocked pending reconciliation |

Do not claim universal exactly-once external computation or email transport. Prove one accepted logical database result and documented external ambiguity handling.

### M10. Verification commands

Run the source/contract checks and all builder suites against the merged tree:

```bash
python tools/verify_contracts.py
python -m compileall -q cde tools
python -m pip check

python tools/run_tests.py --agent merger --tier contract -- tests/contracts tests/alpha/contract tests/beta/contract tests/gamma/contract tests/merger/contract

python tools/run_tests.py --agent merger --tier unit -- tests/alpha/unit tests/beta/unit tests/gamma/unit

python tools/run_tests.py --agent merger --tier integration -- tests/alpha/integration tests/alpha/authorization tests/alpha/failure_injection tests/beta/integration tests/beta/authorization tests/beta/failure_injection tests/gamma/integration tests/gamma/authorization tests/gamma/failure_injection tests/merger/integration tests/merger/failure_injection tests/merger/migration

python tools/run_tests.py --agent merger --tier replay -- tests/beta/workflow_replay

(cd web && npm ci && npm run typecheck && npm run lint && npm test -- --run && npm run build)
```

Then, with explicit external prerequisites and approval:

```bash
python tools/run_tests.py --agent merger --tier live -- tests/gamma/live tests/merger/live
python tools/run_tests.py --agent merger --tier gate -- tests/alpha/gate tests/beta/gate tests/gamma/gate tests/merger/gate tests/merger/recovery
python tools/verify_test_report.py handoff/merger/test-summary.json
```

If a required path has no tests, that is a missing deliverable. Do not remove the path from the command to obtain success.

### M11. Deployment and service qualification

Use actual supplied endpoints, secrets, qualified images, and private test data.

Verify:
- Replica-set transactions and controlled credentials.
- Temporal namespace/service access and worker registrations.
- OIDC issuer/client/audience/redirect configuration.
- Private S3 quarantine/accepted-object boundaries and checksum/version handling.
- Real malware adapter, with unavailable verdict still fail-closed.
- Optional-provider readiness separate from core availability.
- No secrets in React bundles, OMR environment, logs, or Git.
- Worker resource limits and native-library availability.
- Signed reachable webhook endpoint and verified sending identity before email qualification.

After configuring the approved staging target:

```bash
docker compose --env-file .env config --quiet
docker compose --env-file .env build
# Run the single reviewed migration job before admitting application traffic.
docker compose --env-file .env run --rm migrate
docker compose --env-file .env up -d
```

The `migrate` service must invoke the reviewed migration CLI exactly once. Do not also auto-run migrations independently in every API/worker container.

Build success is not readiness, throughput qualification, educational validation, or production certification.

### M12. Recovery and rollback

Document and rehearse recovery of:
- MongoDB data, indexes, validators, and migration ledger.
- Actual Temporal persistence/managed-service recovery procedure.
- Source/report/evidence object versions and hashes.
- Institutional identity configuration and permissions.
- Outbox/stage/revision/delivery reconciliation.

A workflow-history export is not a complete Temporal service backup.

Before reopening admission after restore:
- Verify current roster pointers and locked grade invariants.
- Verify immutable source/report artifacts.
- Reconcile outbox intents with actual workflow state.
- Reject expired/stale stage owners.
- Preserve uncertain provider spend and email acceptance.
- Retain unmatched signed events.
- Confirm current enabled users and assignments.

Measure actual RPO/RTO against the source design targets; do not report targets as measured results.

Rollback distinctions:
- Code rollback requires compatibility with the current schema and workflow histories.
- Migration rollback may require forward repair or restore; do not blindly execute down-migrations that lose data.
- External AI charges and accepted emails cannot be undone by Git rollback.
- Restore testing never overwrites production.

### M13. Release gates and final report

Report each separately:

| Gate | Evidence required |
|---|---|
| Code assembly | Real imports, build, routes, adapters, ownership/source checks |
| Deterministic grading | Real transaction races and locked-grade recovery |
| Physical OMR | Approved held-out physical scans and agreed error bounds |
| Authorization/upload safety | Actual denial matrix and fail-closed malware/integrity behavior |
| Diagnostics | Educator-labeled evaluation, approved policy, valid provenance, budget controls |
| Retrieval/analytics | Hard-filter and denominator/revision tests plus measured bank performance |
| PDF quality | Human approval of exact representative rendered-page hashes |
| Delivery | Live signed-webhook/ambiguity/bounce qualification under approved sender/recipient policy |
| Operations | Monitoring, service recovery, restore reconciliation, actual measured recovery evidence |

Final outputs:

```text
handoff/merger/report.json
handoff/merger/README.md
handoff/merger/test-summary.json
handoff/merger/merge-manifest.json
handoff/merger/migration-evidence.json
handoff/merger/release-gates.json
handoff/merger/open-gaps.md
```

Include:
- Exact merged builder commits and final implementation commit.
- Source/contract/lock hashes.
- Conflict resolutions and integration patches.
- Actual applied migration IDs/checksums and backup/rehearsal references.
- Real adapter bindings and enabled feature targets.
- Actual commands, outputs, collected counts, failures, skips, and external blockers.
- Remaining operator actions with responsible owner.
- Clear determination: blocked, code-ready with gates pending, or qualified for the explicitly tested release scope.

Do not call the application production-ready while mandatory educational, privacy, live-service, physical-scan, or recovery gates remain unproven.

---

# 5. Human Operator Checklist

## Before parallel work

- [ ] Give all three people this full pack and both sources.
- [ ] Establish one canonical repository and approved existing-code baseline.
- [ ] Run Alpha's seed step first.
- [ ] Review and freeze B0 source/contracts/dependency/tooling commit.
- [ ] Create separate clones/worktrees, branches, environments, and run IDs.
- [ ] Confirm no builder can delete another builder's test resources.
- [ ] Keep real student data and paid provider calls disabled without approval.

## During parallel work

- [ ] Alpha is the only shared-spine/migration writer.
- [ ] Beta/Gamma submit shared changes as requests, not direct edits.
- [ ] Every shared update is the same committed change consumed by all agents.
- [ ] Test fakes remain confined to tests.
- [ ] Gamma delivers three incremental slices rather than one late monolith.
- [ ] Missing external evidence remains visibly blocked.

## Before merging

- [ ] Freeze builder handoffs and transfer shared-path ownership to Merger.
- [ ] Verify hashes, ancestry, owned-path diffs, and real test evidence.
- [ ] Merge Alpha, then Beta, then Gamma, verifying after each.
- [ ] Wire real adapters and run cross-agent race/failure tests.
- [ ] Rehearse migration on an isolated restored target before production changes.
- [ ] Qualify optional features separately from useful core grading.

## Decisions that remain external

These are not silently guessed:
- Actual repository/terminal/container capabilities and existing deployment state.
- Approved physical scans, template/identity policy, and OMR acceptance bounds.
- Real malware-verification integration.
- OIDC, S3, MongoDB replica-set, and Temporal endpoints/credentials.
- Reviewer lease policy and operational SLAs.
- AI processing approval, model access, acceptance policy, and provider budgets.
- Question-bank coverage/scale and any later Atlas decision.
- Licensed fonts, supported rendering subset, and human PDF approval.
- Sender/recipient verification, consent/release policy, and conservative retry cutoff.
- Real backup/restore services and production migration authorization.

Missing inputs block their affected operations or release gates, not unrelated offline implementation.

## Optional later improvements

Only after explicit approval and core qualification:
- Atlas retrieval adapter with measured semantics/performance.
- Student portal and additional institutional integrations.
- Broader template/language/script support.
- Multi-institution authorization/data-isolation migration.
- Additional scanner calibration and longitudinal analytics.

**Success means one coherent application with preserved invariants and verifiable evidence—not three green mock demos placed in the same repository.**
