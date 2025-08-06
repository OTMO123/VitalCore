import React from 'react';
import {
  Drawer,
  Box,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Chip,
  Divider,
  Button,
} from '@mui/material';
import {
  Close as CloseIcon,
  Notifications as NotificationsIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon,
  MarkEmailRead as MarkReadIcon,
  DeleteSweep as ClearAllIcon,
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';

import { useAppDispatch, useAppSelector } from '@/store';
import {
  selectNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  clearNotifications,
  closeModal,
  selectModal,
} from '@/store/slices/uiSlice';

// ============================================
// NOTIFICATION CENTER COMPONENT
// ============================================

const NotificationCenter: React.FC = () => {
  const dispatch = useAppDispatch();
  const notifications = useAppSelector(selectNotifications);
  const modalState = useAppSelector(state => selectModal('notifications')(state));
  const isOpen = modalState.open;

  const handleClose = () => {
    dispatch(closeModal('notifications'));
  };

  const handleMarkRead = (notificationId: string) => {
    dispatch(markNotificationRead(notificationId));
  };

  const handleMarkAllRead = () => {
    dispatch(markAllNotificationsRead());
  };

  const handleClearAll = () => {
    dispatch(clearNotifications());
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <SuccessIcon color="success" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <Drawer
      anchor="right"
      open={isOpen}
      onClose={handleClose}
      PaperProps={{
        sx: { width: 400 },
      }}
    >
      <Box>
        {/* Header */}
        <Box
          display="flex"
          alignItems="center"
          justifyContent="space-between"
          p={2}
          borderBottom={1}
          borderColor="divider"
        >
          <Box display="flex" alignItems="center">
            <NotificationsIcon sx={{ mr: 1 }} />
            <Typography variant="h6" fontWeight={600}>
              Notifications
            </Typography>
            {unreadCount > 0 && (
              <Chip
                label={unreadCount}
                size="small"
                color="primary"
                sx={{ ml: 1 }}
              />
            )}
          </Box>
          <IconButton onClick={handleClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>

        {/* Actions */}
        {notifications.length > 0 && (
          <Box p={2} borderBottom={1} borderColor="divider">
            <Box display="flex" gap={1}>
              <Button
                size="small"
                startIcon={<MarkReadIcon />}
                onClick={handleMarkAllRead}
                disabled={unreadCount === 0}
              >
                Mark All Read
              </Button>
              <Button
                size="small"
                startIcon={<ClearAllIcon />}
                onClick={handleClearAll}
                color="error"
              >
                Clear All
              </Button>
            </Box>
          </Box>
        )}

        {/* Notifications List */}
        <Box sx={{ height: 'calc(100vh - 120px)', overflowY: 'auto' }}>
          {notifications.length === 0 ? (
            <Box
              display="flex"
              flexDirection="column"
              alignItems="center"
              justifyContent="center"
              height="100%"
              p={4}
            >
              <NotificationsIcon
                sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }}
              />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No notifications
              </Typography>
              <Typography variant="body2" color="text.secondary" textAlign="center">
                You're all caught up! New notifications will appear here.
              </Typography>
            </Box>
          ) : (
            <List>
              {notifications.map((notification, index) => (
                <React.Fragment key={notification.id}>
                  <ListItem
                    alignItems="flex-start"
                    sx={{
                      backgroundColor: notification.read ? 'transparent' : 'action.hover',
                      cursor: 'pointer',
                      '&:hover': {
                        backgroundColor: 'action.selected',
                      },
                    }}
                    onClick={() => !notification.read && handleMarkRead(notification.id)}
                  >
                    <ListItemIcon sx={{ mt: 1 }}>
                      {getNotificationIcon(notification.type)}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" justifyContent="space-between">
                          <Typography
                            variant="body2"
                            fontWeight={notification.read ? 400 : 600}
                          >
                            {notification.title}
                          </Typography>
                          {!notification.read && (
                            <Box
                              sx={{
                                width: 8,
                                height: 8,
                                borderRadius: '50%',
                                backgroundColor: 'primary.main',
                              }}
                            />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box mt={0.5}>
                          {notification.message && (
                            <Typography
                              variant="body2"
                              color="text.secondary"
                              paragraph
                            >
                              {notification.message}
                            </Typography>
                          )}
                          <Typography variant="caption" color="text.secondary">
                            {formatDistanceToNow(new Date(notification.timestamp), {
                              addSuffix: true,
                            })}
                          </Typography>
                          
                          {notification.actions && notification.actions.length > 0 && (
                            <Box mt={1} display="flex" gap={1}>
                              {notification.actions.map((action) => (
                                <Button
                                  key={action.action}
                                  size="small"
                                  variant="outlined"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    // Handle action
                                    console.log('Notification action:', action);
                                  }}
                                >
                                  {action.label}
                                </Button>
                              ))}
                            </Box>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < notifications.length - 1 && <Divider variant="inset" />}
                </React.Fragment>
              ))}
            </List>
          )}
        </Box>
      </Box>
    </Drawer>
  );
};

export default NotificationCenter;