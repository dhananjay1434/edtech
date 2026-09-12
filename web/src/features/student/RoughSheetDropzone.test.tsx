import { describe, it, expect, vi } from 'vitest';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RoughSheetDropzone } from './RoughSheetDropzone';
import { renderStudent } from '../../test/render';
import * as studentApi from '../../api/student';

vi.mock('../../api/student', async () => {
  const actual = await vi.importActual<typeof import('../../api/student')>('../../api/student');
  return { ...actual, uploadRoughSheet: vi.fn(), declareNoRoughSheet: vi.fn() };
});

function pngFile(name = 'rough.png') {
  return new File(['fake'], name, { type: 'image/png' });
}

describe('RoughSheetDropzone', () => {
  it('rejects a non-image file dropped onto the zone, without calling the API', () => {
    // A real <input accept="image/*"> silently filters non-matching files
    // before onChange ever fires, so drag-and-drop is what exercises this
    // component's own client-side validation.
    renderStudent(<RoughSheetDropzone examId="e1" roughSheetStatus={null} />);
    const dropzone = screen.getByTestId('rough-sheet-dropzone');
    const pdf = new File(['%PDF'], 'rough.pdf', { type: 'application/pdf' });

    fireEvent.drop(dropzone, { dataTransfer: { files: [pdf] } });

    expect(screen.getByTestId('rough-sheet-error')).toHaveTextContent(/PNG or JPEG/);
    expect(studentApi.uploadRoughSheet).not.toHaveBeenCalled();
  });

  it('uploads a selected PNG and shows a success message', async () => {
    vi.mocked(studentApi.uploadRoughSheet).mockResolvedValue({ status: 'uploaded' });
    renderStudent(<RoughSheetDropzone examId="e1" roughSheetStatus={null} />);

    const input = screen.getByTestId('rough-sheet-file-input');
    await userEvent.upload(input, pngFile());
    await userEvent.click(screen.getByTestId('rough-sheet-upload-button'));

    await waitFor(() => expect(studentApi.uploadRoughSheet).toHaveBeenCalledWith('e1', expect.any(File)));
    await waitFor(() => expect(screen.getByTestId('rough-sheet-upload-success')).toBeInTheDocument());
  });

  it('the "no rough work" button calls declareNoRoughSheet', async () => {
    vi.mocked(studentApi.declareNoRoughSheet).mockResolvedValue({ status: 'none_provided' });
    renderStudent(<RoughSheetDropzone examId="e1" roughSheetStatus={null} />);

    await userEvent.click(screen.getByTestId('rough-sheet-none-button'));

    await waitFor(() => expect(studentApi.declareNoRoughSheet).toHaveBeenCalledWith('e1'));
    await waitFor(() => expect(screen.getByTestId('rough-sheet-none-success')).toBeInTheDocument());
  });
});
