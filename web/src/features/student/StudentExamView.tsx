// features/student/StudentExamView.tsx
//
// The Release-A student screen: "My exam" card with a status badge, the
// Processing state (no score data anywhere), and the Result screen (score
// headline, correct/wrong/blank/invalid breakdown with marks, and a
// question-by-question table). Backed by GET /api/me/exams/{exam_id}/report.
import { useQuery } from '@tanstack/react-query';
import { CircleCheck, ClipboardCheck, ScanLine } from 'lucide-react';
import { useRuntime } from '../../app/providers';
import { useFeature } from './useFeatures';
import { FeatureGate } from './FeatureGate';
import { DiagnosisCard } from './DiagnosisCard';
import { DiagnosisSample } from './samples/DiagnosisSample';
import { ApiError, AwardEntry } from '../../api/contracts';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Skeleton } from '../../components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '../../components/ui/alert';
import { Button } from '../../components/ui/button';
import { StatCard } from '../../components/ui/stat-card';
import { StatePill } from '../../components/ui/state-pill';
import {
  Table, TableHeader, TableBody, TableRow, TableHead, TableCell,
} from '../../components/ui/table';

const STATE_LABEL: Record<AwardEntry['state'], string> = {
  correct: 'Correct',
  incorrect: 'Not correct yet',
  blank: 'Blank',
  invalid_multiple: 'Multiple bubbles',
  pending_review: 'Under review',
};

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
  const total = answers.length;
  const rows: Array<{ key: string; label: string; count: number; marks: number; tone: 'success' | 'attention' | 'neutral' }> = [
    { key: 'correct', label: STATE_LABEL.correct, count: groups.correct, marks: marksByState.correct, tone: 'success' },
    { key: 'incorrect', label: STATE_LABEL.incorrect, count: groups.incorrect, marks: marksByState.incorrect, tone: 'attention' },
    { key: 'blank', label: STATE_LABEL.blank, count: groups.blank, marks: marksByState.blank, tone: 'neutral' },
    { key: 'invalid_multiple', label: STATE_LABEL.invalid_multiple, count: groups.invalid_multiple, marks: marksByState.invalid_multiple, tone: 'attention' },
  ];
  return (
    <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4" data-testid="result-breakdown">
      {rows.map(r => (
        <div key={r.key} data-testid={`breakdown-${r.key}`}>
          <StatCard
            label={r.label}
            value={String(r.count)}
            context={`of ${total} question${total === 1 ? '' : 's'} — ${formatMarks(String(r.marks))} marks`}
            tone={r.count > 0 ? r.tone : 'neutral'}
            action={{ label: 'See which ones', onClick: () => document.getElementById('question-table')?.scrollIntoView({ behavior: 'smooth' }) }}
          />
        </div>
      ))}
    </dl>
  );
}

function QuestionTable({ answers }: { answers: AwardEntry[] }) {
  return (
    <div id="question-table" className="overflow-x-auto rounded-lg border border-border">
      <Table data-testid="question-table">
        <TableHeader className="sticky top-0 bg-card">
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
              <TableCell><StatePill state={a.state} /></TableCell>
              <TableCell className={`text-right font-mono font-medium tabular-nums ${Number(a.awarded_marks) < 0 ? 'text-attention' : Number(a.awarded_marks) > 0 ? 'text-success' : 'text-muted-foreground'}`}>
                {formatMarks(a.awarded_marks)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

const STAGES = [
  { key: 'scan', label: 'Sheet scanned', Icon: ScanLine },
  { key: 'check', label: 'Answers checked', Icon: ClipboardCheck },
  { key: 'publish', label: 'Result published', Icon: CircleCheck },
] as const;

function ProcessingCard({ examId }: { examId: string }) {
  return (
    <Card data-testid="processing-screen">
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <CardTitle>Your exam is being processed</CardTitle>
          <Badge variant="secondary" data-testid="status-badge">Processing</Badge>
        </div>
        <CardDescription>We&apos;ll show your result here as soon as it&apos;s ready.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <ol className="space-y-3">
          {STAGES.map((stage, i) => (
            <li key={stage.key} className="flex items-center gap-3 text-sm">
              <stage.Icon className={`h-5 w-5 shrink-0 ${i === 0 ? 'text-primary' : 'text-muted-foreground'}`} aria-hidden="true" />
              <span className={i === 0 ? 'font-medium text-foreground' : 'text-muted-foreground'}>{stage.label}</span>
              {i === 0 && <Badge variant="secondary" className="ml-auto">Now</Badge>}
            </li>
          ))}
        </ol>
        <p className="text-sm text-muted-foreground">
          Nothing is shown until every answer has been fully checked — including
          anything our system wasn&apos;t confident about, which a person always
          double-checks by hand. This can take a little time.
        </p>
        <FeatureGate feature="cognitive.diagnosis" sample={<DiagnosisSample />}>
          <DiagnosisCard examId={examId} />
        </FeatureGate>
      </CardContent>
    </Card>
  );
}

export function StudentExamView({ examId }: { examId: string }) {
  const { api, scope } = useRuntime();
  const growth = useFeature('cognitive.growth');
  const query = useQuery({
    queryKey: [scope, 'my-exam-report', examId],
    queryFn: ({ signal }) => api.myExamReport(examId, signal),
    refetchInterval: (q) => (q.state.data?.status === 'processing' ? 5000 : false),
  });

  return (
    <section className="mx-auto max-w-3xl space-y-6 animate-in fade-in-0 duration-300" data-testid="student-exam-view">
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
            <Button data-testid="student-report-retry" onClick={() => void query.refetch()}>
              Try again
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {query.isSuccess && query.data.status === 'processing' && (
        <ProcessingCard examId={examId} />
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
              <p className="mt-1 text-sm text-muted-foreground">
                {Number(query.data.percentage)}% — marks after negative marking
              </p>
              {!growth.isPending && (
                growth.enabled
                  ? <a href="/student/growth" className="mt-2 inline-block text-sm font-medium text-primary hover:underline">Open growth</a>
                  : <a href="/student/features" className="mt-2 inline-block text-sm font-medium text-primary hover:underline">See what your institute can enable</a>
              )}
            </div>
            <Breakdown answers={query.data.answers} />
            <QuestionTable answers={query.data.answers} />
            <FeatureGate feature="cognitive.diagnosis" sample={<DiagnosisSample />}>
              <DiagnosisCard examId={examId} />
            </FeatureGate>
          </CardContent>
        </Card>
      )}
    </section>
  );
}
