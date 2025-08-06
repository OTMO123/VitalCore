import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Avatar,
  Chip,
  IconButton,
  Tooltip,
  Divider,
} from '@mui/material';
import {
  PersonAdd as PersonAddIcon,
  Login as LoginIcon,
  Sync as SyncIcon,
  Shield as SecurityIcon,
  Shield as ShieldIcon,
  MoreVert as MoreVertIcon,
  AccessTime as TimeIcon,
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';

// ============================================
// RECENT ACTIVITY CARD COMPONENT
// ============================================

interface ActivityItem {
  id: string;
  type: 'patient_created' | 'user_login' | 'sync_completed' | 'audit_event' | 'phi_access';
  description: string;
  timestamp: string;
  user?: string;
  severity?: 'info' | 'warning' | 'error' | 'success';
}

interface RecentActivityCardProps {
  activities: ActivityItem[];
  loading?: boolean;
  maxItems?: number;
}

const RecentActivityCard: React.FC<RecentActivityCardProps> = ({
  activities,
  loading = false,
  maxItems = 5,
}) => {
  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'patient_created':
        return <PersonAddIcon />;
      case 'user_login':
        return <LoginIcon />;
      case 'sync_completed':
        return <SyncIcon />;
      case 'audit_event':
        return <SecurityIcon />;
      case 'phi_access':
        return <ShieldIcon />;
      default:
        return <SecurityIcon />;
    }
  };

  const getActivityColor = (type: string, severity?: string) => {
    if (severity) {
      switch (severity) {
        case 'success':
          return 'success.main';
        case 'warning':
          return 'warning.main';
        case 'error':
          return 'error.main';
        default:
          return 'info.main';
      }
    }

    switch (type) {
      case 'patient_created':
        return 'success.main';
      case 'user_login':
        return 'info.main';
      case 'sync_completed':
        return 'primary.main';
      case 'audit_event':
        return 'warning.main';
      case 'phi_access':
        return 'error.main';
      default:
        return 'grey.500';
    }
  };

  const getSeverityChip = (severity?: string) => {
    if (!severity) return null;

    const colors = {
      success: 'success',
      warning: 'warning',
      error: 'error',
      info: 'info',
    };

    return (
      <Chip
        label={severity.toUpperCase()}
        size="small"
        color={colors[severity as keyof typeof colors] as any}
        variant="outlined"
        sx={{ fontSize: '0.625rem', height: 20 }}
      />
    );
  };

  const displayActivities = activities.slice(0, maxItems);

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center">
            <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
              <TimeIcon />
            </Avatar>
            <Box>
              <Typography variant="h6" fontWeight={600}>
                Recent Activity
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Latest system events and user actions
              </Typography>
            </Box>
          </Box>
          
          <Tooltip title="View all activities">
            <IconButton size="small" aria-label="View all activities">
              <MoreVertIcon />
            </IconButton>
          </Tooltip>
        </Box>

        {loading ? (
          <Box display="flex" justifyContent="center" py={4}>
            <Typography variant="body2" color="text.secondary">
              Loading recent activities...
            </Typography>
          </Box>
        ) : displayActivities.length === 0 ? (
          <Box textAlign="center" py={4}>
            <Typography variant="body2" color="text.secondary">
              No recent activities to display
            </Typography>
          </Box>
        ) : (
          <List sx={{ p: 0 }}>
            {displayActivities.map((activity, index) => (
              <React.Fragment key={activity.id}>
                <ListItem
                  alignItems="flex-start"
                  sx={{
                    px: 0,
                    py: 2,
                    '&:hover': {
                      backgroundColor: 'action.hover',
                      borderRadius: 1,
                    },
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 48, mt: 0.5 }}>
                    <Avatar
                      sx={{
                        bgcolor: getActivityColor(activity.type, activity.severity),
                        width: 32,
                        height: 32,
                      }}
                    >
                      {getActivityIcon(activity.type)}
                    </Avatar>
                  </ListItemIcon>
                  
                  <ListItemText
                    primary={
                      <Box display="flex" alignItems="center" justifyContent="space-between">
                        <Typography variant="body2" fontWeight={500}>
                          {activity.description}
                        </Typography>
                        {getSeverityChip(activity.severity)}
                      </Box>
                    }
                    secondary={
                      <Box mt={0.5}>
                        <Typography variant="caption" color="text.secondary">
                          {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                          {activity.user && (
                            <>
                              {' • '}
                              <Typography 
                                component="span" 
                                variant="caption" 
                                fontWeight={500}
                                color="primary.main"
                              >
                                {activity.user}
                              </Typography>
                            </>
                          )}
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
                
                {index < displayActivities.length - 1 && (
                  <Divider variant="inset" component="li" sx={{ ml: 6 }} />
                )}
              </React.Fragment>
            ))}
          </List>
        )}

        {activities.length > maxItems && (
          <Box textAlign="center" mt={2}>
            <Typography variant="body2" color="primary.main" sx={{ cursor: 'pointer' }}>
              View {activities.length - maxItems} more activities
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default RecentActivityCard;