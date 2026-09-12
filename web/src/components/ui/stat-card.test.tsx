import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { StatCard } from './stat-card';

describe('StatCard', () => {
  it('renders "Not recorded" for a missing value', () => {
    render(<StatCard label="Time per question" value={{ notRecorded: true }}
      context="Not tracked by your institute yet" action={{ label: 'Learn more', onClick: vi.fn() }} />);
    expect(screen.getByText('Not recorded')).toBeInTheDocument();
  });

  it('always renders context and an action', () => {
    render(<StatCard label="Correct" value="4" context="of 8 questions" action={{ label: 'See detail', onClick: vi.fn() }} />);
    expect(screen.getByTestId('stat-card-context')).toHaveTextContent('of 8 questions');
    expect(screen.getByTestId('stat-card-action')).toHaveTextContent('See detail');
  });

  it('supports a link action', () => {
    render(
      <MemoryRouter>
        <StatCard label="Correct" value="4" context="of 8 questions" action={{ label: 'Open growth', to: '/student/growth' }} />
      </MemoryRouter>,
    );
    expect(screen.getByTestId('stat-card-action')).toHaveAttribute('href', '/student/growth');
  });
});
