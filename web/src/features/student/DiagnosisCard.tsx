// features/student/DiagnosisCard.tsx
import { useQuery } from '@tanstack/react-query';
import { getDiagnosis } from '../../api/student';
import { RoughSheetDropzone } from './RoughSheetDropzone';
import { DiagnosisResults } from './DiagnosisResults';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Skeleton } from '../../components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '../../components/ui/alert';

export function DiagnosisCard({ examId }: { examId: string }) {
  const query = useQuery({
    queryKey: ['student', 'diagnosis', examId],
    queryFn: () => getDiagnosis(examId),
    refetchInterval: q => (q.state.data?.status === 'processing' ? 5000 : false),
  });

  return (
    <Card data-testid="diagnosis-card">
      <CardHeader>
        <CardTitle>Rough-work diagnosis</CardTitle>
        <CardDescription>What your working shows for each question you didn’t get right.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {query.isPending && <Skeleton className="h-24 w-full" data-testid="diagnosis-loading" />}

        {query.isError && (
          <Alert variant="destructive">
            <AlertTitle>Could not check your diagnosis</AlertTitle>
            <AlertDescription>Please try again in a moment.</AlertDescription>
          </Alert>
        )}

        {query.isSuccess && query.data.status === 'waiting_for_result' && (
          <p className="text-sm text-muted-foreground" data-testid="diagnosis-waiting">
            This appears once your result is published.
          </p>
        )}

        {query.isSuccess && query.data.status === 'processing' && (
          <div className="space-y-4" data-testid="diagnosis-processing">
            <p className="text-sm text-muted-foreground">
              Your working is being checked. You can attach or replace your rough work while you wait.
            </p>
            <RoughSheetDropzone examId={examId} roughSheetStatus={query.data.rough_sheet_status} />
          </div>
        )}

        {query.isSuccess && query.data.status === 'ready' && (
          <div className="space-y-4">
            <DiagnosisResults view={query.data} />
            <RoughSheetDropzone examId={examId} roughSheetStatus={query.data.rough_sheet_status} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
