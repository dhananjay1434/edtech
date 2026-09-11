export type Portal = 'teacher' | 'admin' | 'student';
export type WorkflowState =
  | 'Uploading'
  | 'Processing'
  | 'Requires Admin Review'
  | 'Graded (Draft)'
  | 'Published';

export class ApiError extends Error {
  constructor(public status: number, public code: string) {
    super(code);
    this.name = 'ApiError';
  }
}

export interface SubmissionStatus {
  id: string;
  state: WorkflowState;
  revision: string;
  updatedAt: string;
  issue?: { message: string; retryable: boolean };
}

export type UploadPreparation =
  | { kind: 'existing'; submissionId: string }
  | {
      kind: 'transfer';
      submissionId: string;
      uploadUrl: string;
    };

export interface ReviewTask {
  id: string;
  cropId: string;
  revision: string;
  kind: 'ambiguous' | 'abstained';
  choices: Array<{ code: string; label: string }>;
  suggestedCode?: string;
}

export interface ResolutionCommand {
  expectedRevision: string;
  decisionCode: string;
  reason: string;
  idempotencyKey: string;
}

// Matches GET /api/me/exams/{exam_id}/report (cde/routes/student.py) exactly —
// the Release-A score report, distinct from the Release-B diagnostic feedback
// shape (PublishedExam, below).
export type AwardState = 'correct' | 'incorrect' | 'blank' | 'invalid_multiple' | 'pending_review';

export interface AwardEntry {
  question_number: number;
  state: AwardState;
  awarded_marks: string;
  selected_option: string | null;
}

export type MyExamReport =
  | { status: 'processing' }
  | {
      status: 'ready';
      score: string;
      maximum: string;
      percentage: string;
      answers: AwardEntry[];
      revision: number;
    };

export interface PublishedExam {
  id: string;
  state: 'Published';
  revision: string;
  title: string;
  publishedAt: string;
  score: number;
  maximum: number;
  answers: Array<{
    id: string;
    questionLabel: string;
    cropId: string;
    score: number;
    maximum: number;
    classLabel: string;
    explanation: string;
    nextStep: string;
    reviewed: boolean;
  }>;
}

export interface CdeApi {
  accessToken(): Promise<string>;
  prepareUpload(
    examId: string,
    file: { sha256: string; bytes: number },
    signal: AbortSignal
  ): Promise<UploadPreparation>;
  completeUpload(
    uploadId: string,
    examId: string,
    sha256: string,
    signal: AbortSignal
  ): Promise<{ submissionId: string }>;
  submissionStatus(id: string, signal: AbortSignal): Promise<SubmissionStatus>;
  reviewQueue(signal: AbortSignal): Promise<ReviewTask[]>;
  resolveTask(id: string, command: ResolutionCommand): Promise<void>;
  studentExam(id: string, signal: AbortSignal): Promise<PublishedExam>;
  myExamReport(examId: string, signal: AbortSignal): Promise<MyExamReport>;
  cropBlob(
    audience: Portal,
    cropId: string,
    signal: AbortSignal
  ): Promise<Blob>;
}

export interface Runtime {
  api: CdeApi;
  scope: string; // opaque authenticated principal/tenant cache namespace
  portals: Portal[];
  signOut(): Promise<void>;
}

export function retryRead(count: number, error: unknown): boolean {
  if (count >= 2) return false;
  return !(error instanceof ApiError && error.status >= 400 && error.status < 500);
}
