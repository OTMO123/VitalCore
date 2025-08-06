import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAppSelector } from '@/store';
import { selectIsAuthenticated, selectAuthLoading } from '@/store/slices/authSlice';
import LoadingScreen from './LoadingScreen';

// ============================================
// PROTECTED ROUTE COMPONENT
// ============================================

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: string;
  requiredPermission?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole,
  requiredPermission,
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

  // Check role-based access
  if (requiredRole && user?.role?.name !== requiredRole) {
    return (
      <Navigate 
        to="/dashboard" 
        state={{ 
          error: `Access denied. Required role: ${requiredRole}` 
        }} 
        replace 
      />
    );
  }

  // Check permission-based access
  if (requiredPermission && user?.permissions) {
    const hasPermission = user.permissions.includes(requiredPermission);
    if (!hasPermission) {
      return (
        <Navigate 
          to="/dashboard" 
          state={{ 
            error: `Access denied. Required permission: ${requiredPermission}` 
          }} 
          replace 
        />
      );
    }
  }

  return <>{children}</>;
};

export default ProtectedRoute;