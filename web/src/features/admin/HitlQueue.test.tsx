import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HitlQueue } from './HitlQueue';
import { Providers } from '../../app/providers';
import type { CdeApi, ReviewTask, Runtime } from '../../api/contracts';

function makeRuntime(overrides: Partial<CdeApi> = {}): Runtime {
  const task: ReviewTask = {
    id: 'task1',
    cropId: 'crop1',
    revision: '1',
    kind: 'ambiguous',
    choices: [
      { code: 'A', label: 'Option A' },
      { code: 'B', label: 'Option B' },
      { code: 'C', label: 'Option C' },
      { code: 'D', label: 'Option D' },
    ],
    suggestedCode: 'B',
  };
  const api: CdeApi = {
    accessToken: async () => 'token',
    prepareUpload: vi.fn(),
    completeUpload: vi.fn(),
    submissionStatus: vi.fn(),
    reviewQueue: vi.fn(async () => [task]),
    resolveTask: vi.fn(async () => {}),
    studentExam: vi.fn(),
    myExamReport: vi.fn(),
    cropBlob: vi.fn(async () => new Blob(['fake'], { type: 'image/png' })),
    ...overrides,
  };
  return { api, scope: 'test', portals: ['admin'], signOut: async () => {} };
}

describe('HitlQueue keyboard-driven review', () => {
  it('lets an admin select an option and confirm using only the keyboard', async () => {
    const runtime = makeRuntime();
    render(<Providers runtime={runtime}><HitlQueue /></Providers>);

    const img = await screen.findByAltText('Scanned handwritten answer');
    fireEvent.load(img); // jsdom never fires real image load events

    const user = userEvent.setup();
    await user.keyboard('b'); // selects option B, no mouse involved
    expect(screen.getByTestId('option-B')).toBeChecked();

    await waitFor(() => expect(screen.getByTestId('submit-resolution')).not.toBeDisabled());
    await user.keyboard('{Enter}');

    await waitFor(() => expect(runtime.api.resolveTask).toHaveBeenCalledWith('task1', expect.objectContaining({
      decisionCode: 'B',
      expectedRevision: '1',
    })));
  });

  it('requires a reason when overriding the suggested reading', async () => {
    const runtime = makeRuntime();
    render(<Providers runtime={runtime}><HitlQueue /></Providers>);

    const img = await screen.findByAltText('Scanned handwritten answer');
    fireEvent.load(img);

    const user = userEvent.setup();
    await user.keyboard('c'); // C != suggested B, so a reason is required
    expect(screen.getByTestId('submit-resolution')).toBeDisabled();
  });
});
