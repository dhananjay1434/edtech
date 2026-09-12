// features/student/samples/diagnosis.ts
//
// A fictional student's worked example — never a real one — shown on the
// locked card so a student can see what this feature does before their
// institute turns it on.
import type { DiagnosisView } from '../../../api/student';

export const SAMPLE_STUDENT_NAME = 'Asha R.';

export const SAMPLE_DIAGNOSIS: Extract<DiagnosisView, { status: 'ready' }> = {
  status: 'ready',
  rough_sheet_status: 'uploaded',
  grade_revision: 1,
  questions: [
    {
      question_number: 4,
      subject: 'Physics',
      status: 'classified',
      error_class: 'Calculation Slip',
      confidence: 0.93,
      summary: 'The working sets up rotational kinetic energy correctly, then a sign is dropped in the final substitution.',
      next_step: 'Redo just the final substitution step, checking each sign against the original equation.',
      abstention_reason: null,
      reviewed: false,
    },
    {
      question_number: 11,
      subject: 'Chemistry',
      status: 'classified',
      error_class: 'Procedural Flaw',
      confidence: 0.62,
      summary: 'The working skips balancing the equation before applying stoichiometry.',
      next_step: 'Balance the equation first, every time, before working out mole ratios.',
      abstention_reason: null,
      reviewed: false,
    },
    {
      question_number: 18,
      subject: 'Mathematics',
      status: 'abstained',
      error_class: null,
      confidence: null,
      summary: null,
      next_step: null,
      abstention_reason: 'missing_or_unmapped_work',
      reviewed: false,
    },
  ],
};
