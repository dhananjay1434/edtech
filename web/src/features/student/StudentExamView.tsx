// features/student/StudentExamView.tsx
//
// The Release-A student screen: "My exam" card with a status badge, the
// Processing state (no score data anywhere), and the Result screen (score
// headline, correct/wrong/blank/invalid breakdown with marks, and a
// question-by-question table). Backed by GET /api/me/exams/{exam_id}/report.
import { useQuery } from '@tanstack/react-query';
import { useRuntime } from '../../app/providers';
import { ApiError, AwardEntry } from '../../api/contracts';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Skeleton } from '../../components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '../../components/ui/alert';
import {
  Table, TableHeader, TableBody, TableRow, TableHead, TableCell,
} from '../../components/ui/table';

const STATE_LABEL: Record<AwardEntry['state'], string> = {
  correct: 'Correct',
  incorrect: 'Wrong',
  blank: 'Blank',
  invalid_multiple: 'Multiple bubbles',
  pending_review: 'Under review',
};

function marksBadgeVariant(marks: number): 'default' | 'destructive' | 'secondary' {
  if (marks > 0) return 'default';
  if (marks < 0) return 'destructive';
  return 'secondary';
}

function formatMarks(marks: string): string {
  const n = Number(marks);
  if (Number.isNaN(n)) return marks;
  return n > 0 ? `+${n}` : `${n}`;
}

function Breakdown({ answers }: { answers: AwardEntry[] }) {
  const groups = { correct: 0, incorrect: 0, blank: 0, invalid_multiple: 0 } as Record<string, number>;
  const marksByState = { correct: 0, incorrect: 0, blank: 0, invalid_multiple: 0 } as Record<string, number>;
  for (const a of answers) {
    if (a.state in groups) {
      groups[a.state] += 1;
      marksByState[a.state] += Number(a.awarded_marks);
    }
  }
  const rows: Array<{ key: string; label: string; count: number; marks: number }> = [
    { key: 'correct', label: 'Correct', count: groups.correct, marks: marksByState.correct },
    { key: 'incorrect', label: 'Wrong', count: groups.incorrect, marks: marksByState.incorrect },
    { key: 'blank', label: 'Blank', count: groups.blank, marks: marksByState.blank },
    { key: 'invalid_multiple', label: 'Multiple bubbles', count: groups.invalid_multiple, marks: marksByState.invalid_multiple },
  ];
  return (
    <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4" data-testid="result-breakdown">
      {rows.map(r => (
        <div key={r.key} className="rounded-lg border border-border p-3" data-testid={`breakdown-${r.key}`}>
          <dt className="text-xs font-medium text-muted-foreground">{r.label}</dt>
          <dd className="mt-1 text-xl font-semibold">{r.count}</dd>
          <dd className={`mt-1 text-sm font-medium ${r.marks < 0 ? 'text-destructive' : r.marks > 0 ? 'text-success' : 'text-muted-foreground'}`}>
            {formatMarks(String(r.marks))} marks
          </dd>
        </div>
      ))}
    </dl>
  );
}

function QuestionTable({ answers }: { answers: AwardEntry[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <Table data-testid="question-table">
        <TableHeader>
          <TableRow>
            <TableHead>Q#</TableHead>
            <TableHead>Your answer</TableHead>
            <TableHead>Result</TableHead>
            <TableHead className="text-right">Marks</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {answers.map(a => (
            <TableRow key={a.question_number} data-testid={`question-row-${a.question_number}`}>
              <TableCell className="font-medium">{a.question_number}</TableCell>
              <TableCell>{a.selected_option ?? <span className="text-muted-foreground">Blank</span>}</TableCell>
              <TableCell>
                <Badge variant={marksBadgeVariant(Number(a.awarded_marks))}>
                  {STATE_LABEL[a.state] ?? a.state}
                </Badge>
              </TableCell>
              <TableCell className={`text-right font-medium ${Number(a.awarded_marks) < 0 ? 'text-destructive' : Number(a.awarded_marks) > 0 ? 'text-success' : 'text-muted-foreground'}`}>
                {formatMarks(a.awarded_marks)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function ProcessingCard() {
  return (
    <Card data-testid="processing-screen">
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <CardTitle>Your exam is being processed</CardTitle>
          <Badge variant="secondary" data-testid="status-badge">Processing</Badge>
        </div>
        <CardDescription>We&apos;ll show your result here as soon as it&apos;s ready.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Your answer sheet has been scanned and is going through a careful review.
          Nothing is shown until every answer has been fully checked — including
          anything our system wasn&apos;t confident about, which a person always
          double-checks by hand. This can take a little time.
        </p>
        <div className="space-y-2" aria-hidden="true">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
        <div className="rounded-lg border border-border bg-muted/40 p-4">
          <h3 className="text-sm font-semibold">Coming soon</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Soon you&apos;ll be able to upload a photo of your rough work here,
            so we can look at your working once your result is ready.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

export function StudentExamView({ examId }: { examId: string }) {
  const { api, scope } = useRuntime();
  const query = useQuery({
    queryKey: [scope, 'my-exam-report', examId],
    queryFn: ({ signal }) => api.myExamReport(examId, signal),
    refetchInterval: (q) => (q.state.data?.status === 'processing' ? 5000 : false),
  });

  return (
    <section className="mx-auto max-w-3xl space-y-6" data-testid="student-exam-view">
      <header>
        <p className="text-sm font-medium text-primary" data-testid="student-exam-id">{examId}</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight" data-testid="student-exam-title">My exam</h1>
      </header>

      {query.isPending && (
        <Card data-testid="student-report-loading" aria-busy="true">
          <CardHeader>
            <Skeleton className="h-6 w-40" />
          </CardHeader>
          <CardContent className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-24 w-full" />
          </CardContent>
        </Card>
      )}

      {query.isError && (
        <Alert variant="destructive" data-testid="student-report-error">
          <AlertTitle>We couldn&apos;t load your exam</AlertTitle>
          <AlertDescription className="space-y-3">
            <p>
              {query.error instanceof ApiError && query.error.status === 403
                ? 'This account is not linked to a student record yet. Ask your institute admin for help.'
                : 'Please check your connection and try again.'}
            </p>
            <button className="action" data-testid="student-report-retry" onClick={() => void query.refetch()}>
              Try again
            </button>
          </AlertDescription>
        </Alert>
      )}

      {query.isSuccess && query.data.status === 'processing' && (
        <ProcessingCard />
      )}

      {query.isSuccess && query.data.status === 'ready' && (
        <Card data-testid="result-screen">
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <CardTitle>Result</CardTitle>
              <Badge data-testid="status-badge">Ready</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div data-testid="score-headline">
              <p className="text-4xl font-semibold tabular-nums" aria-label={`Score ${query.data.score} out of ${query.data.maximum}`}>
                {Number(query.data.score)} <span className="text-xl text-muted-foreground">/ {Number(query.data.maximum)}</span>
              </p>
              <p className="mt-1 text-sm text-muted-foreground">{Number(query.data.percentage)}%</p>
            </div>
            <Breakdown answers={query.data.answers} />
            <QuestionTable answers={query.data.answers} />
          </CardContent>
        </Card>
      )}
    </section>
  );
}
