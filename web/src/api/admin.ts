// api/admin.ts — typed calls to cde/routes/admin.py, the real Phase-1 pipeline.
import { authFetch } from '../auth';

export class AdminApiError extends Error {
  constructor(public status: number, public detail: string) {
    super(detail);
    this.name = 'AdminApiError';
  }
}

async function call<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await authFetch(`/api/admin${path}`, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new AdminApiError(res.status, typeof data.detail === 'string' ? data.detail : 'The request could not be completed.');
  }
  return data as T;
}

import type { FeatureEntry, FeatureKey } from './student';

export function getFeatures() {
  return call<{ features: FeatureEntry[] }>('/features');
}

export function putFeatures(enabled: Partial<Record<FeatureKey, boolean>>) {
  return call<{ features: FeatureEntry[] }>('/features', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled }),
  });
}

export interface RosterRowInput { roll_number: string; name: string }
export interface RosterImportResult { roster_id: string; student_count: number }

export function importRoster(examClass: string, rows: RosterRowInput[]) {
  return call<RosterImportResult>('/rosters', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ exam_class: examClass, rows }),
  });
}

export interface RosterSummary { id: string; exam_class: string; student_count: number }

export function listRosters() {
  return call<{ rosters: RosterSummary[] }>('/rosters');
}

export interface StudentSummary { id: string; name: string; roll_number: string }

export function listStudents(rosterId: string) {
  return call<{ students: StudentSummary[] }>(`/rosters/${encodeURIComponent(rosterId)}/students`);
}

export type AnswerKeyEntryInput =
  | { question_number: number; question_type: 'mcq'; correct_option: string }
  | { question_number: number; question_type: 'integer'; correct_value: number };
export interface SubjectRangeInput { subject: string; first_question: number; last_question: number }
export interface ExamCreateInput {
  name: string;
  roster_id: string;
  question_count: number;
  answer_key: AnswerKeyEntryInput[];
  subject_ranges?: SubjectRangeInput[];
}
export interface ExamCreateResult { exam_id: string; question_count: number }

export function createExam(payload: ExamCreateInput) {
  return call<ExamCreateResult>('/exams', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export interface ExamSummary { id: string; name: string; question_count: number }

export function listExams() {
  return call<{ exams: ExamSummary[] }>('/exams');
}

export interface BatchUploadResult {
  batch_id: string;
  page_count: number;
  count_matches_expected: boolean | null;
}

export function uploadBatch(examId: string, file: File, expectedSheetCount?: number) {
  const body = new FormData();
  body.append('file', file);
  const qs = expectedSheetCount != null ? `?expected_sheet_count=${expectedSheetCount}` : '';
  return call<BatchUploadResult>(`/exams/${encodeURIComponent(examId)}/batches${qs}`, {
    method: 'POST',
    body,
  });
}

export interface SheetSummary {
  sheet_id: string;
  page_number: number;
  state: string;
  student_id: string | null;
}
export interface BatchStatus {
  batch_id: string;
  page_count: number;
  expected_sheet_count: number | null;
  count_matches_expected: boolean | null;
  counts_by_state: Record<string, number>;
  sheets: SheetSummary[];
}

export function batchStatus(examId: string, batchId: string) {
  return call<BatchStatus>(`/exams/${encodeURIComponent(examId)}/batches/${encodeURIComponent(batchId)}`);
}

export interface SheetWithImage {
  sheet_id: string;
  page_number: number;
  state: string;
  student_id: string | null;
  image_id: string | null;
}

export function listSheets(examId: string, state?: string) {
  const qs = state ? `?state=${encodeURIComponent(state)}` : '';
  return call<{ sheets: SheetWithImage[] }>(`/exams/${encodeURIComponent(examId)}/sheets${qs}`);
}

export interface ExceptionsReport {
  rejected_layout: Array<{ sheet_id: string; page_number: number; reasons: string[] }>;
  stray_marks: Array<{ sheet_id: string; page_number: number; questions: number[] }>;
  failed_jobs: Array<{ job_id: string; kind: string; entity_id: string; last_error: string | null; attempt_count: number }>;
}

export function listExceptions(examId: string) {
  return call<ExceptionsReport>(`/exams/${encodeURIComponent(examId)}/exceptions`);
}

export interface PendingIntegerSheet {
  sheet_id: string;
  page_number: number;
  image_id: string | null;
  pending_questions: number[];
}

export function listIntegerQueue(examId: string) {
  return call<{ sheets: PendingIntegerSheet[] }>(`/exams/${encodeURIComponent(examId)}/integer-queue`);
}

export function resolveIntegerAnswer(sheetId: string, questionNumber: number, value: number) {
  return call<{ sheet_id: string; question_number: number; value: number }>(
    `/sheets/${encodeURIComponent(sheetId)}/answers/${questionNumber}/integer`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value }),
    },
  );
}

export function confirmIdentity(sheetId: string, studentId: string) {
  return call<{ sheet_id: string; student_id: string; state: string }>(
    `/sheets/${encodeURIComponent(sheetId)}/identity`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ student_id: studentId }),
    },
  );
}
