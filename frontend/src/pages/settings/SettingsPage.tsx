import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const SettingsPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" fontWeight={600} gutterBottom>
        Settings
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          Settings and configuration coming soon...
          This will include user preferences, system configuration, and admin tools.
        </Typography>
      </Paper>
    </Box>
  );
};

export default SettingsPage;