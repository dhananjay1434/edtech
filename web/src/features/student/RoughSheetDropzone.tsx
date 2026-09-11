import { useEffect, useRef, useState } from 'react';
import { RoughSubmission, uploadRoughSheet } from '../../api/roughSheets';
// mock Api
const mockApi: any = {};

const statusLabels: Record<string, string> = {
  not_uploaded: 'No rough sheet attached', queued: 'Rough sheet saved. Analysis queued.',
  uploading: 'Saving rough sheet...', processing: 'Analyzing your rough sheet...',
  awaiting_grading: 'Rough sheet saved. Waiting for OMR grading.',
  completed: 'Rough sheet analysis complete.', blocked: 'Rough sheet saved. Analysis unavailable.',
  failed: 'Rough sheet saved. Analysis could not be completed.',
};

export function RoughSheetDropzone({ examId, submission, onUploaded }: {
  examId: string; submission: RoughSubmission; onUploaded: () => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const input = useRef<HTMLInputElement>(null);
  const pending = busy || ['uploading', 'queued', 'processing'].includes(submission.analysis_status);
  useEffect(() => {
    if (!file) { setPreview(''); return; }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  function select(next?: File) {
    if (!next || pending) return;
    setError(''); setMessage(''); setFile(null);
    if (!['image/png', 'image/jpeg'].includes(next.type) || !next.size || next.size > 15 * 1024 * 1024) {
      setError('Choose a non-empty PNG or JPEG image, up to 15 MB.');
      if (input.current) input.current.value = '';
      return;
    }
    setFile(next);
  }

  async function upload() {
    if (!file || pending) return;
    setBusy(true); setError(''); setMessage('');
    try {
      await uploadRoughSheet(mockApi, file, examId, submission.submission_id);
      setMessage('Rough sheet saved.'); setFile(null);
      if (input.current) input.current.value = '';
      onUploaded();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Upload failed. Please retry.');
    } finally { setBusy(false); }
  }

  return <section className="space-y-4" data-testid="rough-sheet-panel">
    <h2 className="text-lg font-semibold" data-testid="rough-sheet-title">Rough work</h2>
    <p className="text-sm text-slate-600" role="status" data-testid="rough-sheet-analysis-status">
      {statusLabels[submission.analysis_status] || submission.analysis_status}
    </p>
    <div className="panel border-dashed p-4" data-testid="rough-sheet-dropzone"
      onDragOver={event => event.preventDefault()}
      onDrop={event => { event.preventDefault(); select(event.dataTransfer.files[0]); }}>
      <label htmlFor="rough-sheet-file" className="block font-medium" data-testid="rough-sheet-file-label">Attach your full rough sheet</label>
      <p className="my-2 text-sm text-slate-500" data-testid="rough-sheet-file-requirements">PNG or JPEG · Up to 15 MB</p>
      <input ref={input} id="rough-sheet-file" data-testid="rough-sheet-file-input" type="file"
        accept="image/png,image/jpeg" disabled={pending} onChange={event => select(event.target.files?.[0])} />
      {file && <p className="mt-3 break-words text-sm" data-testid="rough-sheet-selected-file">{file.name}</p>}
      {preview && <img className="rough-sheet-preview mt-4 max-w-sm" src={preview} alt="Full rough sheet selected for upload" data-testid="rough-sheet-preview" />}
    </div>
    <button className="bg-indigo-600 text-white px-4 py-2 rounded-md" data-testid="rough-sheet-upload-button" disabled={!file || pending} onClick={() => void upload()}>
      {busy ? 'Saving...' : submission.rough_sheet_path ? 'Replace rough sheet' : 'Upload rough sheet'}
    </button>
    {message && <p role="status" className="text-green-600" data-testid="rough-sheet-upload-success">{message}</p>}
    {(error || submission.analysis_error) && <p className="text-red-800" role="alert" data-testid="rough-sheet-error">{error || submission.analysis_error}</p>}
  </section>;
}
