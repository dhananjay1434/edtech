// features/student/DiagnosisResults.tsx
//
// Presentational rendering of a ready DiagnosisView, shared by the real
// DiagnosisCard and the locked-card sample so both describe the feature the
// same way. Copy describes the working, never the student.
import type { DiagnosisQuestion, DiagnosisView, ErrorClass } from '../../api/student';
import { Card, CardContent } from '../../components/ui/card';
import { ConfidenceTag } from '../../components/ui/confidence-tag';

const ERROR_CLASS_COPY: Record<ErrorClass, string> = {
  'Calculation Slip': 'The method was right; a calculation step didn’t hold.',
  'Procedural Flaw': 'A step in the procedure was skipped or done out of order.',
  'Reading Comprehension Error': 'The working answers a slightly different question from the one asked.',
  'Conceptual Deficit': 'The working used a relationship that doesn’t apply here.',
};

const ABSTENTION_COPY: Record<string, string> = {
  no_rough_work_provided: 'No rough work was attached for this question.',
  missing_or_unmapped_work: 'We couldn’t find working for this question in the photo.',
  missing_question_context: 'Your institute hasn’t added the question text yet, so nothing can be checked.',
  insufficient_classification_confidence: 'The working was there but not clear enough to read reliably.',
};

function QuestionCard({ q }: { q: DiagnosisQuestion }) {
  return (
    <Card data-testid={`diagnosis-question-${q.question_number}`}>
      <CardContent className="space-y-2 pt-4">
        <p className="text-sm font-medium">
          Q{q.question_number}{q.subject ? ` · ${q.subject}` : ''}
        </p>
        {q.status === 'classified' && q.error_class ? (
          <>
            <p className="text-sm text-muted-foreground">{ERROR_CLASS_COPY[q.error_class]}</p>
            {q.summary && <p className="text-sm">{q.summary}</p>}
            {q.next_step && <p className="text-sm text-muted-foreground">Next: {q.next_step}</p>}
            <ConfidenceTag value={q.confidence} reviewed={q.reviewed} />
          </>
        ) : (
          <p className="text-sm text-muted-foreground" data-testid="diagnosis-abstained-reason">
            {ABSTENTION_COPY[q.abstention_reason ?? ''] ?? 'Not enough could be found to check this question.'}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

export function DiagnosisResults({ view }: { view: Extract<DiagnosisView, { status: 'ready' }> }) {
  if (view.questions.length === 0) {
    return <p className="text-sm text-muted-foreground">Nothing to check yet — every answer was correct.</p>;
  }
  return (
    <div className="space-y-3" data-testid="diagnosis-results">
      {view.questions.map(q => <QuestionCard key={q.question_number} q={q} />)}
    </div>
  );
}
