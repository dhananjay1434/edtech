// features/student/RoughSheetDropzone.tsx
//
// Attach a photo of rough work, or explicitly say there isn't any — distinct
// states, so the diagnosis pipeline abstains rather than waiting forever.
// Never selectable by URL or body: the backend resolves the sheet from the
// authenticated student's own account.
import { useEffect, useRef, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { uploadRoughSheet, declareNoRoughSheet, StudentApiError } from '../../api/student';
import { Button } from '../../components/ui/button';
import { Alert, AlertDescription } from '../../components/ui/alert';

const MAX_BYTES = 15 * 1024 * 1024;
const ALLOWED_TYPES = ['image/png', 'image/jpeg'];

export function RoughSheetDropzone({ examId, roughSheetStatus }: {
  examId: string;
  roughSheetStatus: string | null;
}) {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState('');
  const [error, setError] = useState('');
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!file) { setPreview(''); return; }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const invalidate = () => void queryClient.invalidateQueries({ queryKey: ['student', 'diagnosis', examId] });

  const upload = useMutation({
    mutationFn: (f: File) => uploadRoughSheet(examId, f),
    onSuccess: () => { setFile(null); if (input.current) input.current.value = ''; invalidate(); },
  });
  const declareNone = useMutation({
    mutationFn: () => declareNoRoughSheet(examId),
    onSuccess: invalidate,
  });

  const busy = upload.isPending || declareNone.isPending;

  function select(next?: File) {
    if (!next || busy) return;
    setError('');
    if (!ALLOWED_TYPES.includes(next.type) || !next.size || next.size > MAX_BYTES) {
      setError('Choose a non-empty PNG or JPEG image, up to 15 MB.');
      if (input.current) input.current.value = '';
      return;
    }
    setFile(next);
  }

  function errorMessage(err: unknown): string {
    if (err instanceof StudentApiError) return err.detail;
    return 'Could not save your rough work. Please try again.';
  }

  return (
    <section className="space-y-3" data-testid="rough-sheet-panel">
      <h3 className="text-sm font-medium" data-testid="rough-sheet-title">Your rough work</h3>
      <div className="rounded-lg border border-dashed border-border p-4" data-testid="rough-sheet-dropzone"
        onDragOver={event => event.preventDefault()}
        onDrop={event => { event.preventDefault(); select(event.dataTransfer.files[0]); }}>
        <label htmlFor="rough-sheet-file" className="block text-sm font-medium" data-testid="rough-sheet-file-label">
          Attach a photo of your full rough sheet
        </label>
        <p className="my-2 text-xs text-muted-foreground" data-testid="rough-sheet-file-requirements">
          PNG or JPEG · up to 15 MB
        </p>
        <input ref={input} id="rough-sheet-file" data-testid="rough-sheet-file-input" type="file"
          accept="image/png,image/jpeg" disabled={busy} onChange={event => select(event.target.files?.[0])} />
        {file && <p className="mt-3 break-words text-sm" data-testid="rough-sheet-selected-file">{file.name}</p>}
        {preview && (
          <img className="mt-4 max-w-sm rounded-md" src={preview} alt="Rough sheet selected for upload"
            data-testid="rough-sheet-preview" />
        )}
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <Button data-testid="rough-sheet-upload-button" disabled={!file || busy}
          onClick={() => file && upload.mutate(file)}>
          {upload.isPending ? 'Saving…' : roughSheetStatus === 'uploaded' ? 'Replace rough sheet' : 'Upload rough sheet'}
        </Button>
        <Button variant="outline" data-testid="rough-sheet-none-button" disabled={busy}
          onClick={() => declareNone.mutate()}>
          {declareNone.isPending ? 'Saving…' : 'I don’t have rough work'}
        </Button>
      </div>
      {upload.isSuccess && (
        <p role="status" className="text-sm text-success" data-testid="rough-sheet-upload-success">
          Saved. Your working will be looked at once your result is published.
        </p>
      )}
      {declareNone.isSuccess && (
        <p role="status" className="text-sm text-muted-foreground" data-testid="rough-sheet-none-success">
          Noted — we won’t wait on rough work for this exam.
        </p>
      )}
      {(error || upload.isError || declareNone.isError) && (
        <Alert variant="destructive" data-testid="rough-sheet-error">
          <AlertDescription>
            {error || errorMessage(upload.error) || errorMessage(declareNone.error)}
          </AlertDescription>
        </Alert>
      )}
    </section>
  );
}
