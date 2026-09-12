import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { StudentShell } from './StudentShell';
import { Providers } from './providers';
import { makeRuntime } from '../test/render';

function renderShell(route: string, portals: ('admin' | 'student')[] = ['student']) {
  const runtime = makeRuntime({}, portals);
  return render(
    <Providers runtime={runtime}>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route element={<StudentShell />}>
            <Route path="/student/exams" element={<p>Exams page</p>} />
            <Route path="/student/growth" element={<p>Growth page</p>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </Providers>,
  );
}

describe('StudentShell', () => {
  it('renders five section links with icons', () => {
    renderShell('/student/exams');
    const nav = screen.getByRole('navigation', { name: 'Student sections' });
    for (const label of ['My exams', 'Growth', 'Practice', 'Plan', 'Features']) {
      expect(nav).toHaveTextContent(label);
    }
  });

  it('marks the active section with aria-current', () => {
    renderShell('/student/growth');
    const active = screen.getByRole('link', { name: /Growth/ });
    expect(active).toHaveAttribute('aria-current', 'page');
    const inactive = screen.getByRole('link', { name: /My exams/ });
    expect(inactive).not.toHaveAttribute('aria-current');
  });

  it('shows "Access unavailable" when the account has no student portal', () => {
    renderShell('/student/exams', ['admin']);
    expect(screen.getByRole('alert')).toHaveTextContent('Access unavailable');
    expect(screen.queryByText('Exams page')).not.toBeInTheDocument();
  });
});
