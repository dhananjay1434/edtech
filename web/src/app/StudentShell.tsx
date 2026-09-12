// app/StudentShell.tsx
//
// The student portal's own surface: sharper geometry than the admin console
// (calm-precision), and a section nav that is always fully visible — gating
// lives inside each route via FeatureGate, never by hiding the nav item, so
// a student always sees what exists.
import { NavLink, Outlet } from 'react-router-dom';
import { ClipboardList, TrendingUp, Repeat, CalendarRange, Sparkles } from 'lucide-react';
import { useRuntime } from './providers';

const SECTIONS = [
  { to: '/student/exams', label: 'My exams', Icon: ClipboardList },
  { to: '/student/growth', label: 'Growth', Icon: TrendingUp },
  { to: '/student/practice', label: 'Practice', Icon: Repeat },
  { to: '/student/plan', label: 'Plan', Icon: CalendarRange },
  { to: '/student/features', label: 'Features', Icon: Sparkles },
];

export function StudentShell() {
  const { portals } = useRuntime();

  if (!portals.includes('student')) {
    return (
      <section role="alert">
        <h1>Access unavailable</h1>
        <p>Your current account cannot open this portal.</p>
      </section>
    );
  }

  return (
    <div className="student-surface space-y-6">
      <nav aria-label="Student sections" className="flex flex-wrap gap-1 border-b border-border">
        {SECTIONS.map(({ to, label, Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex min-h-11 items-center gap-2 border-b-2 px-3 text-sm ${
                isActive
                  ? 'border-primary font-medium text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`
            }
          >
            <Icon className="h-4 w-4" aria-hidden="true" />
            {label}
          </NavLink>
        ))}
      </nav>
      <Outlet />
    </div>
  );
}
