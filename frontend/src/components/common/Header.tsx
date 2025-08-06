import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Box,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  Badge,
  Tooltip,
  Chip,
  useTheme,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  AccountCircle as AccountIcon,
  Settings as SettingsIcon,
  Logout as LogoutIcon,
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
  Shield as SecurityIcon,
} from '@mui/icons-material';

import { useAppDispatch, useAppSelector } from '@/store';
import { toggleSidebar, toggleTheme, selectTheme, selectUnreadNotifications } from '@/store/slices/uiSlice';
import { logoutUser, selectUser } from '@/store/slices/authSlice';
import ViewSwitcher from './ViewSwitcher';

// ============================================
// HEADER COMPONENT
// ============================================

const Header: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  
  const currentTheme = useAppSelector(selectTheme);
  const user = useAppSelector(selectUser);
  const unreadNotifications = useAppSelector(selectUnreadNotifications);
  
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [notificationAnchorEl, setNotificationAnchorEl] = useState<null | HTMLElement>(null);

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleNotificationMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchorEl(event.currentTarget);
  };

  const handleNotificationMenuClose = () => {
    setNotificationAnchorEl(null);
  };

  const handleLogout = async () => {
    handleProfileMenuClose();
    await dispatch(logoutUser());
    navigate('/login');
  };

  const handleThemeToggle = () => {
    dispatch(toggleTheme());
  };

  const handleMenuToggle = () => {
    dispatch(toggleSidebar());
  };

  const getRoleColor = (roleName?: string) => {
    switch (roleName?.toLowerCase()) {
      case 'admin':
        return 'error';
      case 'operator':
        return 'primary';
      case 'viewer':
        return 'secondary';
      default:
        return 'default';
    }
  };

  return (
    <AppBar
      position="fixed"
      elevation={1}
      sx={{
        zIndex: theme.zIndex.drawer + 1,
        backgroundColor: theme.palette.background.paper,
        borderBottom: `1px solid ${theme.palette.divider}`,
      }}
    >
      <Toolbar>
        {/* Menu Toggle */}
        <IconButton
          edge="start"
          onClick={handleMenuToggle}
          sx={{ mr: 2 }}
          aria-label="Toggle sidebar menu"
        >
          <MenuIcon />
        </IconButton>

        {/* Page Title */}
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Healthcare AI Platform
          <Typography component="span" variant="caption" color="text.secondary" ml={2}>
            🔒 HIPAA Compliant • SOC2 Certified
          </Typography>
        </Typography>

        {/* Actions */}
        <Box display="flex" alignItems="center" gap={1}>
          {/* View Switcher (Admin only) */}
          <ViewSwitcher />

          {/* Theme Toggle */}
          <Tooltip title={`Switch to ${currentTheme === 'light' ? 'dark' : 'light'} mode`}>
            <IconButton 
              onClick={handleThemeToggle} 
              color="inherit"
              aria-label={`Switch to ${currentTheme === 'light' ? 'dark' : 'light'} theme`}
            >
              {currentTheme === 'light' ? <DarkModeIcon /> : <LightModeIcon />}
            </IconButton>
          </Tooltip>

          {/* Notifications */}
          <Tooltip title="Notifications">
            <IconButton 
              onClick={handleNotificationMenuOpen}
              color="inherit"
              aria-label={`Notifications (${unreadNotifications.length} unread)`}
            >
              <Badge badgeContent={unreadNotifications.length} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
          </Tooltip>

          {/* User Profile */}
          <Box display="flex" alignItems="center" ml={2}>
            {user && (
              <Box mr={2} textAlign="right">
                <Typography variant="body2" fontWeight={600}>
                  {user.username}
                </Typography>
                <Box display="flex" alignItems="center" justifyContent="flex-end">
                  <Chip
                    label={user.role?.name || 'User'}
                    size="small"
                    color={getRoleColor(user.role?.name) as any}
                    sx={{ fontSize: '0.625rem', height: 18 }}
                  />
                  {user.role?.name === 'admin' && (
                    <SecurityIcon sx={{ fontSize: 14, ml: 0.5, color: 'error.main' }} />
                  )}
                </Box>
              </Box>
            )}
            
            <Tooltip title="Account settings">
              <IconButton 
                onClick={handleProfileMenuOpen} 
                color="inherit"
                aria-label="Open account settings menu"
              >
                <Avatar
                  sx={{
                    width: 32,
                    height: 32,
                    bgcolor: 'primary.main',
                    fontSize: '0.875rem',
                  }}
                >
                  {user?.username?.charAt(0).toUpperCase() || 'U'}
                </Avatar>
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Profile Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleProfileMenuClose}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
        >
          <MenuItem onClick={() => { handleProfileMenuClose(); navigate('/settings'); }}>
            <AccountIcon sx={{ mr: 2 }} />
            Profile Settings
          </MenuItem>
          <MenuItem onClick={() => { handleProfileMenuClose(); navigate('/settings?tab=admin'); }}>
            <SettingsIcon sx={{ mr: 2 }} />
            System Settings
          </MenuItem>
          <Divider />
          <MenuItem onClick={handleLogout} sx={{ color: 'error.main' }}>
            <LogoutIcon sx={{ mr: 2 }} />
            Logout
          </MenuItem>
        </Menu>

        {/* Notifications Menu */}
        <Menu
          anchorEl={notificationAnchorEl}
          open={Boolean(notificationAnchorEl)}
          onClose={handleNotificationMenuClose}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
          PaperProps={{
            sx: { width: 320, maxHeight: 400 },
          }}
        >
          <Box p={2} borderBottom={1} borderColor="divider">
            <Typography variant="h6" fontWeight={600}>
              Notifications
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {unreadNotifications.length} unread notifications
            </Typography>
          </Box>
          
          {unreadNotifications.length === 0 ? (
            <Box p={3} textAlign="center">
              <Typography variant="body2" color="text.secondary">
                No new notifications
              </Typography>
            </Box>
          ) : (
            unreadNotifications.slice(0, 5).map((notification) => (
              <MenuItem key={notification.id} onClick={handleNotificationMenuClose}>
                <Box>
                  <Typography variant="body2" fontWeight={500}>
                    {notification.title}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {notification.message}
                  </Typography>
                </Box>
              </MenuItem>
            ))
          )}
          
          {unreadNotifications.length > 0 && (
            <>
              <Divider />
              <MenuItem onClick={handleNotificationMenuClose}>
                <Typography variant="body2" color="primary.main" textAlign="center" width="100%">
                  View all notifications
                </Typography>
              </MenuItem>
            </>
          )}
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default Header;