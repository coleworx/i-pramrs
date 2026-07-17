import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './components/ui/Toast';
import { AppLayout, AuthLayout } from './components/layout/AppLayout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import NewProject from './pages/NewProject';
import ProjectDetail from './pages/ProjectDetail';
import LogRisk from './pages/LogRisk';
import RiskDetail from './pages/RiskDetail';
import EditProject from './pages/EditProject';
import EditRisk from './pages/EditRisk';


export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ToastProvider>
          <BrowserRouter>
            <Routes>
              {/* Auth routes (redirect if logged in) */}
              <Route element={<AuthLayout />}>
                <Route path="/login"    element={<Login />} />
                <Route path="/register" element={<Register />} />
              </Route>

              {/* Protected app routes */}
              <Route element={<AppLayout />}>
                <Route path="/dashboard"           element={<Dashboard />} />
                <Route path="/projects"            element={<Projects />} />
                <Route path="/projects/new"        element={<NewProject />} />
                <Route path="/projects/:id"        element={<ProjectDetail />} />
                <Route path="/projects/:id/edit"   element={<EditProject />} />
                <Route path="/risks/new/:projectId" element={<LogRisk />} />
                <Route path="/risks/:id"           element={<RiskDetail />} />
                <Route path="/risks/:id/edit"      element={<EditRisk />} />
              </Route>

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/login" replace />} />
            </Routes>
          </BrowserRouter>
        </ToastProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
