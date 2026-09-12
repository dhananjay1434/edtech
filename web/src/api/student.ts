// api/student.ts — typed calls to cde/routes/student.py's /api/me/* surface.
import { authFetch } from '../auth';

export class StudentApiError extends Error {
  constructor(public status: number, public detail: string) {
    super(detail);
    this.name = 'StudentApiError';
  }
}

async function call<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await authFetch(`/api/me${path}`, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new StudentApiError(res.status, typeof data.detail === 'string' ? data.detail : 'The request could not be completed.');
  }
  return data as T;
}

export type FeatureKey =
  | 'cognitive.diagnosis'
  | 'cognitive.growth'
  | 'cognitive.heatmap'
  | 'cognitive.patterns'
  | 'cognitive.calibration'
  | 'cognitive.exam_history'
  | 'learning.spaced_review'
  | 'learning.planner'
  | 'learning.micro_wins'
  | 'learning.trajectory';

export interface FeatureEntry {
  key: FeatureKey;
  title: string;
  description: string;
  tier: 2 | 3;
  status: 'available' | 'preview';
  enabled: boolean;
}

export function listFeatures() {
  return call<{ features: FeatureEntry[] }>('/features');
}

export interface MyExam { exam_id: string; name: string; status: 'ready' | 'processing' }

export function listMyExams() {
  return call<{ exams: MyExam[] }>('/exams');
}
