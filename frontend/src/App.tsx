import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, ThemeProvider } from '@mui/material';

import { useAppDispatch, useAppSelector } from './store';
import { initializeAuthFromToken } from './store/slices/authSlice';
import { initializeUIFromStorage, selectTheme } from './store/slices/uiSlice';
import { createAppTheme } from './utils/theme';

// Components
import Layout from './components/common/Layout';
import ProtectedRoute from './components/common/ProtectedRoute';
import AdminRoute from './components/common/AdminRoute';
import LoadingScreen from './components/common/LoadingScreen';
import NotificationCenter from './components/common/NotificationCenter';
import GlobalSnackbar from './components/common/GlobalSnackbar';

// Pages
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import DashboardPage from './pages/dashboard/DashboardPage';
import PatientListPage from './pages/patients/PatientListPage';
import PatientDetailPage from './pages/patients/PatientDetailPage';
import PatientFormPage from './pages/patients/PatientFormPage';
import SymptomInputPage from './pages/patients/SymptomInputPage';
import HealthcareRecordsPage from './pages/healthcare/HealthcareRecordsPage';
import IRISIntegrationPage from './pages/iris/IRISIntegrationPage';
import AuditLogsPage from './pages/audit/AuditLogsPage';
import CompliancePage from './pages/compliance/CompliancePage';
import SettingsPage from './pages/settings/SettingsPage';

// Killer AI Features - Competition Demo
import VoiceClinicalInput from './components/VoiceClinicalInput';
import PredictiveHealthTrajectory from './components/PredictiveHealthTrajectory';
import IntelligentPHIGuardian from './components/IntelligentPHIGuardian';
import PatientDailyCheckin from './components/PatientDailyCheckin';
import AIAgentsPage from './pages/ai-agents/AIAgentsPage';
import DocumentManagementPage from './pages/documents/DocumentManagementPage';
import DoctorHistoryPage from './pages/doctor/DoctorHistoryPage';
import DoctorTimelinePage from './pages/doctor/DoctorTimelinePage';
import NotFoundPage from './pages/NotFoundPage';

// ============================================
// MAIN APP COMPONENT
// ============================================

const App: React.FC = () => {
  const dispatch = useAppDispatch();
  const theme = useAppSelector(selectTheme);
  const isAuthenticated = useAppSelector((state) => state.auth.isAuthenticated);
  const authLoading = useAppSelector((state) => state.auth.loading);

  // Initialize app on mount
  useEffect(() => {
    try {
      console.log('Initializing app...');
      dispatch(initializeUIFromStorage());
      dispatch(initializeAuthFromToken());
      console.log('App initialized successfully');
    } catch (error) {
      console.error('App initialization failed:', error);
    }
  }, [dispatch]);

  // Update body background based on theme
  useEffect(() => {
    const body = document.body;
    if (theme === 'dark') {
      body.style.backgroundColor = '#121212';
      body.style.color = '#ffffff';
      body.classList.add('dark-theme');
    } else {
      body.style.backgroundColor = '#fafafa';
      body.style.color = '#212121';
      body.classList.remove('dark-theme');
    }
  }, [theme]);

  // Show loading screen while checking authentication
  if (authLoading === 'loading') {
    return <LoadingScreen />;
  }

  return (
    <ThemeProvider theme={createAppTheme(theme)}>
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Routes>
          {/* Test Route */}
          <Route path="/test" element={<div style={{padding: '20px', fontSize: '18px'}}>Test Page - App is working!</div>} />
          
          {/* Debug Route */}
          <Route path="/debug" element={
            <div style={{padding: '20px'}}>
              <h1>Debug Info</h1>
              <p>Auth State: {JSON.stringify({isAuthenticated, authLoading})}</p>
              <p>Theme: {theme}</p>
              <button onClick={() => console.log('Redux State:', {isAuthenticated, authLoading, theme})}>
                Log State to Console
              </button>
            </div>
          } />
          
          {/* Public Routes */}
          <Route path="/symptoms" element={<SymptomInputPage />} />
          <Route path="/doctor-demo" element={<DoctorHistoryPage />} />
          <Route path="/timeline-demo" element={<DoctorTimelinePage />} />
          
          {/* Killer AI Features - Competition Demo Routes */}
          <Route path="/ai/voice-clinical" element={<VoiceClinicalInput />} />
          <Route path="/ai/health-trajectories" element={<PredictiveHealthTrajectory />} />
          <Route path="/ai/phi-guardian" element={<IntelligentPHIGuardian />} />
          
          {/* Patient Daily Check-in - Russian language with HIPAA compliance */}
          <Route path="/daily-checkin" element={<PatientDailyCheckin patientId="P001" patientName="Sarah Johnson" />} />
          <Route
            path="/login"
            element={
              isAuthenticated ? (
                <Navigate to="/dashboard" replace />
              ) : (
                <LoginPage />
              )
            }
          />
          <Route
            path="/register"
            element={
              isAuthenticated ? (
                <Navigate to="/dashboard" replace />
              ) : (
                <RegisterPage />
              )
            }
          />

          {/* Protected Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            {/* Dashboard */}
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />

            {/* Patient Management */}
            <Route path="patients" element={<PatientListPage />} />
            <Route path="patients/new" element={<PatientFormPage />} />
            <Route path="patients/symptoms" element={<SymptomInputPage />} />
            <Route path="patients/:id" element={<PatientDetailPage />} />
            <Route path="patients/:id/edit" element={<PatientFormPage />} />
            
            {/* Patient Daily Check-in (Protected) */}
            <Route path="patients/daily-checkin" element={<PatientDailyCheckin patientId="P001" patientName="Sarah Johnson" />} />

            {/* Healthcare Records */}
            <Route path="healthcare" element={<HealthcareRecordsPage />} />

            {/* Document Management */}
            <Route path="documents" element={<DocumentManagementPage />} />

            {/* IRIS Integration */}
            <Route path="iris" element={<IRISIntegrationPage />} />

            {/* Doctor Interface */}
            <Route path="doctor/history" element={<DoctorHistoryPage />} />
            <Route path="doctor/timeline" element={<DoctorTimelinePage />} />

            {/* Audit & Compliance */}
            <Route path="audit" element={<AuditLogsPage />} />
            <Route path="compliance" element={<CompliancePage />} />

            {/* AI Agents (Admin Only) */}
            <Route 
              path="ai-agents" 
              element={
                <AdminRoute feature="AI Agent Management Platform">
                  <AIAgentsPage />
                </AdminRoute>
              } 
            />

            {/* Settings */}
            <Route path="settings" element={<SettingsPage />} />

            {/* Catch all */}
            <Route path="*" element={<NotFoundPage />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>

        {/* Global Components */}
        <NotificationCenter />
        <GlobalSnackbar />
      </Box>
    </ThemeProvider>
  );
};

export default App;