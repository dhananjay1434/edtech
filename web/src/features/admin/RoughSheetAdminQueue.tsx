import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { roughRequest } from '../../api/roughSheets';

interface DiagnosticsQueueItem {
  id: string;
  exam_id: string;
  student_id: string;
  rough_sheet_path: string | null;
  download_url: string | null;
  rough_sheet_analysis_status: string;
  rough_sheet_analysis_error: string | null;
  answers: Array<{
    question_number: number;
    diagnostic_error?: string;
    diagnostic?: { error_class: string; summary: string; status: string };
  }>;
}

const ERROR_TYPES = [
  'Calculation Slip',
  'Procedural Flaw',
  'Reading Comprehension Error',
  'Conceptual Deficit',
] as const;

const mockApi: any = {};

export function RoughSheetAdminQueue({ examId }: { examId?: string }) {
  const client = useQueryClient();
  const queryKey = ['diagnostics-queue', examId];

  const query = useQuery({
    queryKey,
    queryFn: ({ signal }) =>
      roughRequest<{ queue: DiagnosticsQueueItem[]; total: number }>(
        mockApi,
        `/api/admin/diagnostics-queue${examId ? `?exam_id=${examId}` : ''}`,
        { signal }
      ),
    refetchInterval: 15000,
  });

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">Rough Sheet Diagnostics Queue</h1>
      <p className="text-sm text-slate-600">
        Submissions where AI diagnostics failed or partially succeeded.
      </p>
      {query.isPending && <p role="status">Loading queue...</p>}
      {query.isError && <p role="alert" className="text-red-800">Queue failed to load.</p>}
      {query.data?.queue.map(item => (
        <QueueItem
          key={item.id}
          item={item}
          onAction={() => client.invalidateQueries({ queryKey })}
        />
      ))}
      {query.data?.queue.length === 0 && (
        <p className="text-slate-500">No failed diagnostics. All caught up.</p>
      )}
    </section>
  );
}

function QueueItem({ item, onAction }: { item: DiagnosticsQueueItem; onAction: () => void }) {
  const retryMutation = useMutation({
    mutationFn: () =>
      roughRequest(mockApi, `/api/submissions/${item.id}/rough-sheets/retry`, { method: 'POST' }),
    onSuccess: onAction,
  });

  return (
    <article className="rounded-lg border border-amber-200 bg-amber-50 p-5 space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-mono text-sm text-slate-500">{item.id}</p>
          <p className="text-sm">
            Status: <span className="font-medium">{item.rough_sheet_analysis_status}</span>
          </p>
          {item.rough_sheet_analysis_error && (
            <p className="text-sm text-red-700 mt-1">{item.rough_sheet_analysis_error}</p>
          )}
        </div>
        <button
          className="rounded bg-indigo-600 px-3 py-1.5 text-sm text-white disabled:opacity-50"
          disabled={retryMutation.isPending}
          onClick={() => retryMutation.mutate()}
        >
          {retryMutation.isPending ? 'Retrying...' : 'Retry AI'}
        </button>
      </div>
      {item.download_url && (
        <img
          src={item.download_url}
          alt="Student rough sheet"
          className="max-h-64 rounded border border-slate-200 object-contain"
        />
      )}
      <div className="space-y-3">
        {item.answers.map(answer => (
          <OverrideForm
            key={answer.question_number}
            submissionId={item.id}
            answer={answer}
            onSaved={onAction}
          />
        ))}
      </div>
    </article>
  );
}

function OverrideForm({
  submissionId, answer, onSaved,
}: {
  submissionId: string;
  answer: DiagnosticsQueueItem['answers'][number];
  onSaved: () => void;
}) {
  const [errorType, setErrorType] = useState<string>(ERROR_TYPES[0]);
  const [explanation, setExplanation] = useState('');
  const [saved, setSaved] = useState(false);

  const mutation = useMutation({
    mutationFn: () =>
      roughRequest(mockApi, `/api/submissions/${submissionId}/rough-sheets/override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question_number: answer.question_number,
          error_type: errorType,
          explanation,
        }),
      }),
    onSuccess: () => { setSaved(true); onSaved(); },
  });

  if (saved) {
    return <p className="text-sm text-green-700">Q{answer.question_number}: Override saved.</p>;
  }

  if (answer.diagnostic?.status === 'classified') {
    return (
      <p className="text-sm text-slate-500">
        Q{answer.question_number}: Already classified as{' '}
        <span className="font-medium">{answer.diagnostic.error_class}</span>.
      </p>
    );
  }

  return (
    <div className="rounded border border-slate-200 bg-white p-4 space-y-3">
      <p className="font-medium text-sm">Question {answer.question_number}</p>
      {answer.diagnostic_error && (
        <p className="text-xs text-red-600">AI error: {answer.diagnostic_error}</p>
      )}
      <label className="block text-sm">
        Error type
        <select
          className="mt-1 block w-full rounded border border-slate-300 p-2 text-sm"
          value={errorType}
          onChange={e => setErrorType(e.target.value)}
        >
          {ERROR_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </label>
      <label className="block text-sm">
        Explanation
        <textarea
          className="mt-1 block w-full rounded border border-slate-300 p-2 text-sm"
          rows={3}
          value={explanation}
          onChange={e => setExplanation(e.target.value)}
          placeholder="Describe what the student did wrong..."
        />
      </label>
      <button
        className="rounded bg-indigo-600 px-3 py-1.5 text-sm text-white disabled:opacity-50"
        disabled={!explanation.trim() || mutation.isPending}
        onClick={() => mutation.mutate()}
      >
        {mutation.isPending ? 'Saving...' : 'Save override'}
      </button>
      {mutation.isError && <p className="text-sm text-red-700">Save failed. Try again.</p>}
    </div>
  );
}
