import { Outlet, Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Sidebar } from './Sidebar';
import { PageLoader } from '../ui/Spinner';

export function AppLayout() {
  const { user, loading } = useAuth();
  if (loading) return <PageLoader />;
  if (!user) return <Navigate to="/login" replace />;
  return (
    <div className="h-screen bg-background flex flex-col md:flex-row overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <main className="flex-1 overflow-y-auto px-4 pt-0 pb-8 md:px-8 w-full animate-fade-in">
          <Outlet />
        </main>
        <footer className="border-t border-border bg-card/30 shrink-0">
          <div className="px-4 py-4 md:px-8 text-center text-xs text-muted-foreground w-full">
            I-PRAMRS &mdash; Intelligent Project Risk Assessment &amp; Mitigation Recommendation System
            &mdash; Cavendish University Zambia &copy; 2026
          </div>
        </footer>
      </div>
    </div>
  );

}


export function AuthLayout() {
  const { user, loading } = useAuth();
  if (loading) return <PageLoader />;
  if (user) return <Navigate to="/dashboard" replace />;
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <div className="flex-1 flex items-center justify-center p-4">
        <Outlet />
      </div>
    </div>
  );
}
