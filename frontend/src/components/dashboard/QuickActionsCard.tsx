import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Avatar,
  Grid,
  Divider,
} from '@mui/material';
import {
  PersonAdd as PersonAddIcon,
  CloudSync as CloudSyncIcon,
  Assessment as ReportIcon,
  Shield as SecurityIcon,
  HealthAndSafety as HealthIcon,
  SmartToy as AIIcon,
} from '@mui/icons-material';

import { useAppDispatch } from '@/store';
import { openModal, showSnackbar } from '@/store/slices/uiSlice';

// ============================================
// QUICK ACTIONS CARD COMPONENT
// ============================================

interface QuickAction {
  id: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  action: () => void;
  disabled?: boolean;
  comingSoon?: boolean;
}

const QuickActionsCard: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();

  const quickActions: QuickAction[] = [
    {
      id: 'add-patient',
      label: 'Add Patient',
      description: 'Create new patient record',
      icon: <PersonAddIcon />,
      color: 'primary.main',
      action: () => {
        dispatch(openModal({ modal: 'create-patient' }));
      },
    },
    {
      id: 'sync-iris',
      label: 'Sync IRIS',
      description: 'Trigger data synchronization',
      icon: <CloudSyncIcon />,
      color: 'info.main',
      action: () => {
        navigate('/iris?tab=sync&action=trigger');
      },
    },
    {
      id: 'generate-report',
      label: 'Generate Report',
      description: 'Create compliance report',
      icon: <ReportIcon />,
      color: 'success.main',
      action: () => {
        navigate('/compliance?action=generate');
      },
    },
    {
      id: 'security-scan',
      label: 'Security Scan',
      description: 'Run security audit',
      icon: <SecurityIcon />,
      color: 'warning.main',
      action: () => {
        dispatch(showSnackbar({
          message: 'Security scan initiated',
          severity: 'info',
        }));
      },
    },
    {
      id: 'health-check',
      label: 'Health Check',
      description: 'System diagnostics',
      icon: <HealthIcon />,
      color: 'success.main',
      action: () => {
        navigate('/iris?tab=health');
      },
    },
    {
      id: 'deploy-ai',
      label: 'Deploy AI Bot',
      description: 'Deploy new AI agent',
      icon: <AIIcon />,
      color: 'secondary.main',
      action: () => {
        dispatch(showSnackbar({
          message: 'AI bot deployment coming soon!',
          severity: 'info',
        }));
      },
      comingSoon: true,
    },
  ];

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" alignItems="center" mb={3}>
          <Avatar sx={{ bgcolor: 'secondary.main', mr: 2 }}>
            <SecurityIcon />
          </Avatar>
          <Box>
            <Typography variant="h6" fontWeight={600}>
              Quick Actions
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Common tasks and operations
            </Typography>
          </Box>
        </Box>

        <Grid container spacing={2}>
          {quickActions.map((action, index) => (
            <Grid item xs={12} key={action.id}>
              <Button
                fullWidth
                variant="outlined"
                onClick={action.action}
                disabled={action.disabled || action.comingSoon}
                sx={{
                  justifyContent: 'flex-start',
                  textAlign: 'left',
                  p: 2,
                  height: 'auto',
                  borderColor: action.comingSoon ? 'grey.300' : 'divider',
                  '&:hover': {
                    borderColor: action.comingSoon ? 'grey.300' : action.color,
                    backgroundColor: action.comingSoon ? 'transparent' : 'action.hover',
                  },
                }}
              >
                <Box display="flex" alignItems="center" width="100%">
                  <Avatar
                    sx={{
                      bgcolor: action.comingSoon ? 'grey.300' : action.color,
                      width: 32,
                      height: 32,
                      mr: 2,
                    }}
                  >
                    {action.icon}
                  </Avatar>
                  <Box flexGrow={1}>
                    <Typography 
                      variant="body2" 
                      fontWeight={600}
                      color={action.comingSoon ? 'text.disabled' : 'text.primary'}
                    >
                      {action.label}
                      {action.comingSoon && (
                        <Typography 
                          component="span" 
                          variant="caption" 
                          color="text.secondary"
                          ml={1}
                        >
                          (Coming Soon)
                        </Typography>
                      )}
                    </Typography>
                    <Typography 
                      variant="caption" 
                      color={action.comingSoon ? 'text.disabled' : 'text.secondary'}
                      display="block"
                    >
                      {action.description}
                    </Typography>
                  </Box>
                </Box>
              </Button>
              
              {index < quickActions.length - 1 && (
                <Divider sx={{ my: 1 }} />
              )}
            </Grid>
          ))}
        </Grid>

        <Box mt={3} textAlign="center">
          <Typography variant="caption" color="text.secondary">
            More actions available in each module
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default QuickActionsCard;