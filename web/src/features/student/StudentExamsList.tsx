// features/student/StudentExamsList.tsx
//
// Landing page for the student portal: every exam this student has a
// sheet in, linking through to the report. Backed by GET /api/me/exams,
// which returns status only — no scores appear until a report is published.
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { listMyExams, StudentApiError } from '../../api/student';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Skeleton } from '../../components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '../../components/ui/alert';

export function StudentExamsList() {
  const query = useQuery({
    queryKey: ['student', 'my-exams'],
    queryFn: async () => (await listMyExams()).exams,
  });

  return (
    <Card data-testid="student-exams-list">
      <CardHeader>
        <CardTitle>My exams</CardTitle>
        <CardDescription>Results appear here once every answer on your sheet is confirmed.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {query.isPending && <Skeleton className="h-12 w-full" />}
        {query.isError && (
          <Alert variant="destructive">
            <AlertTitle>Could not load your exams</AlertTitle>
            <AlertDescription>
              {query.error instanceof StudentApiError && query.error.status === 403
                ? 'This login is not linked to a student record yet. Ask your institute admin.'
                : 'Please try again in a moment.'}
            </AlertDescription>
          </Alert>
        )}
        {query.isSuccess && query.data.length === 0 && (
          <p className="text-sm text-muted-foreground">No exams yet.</p>
        )}
        {query.isSuccess && query.data.map(exam => (
          <Link key={exam.exam_id} to={`/student/exams/${exam.exam_id}`}
            className="flex min-h-11 items-center justify-between rounded-lg border border-border px-4 hover:bg-accent"
            data-testid={`student-exam-link-${exam.exam_id}`}>
            <span>{exam.name}</span>
            <Badge variant={exam.status === 'ready' ? 'default' : 'secondary'}>
              {exam.status === 'ready' ? 'Result ready' : 'Processing'}
            </Badge>
          </Link>
        ))}
      </CardContent>
    </Card>
  );
}
