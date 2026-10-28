import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/common/ProtectedRoute';
import AppShell from './components/layout/AppShell';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import JobsList from './pages/JobsList';
import CreateJob from './pages/CreateJob';
import JobDetail from './pages/JobDetail';
import Settings from './pages/Settings';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Auth Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected Application Routes */}
          <Route
            element={
              <ProtectedRoute>
                <AppShell />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/jobs" element={<JobsList />} />
            <Route path="/jobs/new" element={<CreateJob />} />
            <Route path="/jobs/:id" element={<JobDetail />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Route>

          {/* Catch-all Fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
