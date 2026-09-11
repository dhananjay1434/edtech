# Cognitive Diagnostic Engine — Agent Beta Prompt
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
