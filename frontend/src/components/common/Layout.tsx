import React from 'react';
import { Outlet } from 'react-router-dom';
import { Box, useTheme } from '@mui/material';

import Sidebar from './Sidebar';
import Header from './Header';
import { useAppSelector } from '@/store';
import { selectSidebarOpen } from '@/store/slices/uiSlice';

// ============================================
// LAYOUT CONSTANTS
// ============================================

const SIDEBAR_WIDTH = 280;
const SIDEBAR_COLLAPSED_WIDTH = 64;
const HEADER_HEIGHT = 64;

// ============================================
// LAYOUT COMPONENT
// ============================================

const Layout: React.FC = () => {
  const theme = useTheme();
  const sidebarOpen = useAppSelector(selectSidebarOpen);

  return (
    <Box sx={{ height: '100vh', backgroundColor: theme.palette.background.default }}>
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          minHeight: '100vh',
          paddingLeft: sidebarOpen ? `${SIDEBAR_WIDTH}px` : `${SIDEBAR_COLLAPSED_WIDTH}px`,
          transition: theme.transitions.create(['padding-left'], {
            easing: theme.transitions.easing.easeInOut,
            duration: theme.transitions.duration.standard,
          }),
        }}
      >
        {/* Header */}
        <Header />

        {/* Page Content */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            padding: theme.spacing(2),
            marginTop: `${HEADER_HEIGHT}px`,
            overflowY: 'auto',
            minHeight: `calc(100vh - ${HEADER_HEIGHT}px)`,
            display: 'flex',
            justifyContent: 'center',
            width: '100%',
          }}
        >
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;