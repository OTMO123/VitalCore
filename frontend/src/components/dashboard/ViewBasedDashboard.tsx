import React from 'react';
import { Box, Card, CardContent, Typography, Alert } from '@mui/material';
import {
  AdminPanelSettings as AdminIcon,
  LocalHospital as DoctorIcon,
  Person as PatientIcon,
} from '@mui/icons-material';

import { useAppSelector } from '@/store';
import { selectCurrentView } from '@/store/slices/viewSlice';

// Import your existing dashboard component
import DashboardPageContent from './DashboardPageContent';

const ViewBasedDashboard: React.FC = () => {
  const currentView = useAppSelector(selectCurrentView);

  const renderViewContent = () => {
    switch (currentView) {
      case 'admin':
        return <DashboardPageContent />;
      
      case 'doctor':
        return (
          <Box sx={{ width: '100%', maxWidth: '1200px' }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              <Box display="flex" alignItems="center" gap={1}>
                <DoctorIcon />
                <Typography variant="body2">
                  You are viewing the Healthcare Provider dashboard. This interface is optimized for clinical workflows and patient care.
                </Typography>
              </Box>
            </Alert>
            
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 6 }}>
                <DoctorIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
                <Typography variant="h4" gutterBottom>
                  Healthcare Provider Dashboard
                </Typography>
                <Typography variant="body1" color="text.secondary" mb={3}>
                  Clinical workflows, patient management, and healthcare analytics
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  This specialized view will include:
                </Typography>
                <Box component="ul" sx={{ textAlign: 'left', maxWidth: 400, mx: 'auto', mt: 2 }}>
                  <li>Patient appointment management</li>
                  <li>Clinical decision support tools</li>
                  <li>Medical record access</li>
                  <li>Treatment planning interface</li>
                  <li>Healthcare analytics and insights</li>
                </Box>
              </CardContent>
            </Card>
          </Box>
        );
      
      case 'patient':
        return (
          <Box sx={{ width: '100%', maxWidth: '1200px' }}>
            <Alert severity="success" sx={{ mb: 3 }}>
              <Box display="flex" alignItems="center" gap={1}>
                <PatientIcon />
                <Typography variant="body2">
                  You are viewing the Patient Portal. This interface provides secure access to personal health information.
                </Typography>
              </Box>
            </Alert>
            
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 6 }}>
                <PatientIcon sx={{ fontSize: 64, color: 'secondary.main', mb: 2 }} />
                <Typography variant="h4" gutterBottom>
                  Patient Portal Dashboard
                </Typography>
                <Typography variant="body1" color="text.secondary" mb={3}>
                  Your personal health information and care management
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  This personalized view will include:
                </Typography>
                <Box component="ul" sx={{ textAlign: 'left', maxWidth: 400, mx: 'auto', mt: 2 }}>
                  <li>Personal health records</li>
                  <li>Appointment scheduling</li>
                  <li>Test results and reports</li>
                  <li>Medication management</li>
                  <li>Health tracking and goals</li>
                </Box>
              </CardContent>
            </Card>
          </Box>
        );
      
      default:
        return <DashboardPageContent />;
    }
  };

  return (
    <Box sx={{ 
      width: '100%', 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center',
      justifyContent: 'center' 
    }}>
      {currentView !== 'admin' && (
        <Box sx={{ mb: 2, maxWidth: '1200px', width: '100%' }}>
          <Alert severity="warning">
            <Typography variant="body2">
              <strong>Admin View Override:</strong> You are currently viewing the {currentView} dashboard as an administrator. 
              Use the view switcher in the header to return to the admin dashboard.
            </Typography>
          </Alert>
        </Box>
      )}
      
      {renderViewContent()}
    </Box>
  );
};

export default ViewBasedDashboard;