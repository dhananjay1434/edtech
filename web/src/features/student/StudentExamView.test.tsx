import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { StudentExamView } from './StudentExamView';
import { Providers } from '../../app/providers';
import type { CdeApi, MyExamReport, Runtime } from '../../api/contracts';

function makeRuntime(myExamReport: CdeApi['myExamReport']): Runtime {
  const api: CdeApi = {
    accessToken: async () => 'token',
    prepareUpload: vi.fn(),
    completeUpload: vi.fn(),
    submissionStatus: vi.fn(),
    reviewQueue: vi.fn(),
    resolveTask: vi.fn(),
    studentExam: vi.fn(),
    myExamReport,
    cropBlob: vi.fn(),
  };
  return { api, scope: 'test', portals: ['student'], signOut: async () => {} };
}

describe('StudentExamView', () => {
  it('renders the processing screen with no score element while processing', async () => {
    const report: MyExamReport = { status: 'processing' };
    const runtime = makeRuntime(async () => report);

    render(<Providers runtime={runtime}><StudentExamView examId="examV" /></Providers>);

    await waitFor(() => expect(screen.getByTestId('processing-screen')).toBeInTheDocument());
    expect(screen.queryByTestId('score-headline')).not.toBeInTheDocument();
    expect(screen.queryByTestId('result-screen')).not.toBeInTheDocument();
    // No raw numbers that could be mistaken for a score anywhere in the DOM.
    expect(screen.getByTestId('processing-screen').textContent).not.toMatch(/\d+\s*\/\s*\d+/);
  });

  it('renders the result screen with the score and negative marks shown explicitly', async () => {
    const report: MyExamReport = {
      status: 'ready',
      score: '3.000',
      maximum: '8.000',
      percentage: '37.500',
      revision: 1,
      answers: [
        { question_number: 1, state: 'correct', awarded_marks: '4.000', selected_option: 'A' },
        { question_number: 2, state: 'incorrect', awarded_marks: '-1.000', selected_option: 'C' },
      ],
    };
    const runtime = makeRuntime(async () => report);

    render(<Providers runtime={runtime}><StudentExamView examId="examV" /></Providers>);

    await waitFor(() => expect(screen.getByTestId('result-screen')).toBeInTheDocument());
    expect(screen.getByTestId('score-headline')).toHaveTextContent('3');
    expect(screen.getByTestId('score-headline')).toHaveTextContent('8');
    // The -1 penalty must be visible, not hidden inside an aggregate number.
    expect(screen.getByTestId('breakdown-incorrect').textContent).toMatch(/-1/);
    expect(screen.getByTestId('question-row-2').textContent).toMatch(/-1/);
  });

  it('shows a retry action on error, never a raw error object', async () => {
    const runtime = makeRuntime(async () => { throw new Error('network down'); });

    render(<Providers runtime={runtime}><StudentExamView examId="examV" /></Providers>);

    await waitFor(() => expect(screen.getByTestId('student-report-error')).toBeInTheDocument(),
      { timeout: 10000 });
    expect(screen.getByTestId('student-report-error').textContent).not.toMatch(/Error:|network down/);
    expect(screen.getByTestId('student-report-retry')).toBeInTheDocument();
  });
});
