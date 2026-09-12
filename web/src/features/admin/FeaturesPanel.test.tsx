import { describe, it, expect, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FeaturesPanel } from './FeaturesPanel';
import { renderStudent, SAMPLE_FEATURES } from '../../test/render';
import * as adminApi from '../../api/admin';

vi.mock('../../api/admin', async () => {
  const actual = await vi.importActual<typeof import('../../api/admin')>('../../api/admin');
  return { ...actual, getFeatures: vi.fn(), putFeatures: vi.fn() };
});

describe('FeaturesPanel', () => {
  it('lists every catalog entry with a switch', async () => {
    vi.mocked(adminApi.getFeatures).mockResolvedValue({ features: SAMPLE_FEATURES });

    renderStudent(<FeaturesPanel />);

    await waitFor(() =>
      expect(screen.getByTestId(`feature-switch-${SAMPLE_FEATURES[0]!.key}`)).toBeInTheDocument());
    for (const f of SAMPLE_FEATURES) {
      expect(screen.getByTestId(`feature-switch-${f.key}`)).toBeInTheDocument();
    }
  });

  it('toggling a switch calls putFeatures with only the changed key', async () => {
    vi.mocked(adminApi.getFeatures).mockResolvedValue({ features: SAMPLE_FEATURES });
    vi.mocked(adminApi.putFeatures).mockResolvedValue({ features: SAMPLE_FEATURES });

    renderStudent(<FeaturesPanel />);

    const target = SAMPLE_FEATURES[0]!;
    const toggle = await screen.findByTestId(`feature-switch-${target.key}`);
    await userEvent.click(toggle);

    await waitFor(() => expect(adminApi.putFeatures).toHaveBeenCalledWith({ [target.key]: true }));
  });
});
