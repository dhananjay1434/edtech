import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { StudentExamView } from './StudentExamView';
import { Providers } from '../../app/providers';
import type { MyExamReport } from '../../api/contracts';
import { makeRuntime } from '../../test/render';
import * as studentApi from '../../api/student';

vi.mock('../../api/student', async () => {
  const actual = await vi.importActual<typeof import('../../api/student')>('../../api/student');
  return { ...actual, listFeatures: vi.fn() };
});

// StudentExamView checks the cognitive.growth entitlement for its "Open
// growth" link — stub it disabled so these tests never make a real fetch.
vi.mocked(studentApi.listFeatures).mockResolvedValue({ features: [] });

function runtimeWithReport(myExamReport: () => Promise<MyExamReport>) {
  return makeRuntime({ myExamReport });
}

describe('StudentExamView', () => {
  it('renders the processing screen with no score element while processing', async () => {
    const report: MyExamReport = { status: 'processing' };
    const runtime = runtimeWithReport(async () => report);

    render(<Providers runtime={runtime}><StudentExamView examId="examV" /></Providers>);

    await waitFor(() => expect(screen.getByTestId('processing-screen')).toBeInTheDocument());
    expect(screen.queryByTestId('score-headline')).not.toBeInTheDocument();
    expect(screen.queryByTestId('result-screen')).not.toBeInTheDocument();
    // No raw numbers that could be mistaken for a score anywhere in the DOM.
    expect(screen.getByTestId('processing-screen').textContent).not.toMatch(/\d+\s*\/\s*\d+/);
  });

  it('processing screen offers exactly one action', async () => {
    const report: MyExamReport = { status: 'processing' };
    const runtime = runtimeWithReport(async () => report);

    render(<Providers runtime={runtime}><StudentExamView examId="examV" /></Providers>);

    await waitFor(() => expect(screen.getByTestId('processing-screen')).toBeInTheDocument());
    // No action controls at all while processing — the stage list is informational only.
    expect(screen.queryAllByRole('button')).toHaveLength(0);
    expect(screen.queryAllByRole('link')).toHaveLength(0);
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
    const runtime = runtimeWithReport(async () => report);

    render(<Providers runtime={runtime}><StudentExamView examId="examV" /></Providers>);

    await waitFor(() => expect(screen.getByTestId('result-screen')).toBeInTheDocument());
    expect(screen.getByTestId('score-headline')).toHaveTextContent('3');
    expect(screen.getByTestId('score-headline')).toHaveTextContent('8');
    // The -1 penalty must be visible, not hidden inside an aggregate number.
    expect(screen.getByTestId('breakdown-incorrect').textContent).toMatch(/-1/);
    expect(screen.getByTestId('question-row-2').textContent).toMatch(/-1/);
    // "Not correct yet", never "Wrong" — the calm-precision copy rule.
    expect(screen.getByTestId('result-screen').textContent).not.toMatch(/\bwrong\b/i);
    expect(screen.getByTestId('question-row-2').textContent).toMatch(/Not correct yet/);
    // Incorrect marks use the muted attention tone, never saturated destructive red.
    const marksCell = screen.getByTestId('question-row-2').querySelector('td:last-child');
    expect(marksCell?.className).toMatch(/text-attention/);
    expect(marksCell?.className).not.toMatch(/text-destructive/);
  });

  it('shows a retry action on error, never a raw error object', async () => {
    const runtime = runtimeWithReport(async () => { throw new Error('network down'); });

    render(<Providers runtime={runtime}><StudentExamView examId="examV" /></Providers>);

    await waitFor(() => expect(screen.getByTestId('student-report-error')).toBeInTheDocument(),
      { timeout: 10000 });
    expect(screen.getByTestId('student-report-error').textContent).not.toMatch(/Error:|network down/);
    expect(screen.getByTestId('student-report-retry')).toBeInTheDocument();
  });
});
