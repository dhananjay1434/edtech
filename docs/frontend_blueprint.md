# frontend_blueprint.md

## 1. Decision and hardened implementation plan

**Product:** A responsive, web-based Cognitive Diagnostic Engine for teachers, pseudonymous operational reviewers, and students.

**Architecture:** React + TypeScript frontend; retain FastAPI, Temporal, MongoDB, and Keycloak. Use a React SPA rather than introducing Next.js or another application backend.

### Build order
1. **Verify the integration contracts.** Obtain deployed OpenAPI schemas and contract tests for resumable uploads, workflow status, evidence authorization, HITL revisions, teacher overrides, and publication. Treat missing capabilities as backend dependencies—not frontend workarounds.
2. **Build the secure application foundation.** Keycloak authentication, tenant-scoped query caches, role-specific routes, accessible navigation, and authorized evidence delivery.
3. **Complete the teacher journey.** Select roster/exam → upload PDFs → monitor processing/review → inspect draft → override with an audit reason → explicitly publish.
4. **Complete the review journey.** Open a pseudonymous task → inspect its crop → submit a versioned resolution → advance only after acknowledgement. Remove stale tasks on `409`, then reconcile with the server.
5. **Complete the student journey.** Open a published exam → see grade and handwriting evidence → read an answer-scoped explanation and a constructive next step.
6. **Gate release on adversarial tests.** Cross-tenant access, interrupted uploads, duplicate completion, concurrent resolution, stale publication, expired authentication, inaccessible crops, and accidental disclosure of draft grades.

**Excluded from v1:** aggregate analytics, policy tuning, full operations dashboards, and automated post-publication correction workflows. A minimal operational failure/recovery surface remains necessary.

### Three constraints worth challenging
- **Tus is not a frontend-only feature.** FastAPI or an authorized upload service must support creation, offset recovery, expiration, ownership checks, and idempotent completion. Ordinary multipart upload cannot satisfy this requirement.
- **Masking the top 15% is not an anonymity guarantee.** Names can appear elsewhere. Admin evidence needs a server-enforced redaction eligibility gate; unsafe crops must enter a separate restricted exception process.
- **Frozen thresholds are necessary but insufficient for reproducibility.** Also version the input, answer key, crop/transformation pipeline, prompt, model identifier, grading rules, and human revisions. Model reruns are not guaranteed to reproduce an earlier response; retain the original artifacts and outputs.

## 2. Evidence and integration status

I inspected the repository overview and [`contracts/interface-catalog.md`](https://github.com/dhananjay1434/edtech/blob/main/contracts/interface-catalog.md). That catalog lists internal ports, not HTTP request/response schemas.

Accordingly:
- `/submissions/{id}/status` is a **user-supplied contract**, not an endpoint verified by this inspection.
- Tus support, publication endpoints, revision formats, Keycloak claim mappings, and evidence URLs remain **integration gates**.
- The code below implements frontend behavior against an explicit typed facade. Its methods are required capabilities, **not invented claims about existing REST endpoints**.
- These are foundational reference implementations, not an executed or audited repository patch. They should not be described as production-ready until the adapter, authorization tests, and browser tests pass.

## 3. Technology and visual direction

| Choice | Reason |
|---|---|
| React + TypeScript + Vite | Fast, typed, client-rendered application; authenticated portals do not need SEO rendering. |
| React Router | Explicit portal boundaries and durable deep links. |
| TanStack Query | Server-state caching, polling, cancellation, mutation lifecycle, and reconciliation. |
| Keycloak JS | OIDC Authorization Code flow with PKCE; no hand-built JWT login. |
| tus-js-client | Resumable transfer primitives with explicit control over credentials and persistence. |
| Tailwind CSS | Shared visual tokens and consistent responsive layouts. |
| Zod | Runtime validation at the API adapter boundary; TypeScript alone does not validate responses. |
| Vitest + Testing Library + Playwright | Component behavior and end-to-end failure/concurrency tests. |

**No Redux initially.** Keep server data in Query, navigation/filter state in URLs, and transient form state in components. Do not mirror workflow state into a second global store.

**Visual language:** slate text, off-white canvas, white evidence panels, restrained indigo actions, amber calculation-slip indicators, and violet concept-review indicators. Reserve destructive red for actual failures—not learner identity. Every status includes text and an icon or shape, never color alone.

Use a system typography stack initially, tabular numerals for grades, visible keyboard focus, comfortable touch targets, reduced-motion support, and WCAG 2.2 AA contrast. Desktop evidence is side-by-side; mobile places the crop immediately above its explanation. Prefer informative empty/error states over decorative animation.

## 4. Routing and component architecture

```text
web/
  package.json
  src/
    main.tsx
    app/
      router.tsx
      Shell.tsx
      providers.tsx
      auth.ts
      styles.css
    api/
      contracts.ts
      client.ts             # authenticated HTTP transport
      adapter.ts            # verified wire schemas -> frontend DTOs
      schemas.ts
    features/
      teacher/
        ExamList.tsx
        TeacherUploadBay.tsx
        SubmissionStatus.tsx
        DraftReview.tsx
        PublishDialog.tsx
      admin/
        HitlQueue.tsx
        ResolutionForm.tsx
      student/
        ExamFeed.tsx
        StudentDiagnosticView.tsx
    shared/
      Evidence.tsx
      ErrorBoundary.tsx
      EmptyState.tsx
    tests/
      contracts/
      components/
      e2e/
```

| Route | Audience and behavior |
|---|---|
| `/auth/callback` | Complete Keycloak redirect; do not render private content before bootstrap finishes. |
| `/teacher/exams` | Authorized rosters/exams and recoverable submissions. |
| `/teacher/exams/:examId/upload` | Bulk PDF selection and resumable transfer. |
| `/teacher/submissions/:submissionId` | Processing state, draft review, overrides, and publication. |
| `/admin/review` | Pseudonymous HITL inbox; preserve filter/task selection in the URL. |
| `/student/exams` | Published exams only. |
| `/student/exams/:examId` | Published snapshot and answer evidence. |

A multi-role user explicitly switches portals. Do not silently redirect an admin into a teacher view containing PII. Route guards improve UX; **FastAPI must enforce every authorization rule independently**.

## 5. Contracts that must be settled before integration

| Capability | Required guarantee |
|---|---|
| Authorization | School isolation, explicit teacher roster membership, student ownership, and separately scoped review privileges on every request. |
| Upload preparation | Server-owned upload session; authorized resumable URL; documented size/page limits and expiration; duplicate handling scoped to principal, roster, and exam. |
| Upload completion | Server validates bytes/checksum/PDF and commits durable processing exactly once. A completed byte transfer is not proof that Temporal has started. |
| Status | Authoritative state, revision, timestamps, and actionable processing/upload failures. Unknown wire states fail visibly rather than being coerced to success. |
| Review queue | Only eligible redacted crops, opaque identifiers, task kind, revision, and allowed resolutions. No names or full-page originals, including in hidden JSON fields. |
| Review resolution | Expected revision, validated decision type, audit attribution, idempotency key, and machine-readable conflict semantics. |
| Teacher override | Draft-only revision-checked mutation with reason; preserve the original AI result. Invalidates any derived grade/summary that needs recomputation. |
| Publication | Atomic expected-revision check; all required review/recomputation complete; immutable published snapshot; idempotent response to repeated clicks. |
| Evidence | Per-request authorization, immutable/versioned crop identifiers, correct redaction variant, private caching policy, and no public object URLs. |

**Duplicate upload policy:** retrying the same upload intent resumes it; intentionally submitting the same bytes again requires an explicit new attempt. A checksum alone must not prohibit legitimate retakes or cross-exam reuse.

**Publication scope still needs a contract:** one student submission versus a whole exam/roster. The UI must name the exact audience and affected count. Do not infer this from the route name.

## 6. State, authentication, and recovery

### Authentication
- Keycloak public client, Authorization Code + PKCE S256, exact redirect URIs, and no browser client secret.
- Keep tokens in memory, not `localStorage`, IndexedDB, or query persistence.
- Refresh through one shared in-flight promise before requests. If authentication cannot recover, pause uploads and require sign-in; do not report an unsaved mutation as successful.
- Bootstrap effective portal permissions from a verified claim mapping or server capability response. Never assume realm-role names or allow tenant switching through an unchecked query parameter.
- Query keys include the authenticated principal/tenant scope. On logout or tenant change: abort transfers/requests, clear the Query cache, unmount evidence, revoke blob URLs, and notify other tabs.
- Do not persist student responses, cropped images, review drafts, or tokens offline. Avoid service-worker caching of private routes and API responses.

### Workflow state

```text
Uploading -> Processing -> Requires Admin Review -> Graded (Draft) -> Published
                      \--------------------------> Graded (Draft)
```

Review/reprocessing may move back into `Processing`; accept authoritative server transitions. Do not assume every submission visits every state.

- Byte progress comes from Tus; processing progress comes from FastAPI.
- Rendering/alignment/extraction/diagnosis may appear as secondary details **only if the backend exposes them**. Never fabricate percentages.
- Network failure is a transport condition, not a new Temporal state. Display last-known status and freshness separately.
- Poll active submissions with backoff and jitter; pause background/offline polling and refetch on reconnect/focus. Stop routine polling at draft/published and invalidate after mutations.
- Distinguish “nothing needs review” from “the queue could not be loaded.” Never turn a failed request into an empty array.
- Unknown submission/review states block actions and show a recoverable compatibility error.

### Resumption
A closed browser cannot continue reading an ordinary selected file. On return, recover upload sessions from the server and ask the teacher to reselect the original file when necessary. Verify its checksum before resuming; Tus `HEAD` determines the offset. Do not promise unattended cross-browser continuation.

The upload reference below supports multiple PDFs sequentially to bound memory/network load. Concurrent transfers can be introduced after size and load testing. A PDF may contain 100+ pages; page limits and document validation remain server-enforced.

### Mutations
- **No optimistic approval, grade override, or publication.** Show an in-flight state and wait for acknowledgement.
- Reuse an idempotency key for retries of the same resolution intent. Generate a new key when its payload changes.
- A review `409` removes the stale local task and refreshes the queue. Say “changed or resolved,” not “another admin approved it.” A still-editable task may reappear with its new revision.
- Do not apply this behavior to Tus offset conflicts: those are transfer-protocol recovery events, not review conflicts.
- Published results are read-only in v1. A later correction flow requires explicit versioning, notification, and audit policy; it must not silently rewrite the original publication.

## 7. Foundational code

### 7.1 Dependency spine — `package.json`

These are major-version baselines, not a claim that they are the latest patch releases. Resolve compatible versions, audit them, and commit the lockfile before deployment. CI uses `npm ci`.

```json
{
  "name": "cde-web",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "engines": { "node": ">=22.12.0" },
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:e2e": "playwright test",
    "typecheck": "tsc -b --pretty false"
  },
  "dependencies": {
    "@tanstack/react-query": "^5.0.0",
    "keycloak-js": "^26.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.0.0",
    "tus-js-client": "^4.0.0",
    "zod": "^4.0.0"
  },
  "devDependencies": {
    "@playwright/test": "^1.51.0",
    "@tailwindcss/vite": "^4.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/user-event": "^14.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^5.0.0",
    "jsdom": "^26.0.0",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.0.0",
    "vite": "^7.0.0",
    "vitest": "^3.0.0"
  }
}
```

No Gemini SDK, Temporal SDK, database client, or private infrastructure credentials belong in this package.

### 7.2 Explicit API boundary — `api/contracts.ts`

The adapter must validate wire responses, normalize verified state/role enums, attach authentication, and raise `ApiError`. Map methods to actual endpoints only after the contract gate passes.

```ts
export type Portal = 'teacher' | 'admin' | 'student';
export type WorkflowState =
  | 'Uploading'
  | 'Processing'
  | 'Requires Admin Review'
  | 'Graded (Draft)'
  | 'Published';

export class ApiError extends Error {
  constructor(public status: number, public code: string) {
    super(code);
    this.name = 'ApiError';
  }
}

export interface SubmissionStatus {
  id: string;
  state: WorkflowState;
  revision: string;
  updatedAt: string;
  issue?: { message: string; retryable: boolean };
}

export type UploadPreparation =
  | { kind: 'existing'; submissionId: string }
  | {
      kind: 'transfer';
      submissionId: string;
      uploadUrl: string;
    };

export interface ReviewTask {
  id: string;
  cropId: string;
  revision: string;
  kind: 'ambiguous' | 'abstained';
  choices: Array<{ code: string; label: string }>;
  suggestedCode?: string;
}

export interface ResolutionCommand {
  expectedRevision: string;
  decisionCode: string;
  reason: string;
  idempotencyKey: string;
}

export interface PublishedExam {
  id: string;
  state: 'Published';
  revision: string;
  title: string;
  publishedAt: string;
  score: number;
  maximum: number;
  answers: Array<{
    id: string;
    questionLabel: string;
    cropId: string;
    score: number;
    maximum: number;
    classLabel: string;
    explanation: string;
    nextStep: string;
    reviewed: boolean;
  }>;
}

export interface CdeApi {
  accessToken(): Promise<string>;
  prepareUpload(
    examId: string,
    file: { sha256: string; bytes: number },
    signal: AbortSignal
  ): Promise<UploadPreparation>;
  completeUpload(
    submissionId: string,
    sha256: string,
    signal: AbortSignal
  ): Promise<void>;
  submissionStatus(id: string, signal: AbortSignal): Promise<SubmissionStatus>;
  reviewQueue(signal: AbortSignal): Promise<ReviewTask[]>;
  resolveTask(id: string, command: ResolutionCommand): Promise<void>;
  studentExam(id: string, signal: AbortSignal): Promise<PublishedExam>;
  cropBlob(
    audience: Portal,
    cropId: string,
    signal: AbortSignal
  ): Promise<Blob>;
}

export interface Runtime {
  api: CdeApi;
  scope: string; // opaque authenticated principal/tenant cache namespace
  portals: Portal[];
  signOut(): Promise<void>;
}

export function retryRead(count: number, error: unknown): boolean {
  if (count >= 2) return false;
  return !(error instanceof ApiError && error.status >= 400 && error.status < 500);
}
```

Additional adapter obligations:
- `existing` means an acknowledged existing submission, not “file probably uploaded.”
- `completeUpload` must be idempotent for that submission/checksum, including after a lost response.
- Validate image MIME type and byte limits; reject SVG/HTML evidence. Return only the permitted redacted/original variant.
- Honor server retry timing/rate limits in transport configuration; do not automatically retry writes without their idempotency contract.
- Error messages sent to the UI must be safe summaries, not stack traces, student records, tokens, or model prompts.

### 7.3 Providers and navigation shell

```tsx
// app/providers.tsx
import { createContext, useContext, useState, type ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { Runtime } from '../api/contracts';
import { retryRead } from '../api/contracts';

const RuntimeContext = createContext<Runtime | null>(null);

export function useRuntime(): Runtime {
  const value = useContext(RuntimeContext);
  if (!value) throw new Error('Runtime provider missing');
  return value;
}

export function Providers({ runtime, children }: {
  runtime: Runtime;
  children: ReactNode;
}) {
  const [client] = useState(() => new QueryClient({
    defaultOptions: {
      queries: { staleTime: 5000, retry: retryRead },
      mutations: { retry: false }
    }
  }));

  return (
    <RuntimeContext.Provider value={runtime}>
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    </RuntimeContext.Provider>
  );
}
```

Mount `Providers` with `key={runtime.scope}` after authenticated bootstrap. Logout/tenant-switch orchestration must cancel and clear the old client before removing that authenticated tree; a React key alone does not cancel every side effect.

```tsx
// app/Shell.tsx
import { NavLink, Outlet } from 'react-router-dom';
import { useRuntime } from './providers';
import type { Portal } from '../api/contracts';

const entries: Array<{ role: Portal; to: string; label: string }> = [
  { role: 'teacher', to: '/teacher/exams', label: 'Teaching' },
  { role: 'admin', to: '/admin/review', label: 'Review queue' },
  { role: 'student', to: '/student/exams', label: 'My exams' }
];

export function RequirePortal({ role }: { role: Portal }) {
  const { portals } = useRuntime();
  if (!portals.includes(role)) {
    return <section role="alert"><h1>Access unavailable</h1>
      <p>Your current account cannot open this portal.</p></section>;
  }
  return <Outlet />;
}

export function Shell() {
  const { portals, signOut } = useRuntime();
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <a href="#main" className="skip-link">Skip to content</a>
      <header className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-6">
          <span className="font-semibold tracking-tight">Cognitive Diagnostic Engine</span>
          <nav aria-label="Portals" className="flex flex-wrap gap-4">
            {entries.filter(x => portals.includes(x.role)).map(x => (
              <NavLink key={x.role} to={x.to}
                className={({ isActive }) => isActive
                  ? 'font-semibold text-indigo-800 underline underline-offset-8'
                  : 'text-slate-600'}>
                {x.label}
              </NavLink>
            ))}
          </nav>
          <button className="ml-auto" onClick={() => void signOut()}>Sign out</button>
        </div>
      </header>
      <main id="main" tabIndex={-1} className="mx-auto max-w-7xl p-4 md:p-8">
        <Outlet />
      </main>
    </div>
  );
}
```

```css
/* app/styles.css */
@import "tailwindcss";

:root {
  font-family: Inter, ui-sans-serif, system-ui, sans-serif;
  color-scheme: light;
  font-variant-numeric: tabular-nums;
}
button, input, select, textarea { font: inherit; }
button, select, input[type="file"] { min-height: 44px; }
button { cursor: pointer; }
button:disabled { cursor: not-allowed; opacity: .55; }
:focus-visible { outline: 3px solid #4338ca; outline-offset: 3px; }
.skip-link { position: absolute; left: -10000px; }
.skip-link:focus { left: 1rem; top: 1rem; z-index: 100; background: white; padding: 1rem; }
.panel { background: white; border: 1px solid #cbd5e1; border-radius: 12px; padding: 1.5rem; }
.action { background: #3730a3; color: white; border-radius: 8px; padding: .6rem 1rem; }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; animation: none !important; }
}
```

Wire `Shell` beneath authenticated bootstrap and an error boundary; nest portal routes beneath their respective `RequirePortal`. Route changes should update the document title and move focus to the page heading.

### 7.4 Authorized evidence component

No bearer token in an image URL. Fetch through the authenticated adapter, display a temporary blob URL, and release it on unmount. Admin mutations remain disabled until the image actually loads.

```tsx
// shared/Evidence.tsx
import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRuntime } from '../app/providers';
import type { Portal } from '../api/contracts';

export function Evidence({ cropId, audience, onReady }: {
  cropId: string;
  audience: Portal;
  onReady?: (ready: boolean) => void;
}) {
  const { api, scope } = useRuntime();
  const [src, setSrc] = useState('');
  const [broken, setBroken] = useState(false);
  const query = useQuery({
    queryKey: [scope, 'evidence', audience, cropId],
    queryFn: ({ signal }) => api.cropBlob(audience, cropId, signal),
    gcTime: 0,
    staleTime: Infinity
  });

  useEffect(() => {
    onReady?.(false);
    if (!query.data) return;
    const url = URL.createObjectURL(query.data);
    setSrc(url);
    setBroken(false);
    return () => {
      URL.revokeObjectURL(url);
      onReady?.(false);
    };
  }, [query.data, onReady]);

  if (query.isError || broken) return (
    <div role="alert">
      <p>Evidence is unavailable. Do not resolve this answer without it.</p>
      <button onClick={() => void query.refetch()}>Reload evidence</button>
    </div>
  );
  if (!src) return <div role="status" className="h-56 animate-pulse bg-slate-100">Loading evidence…</div>;

  return <img src={src} alt="Scanned handwritten answer"
    className="max-h-[65vh] w-full rounded-lg border border-slate-200 object-contain"
    referrerPolicy="no-referrer"
    onLoad={() => onReady?.(true)}
    onError={() => { setBroken(true); onReady?.(false); }} />;
}
```

Mount this component with an audience/crop key so a changed task never inherits the previous crop's readiness. Add accessible zoom/pan controls during UI completion. Never generate unverified alt-text transcription for unreadable handwriting.

### 7.5 Teacher Upload Bay

This reference uses server-created, same-origin Tus resources and **does not persist file blobs or upload URLs in local storage**. A different-origin upload service requires a separately reviewed token/audience strategy; do not forward Keycloak tokens to arbitrary URLs.

```tsx
// features/teacher/TeacherUploadBay.tsx
import { useEffect, useRef, useState } from 'react';
import { Upload } from 'tus-js-client';
import { useRuntime } from '../../app/providers';
import { SubmissionStatusView } from './SubmissionStatus';

async function checksum(file: File): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', await file.arrayBuffer());
  return Array.from(new Uint8Array(digest), n => n.toString(16).padStart(2, '0')).join('');
}

export function TeacherUploadBay({ examId, maxFileBytes }: {
  examId: string;
  maxFileBytes: number; // obtained from verified server configuration
}) {
  const { api } = useRuntime();
  const [files, setFiles] = useState<File[]>([]);
  const [ids, setIds] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [progress, setProgress] = useState<number | null>(null);
  const locked = useRef(false);
  const controller = useRef<AbortController | null>(null);
  const live = useRef(true);

  useEffect(() => {
    live.current = true;
    return () => { live.current = false; controller.current?.abort(); };
  }, []);

  function selectFiles(selected: File[]) {
    if (locked.current) return;
    if (selected.some(f => !f.name.toLowerCase().endsWith('.pdf') ||
        f.size === 0 || f.size > maxFileBytes)) {
      setMessage('Choose non-empty PDFs within the allowed file-size limit.');
      return;
    }
    setFiles(selected);
    setMessage(`${selected.length} PDF(s) selected. Files transfer sequentially.`);
    setProgress(null);
  }

  async function run() {
    if (locked.current || !files.length) return;
    locked.current = true;
    setBusy(true);
    const abort = new AbortController();
    controller.current = abort;
    const { signal } = abort;

    try {
      for (const file of files) {
        signal.throwIfAborted();
        setProgress(null);
        setMessage(`Checking ${file.name}…`);
        const sha256 = await checksum(file);
        signal.throwIfAborted();
        const session = await api.prepareUpload(examId, { sha256, bytes: file.size }, signal);
        signal.throwIfAborted();
        setIds(old => old.includes(session.submissionId) ? old : [...old, session.submissionId]);
        if (session.kind === 'existing') continue;

        const url = new URL(session.uploadUrl, window.location.origin);
        if (url.origin !== window.location.origin) {
          throw new Error('Unapproved upload origin');
        }
        setMessage(`Uploading ${file.name}…`);

        await new Promise<void>((resolve, reject) => {
          const upload = new Upload(file, {
            uploadUrl: url.href,
            chunkSize: 5 * 1024 * 1024,
            storeFingerprintForResuming: false,
            retryDelays: [0, 1000, 3000, 5000, 10000],
            onBeforeRequest: async request => {
              signal.throwIfAborted();
              const token = await api.accessToken();
              signal.throwIfAborted();
              request.setHeader('Authorization', `Bearer ${token}`);
            },
            onShouldRetry: error => {
              const status = error.originalResponse?.getStatus() ?? 0;
              return !signal.aborted && (status === 0 || status === 408 ||
                status === 409 || status === 423 || status === 429 || status >= 500);
            },
            onProgress: (sent, total) => {
              if (!signal.aborted && live.current) setProgress(total ? sent / total : 0);
            },
            onError: error => { cleanup(); reject(error); },
            onSuccess: () => { cleanup(); resolve(); }
          });
          const stop = () => {
            cleanup();
            void upload.abort(false).catch(() => undefined);
            reject(new DOMException('Paused', 'AbortError'));
          };
          const cleanup = () => signal.removeEventListener('abort', stop);
          signal.addEventListener('abort', stop, { once: true });
          if (signal.aborted) stop();
          else upload.start();
        });

        signal.throwIfAborted();
        setMessage('Transfer complete. Confirming processing…');
        await api.completeUpload(session.submissionId, sha256, signal);
      }
      if (live.current) setMessage('Uploads acknowledged. Processing continues on the server.');
    } catch {
      if (live.current) setMessage(abort.signal.aborted
        ? 'Paused. Retry to resume the same upload sessions.'
        : 'Upload or completion could not be confirmed. Retry to reconcile and resume; do not create a new attempt.');
    } finally {
      locked.current = false;
      if (live.current) setBusy(false);
    }
  }

  return (
    <section className="space-y-4" aria-labelledby="upload-title">
      <h1 id="upload-title" className="text-2xl font-semibold">Upload exam scans</h1>
      <div className="panel border-dashed"
        onDragOver={event => event.preventDefault()}
        onDrop={event => {
          event.preventDefault();
          selectFiles(Array.from(event.dataTransfer.files));
        }}>
        <label htmlFor="pdfs" className="block font-medium">Drop PDFs here or choose files</label>
        <p className="my-2 text-sm text-slate-600">
          After closing this browser, you may need to reselect the original PDFs to resume.
        </p>
        <input id="pdfs" type="file" accept="application/pdf,.pdf" multiple disabled={busy}
          onChange={event => selectFiles(Array.from(event.target.files ?? []))} />
      </div>
      <div className="flex gap-3">
        <button className="action" disabled={busy || !files.length} onClick={() => void run()}>
          Upload / resume selected PDFs
        </button>
        {busy && <button onClick={() => controller.current?.abort()}>Pause transfer</button>}
      </div>
      <p role="status">{message}</p>
      {progress !== null && <progress aria-label="Current PDF byte transfer" max={1} value={progress} />}
      <div className="space-y-3">
        {ids.map(id => <SubmissionStatusView key={id} id={id} />)}
      </div>
    </section>
  );
}
```

For substantially larger permitted files, replace whole-file hashing with a tested worker-based streaming hasher to bound memory. Server-side checksum/PDF verification remains mandatory regardless of the client hash. Mount the upload bay with `key={examId}`; recover previously created submissions from the teacher list after reload.

```tsx
// features/teacher/SubmissionStatus.tsx
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { ApiError } from '../../api/contracts';
import { useRuntime } from '../../app/providers';

export function SubmissionStatusView({ id }: { id: string }) {
  const { api, scope } = useRuntime();
  const query = useQuery({
    queryKey: [scope, 'submission', id],
    queryFn: ({ signal }) => api.submissionStatus(id, signal),
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
    refetchInterval: q => {
      const error = q.state.error;
      if (error instanceof ApiError && [401, 403, 404].includes(error.status)) return false;
      const state = q.state.data?.state;
      if (state === 'Graded (Draft)' || state === 'Published') return false;
      const delay = Math.min(30000, 3000 * 2 ** Math.min(q.state.fetchFailureCount, 3));
      return delay + Math.floor(Math.random() * 1000);
    }
  });

  return <article className="panel">
    <Link to={`/teacher/submissions/${encodeURIComponent(id)}`}>Open submission</Link>
    <p role="status">{query.data?.state ?? 'Checking server status…'}</p>
    {query.data && <p className="text-sm text-slate-600">
      Server update: <time dateTime={query.data.updatedAt}>{new Date(query.data.updatedAt).toLocaleString()}</time>
    </p>}
    {query.data?.issue && <p role="alert">{query.data.issue.message}</p>}
    {query.isError && <div role="alert">
      Status could not be refreshed. Any displayed state may be out of date.
      <button onClick={() => void query.refetch()}>Retry status</button>
    </div>}
  </article>;
}
```

### 7.6 Admin HITL queue and resolution form

The facade returns a bounded oldest-first batch. Production inbox completion adds cursor pagination and filters; it must not fetch the entire backlog. The focused-task design avoids rendering dozens of sensitive images simultaneously.

```tsx
// features/admin/HitlQueue.tsx
import { useEffect, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ApiError, type ResolutionCommand, type ReviewTask } from '../../api/contracts';
import { useRuntime } from '../../app/providers';
import { Evidence } from '../../shared/Evidence';

export function HitlQueue() {
  const { api, scope } = useRuntime();
  const client = useQueryClient();
  const key = [scope, 'review-queue'] as const;
  const [notice, setNotice] = useState('');
  const query = useQuery({
    queryKey: key,
    queryFn: ({ signal }) => api.reviewQueue(signal),
    refetchOnWindowFocus: true,
    refetchInterval: q => q.state.error ? false : 15000,
    refetchIntervalInBackground: false
  });

  async function reconcile(taskId: string, message: string) {
    await client.cancelQueries({ queryKey: key });
    client.setQueryData<ReviewTask[]>(key, old => old?.filter(t => t.id !== taskId));
    setNotice(message);
    await client.invalidateQueries({ queryKey: key });
  }

  const task = query.data?.[0];
  return <section className="space-y-4">
    <h1 className="text-2xl font-semibold">Review queue</h1>
    <p className="text-sm text-slate-600">Only isolated, approved-for-review evidence appears here.</p>
    <p role="status" aria-live="polite">{notice}</p>
    {query.isPending && <p role="status">Loading review tasks…</p>}
    {query.isError && <div role="alert">
      The queue could not be refreshed. Resolution is paused until it reconnects.
      <button onClick={() => void query.refetch()}>Reconnect</button>
    </div>}
    {!query.isPending && !query.isError && !task && <p>No tasks currently require your review.</p>}
    {task && <ResolutionForm key={`${task.id}:${task.revision}`} task={task}
      blocked={query.isError}
      onRemoved={message => reconcile(task.id, message)} />}
  </section>;
}

function ResolutionForm({ task, blocked, onRemoved }: {
  task: ReviewTask;
  blocked: boolean;
  onRemoved: (message: string) => Promise<void>;
}) {
  const { api } = useRuntime();
  const [ready, setReady] = useState(false);
  const [choice, setChoice] = useState('');
  const [reason, setReason] = useState('');
  const [error, setError] = useState('');
  const heading = useRef<HTMLHeadingElement>(null);
  const locked = useRef(false);
  const last = useRef<{ payload: string; key: string } | null>(null);
  const mutation = useMutation({
    mutationFn: (command: ResolutionCommand) => api.resolveTask(task.id, command),
    retry: false
  });
  useEffect(() => { heading.current?.focus(); }, []);

  const changesSuggestion = choice !== task.suggestedCode;
  const valid = task.choices.some(option => option.code === choice) &&
    (!changesSuggestion || Boolean(reason.trim()));

  async function submit() {
    if (locked.current || blocked || !ready || !valid) return;
    locked.current = true;
    setError('');
    const payload = JSON.stringify([task.id, task.revision, choice, reason.trim()]);
    if (last.current?.payload !== payload) last.current = { payload, key: crypto.randomUUID() };
    try {
      await mutation.mutateAsync({
        expectedRevision: task.revision,
        decisionCode: choice,
        reason: reason.trim(),
        idempotencyKey: last.current.key
      });
      await onRemoved('Resolution saved. Next task loaded.');
    } catch (failure) {
      if (failure instanceof ApiError && failure.status === 409) {
        await onRemoved('This task changed or was resolved. Its stale version was removed and the queue refreshed.');
      } else {
        setError('Resolution was not confirmed. Your selection is preserved; reconnect and retry the same decision.');
      }
    } finally {
      locked.current = false;
    }
  }

  return <article className="panel grid gap-6 lg:grid-cols-2">
    <div>
      <h2 ref={heading} tabIndex={-1} className="mb-3 font-semibold">Crop {task.cropId}</h2>
      <Evidence key={`admin:${task.cropId}`} cropId={task.cropId} audience="admin" onReady={setReady} />
    </div>
    <form className="space-y-4" onSubmit={event => { event.preventDefault(); void submit(); }}>
      <p className="font-medium">{task.kind === 'ambiguous' ? 'Ambiguous bubble reading' : 'Diagnosis requires human review'}</p>
      <p className="text-sm text-slate-600">Inspect the evidence before choosing a resolution. No option is selected automatically.</p>
      <fieldset disabled={mutation.isPending || blocked} className="space-y-2">
        <legend className="mb-2 font-medium">Resolution</legend>
        {task.choices.map(option => <label key={option.code} className="flex min-h-11 items-center gap-3">
          <input type="radio" name={`resolution-${task.id}`} value={option.code}
            checked={choice === option.code} onChange={() => setChoice(option.code)} />
          <span>{option.label}{option.code === task.suggestedCode ? ' — suggested reading' : ''}</span>
        </label>)}
      </fieldset>
      <label className="block">
        <span className="block font-medium">Reason {changesSuggestion ? '(required)' : '(optional)'}</span>
        <textarea value={reason} rows={3} disabled={mutation.isPending || blocked}
          onChange={event => setReason(event.target.value)}
          className="mt-2 w-full rounded-lg border border-slate-300 p-3" />
      </label>
      <p className="text-sm text-slate-600">Do not enter names or other identifying information.</p>
      {error && <p role="alert">{error}</p>}
      <button className="action" type="submit"
        disabled={!ready || !valid || blocked || mutation.isPending}>
        {mutation.isPending ? 'Saving resolution…' : 'Save resolution and continue'}
      </button>
    </form>
  </article>;
}
```

Important integration rules:
- `ambiguous` choices must represent valid bubble outcomes; `abstained` choices must represent the permitted diagnostic taxonomy. The server validates kind-specific decisions.
- Provide a legitimate unreadable/escalation path. Never force an administrator to invent a diagnosis merely to empty the queue.
- Keyboard-first completion uses native tab/radio/submit behavior initially. Add documented shortcuts only with input-focus guards and accessibility tests; avoid single-key accidental approvals.
- A conflict refresh must not reapply an old draft automatically to a new revision. This implementation remounts the form when the revision changes.

### 7.7 Student diagnostic viewer

The student endpoint must return only published snapshots. A frontend visibility check cannot protect a draft already delivered over the network.

```tsx
// features/student/StudentDiagnosticView.tsx
import { useQuery } from '@tanstack/react-query';
import { ApiError } from '../../api/contracts';
import { useRuntime } from '../../app/providers';
import { Evidence } from '../../shared/Evidence';

export function StudentDiagnosticView({ examId }: { examId: string }) {
  const { api, scope } = useRuntime();
  const query = useQuery({
    queryKey: [scope, 'published-exam', examId],
    queryFn: ({ signal }) => api.studentExam(examId, signal)
  });

  if (query.isPending) return <section role="status" aria-busy="true">Loading your feedback…</section>;
  if (query.isError) {
    const unavailable = query.error instanceof ApiError &&
      [403, 404].includes(query.error.status);
    return <section role="alert">
      <h1 className="text-2xl font-semibold">{unavailable ? 'This feedback is not available' : 'Feedback could not be loaded'}</h1>
      <p>{unavailable ? 'Return to your exam list or ask your teacher for help.' : 'Your results have not been changed.'}</p>
      {!unavailable && <button onClick={() => void query.refetch()}>Try again</button>}
    </section>;
  }

  const exam = query.data;
  if (exam.state !== 'Published') return <p role="alert">This feedback is not available.</p>;

  return <section className="space-y-6">
    <header className="panel">
      <p className="text-sm font-medium text-indigo-800">Feedback for this exam</p>
      <h1 className="mt-2 text-3xl font-semibold">{exam.title}</h1>
      <p className="mt-4 text-3xl font-semibold" aria-label={`Score ${exam.score} out of ${exam.maximum}`}>
        {exam.score} <span className="text-lg text-slate-500">/ {exam.maximum}</span>
      </p>
      <p className="mt-3 max-w-2xl text-slate-600">
        These observations describe your work on this exam—not your ability or potential.
        Use each next step to decide what to practise.
      </p>
      <p className="mt-2 text-sm text-slate-500">
        Published <time dateTime={exam.publishedAt}>{new Date(exam.publishedAt).toLocaleDateString()}</time>
      </p>
    </header>

    {exam.answers.map(answer => <article key={answer.id} className="panel">
      <header className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold">{answer.questionLabel}</h2>
        <span>{answer.score} / {answer.maximum}</span>
      </header>
      <div className="grid items-start gap-6 lg:grid-cols-2">
        <figure>
          <Evidence key={`student:${answer.cropId}`} cropId={answer.cropId} audience="student" />
          <figcaption className="mt-2 text-sm text-slate-500">Your handwritten work</figcaption>
        </figure>
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold">What to notice in this answer</h3>
            <p className="mt-2 inline-block rounded-md bg-indigo-50 px-3 py-1 text-indigo-900">{answer.classLabel}</p>
          </div>
          <p className="whitespace-pre-wrap leading-relaxed">{answer.explanation}</p>
          <section className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <h3 className="font-semibold">Try this next</h3>
            <p className="mt-2 whitespace-pre-wrap leading-relaxed">{answer.nextStep}</p>
          </section>
          {answer.reviewed && <p className="text-sm text-slate-600">This answer includes a human-reviewed correction.</p>}
        </div>
      </div>
    </article>)}
  </section>;
}
```

Feedback is rendered as text, not trusted HTML. Provide concise, student-facing explanations grounded in the crop—not internal model chain-of-thought, hidden prompts, or a claim that the model knows the student's internal reasoning. If mathematical typesetting is required, add a constrained renderer with unsafe HTML and trusted commands disabled.

## 8. Teacher draft and publication behavior

The remaining teacher review screen uses the same evidence component and mutation discipline:
- Fetch the current draft and revision; show unresolved/recomputing items explicitly.
- An override selects an allowed error class and records a reason. Retain original versus corrected values and reviewer attribution in the backend audit trail.
- Refetch after acknowledgement. Do not optimistically alter the score or enable publication while recomputation is pending.
- Publish opens an accessible confirmation dialog naming the exam, audience, and affected count.
- Submit the expected draft revision and an idempotency key. The backend atomically validates readiness and creates the publication snapshot.
- On a publication conflict, refresh and require the teacher to review the changed draft. Do not silently retry with a newer revision.
- Student query caches are invalidated/refetched through normal authorized reads; publication never pushes private teacher data directly into a student cache.

## 9. Release gates and unresolved decisions

### Must-pass tests
- A teacher changes a `roster_id`, submission ID, crop ID, or exam ID in a request and cannot cross authorization boundaries.
- An admin receives neither identity fields nor unsafe images in API responses, browser logs, telemetry, filenames, or object metadata.
- A student cannot retrieve unpublished grades or crops by guessing a URL.
- A 50MB+ PDF survives a network drop, a tab close/reselection, token expiry, and loss of the completion response without a duplicate workflow.
- Wrong-file resumption is rejected; expired upload sessions offer explicit recovery without deleting an existing submission.
- Two administrators resolve one revision: at most one effective decision; the other sees a reconciled conflict.
- A lost resolution acknowledgement can be retried safely; publication cannot race with an override or outstanding review.
- Missing/failed evidence disables admin resolution without blocking the student's access to otherwise available published feedback.
- Unknown states, backend errors, and offline mode never appear as successful completion or an empty queue.
- Keyboard-only and screen-reader journeys pass; screenshot/DOM/error telemetry does not collect student work. Large result sets use pagination or windowing rather than rendering every crop at once.

### Decisions still requiring confirmation or verified contracts
- Actual Tus deployment, upload lifetime, file/page limits, duplicate-intent semantics, and bandwidth/load targets.
- Whether publication is per submission or atomic across an exam/roster.
- Approved handling of unsafe/unreadable crops and genuinely unresolvable diagnoses.
- Exact role/tenant claim mapping, reviewer tenant scope, retention/deletion rules, and deployed CSP/CORS configuration.
- The authorized operational procedure for a necessary correction after publication.

**Release standard:** a smaller interface with correct permissions, recoverable uploads, honest uncertainty, and auditable publication is preferable to a visually impressive interface that invents backend guarantees.
