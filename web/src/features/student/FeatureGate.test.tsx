import { describe, it, expect, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { FeatureGate } from './FeatureGate';
import { renderStudent } from '../../test/render';
import * as studentApi from '../../api/student';

vi.mock('../../api/student', async () => {
  const actual = await vi.importActual<typeof import('../../api/student')>('../../api/student');
  return { ...actual, listFeatures: vi.fn() };
});

const disabledEntry = {
  key: 'cognitive.growth' as const,
  title: 'Growth against your own previous best',
  description: 'Each new result compared with your own earlier best.',
  tier: 2 as const,
  status: 'available' as const,
  enabled: false,
};

describe('FeatureGate', () => {
  it('shows the locked notice and sample when disabled', async () => {
    vi.mocked(studentApi.listFeatures).mockResolvedValue({ features: [disabledEntry] });

    renderStudent(
      <FeatureGate feature="cognitive.growth" sample={<p>Sample chart</p>}>
        <p data-testid="real-content">Real content</p>
      </FeatureGate>,
    );

    await waitFor(() => expect(screen.getByTestId('locked-notice')).toBeInTheDocument());
    expect(screen.getByTestId('sample-preview')).toHaveTextContent('Example — not your data');
    expect(screen.getByText('Sample chart')).toBeInTheDocument();
    expect(screen.queryByTestId('real-content')).not.toBeInTheDocument();
  });

  it('renders children and no sample when enabled', async () => {
    vi.mocked(studentApi.listFeatures).mockResolvedValue({
      features: [{ ...disabledEntry, enabled: true }],
    });

    renderStudent(
      <FeatureGate feature="cognitive.growth" sample={<p>Sample chart</p>}>
        <p data-testid="real-content">Real content</p>
      </FeatureGate>,
    );

    await waitFor(() => expect(screen.getByTestId('real-content')).toBeInTheDocument());
    expect(screen.queryByTestId('sample-preview')).not.toBeInTheDocument();
  });

  it('shows retry-worthy error state, not children, when features cannot load', async () => {
    vi.mocked(studentApi.listFeatures).mockRejectedValue(new Error('network down'));

    renderStudent(
      <FeatureGate feature="cognitive.growth" sample={<p>Sample chart</p>}>
        <p data-testid="real-content">Real content</p>
      </FeatureGate>,
    );

    await waitFor(() => expect(screen.getByTestId('feature-gate-error')).toBeInTheDocument(),
      { timeout: 10000 });
    expect(screen.queryByTestId('real-content')).not.toBeInTheDocument();
  });

  it('never renders price or upgrade language', async () => {
    vi.mocked(studentApi.listFeatures).mockResolvedValue({ features: [disabledEntry] });

    const { container } = renderStudent(
      <FeatureGate feature="cognitive.growth" sample={<p>Sample chart</p>}>
        <p>Real content</p>
      </FeatureGate>,
    );

    await waitFor(() => expect(screen.getByTestId('locked-notice')).toBeInTheDocument());
    expect(container.textContent).not.toMatch(/upgrade|premium|price/i);
  });
});
