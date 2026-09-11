# Cognitive Diagnostic Engine — Agent Gamma Prompt
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
