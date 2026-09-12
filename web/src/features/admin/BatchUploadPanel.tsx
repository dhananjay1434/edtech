// features/admin/BatchUploadPanel.tsx
//
// Drop the scanned PDF, then a live progress view: per-sheet status, counts
// of pending/rejected/graded, and "45 pages received, 45 accounted for."
import { useRef, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { listExams, uploadBatch, batchStatus, AdminApiError } from '../../api/admin';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Alert, AlertTitle, AlertDescription } from '../../components/ui/alert';
import { Skeleton } from '../../components/ui/skeleton';
import { Button } from '../../components/ui/button';

const STATE_LABEL: Record<string, string> = {
  pending_read: 'Reading bubbles',
  pending_identity: 'Awaiting identity',
  identified: 'Identified',
  rejected_layout: 'Rejected (wrong layout)',
  published: 'Graded',
};

function stateBadgeVariant(state: string): 'default' | 'destructive' | 'secondary' {
  if (state === 'rejected_layout') return 'destructive';
  if (state === 'published') return 'default';
  return 'secondary';
}

export function BatchUploadPanel() {
  const exams = useQuery({ queryKey: ['admin', 'exams'], queryFn: () => listExams() });
  const [examId, setExamId] = useState('');
  const [expected, setExpected] = useState<number | ''>('');
  const [file, setFile] = useState<File | null>(null);
  const [batchId, setBatchId] = useState('');
  const input = useRef<HTMLInputElement>(null);

  const upload = useMutation({
    mutationFn: () => uploadBatch(examId, file as File, expected === '' ? undefined : expected),
    onSuccess: r => setBatchId(r.batch_id),
  });

  const status = useQuery({
    queryKey: ['admin', 'batch-status', examId, batchId],
    queryFn: () => batchStatus(examId, batchId),
    enabled: Boolean(examId && batchId),
    refetchInterval: q => {
      const counts = q.state.data?.counts_by_state ?? {};
      const total = q.state.data?.page_count ?? 0;
      const settled = Object.entries(counts)
        .filter(([state]) => state !== 'pending_read')
        .reduce((sum, [, n]) => sum + n, 0);
      return settled >= total ? false : 3000;
    },
  });

  return (
    <div className="space-y-4">
      <Card data-testid="batch-upload-panel">
        <CardHeader>
          <CardTitle>Upload scanned answer sheets</CardTitle>
          <CardDescription>One PDF with every student&apos;s sheet, one page per sheet.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="batch-exam">Exam</Label>
              {exams.isPending && <Skeleton className="h-9 w-full" />}
              {exams.isSuccess && (
                <select id="batch-exam" data-testid="batch-exam-select"
                  className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
                  value={examId} onChange={e => { setExamId(e.target.value); setBatchId(''); }}>
                  <option value="">Select an exam…</option>
                  {exams.data.exams.map(e => (
                    <option key={e.id} value={e.id}>{e.name} ({e.question_count}q)</option>
                  ))}
                </select>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="expected-count">Expected sheet count (optional)</Label>
              <Input id="expected-count" type="number" min={1}
                value={expected} onChange={e => setExpected(e.target.value ? Number(e.target.value) : '')}
                placeholder="e.g. 45" data-testid="expected-count-input" />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="batch-file">Scanned PDF</Label>
            <input ref={input} id="batch-file" type="file" accept="application/pdf"
              data-testid="batch-file-input"
              onChange={e => setFile(e.target.files?.[0] ?? null)} />
          </div>

          {upload.isError && (
            <Alert variant="destructive">
              <AlertTitle>Upload failed</AlertTitle>
              <AlertDescription>
                {upload.error instanceof AdminApiError ? upload.error.detail : 'Please try again.'}
              </AlertDescription>
            </Alert>
          )}

          <Button data-testid="batch-upload-button"
            disabled={!examId || !file || upload.isPending}
            onClick={() => void upload.mutateAsync()}>
            {upload.isPending ? 'Uploading…' : 'Upload batch'}
          </Button>
        </CardContent>
      </Card>

      {batchId && status.isSuccess && (
        <Card data-testid="batch-progress-panel">
          <CardHeader>
            <CardTitle>Batch progress</CardTitle>
            <CardDescription data-testid="batch-accounted-line">
              {status.data.page_count} pages received
              {status.data.expected_sheet_count != null && (
                status.data.count_matches_expected
                  ? `, all ${status.data.expected_sheet_count} accounted for`
                  : `, but ${status.data.expected_sheet_count} were expected — check the scan`
              )}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2" data-testid="batch-state-counts">
              {Object.entries(status.data.counts_by_state).map(([state, count]) => (
                <Badge key={state} variant={stateBadgeVariant(state)}>
                  {STATE_LABEL[state] ?? state}: {count}
                </Badge>
              ))}
            </div>
            <ul className="grid grid-cols-2 gap-2 sm:grid-cols-4 md:grid-cols-6" data-testid="batch-sheet-list">
              {status.data.sheets.map(s => (
                <li key={s.sheet_id} className="rounded-md border border-border p-2 text-center text-xs"
                  data-testid={`batch-sheet-${s.page_number}`}>
                  <div className="font-medium">#{s.page_number}</div>
                  <Badge variant={stateBadgeVariant(s.state)} className="mt-1">
                    {STATE_LABEL[s.state] ?? s.state}
                  </Badge>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
