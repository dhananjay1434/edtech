// features/admin/IdentityQueuePanel.tsx
//
// Sheet image beside a searchable roster list; confirm in one click.
// A name on a sheet never grants account access — this only links a
// scanned sheet to a roster student record.
import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  listExams, listSheets, listRosters, listStudents, confirmIdentity, AdminApiError,
} from '../../api/admin';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Alert, AlertTitle, AlertDescription } from '../../components/ui/alert';
import { Skeleton } from '../../components/ui/skeleton';

export function IdentityQueuePanel() {
  const exams = useQuery({ queryKey: ['admin', 'exams'], queryFn: () => listExams() });
  const rosters = useQuery({ queryKey: ['admin', 'rosters'], queryFn: () => listRosters() });
  const [examId, setExamId] = useState('');
  const [rosterId, setRosterId] = useState('');
  const [search, setSearch] = useState('');

  const sheets = useQuery({
    queryKey: ['admin', 'sheets', examId, 'pending_identity'],
    queryFn: () => listSheets(examId, 'pending_identity'),
    enabled: Boolean(examId),
  });
  const students = useQuery({
    queryKey: ['admin', 'students', rosterId],
    queryFn: () => listStudents(rosterId),
    enabled: Boolean(rosterId),
  });

  const client = useQueryClient();
  const confirm = useMutation({
    mutationFn: ({ sheetId, studentId }: { sheetId: string; studentId: string }) =>
      confirmIdentity(sheetId, studentId),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ['admin', 'sheets', examId, 'pending_identity'] });
    },
  });

  const currentSheet = sheets.data?.sheets[0];
  const filteredStudents = useMemo(() => {
    const list = students.data?.students ?? [];
    const q = search.trim().toLowerCase();
    if (!q) return list;
    return list.filter(s => s.name.toLowerCase().includes(q) || s.roll_number.toLowerCase().includes(q));
  }, [students.data, search]);

  return (
    <Card data-testid="identity-queue-panel">
      <CardHeader>
        <CardTitle>Identity queue</CardTitle>
        <CardDescription>Confirm whose sheet each scan belongs to. Nothing is guessed.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="identity-exam">Exam</Label>
            {exams.isSuccess && (
              <select id="identity-exam" data-testid="identity-exam-select"
                className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
                value={examId} onChange={e => setExamId(e.target.value)}>
                <option value="">Select an exam…</option>
                {exams.data.exams.map(e => <option key={e.id} value={e.id}>{e.name}</option>)}
              </select>
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="identity-roster">Roster</Label>
            {rosters.isSuccess && (
              <select id="identity-roster" data-testid="identity-roster-select"
                className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
                value={rosterId} onChange={e => setRosterId(e.target.value)}>
                <option value="">Select a roster…</option>
                {rosters.data.rosters.map(r => <option key={r.id} value={r.id}>{r.exam_class}</option>)}
              </select>
            )}
          </div>
        </div>

        {examId && sheets.isPending && <Skeleton className="h-64 w-full" />}

        {examId && sheets.isSuccess && !currentSheet && (
          <div className="rounded-lg border border-border p-8 text-center text-muted-foreground" data-testid="identity-empty">
            No sheets are waiting on identity confirmation for this exam.
          </div>
        )}

        {currentSheet && (
          <div className="grid gap-6 lg:grid-cols-2" data-testid="identity-review-pair">
            <div>
              <p className="mb-2 text-sm font-medium">Sheet #{currentSheet.page_number}</p>
              {currentSheet.image_id
                ? <img src={`/api/images/${currentSheet.image_id}`} alt={`Scanned sheet, page ${currentSheet.page_number}`}
                    className="max-h-[60vh] w-full rounded-lg border border-border object-contain" />
                : <div className="rounded-lg border border-dashed border-border p-8 text-center text-muted-foreground">No image available</div>}
            </div>
            <div className="space-y-3">
              <Label htmlFor="student-search">Search roster</Label>
              <Input id="student-search" placeholder="Name or roll number" value={search}
                onChange={e => setSearch(e.target.value)} data-testid="student-search-input" />
              {!rosterId && <p className="text-sm text-muted-foreground">Select a roster above to search students.</p>}
              {confirm.isError && (
                <Alert variant="destructive">
                  <AlertTitle>Could not confirm identity</AlertTitle>
                  <AlertDescription>
                    {confirm.error instanceof AdminApiError ? confirm.error.detail : 'Please try again.'}
                  </AlertDescription>
                </Alert>
              )}
              <ul className="max-h-96 space-y-1 overflow-y-auto" data-testid="student-search-results">
                {filteredStudents.map(s => (
                  <li key={s.id}>
                    <button className="flex w-full items-center justify-between rounded-lg border border-border px-3 py-2 text-left text-sm hover:bg-accent"
                      data-testid={`confirm-student-${s.id}`}
                      disabled={confirm.isPending}
                      onClick={() => void confirm.mutateAsync({ sheetId: currentSheet.sheet_id, studentId: s.id })}>
                      <span>{s.name}</span>
                      <Badge variant="secondary">{s.roll_number}</Badge>
                    </button>
                  </li>
                ))}
                {rosterId && filteredStudents.length === 0 && (
                  <li className="p-3 text-center text-sm text-muted-foreground">No matching students.</li>
                )}
              </ul>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
