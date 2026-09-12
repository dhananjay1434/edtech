import { describe, it, expect, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { FeaturesOverview } from './FeaturesOverview';
import { renderStudent, SAMPLE_FEATURES, featuresWith } from '../../test/render';
import * as studentApi from '../../api/student';

vi.mock('../../api/student', async () => {
  const actual = await vi.importActual<typeof import('../../api/student')>('../../api/student');
  return { ...actual, listFeatures: vi.fn() };
});

describe('FeaturesOverview', () => {
  it('lists all ten catalog entries with correct enabled/not-enabled copy', async () => {
    vi.mocked(studentApi.listFeatures).mockResolvedValue(
      featuresWith(['cognitive.growth']),
    );

    renderStudent(<FeaturesOverview />);

    for (const f of SAMPLE_FEATURES) {
      const row = await screen.findByTestId(`feature-overview-${f.key}`);
      if (f.key === 'cognitive.growth') {
        expect(row).toHaveTextContent('Enabled for you');
      } else {
        expect(row).toHaveTextContent('Not enabled for your institute yet');
      }
    }
  });

  it('contains no denylisted text', async () => {
    vi.mocked(studentApi.listFeatures).mockResolvedValue({ features: SAMPLE_FEATURES });

    const { container } = renderStudent(<FeaturesOverview />);

    await waitFor(() => expect(screen.getByTestId('features-overview')).toBeInTheDocument());
    expect(container.textContent).not.toMatch(/upgrade|premium|price|leaderboard/i);
  });
});
