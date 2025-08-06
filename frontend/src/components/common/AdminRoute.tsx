import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAppSelector } from '@/store';
import { selectIsAuthenticated, selectAuthLoading } from '@/store/slices/authSlice';
import { Alert, Box, Typography, Paper, Button } from '@mui/material';
import { Security as SecurityIcon, Dashboard as DashboardIcon } from '@mui/icons-material';
import LoadingScreen from './LoadingScreen';

// ============================================
// ADMIN-ONLY ROUTE COMPONENT
// ============================================

interface AdminRouteProps {
  children: React.ReactNode;
  requiredPermission?: string;
  feature?: string;
}

const AdminRoute: React.FC<AdminRouteProps> = ({
  children,
  requiredPermission,
  feature = "this feature",
}) => {
  const location = useLocation();
  const isAuthenticated = useAppSelector(selectIsAuthenticated);
  const authLoading = useAppSelector(selectAuthLoading);
  const user = useAppSelector((state) => state.auth.user);

  // Show loading while checking authentication
  if (authLoading === 'loading') {
    return <LoadingScreen />;
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check if user is admin
  const userRoleString = user?.role?.name || user?.role;
  const isAdmin = userRoleString === 'admin' || userRoleString === 'ADMIN';
  
  if (!isAdmin) {
    return (
      <Box sx={{ p: 3, maxWidth: 600, mx: 'auto', mt: 8 }}>
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <SecurityIcon sx={{ fontSize: 64, color: 'error.main', mb: 2 }} />
          
          <Typography variant="h4" fontWeight={600} gutterBottom color="error.main">
            Access Restricted
          </Typography>
          
          <Typography variant="h6" color="text.secondary" mb={3}>
            Administrator Access Required
          </Typography>
          
          <Alert severity="error" sx={{ mb: 3 }}>
            <Typography variant="body1">
              <strong>Access Denied:</strong> {feature} requires administrator privileges for security and compliance reasons.
            </Typography>
            <Box mt={2}>
              <Typography variant="body2" color="text.secondary">
                • Current role: <strong>{user?.role?.name || user?.role || 'User'}</strong>
                <br />
                • Required role: <strong>Administrator</strong>
                <br />
                • Contact your system administrator to request access
              </Typography>
            </Box>
          </Alert>

          <Typography variant="body2" color="text.secondary" mb={3}>
            This restriction is in place to maintain SOC2 Type 2 compliance and protect sensitive healthcare data.
          </Typography>

          <Button
            variant="contained"
            startIcon={<DashboardIcon />}
            href="/dashboard"
            size="large"
          >
            Return to Dashboard
          </Button>
        </Paper>
      </Box>
    );
  }

  // Check permission-based access if specified
  if (requiredPermission && user?.permissions) {
    const hasPermission = user.permissions.includes(requiredPermission);
    if (!hasPermission) {
      return (
        <Box sx={{ p: 3, maxWidth: 600, mx: 'auto', mt: 8 }}>
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <SecurityIcon sx={{ fontSize: 64, color: 'warning.main', mb: 2 }} />
            
            <Typography variant="h5" fontWeight={600} gutterBottom color="warning.main">
              Insufficient Permissions
            </Typography>
            
            <Alert severity="warning" sx={{ mb: 3 }}>
              <Typography variant="body1">
                You need the <strong>{requiredPermission}</strong> permission to access {feature}.
              </Typography>
            </Alert>

            <Button
              variant="contained"
              startIcon={<DashboardIcon />}
              href="/dashboard"
            >
              Return to Dashboard
            </Button>
          </Paper>
        </Box>
      );
    }
  }

  return <>{children}</>;
};

export default AdminRoute;