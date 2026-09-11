// features/student/StudentDiagnosticView.tsx
import { useQuery } from '@tanstack/react-query';
import { ApiError } from '../../api/contracts';
import { useRuntime } from '../../app/providers';
import { Evidence } from '../../shared/Evidence';

export function StudentDiagnosticView({ examId }: { examId: string }) {
  const { api, scope } = useRuntime();
  const query = useQuery({
    queryKey: [scope, 'published-exam', examId],
    queryFn: ({ signal }) => api.studentExam(examId, signal)
  });

  if (query.isPending) return <section role="status" aria-busy="true">Loading your feedback…</section>;
  if (query.isError) {
    const unavailable = query.error instanceof ApiError &&
      [403, 404].includes(query.error.status);
    return <section role="alert">
      <h1 className="text-2xl font-semibold">{unavailable ? 'This feedback is not available' : 'Feedback could not be loaded'}</h1>
      <p>{unavailable ? 'Return to your exam list or ask your teacher for help.' : 'Your results have not been changed.'}</p>
      {!unavailable && <button onClick={() => void query.refetch()}>Try again</button>}
    </section>;
  }

  const exam = query.data;
  if (exam.state !== 'Published') return <p role="alert">This feedback is not available.</p>;

  return <section className="space-y-6">
    <header className="panel">
      <p className="text-sm font-medium text-indigo-800">Feedback for this exam</p>
      <h1 className="mt-2 text-3xl font-semibold">{exam.title}</h1>
      <p className="mt-4 text-3xl font-semibold" aria-label={`Score ${exam.score} out of ${exam.maximum}`}>
        {exam.score} <span className="text-lg text-slate-500">/ {exam.maximum}</span>
      </p>
      <p className="mt-3 max-w-2xl text-slate-600">
        These observations describe your work on this exam—not your ability or potential.
        Use each next step to decide what to practise.
      </p>
      <p className="mt-2 text-sm text-slate-500">
        Published <time dateTime={exam.publishedAt}>{new Date(exam.publishedAt).toLocaleDateString()}</time>
      </p>
    </header>

    {exam.answers.map(answer => <article key={answer.id} className="panel">
      <header className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold">{answer.questionLabel}</h2>
        <span>{answer.score} / {answer.maximum}</span>
      </header>
      <div className="grid items-start gap-6 lg:grid-cols-2">
        <figure>
          <Evidence key={`student:${answer.cropId}`} cropId={answer.cropId} audience="student" />
          <figcaption className="mt-2 text-sm text-slate-500">Your handwritten work</figcaption>
        </figure>
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold">What to notice in this answer</h3>
            <p className="mt-2 inline-block rounded-md bg-indigo-50 px-3 py-1 text-indigo-900">{answer.classLabel}</p>
          </div>
          <p className="whitespace-pre-wrap leading-relaxed">{answer.explanation}</p>
          <section className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <h3 className="font-semibold">Try this next</h3>
            <p className="mt-2 whitespace-pre-wrap leading-relaxed">{answer.nextStep}</p>
          </section>
          {answer.reviewed && <p className="text-sm text-slate-600">This answer includes a human-reviewed correction.</p>}
        </div>
      </div>
    </article>)}
  </section>;
}
