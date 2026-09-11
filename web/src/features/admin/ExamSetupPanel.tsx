// features/admin/ExamSetupPanel.tsx
//
// Question count, answer key entry, marking policy (fixed at the client's
// JEE Main scheme: +4 / -1 / 0 / -1 for multiple), and optional subject
// ranges. The answer key must cover every question exactly once — the
// backend enforces this too (cde/services/exams.py), this UI just makes it
// fast to satisfy the first time.
import { useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { createExam, listRosters, AdminApiError, type SubjectRangeInput } from '../../api/admin';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Alert, AlertTitle, AlertDescription } from '../../components/ui/alert';
import { Skeleton } from '../../components/ui/skeleton';

const OPTIONS = ['A', 'B', 'C', 'D'] as const;

interface KeyEntry { type: 'mcq' | 'integer'; option: string; value: string }
const emptyEntry: KeyEntry = { type: 'mcq', option: '', value: '' };

export function ExamSetupPanel() {
  const rosters = useQuery({ queryKey: ['admin', 'rosters'], queryFn: () => listRosters() });
  const [name, setName] = useState('');
  const [rosterId, setRosterId] = useState('');
  const [questionCount, setQuestionCount] = useState(75);
  const [answerKey, setAnswerKey] = useState<Record<number, KeyEntry>>({});
  const [subjectRanges, setSubjectRanges] = useState<SubjectRangeInput[]>([
    { subject: 'Physics', first_question: 1, last_question: 25 },
    { subject: 'Chemistry', first_question: 26, last_question: 50 },
    { subject: 'Mathematics', first_question: 51, last_question: 75 },
  ]);
  const [result, setResult] = useState<{ exam_id: string } | null>(null);

  const mutation = useMutation({
    mutationFn: createExam,
  });

  const questions = useMemo(
    () => Array.from({ length: Math.max(0, Math.min(180, questionCount)) }, (_, i) => i + 1),
    [questionCount],
  );
  const unanswered = questions.filter(q => {
    const e = answerKey[q];
    if (!e) return true;
    return e.type === 'mcq' ? !e.option : e.value.trim() === '';
  });
  const activeRanges = subjectRanges.filter(r => r.subject.trim().length > 0);
  const outOfRangeSubjects = activeRanges.filter(
    r => r.first_question < 1 || r.last_question > questions.length || r.first_question > r.last_question,
  );
  const overlappingSubjects = activeRanges.some((r, i) =>
    activeRanges.some((other, j) => i !== j &&
      r.first_question <= other.last_question && other.first_question <= r.last_question));
  const canSubmit = name.trim().length > 0 && rosterId.length > 0 &&
    questions.length > 0 && unanswered.length === 0 &&
    outOfRangeSubjects.length === 0 && !overlappingSubjects;

  async function submit() {
    if (!canSubmit) return;
    setResult(null);
    const created = await mutation.mutateAsync({
      name: name.trim(),
      roster_id: rosterId,
      question_count: questions.length,
      answer_key: questions.map(q => {
        const e = answerKey[q] ?? emptyEntry;
        return e.type === 'integer'
          ? { question_number: q, question_type: 'integer' as const, correct_value: Number(e.value) }
          : { question_number: q, question_type: 'mcq' as const, correct_option: e.option };
      }),
      subject_ranges: subjectRanges.filter(r => r.subject.trim().length > 0),
    });
    setResult(created);
  }

  return (
    <Card data-testid="exam-setup-panel">
      <CardHeader>
        <CardTitle>Set up exam</CardTitle>
        <CardDescription>
          Marking is fixed at +4 correct / −1 wrong / 0 blank / −1 multiple bubbles.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="exam-name">Exam name</Label>
            <Input id="exam-name" value={name} onChange={e => setName(e.target.value)}
              placeholder="e.g. Mock Test 1" data-testid="exam-name-input" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="exam-roster">Roster</Label>
            {rosters.isPending && <Skeleton className="h-9 w-full" />}
            {rosters.isSuccess && (
              <select id="exam-roster" data-testid="exam-roster-select"
                className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
                value={rosterId} onChange={e => setRosterId(e.target.value)}>
                <option value="">Select a roster…</option>
                {rosters.data.rosters.map(r => (
                  <option key={r.id} value={r.id}>{r.exam_class} ({r.student_count} students)</option>
                ))}
              </select>
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="question-count">Question count</Label>
            <Input id="question-count" type="number" min={1} max={180} value={questionCount}
              onChange={e => setQuestionCount(Number(e.target.value) || 0)}
              data-testid="question-count-input" />
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="font-medium">Answer key</h3>
            <p className="text-sm text-muted-foreground" data-testid="answer-key-progress">
              {questions.length - unanswered.length} / {questions.length} set
            </p>
          </div>
          <p className="text-xs text-muted-foreground">
            Mark a question &quot;Integer&quot; for JEE Main Section B numerical-answer questions —
            these are never auto-read; an admin always enters the value from the scanned sheet.
          </p>
          <div className="grid max-h-96 grid-cols-1 gap-x-6 gap-y-2 overflow-y-auto rounded-lg border border-border p-3 sm:grid-cols-2 lg:grid-cols-3">
            {questions.map(q => {
              const entry = answerKey[q] ?? emptyEntry;
              const setEntry = (patch: Partial<KeyEntry>) =>
                setAnswerKey(prev => ({ ...prev, [q]: { ...(prev[q] ?? emptyEntry), ...patch } }));
              return (
                <div key={q} className="flex items-center justify-between gap-2" data-testid={`answer-key-row-${q}`}>
                  <span className="w-10 shrink-0 text-sm text-muted-foreground">Q{q}</span>
                  <select className="h-8 rounded-md border border-input bg-transparent px-1 text-xs"
                    value={entry.type} data-testid={`answer-key-type-${q}`}
                    onChange={e => setEntry({ type: e.target.value as KeyEntry['type'] })}>
                    <option value="mcq">MCQ</option>
                    <option value="integer">Integer</option>
                  </select>
                  {entry.type === 'mcq' ? (
                    <select className="h-8 rounded-md border border-input bg-transparent px-2 text-sm"
                      value={entry.option} data-testid={`answer-key-select-${q}`}
                      onChange={e => setEntry({ option: e.target.value })}>
                      <option value="">–</option>
                      {OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
                    </select>
                  ) : (
                    <input type="number" min={0} max={9999} placeholder="value"
                      className="h-8 w-20 rounded-md border border-input bg-transparent px-2 text-sm"
                      value={entry.value} data-testid={`answer-key-value-${q}`}
                      onChange={e => setEntry({ value: e.target.value })} />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div className="space-y-2">
          <h3 className="font-medium">Subject ranges (optional)</h3>
          <div className="space-y-2">
            {subjectRanges.map((r, i) => {
              const invalid = r.subject.trim().length > 0 && outOfRangeSubjects.includes(r);
              return (
                <div key={i} className="flex flex-wrap items-center gap-2" data-testid={`subject-range-${i}`}>
                  <Input className="w-40" value={r.subject} placeholder="Subject"
                    onChange={e => setSubjectRanges(prev => prev.map((row, idx) => idx === i ? { ...row, subject: e.target.value } : row))} />
                  <Input className={`w-24 ${invalid ? 'border-destructive' : ''}`} type="number" value={r.first_question}
                    onChange={e => setSubjectRanges(prev => prev.map((row, idx) => idx === i ? { ...row, first_question: Number(e.target.value) || 0 } : row))} />
                  <span className="text-sm text-muted-foreground">to</span>
                  <Input className={`w-24 ${invalid ? 'border-destructive' : ''}`} type="number" value={r.last_question}
                    onChange={e => setSubjectRanges(prev => prev.map((row, idx) => idx === i ? { ...row, last_question: Number(e.target.value) || 0 } : row))} />
                </div>
              );
            })}
          </div>
          {outOfRangeSubjects.length > 0 && (
            <p className="text-sm text-destructive" data-testid="subject-range-error">
              Subject ranges must fall within 1–{questions.length} (the question count above).
            </p>
          )}
          {overlappingSubjects && (
            <p className="text-sm text-destructive" data-testid="subject-range-overlap-error">
              Subject ranges must not overlap.
            </p>
          )}
        </div>

        {mutation.isError && (
          <Alert variant="destructive">
            <AlertTitle>Could not create exam</AlertTitle>
            <AlertDescription>
              {mutation.error instanceof AdminApiError ? mutation.error.detail : 'Please try again.'}
            </AlertDescription>
          </Alert>
        )}
        {result && (
          <Alert data-testid="exam-setup-success">
            <AlertTitle>Exam created</AlertTitle>
            <AlertDescription>Exam id: {result.exam_id}</AlertDescription>
          </Alert>
        )}

        <button className="action" data-testid="exam-submit-button"
          disabled={!canSubmit || mutation.isPending} onClick={() => void submit()}>
          {mutation.isPending ? 'Creating…' : 'Create exam'}
        </button>
      </CardContent>
    </Card>
  );
}
