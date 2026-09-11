import type { CdeApi } from './contracts';
import { getToken } from '../auth';

export const API_BASE = '';

export interface RoughSubmission {
  submission_id: string;
  exam_id: string;
  state: string;
  rough_sheet_path: string | null;
  analysis_status: string;
  analysis_error: string | null;
}
export interface ClassInsight {
  question_number: number;
  error_type: string;
  count: number;
  sample_explanation: string;
}

export async function roughRequest<T>(_api: CdeApi, path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set('Authorization', `Bearer ${getToken() ?? ''}`);
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'The request could not be completed. Please retry.');
  return data;
}

export const examPath = (examId: string) => `/api/exams/${encodeURIComponent(examId)}`;

export function uploadRoughSheet(api: CdeApi, file: File, examId: string, submissionId: string) {
  const body = new FormData();
  body.append('file', file);
  return roughRequest<{status: string; rough_sheet_path: string; analysis_status: string}>(
    api, `${examPath(examId)}/submissions/${encodeURIComponent(submissionId)}/rough-sheets`,
    { method: 'POST', body },
  );
}
