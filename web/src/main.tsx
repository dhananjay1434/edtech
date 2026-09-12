import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider, Navigate, useParams } from 'react-router-dom';
import { Providers } from './app/providers';
import { Shell, RequirePortal } from './app/Shell';
import { HitlQueue } from './features/admin/HitlQueue';
import { AdminConsole } from './features/admin/AdminConsole';
import { StudentExamView } from './features/student/StudentExamView';
import { StudentExamsList } from './features/student/StudentExamsList';
import { CdeApiClient } from './api/client';
import { Runtime } from './api/contracts';
import { initAuth, getToken, hasRole, logout } from './auth';
import './app/styles.css';

await initAuth();

function StudentExamRoute() {
    const { examId } = useParams();
    return examId ? <StudentExamView examId={examId} /> : <Navigate to="/student/exams" replace />;
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
            { index: true, element: <Navigate to="exams" replace /> },
            { path: 'exams', element: <StudentExamsList /> },
            { path: 'exams/:examId', element: <StudentExamRoute /> }
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
