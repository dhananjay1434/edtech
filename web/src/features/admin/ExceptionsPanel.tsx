// features/admin/ExceptionsPanel.tsx
//
// Rejected layouts, stray marks in unused rows, and failed jobs — the
// things the system refused to guess at and needs a human to look at.
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { listExams, listExceptions } from '../../api/admin';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Skeleton } from '../../components/ui/skeleton';

export function ExceptionsPanel() {
  const exams = useQuery({ queryKey: ['admin', 'exams'], queryFn: () => listExams() });
  const [examId, setExamId] = useState('');

  const exceptions = useQuery({
    queryKey: ['admin', 'exceptions', examId],
    queryFn: () => listExceptions(examId),
    enabled: Boolean(examId),
  });

  const total = exceptions.data
    ? exceptions.data.rejected_layout.length + exceptions.data.stray_marks.length + exceptions.data.failed_jobs.length
    : 0;

  return (
    <Card data-testid="exceptions-panel">
      <CardHeader>
        <CardTitle>Exceptions</CardTitle>
        <CardDescription>Anything the system refused to guess. Nothing here is scored until resolved.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="space-y-1.5 sm:max-w-xs">
          <Label htmlFor="exceptions-exam">Exam</Label>
          {exams.isSuccess && (
            <select id="exceptions-exam" data-testid="exceptions-exam-select"
              className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
              value={examId} onChange={e => setExamId(e.target.value)}>
              <option value="">Select an exam…</option>
              {exams.data.exams.map(e => <option key={e.id} value={e.id}>{e.name}</option>)}
            </select>
          )}
        </div>

        {examId && exceptions.isPending && <Skeleton className="h-40 w-full" />}

        {examId && exceptions.isSuccess && total === 0 && (
          <div className="rounded-lg border border-border p-8 text-center text-muted-foreground" data-testid="exceptions-empty">
            No exceptions for this exam.
          </div>
        )}

        {exceptions.isSuccess && exceptions.data.rejected_layout.length > 0 && (
          <section className="space-y-2" data-testid="exceptions-rejected">
            <h3 className="font-medium">Rejected layouts</h3>
            <ul className="space-y-2">
              {exceptions.data.rejected_layout.map(r => (
                <li key={r.sheet_id} className="rounded-lg border border-border p-3 text-sm">
                  <span className="font-medium">Sheet #{r.page_number}</span>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {r.reasons.map(reason => <Badge key={reason} variant="destructive">{reason}</Badge>)}
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )}

        {exceptions.isSuccess && exceptions.data.stray_marks.length > 0 && (
          <section className="space-y-2" data-testid="exceptions-stray">
            <h3 className="font-medium">Stray marks in unused rows</h3>
            <ul className="space-y-2">
              {exceptions.data.stray_marks.map(r => (
                <li key={r.sheet_id} className="rounded-lg border border-border p-3 text-sm">
                  <span className="font-medium">Sheet #{r.page_number}</span>
                  <span className="ml-2 text-muted-foreground">questions {r.questions.join(', ')}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {exceptions.isSuccess && exceptions.data.failed_jobs.length > 0 && (
          <section className="space-y-2" data-testid="exceptions-failed-jobs">
            <h3 className="font-medium">Failed jobs</h3>
            <ul className="space-y-2">
              {exceptions.data.failed_jobs.map(j => (
                <li key={j.job_id} className="rounded-lg border border-border p-3 text-sm">
                  <span className="font-medium">{j.kind}</span>
                  <span className="ml-2 text-muted-foreground">({j.attempt_count} attempts)</span>
                  {j.last_error && <p className="mt-1 text-destructive">{j.last_error}</p>}
                </li>
              ))}
            </ul>
          </section>
        )}
      </CardContent>
    </Card>
  );
}
