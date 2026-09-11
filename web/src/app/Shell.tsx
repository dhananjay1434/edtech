// app/Shell.tsx
import { NavLink, Outlet } from 'react-router-dom';
import { useRuntime } from './providers';
import type { Portal } from '../api/contracts';

const entries: Array<{ role: Portal; to: string; label: string }> = [
  { role: 'teacher', to: '/teacher/exams', label: 'Teaching' },
  { role: 'admin', to: '/admin/setup', label: 'Setup' },
  { role: 'admin', to: '/admin/review', label: 'Review queue' },
  { role: 'student', to: '/student/exams', label: 'My exams' }
];

export function RequirePortal({ role }: { role: Portal }) {
  const { portals } = useRuntime();
  if (!portals.includes(role)) {
    return <section role="alert"><h1>Access unavailable</h1>
      <p>Your current account cannot open this portal.</p></section>;
  }
  return <Outlet />;
}

export function Shell() {
  const { portals, signOut } = useRuntime();
  return (
    <div className="min-h-screen bg-background text-foreground">
      <a href="#main" className="skip-link">Skip to content</a>
      <header className="border-b border-border bg-card px-6 py-4">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-6">
          <span className="font-semibold tracking-tight">Cognitive Diagnostic Engine</span>
          <nav aria-label="Portals" className="flex flex-wrap gap-4">
            {entries.filter(x => portals.includes(x.role)).map(x => (
              <NavLink key={x.to} to={x.to}
                className={({ isActive }) => isActive
                  ? 'font-semibold text-primary underline underline-offset-8'
                  : 'text-muted-foreground'}>
                {x.label}
              </NavLink>
            ))}
          </nav>
          <button className="ml-auto" onClick={() => void signOut()}>Sign out</button>
        </div>
      </header>
      <main id="main" tabIndex={-1} className="mx-auto max-w-7xl p-4 md:p-8">
        <Outlet />
      </main>
    </div>
  );
}
