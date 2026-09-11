import os

os.makedirs("web/src/api", exist_ok=True)
with open("web/src/api/roughSheets.ts", "w", encoding="utf-8") as f:
    f.write("""declare const process: { env: { REACT_APP_BACKEND_URL: string } };
import type { CdeApi } from './client';

export const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

export interface RoughSubmission {
  submission_id: string;
  exam_id: string;
  state: string;
  rough_sheet_path: string | null;
  analysis_status: string;
  analysis_error: string | null;
}
export interface ClassInsight {
  question_number: number;
  error_type: string;
  count: number;
  sample_explanation: string;
}

export async function roughRequest<T>(api: CdeApi, path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set('Authorization', `Bearer mock_token`);
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'The request could not be completed. Please retry.');
  return data;
}

export const examPath = (examId: string) => `/api/exams/${encodeURIComponent(examId)}`;

export function uploadRoughSheet(api: CdeApi, file: File, examId: string, submissionId: string) {
  const body = new FormData();
  body.append('file', file);
  return roughRequest<{status: string; rough_sheet_path: string; analysis_status: string}>(
    api, `${examPath(examId)}/submissions/${encodeURIComponent(submissionId)}/rough-sheets`,
    { method: 'POST', body },
  );
}
""")

os.makedirs("web/src/features/teacher", exist_ok=True)
with open("web/src/features/teacher/TeacherDashboard.tsx", "w", encoding="utf-8") as f:
    f.write("""import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { ClassInsight, examPath, roughRequest } from '../../api/roughSheets';
// Using a mock API object for now
const mockApi: any = {};

export function TeacherDashboard({ examId }: { examId: string }) {
  const query = useQuery({
    queryKey: ['class-insights', examId],
    queryFn: ({ signal }) => roughRequest<{insights: ClassInsight[]}>(mockApi, `${examPath(examId)}/insights`, { signal }),
    refetchInterval: 10000,
  });
  const insights = query.data?.insights || [];
  return <section className="space-y-6" data-testid="teacher-insights-dashboard">
    <header className="flex flex-wrap items-start justify-between gap-4">
      <div><p className="text-sm text-indigo-800" data-testid="teacher-insights-exam-id">{examId}</p>
        <h1 className="mt-2 text-2xl font-semibold" data-testid="teacher-insights-title">Class insights</h1></div>
      <div className="flex flex-wrap items-center gap-4">
        <button className="action" data-testid="teacher-insights-refresh" disabled={query.isFetching} onClick={() => void query.refetch()}>{query.isFetching ? 'Refreshing...' : 'Refresh insights'}</button>
      </div>
    </header>
    {query.isPending && <p role="status" data-testid="teacher-insights-loading">Loading class insights...</p>}
    {query.isError && <p role="alert" className="text-red-800" data-testid="teacher-insights-error">Insights could not be refreshed. {query.error?.message}</p>}
    {!query.isPending && !query.isError && !insights.length && <div className="panel" data-testid="teacher-insights-empty">
      <h2 className="text-lg font-semibold">No diagnosed errors yet</h2>
      <p className="mt-2 text-slate-600">Class insights will appear when incorrect answers have completed diagnostics.</p>
    </div>}
    <div className="insights-panel space-y-4" data-testid="teacher-insights-list">
      {insights.map((insight: any, index: number) => <article key={`${insight.question_number}-${insight.error_type}`}
        className={`rounded-md border p-5 ${insight.count >= 2 ? 'border-red-200 bg-red-50' : 'border-slate-200 bg-white'}`}
        data-testid={`teacher-insight-${index}`}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold" data-testid={`teacher-insight-title-${index}`}>{insight.count >= 2 ? 'Action Required' : 'Review'}: Question {insight.question_number}</h2>
          <span className="text-sm font-medium text-red-800" data-testid={`teacher-insight-count-${index}`}>{insight.count} {insight.count === 1 ? 'student' : 'students'}</span>
        </div>
        <p className="mt-3" data-testid={`teacher-insight-error-type-${index}`}>{insight.count} {insight.count === 1 ? 'student made' : 'students made'} this error: <strong>{insight.error_type}</strong></p>
        <p className="mt-2 whitespace-pre-wrap break-words text-sm italic text-slate-600" data-testid={`teacher-insight-explanation-${index}`}>Example: {insight.sample_explanation || 'No explanation available.'}</p>
      </article>)}
    </div>
  </section>;
}
""")

os.makedirs("web/src/features/student", exist_ok=True)
with open("web/src/features/student/RoughSheetDropzone.tsx", "w", encoding="utf-8") as f:
    f.write("""import { useEffect, useRef, useState } from 'react';
import { RoughSubmission, uploadRoughSheet } from '../../api/roughSheets';
// mock Api
const mockApi: any = {};

const statusLabels: Record<string, string> = {
  not_uploaded: 'No rough sheet attached', queued: 'Rough sheet saved. Analysis queued.',
  uploading: 'Saving rough sheet...', processing: 'Analyzing your rough sheet...',
  awaiting_grading: 'Rough sheet saved. Waiting for OMR grading.',
  completed: 'Rough sheet analysis complete.', blocked: 'Rough sheet saved. Analysis unavailable.',
  failed: 'Rough sheet saved. Analysis could not be completed.',
};

export function RoughSheetDropzone({ examId, submission, onUploaded }: {
  examId: string; submission: RoughSubmission; onUploaded: () => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const input = useRef<HTMLInputElement>(null);
  const pending = busy || ['uploading', 'queued', 'processing'].includes(submission.analysis_status);
  useEffect(() => {
    if (!file) { setPreview(''); return; }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  function select(next?: File) {
    if (!next || pending) return;
    setError(''); setMessage(''); setFile(null);
    if (!['image/png', 'image/jpeg'].includes(next.type) || !next.size || next.size > 15 * 1024 * 1024) {
      setError('Choose a non-empty PNG or JPEG image, up to 15 MB.');
      if (input.current) input.current.value = '';
      return;
    }
    setFile(next);
  }

  async function upload() {
    if (!file || pending) return;
    setBusy(true); setError(''); setMessage('');
    try {
      await uploadRoughSheet(mockApi, file, examId, submission.submission_id);
      setMessage('Rough sheet saved.'); setFile(null);
      if (input.current) input.current.value = '';
      onUploaded();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Upload failed. Please retry.');
    } finally { setBusy(false); }
  }

  return <section className="space-y-4" data-testid="rough-sheet-panel">
    <h2 className="text-lg font-semibold" data-testid="rough-sheet-title">Rough work</h2>
    <p className="text-sm text-slate-600" role="status" data-testid="rough-sheet-analysis-status">
      {statusLabels[submission.analysis_status] || submission.analysis_status}
    </p>
    <div className="panel border-dashed p-4" data-testid="rough-sheet-dropzone"
      onDragOver={event => event.preventDefault()}
      onDrop={event => { event.preventDefault(); select(event.dataTransfer.files[0]); }}>
      <label htmlFor="rough-sheet-file" className="block font-medium" data-testid="rough-sheet-file-label">Attach your full rough sheet</label>
      <p className="my-2 text-sm text-slate-500" data-testid="rough-sheet-file-requirements">PNG or JPEG · Up to 15 MB</p>
      <input ref={input} id="rough-sheet-file" data-testid="rough-sheet-file-input" type="file"
        accept="image/png,image/jpeg" disabled={pending} onChange={event => select(event.target.files?.[0])} />
      {file && <p className="mt-3 break-words text-sm" data-testid="rough-sheet-selected-file">{file.name}</p>}
      {preview && <img className="rough-sheet-preview mt-4 max-w-sm" src={preview} alt="Full rough sheet selected for upload" data-testid="rough-sheet-preview" />}
    </div>
    <button className="bg-indigo-600 text-white px-4 py-2 rounded-md" data-testid="rough-sheet-upload-button" disabled={!file || pending} onClick={() => void upload()}>
      {busy ? 'Saving...' : submission.rough_sheet_path ? 'Replace rough sheet' : 'Upload rough sheet'}
    </button>
    {message && <p role="status" className="text-green-600" data-testid="rough-sheet-upload-success">{message}</p>}
    {(error || submission.analysis_error) && <p className="text-red-800" role="alert" data-testid="rough-sheet-error">{error || submission.analysis_error}</p>}
  </section>;
}
""")

with open("web/src/features/student/StudentExamView.tsx", "w", encoding="utf-8") as f:
    f.write("""import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { examPath, RoughSubmission, roughRequest } from '../../api/roughSheets';
import { RoughSheetDropzone } from './RoughSheetDropzone';
const mockApi: any = {};

export function StudentExamView({ examId }: { examId: string }) {
  const [params] = useSearchParams();
  const [selected, setSelected] = useState(params.get('submission') || '');
  const query = useQuery({
    queryKey: ['rough-submissions', examId],
    queryFn: ({ signal }) => roughRequest<{submissions: RoughSubmission[]}>(mockApi, `${examPath(examId)}/submissions`, { signal }),
    refetchInterval: 4000,
  });
  const submissions = query.data?.submissions || [];
  useEffect(() => { setSelected(params.get('submission') || ''); }, [examId, params]);
  const submission = submissions.find((item: any) => item.submission_id === selected) || submissions[0];
  return <section className="space-y-6" data-testid="student-exam-view">
    <header className="flex flex-wrap items-start justify-between gap-4">
      <div><p className="text-sm text-indigo-800" data-testid="student-exam-id">{examId}</p>
        <h1 className="mt-2 text-2xl font-semibold" data-testid="student-exam-title">My exam submission</h1></div>
    </header>
    {query.isPending && <p role="status" data-testid="student-submissions-loading">Loading submissions...</p>}
    {query.isError && <div role="alert" data-testid="student-submissions-error">
      <p>Submissions could not be loaded.</p><button className="action mt-3" data-testid="student-submissions-retry" onClick={() => void query.refetch()}>Try again</button>
    </div>}
    {!query.isPending && !query.isError && !submission && <div className="panel" data-testid="student-no-submissions">
      <h2 className="text-lg font-semibold">No accepted OMR submission yet</h2>
      <p className="mt-2 text-slate-600">Your rough sheet can be attached once an OMR submission is accepted.</p>
    </div>}
    {submission && <>
      <div className="space-y-2">
        <label htmlFor="submission-select" className="block text-sm font-medium" data-testid="student-submission-label">Accepted submission</label>
        <select id="submission-select" className="max-w-full rounded-md border bg-white p-2 text-sm" data-testid="student-submission-select"
          value={submission.submission_id} onChange={event => setSelected(event.target.value)}>
          {submissions.map((item: any) => <option key={item.submission_id} value={item.submission_id} data-testid={`student-submission-option-${item.submission_id}`}>{item.submission_id}</option>)}
        </select>
        <p className="text-sm text-slate-600" data-testid="student-omr-status">OMR status: {submission.state}</p>
      </div>
      <RoughSheetDropzone key={submission.submission_id} examId={examId} submission={submission} onUploaded={() => void query.refetch()} />
    </>}
  </section>;
}
""")
print("Frontend components created.")
