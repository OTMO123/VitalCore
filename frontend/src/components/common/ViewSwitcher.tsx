import React, { useState, useEffect } from 'react';
import {
  IconButton,
  Menu,
  MenuItem,
  Box,
  Typography,
  Tooltip,
  Chip,
  Divider,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  AdminPanelSettings as AdminIcon,
  LocalHospital as DoctorIcon,
  Person as PatientIcon,
  KeyboardArrowDown as ArrowDownIcon,
} from '@mui/icons-material';

import { useAppDispatch, useAppSelector } from '@/store';
import { selectUser } from '@/store/slices/authSlice';
import { setCurrentView, selectCurrentView, selectAvailableViews, setAvailableViews, type ViewMode } from '@/store/slices/viewSlice';

const ViewSwitcher: React.FC = () => {
  const dispatch = useAppDispatch();
  const user = useAppSelector(selectUser);
  const currentView = useAppSelector(selectCurrentView);
  const availableViews = useAppSelector(selectAvailableViews);
  
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  // Set available views based on user role
  useEffect(() => {
    // Always show all views for testing
    dispatch(setAvailableViews(['admin', 'doctor', 'patient']));
    
    // Original logic:
    // if (user?.role?.name === 'admin') {
    //   dispatch(setAvailableViews(['admin', 'doctor', 'patient']));
    // } else if (user?.role?.name === 'doctor') {
    //   dispatch(setAvailableViews(['doctor', 'patient']));
    // } else {
    //   dispatch(setAvailableViews(['patient']));
    // }
  }, [user, dispatch]);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleViewChange = (view: ViewMode) => {
    dispatch(setCurrentView(view));
    handleMenuClose();
  };

  const getViewIcon = (view: ViewMode) => {
    switch (view) {
      case 'admin':
        return <AdminIcon sx={{ fontSize: 16 }} />;
      case 'doctor':
        return <DoctorIcon sx={{ fontSize: 16 }} />;
      case 'patient':
        return <PatientIcon sx={{ fontSize: 16 }} />;
    }
  };

  const getViewLabel = (view: ViewMode) => {
    switch (view) {
      case 'admin':
        return 'Administrator View';
      case 'doctor':
        return 'Healthcare Provider View';
      case 'patient':
        return 'Patient Portal View';
    }
  };

  const getViewColor = (view: ViewMode) => {
    switch (view) {
      case 'admin':
        return 'error';
      case 'doctor':
        return 'primary';
      case 'patient':
        return 'secondary';
    }
  };

  const getViewDescription = (view: ViewMode) => {
    switch (view) {
      case 'admin':
        return 'Full system access and management';
      case 'doctor':
        return 'Clinical workflows and patient care';
      case 'patient':
        return 'Personal health information';
    }
  };

  // Always show for testing
  // if (availableViews.length <= 1 && user?.role?.name !== 'admin') {
  //   return null;
  // }

  return (
    <Box>
      <Tooltip title="Switch dashboard view">
        <IconButton
          onClick={handleMenuOpen}
          color="inherit"
          size="medium"
          sx={{
            bgcolor: 'primary.main',
            color: 'white',
            '&:hover': {
              bgcolor: 'primary.dark',
            },
            mr: 1
          }}
        >
          <Box display="flex" alignItems="center" gap={0.5}>
            {getViewIcon(currentView)}
            <ArrowDownIcon sx={{ fontSize: 16 }} />
          </Box>
        </IconButton>
      </Tooltip>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        PaperProps={{
          sx: { 
            width: 300,
            mt: 1,
            maxHeight: 400,
          },
        }}
        MenuListProps={{
          sx: { p: 0 }
        }}
      >
        <Box p={2} borderBottom={1} borderColor="divider">
          <Typography variant="subtitle2" fontWeight={600}>
            Switch Dashboard View
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Change your interface perspective
          </Typography>
        </Box>

        {availableViews.map((view) => (
          <MenuItem
            key={view}
            onClick={() => handleViewChange(view)}
            selected={currentView === view}
            sx={{ 
              py: 2,
              px: 2,
              minHeight: 60,
              '&:hover': {
                bgcolor: 'action.hover',
              },
              '&.Mui-selected': {
                bgcolor: 'action.selected',
              }
            }}
          >
            <Box display="flex" alignItems="center" width="100%">
              <Box mr={2}>
                {getViewIcon(view)}
              </Box>
              <Box flexGrow={1}>
                <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                  <Typography variant="body2" fontWeight={500}>
                    {getViewLabel(view)}
                  </Typography>
                  {currentView === view && (
                    <Chip
                      label="Current"
                      size="small"
                      color={getViewColor(view) as any}
                      sx={{ 
                        fontSize: '0.625rem', 
                        height: 16,
                        '& .MuiChip-label': { px: 1 }
                      }}
                    />
                  )}
                </Box>
                <Typography variant="caption" color="text.secondary">
                  {getViewDescription(view)}
                </Typography>
              </Box>
            </Box>
          </MenuItem>
        ))}

        <Divider />
        <Box p={2}>
          <Typography variant="caption" color="text.secondary" display="flex" alignItems="center">
            <AdminIcon sx={{ fontSize: 12, mr: 0.5 }} />
            Admin Override Active
          </Typography>
        </Box>
      </Menu>
    </Box>
  );
};

export default ViewSwitcher;