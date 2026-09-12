import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider, Navigate, useParams } from 'react-router-dom';
import { Providers } from './app/providers';
import { Shell, RequirePortal } from './app/Shell';
import { StudentShell } from './app/StudentShell';
import { HitlQueue } from './features/admin/HitlQueue';
import { AdminConsole } from './features/admin/AdminConsole';
import { StudentExamView } from './features/student/StudentExamView';
import { StudentExamsList } from './features/student/StudentExamsList';
import { FeaturesOverview } from './features/student/FeaturesOverview';
import { FeatureGate } from './features/student/FeatureGate';
import { CdeApiClient } from './api/client';
import { Runtime } from './api/contracts';
import { initAuth, getToken, hasRole, logout } from './auth';
import './app/styles.css';

await initAuth();

function StudentExamRoute() {
    const { examId } = useParams();
    return examId ? <StudentExamView examId={examId} /> : <Navigate to="/student/exams" replace />;
}

// Placeholder until its phase lands: the route exists and is gated for real,
// it just has nothing built behind it yet beyond the locked/sample card.
function ComingRoute({ feature, title }: { feature: Parameters<typeof FeatureGate>[0]['feature']; title: string }) {
    return (
        <FeatureGate feature={feature} sample={<p className="text-sm text-muted-foreground">{title} — coming to this portal.</p>}>
            <p className="text-sm text-muted-foreground">{title} is enabled, but not built yet.</p>
        </FeatureGate>
    );
}

const apiClient = new CdeApiClient(async () => getToken() ?? '');
// Note: 'teacher' is deliberately absent - there is no teacher role in this product.
const runtime: Runtime = {
    api: apiClient,
    scope: "dev_tenant",
    portals: [hasRole('admin') && 'admin', hasRole('student') && 'student']
        .filter(Boolean) as Runtime['portals'],
    signOut: async () => { logout(); }
};

function HomeRedirect() {
  if (runtime.portals.includes('admin')) return <Navigate to="/admin/setup" replace />;
  if (runtime.portals.includes('student')) return <Navigate to="/student/exams" replace />;
  return <section role="alert"><h1>No portal available</h1><p>This account has no admin or student role.</p></section>;
}

const router = createBrowserRouter([
  {
    path: '/',
    element: <Providers runtime={runtime}><Shell /></Providers>,
    children: [
      { index: true, element: <HomeRedirect /> },
      {
        path: 'admin',
        element: <RequirePortal role="admin" />,
        children: [
            { index: true, element: <Navigate to="setup" replace /> },
            { path: 'setup', element: <AdminConsole /> },
            { path: 'review', element: <HitlQueue /> }
        ]
      },
      {
        path: 'student',
        element: <RequirePortal role="student" />,
        children: [
            {
                element: <StudentShell />,
                children: [
                    { index: true, element: <Navigate to="exams" replace /> },
                    { path: 'exams', element: <StudentExamsList /> },
                    { path: 'exams/:examId', element: <StudentExamRoute /> },
                    { path: 'growth', element: <ComingRoute feature="cognitive.growth" title="Growth" /> },
                    { path: 'practice', element: <ComingRoute feature="learning.spaced_review" title="Practice" /> },
                    { path: 'plan', element: <ComingRoute feature="learning.planner" title="Study plan" /> },
                    { path: 'features', element: <FeaturesOverview /> },
                ],
            },
        ]
      }
    ]
  }
]);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
);
