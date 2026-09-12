// features/admin/IntegerAnswersPanel.tsx
//
// Section-B numerical questions are never auto-read — the admin looks at
// the scanned sheet and types in the value themselves. One question at a
// time, full sheet image alongside a single numeric input.
import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { listExams, listIntegerQueue, resolveIntegerAnswer, AdminApiError } from '../../api/admin';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Alert, AlertTitle, AlertDescription } from '../../components/ui/alert';
import { Skeleton } from '../../components/ui/skeleton';
import { AuthImage } from '../../components/AuthImage';

export function IntegerAnswersPanel() {
  const exams = useQuery({ queryKey: ['admin', 'exams'], queryFn: () => listExams() });
  const [examId, setExamId] = useState('');
  const [value, setValue] = useState('');

  const queue = useQuery({
    queryKey: ['admin', 'integer-queue', examId],
    queryFn: () => listIntegerQueue(examId),
    enabled: Boolean(examId),
  });

  const client = useQueryClient();
  const resolve = useMutation({
    mutationFn: ({ sheetId, questionNumber, value }: { sheetId: string; questionNumber: number; value: number }) =>
      resolveIntegerAnswer(sheetId, questionNumber, value),
    onSuccess: () => {
      setValue('');
      void client.invalidateQueries({ queryKey: ['admin', 'integer-queue', examId] });
    },
  });

  const current = queue.data?.sheets[0];
  const currentQuestion = current?.pending_questions[0];

  return (
    <Card data-testid="integer-answers-panel">
      <CardHeader>
        <CardTitle>Integer answers</CardTitle>
        <CardDescription>
          Section-B numerical questions. Look at the sheet and type the value the student bubbled — nothing is guessed.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="space-y-1.5 sm:max-w-xs">
          <Label htmlFor="integer-exam">Exam</Label>
          {exams.isSuccess && (
            <select id="integer-exam" data-testid="integer-exam-select"
              className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
              value={examId} onChange={e => setExamId(e.target.value)}>
              <option value="">Select an exam…</option>
              {exams.data.exams.map(e => <option key={e.id} value={e.id}>{e.name}</option>)}
            </select>
          )}
        </div>

        {examId && queue.isPending && <Skeleton className="h-64 w-full" />}

        {examId && queue.isSuccess && !current && (
          <div className="rounded-lg border border-border p-8 text-center text-muted-foreground" data-testid="integer-queue-empty">
            No pending Section-B answers for this exam.
          </div>
        )}

        {current && currentQuestion != null && (
          <div className="grid gap-6 lg:grid-cols-2" data-testid="integer-review-pair">
            <div>
              <p className="mb-2 text-sm font-medium">
                Sheet #{current.page_number} — Question {currentQuestion}
                {current.pending_questions.length > 1 && (
                  <Badge variant="secondary" className="ml-2">
                    +{current.pending_questions.length - 1} more on this sheet
                  </Badge>
                )}
              </p>
              {current.image_id
                ? <AuthImage src={`/api/images/${current.image_id}`} alt={`Scanned sheet, page ${current.page_number}`}
                    className="max-h-[65vh] w-full rounded-lg border border-border object-contain" />
                : <div className="rounded-lg border border-dashed border-border p-8 text-center text-muted-foreground">No image available</div>}
            </div>
            <form className="space-y-3" onSubmit={e => {
              e.preventDefault();
              if (value.trim() === '') return;
              void resolve.mutateAsync({ sheetId: current.sheet_id, questionNumber: currentQuestion, value: Number(value) });
            }}>
              <Label htmlFor="integer-value">Value for Question {currentQuestion}</Label>
              <Input id="integer-value" type="number" min={0} max={9999} value={value}
                onChange={e => setValue(e.target.value)} data-testid="integer-value-input"
                autoFocus />
              {resolve.isError && (
                <Alert variant="destructive">
                  <AlertTitle>Could not save</AlertTitle>
                  <AlertDescription>
                    {resolve.error instanceof AdminApiError ? resolve.error.detail : 'Please try again.'}
                  </AlertDescription>
                </Alert>
              )}
              <button className="action" type="submit" data-testid="integer-submit-button"
                disabled={value.trim() === '' || resolve.isPending}>
                {resolve.isPending ? 'Saving…' : 'Save and continue'}
              </button>
            </form>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
