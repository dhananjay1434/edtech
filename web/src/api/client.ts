import { CdeApi, UploadPreparation, SubmissionStatus, ReviewTask, ResolutionCommand, PublishedExam, MyExamReport, ApiError, Portal } from './contracts';

export class CdeApiClient implements CdeApi {
    private baseUrl = '';
    
    constructor(private getToken: () => Promise<string>) {}

    async accessToken(): Promise<string> {
        return this.getToken();
    }

    private async fetch(path: string, options: RequestInit): Promise<Response> {
        const token = await this.accessToken();
        const headers = new Headers(options.headers);
        headers.set('Authorization', `Bearer ${token}`);
        
        const res = await fetch(`${this.baseUrl}${path}`, { ...options, headers });
        if (!res.ok) {
            throw new ApiError(res.status, res.statusText);
        }
        return res;
    }

    async prepareUpload(examId: string, file: { sha256: string; bytes: number }, signal: AbortSignal): Promise<UploadPreparation> {
        const res = await this.fetch(`/api/exams/${examId}/uploads`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_id: "anonymous", expected_size: file.bytes, checksum_sha256: file.sha256 }),
            signal
        });
        const data = await res.json();
        return {
            kind: 'transfer',
            submissionId: data.upload_id,
            uploadUrl: data.presigned_url
        };
    }

    async completeUpload(uploadId: string, examId: string, _sha256: string, signal: AbortSignal): Promise<{ submissionId: string }> {
        const res = await this.fetch(`/api/uploads/${uploadId}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ exam_id: examId, request: { idempotency_key: crypto.randomUUID(), object_version: "1" } }),
            signal
        });
        const data = await res.json();
        // Both "accepted" and "already_accepted" responses carry the real
        // submission id — the upload session id used to PUT the file is a
        // different, ephemeral id and is not what /api/submissions/{id} reads.
        return { submissionId: data.submission_id ?? uploadId };
    }

    async submissionStatus(id: string, signal: AbortSignal): Promise<SubmissionStatus> {
        const res = await this.fetch(`/api/submissions/${id}`, { signal });
        const data = await res.json();
        return {
            id,
            state: data.state || 'Processing',
            revision: '1',
            updatedAt: data.created_at || new Date().toISOString()
        };
    }

    async reviewQueue(signal: AbortSignal): Promise<ReviewTask[]> {
        const res = await this.fetch(`/api/review-tasks`, { signal });
        return res.json();
    }

    async resolveTask(id: string, command: ResolutionCommand): Promise<void> {
        await this.fetch(`/api/review-tasks/${id}/resolve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(command)
        });
    }

    async studentExam(id: string, signal: AbortSignal): Promise<PublishedExam> {
        const res = await this.fetch(`/api/exams/${id}`, { signal });
        return res.json();
    }

    async myExamReport(examId: string, signal: AbortSignal): Promise<MyExamReport> {
        const res = await this.fetch(`/api/me/exams/${examId}/report`, { signal });
        return res.json();
    }

    async cropBlob(_audience: Portal, cropId: string, signal: AbortSignal): Promise<Blob> {
        const res = await this.fetch(`/api/evidence/${cropId}`, { signal });
        return res.blob();
    }
}
