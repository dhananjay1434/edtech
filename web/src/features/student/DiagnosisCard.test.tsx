import { describe, it, expect, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { DiagnosisCard } from './DiagnosisCard';
import { renderStudent } from '../../test/render';
import * as studentApi from '../../api/student';
import type { DiagnosisView } from '../../api/student';

vi.mock('../../api/student', async () => {
  const actual = await vi.importActual<typeof import('../../api/student')>('../../api/student');
  return { ...actual, getDiagnosis: vi.fn(), uploadRoughSheet: vi.fn(), declareNoRoughSheet: vi.fn() };
});

describe('DiagnosisCard', () => {
  it('processing state shows the dropzone and no verdicts', async () => {
    const view: DiagnosisView = { status: 'processing', rough_sheet_status: null };
    vi.mocked(studentApi.getDiagnosis).mockResolvedValue(view);

    renderStudent(<DiagnosisCard examId="e1" />);

    await waitFor(() => expect(screen.getByTestId('diagnosis-processing')).toBeInTheDocument());
    expect(screen.getByTestId('rough-sheet-panel')).toBeInTheDocument();
    expect(screen.queryByTestId('diagnosis-results')).not.toBeInTheDocument();
  });

  it('ready state renders one card per question with a confidence tag', async () => {
    const view: DiagnosisView = {
      status: 'ready', rough_sheet_status: 'uploaded', grade_revision: 1,
      questions: [
        { question_number: 4, subject: 'Physics', status: 'classified', error_class: 'Calculation Slip',
          confidence: 0.95, summary: 's', next_step: 'n', abstention_reason: null, reviewed: false },
        { question_number: 7, subject: 'Chemistry', status: 'classified', error_class: 'Procedural Flaw',
          confidence: 0.5, summary: 's2', next_step: 'n2', abstention_reason: null, reviewed: false },
      ],
    };
    vi.mocked(studentApi.getDiagnosis).mockResolvedValue(view);

    renderStudent(<DiagnosisCard examId="e1" />);

    await waitFor(() => expect(screen.getByTestId('diagnosis-question-4')).toBeInTheDocument());
    expect(screen.getByTestId('diagnosis-question-7')).toBeInTheDocument();
    expect(screen.getAllByTestId('confidence-tag')).toHaveLength(2);
  });

  it('low confidence is visually distinguished and labelled', async () => {
    const view: DiagnosisView = {
      status: 'ready', rough_sheet_status: 'uploaded', grade_revision: 1,
      questions: [
        { question_number: 7, subject: 'Chemistry', status: 'classified', error_class: 'Procedural Flaw',
          confidence: 0.5, summary: 's2', next_step: 'n2', abstention_reason: null, reviewed: false },
      ],
    };
    vi.mocked(studentApi.getDiagnosis).mockResolvedValue(view);

    renderStudent(<DiagnosisCard examId="e1" />);

    await waitFor(() => expect(screen.getByTestId('confidence-tag')).toHaveTextContent('Low confidence'));
    expect(screen.getByTestId('confidence-tag').innerHTML).toMatch(/border-dashed/);
  });

  it('abstained question shows the honest reason, not an empty state', async () => {
    const view: DiagnosisView = {
      status: 'ready', rough_sheet_status: 'uploaded', grade_revision: 1,
      questions: [
        { question_number: 18, subject: 'Mathematics', status: 'abstained', error_class: null,
          confidence: null, summary: null, next_step: null,
          abstention_reason: 'missing_or_unmapped_work', reviewed: false },
      ],
    };
    vi.mocked(studentApi.getDiagnosis).mockResolvedValue(view);

    renderStudent(<DiagnosisCard examId="e1" />);

    await waitFor(() => expect(screen.getByTestId('diagnosis-abstained-reason')).toBeInTheDocument());
    expect(screen.getByTestId('diagnosis-abstained-reason').textContent).not.toBe('');
  });

  it('never renders the raw error_class word "Deficit"', async () => {
    const view: DiagnosisView = {
      status: 'ready', rough_sheet_status: 'uploaded', grade_revision: 1,
      questions: [
        { question_number: 3, subject: 'Mathematics', status: 'classified', error_class: 'Conceptual Deficit',
          confidence: 0.95, summary: 's', next_step: 'n', abstention_reason: null, reviewed: false },
      ],
    };
    vi.mocked(studentApi.getDiagnosis).mockResolvedValue(view);

    const { container } = renderStudent(<DiagnosisCard examId="e1" />);

    await waitFor(() => expect(screen.getByTestId('diagnosis-question-3')).toBeInTheDocument());
    expect(container.textContent).not.toMatch(/Deficit/);
  });
});
