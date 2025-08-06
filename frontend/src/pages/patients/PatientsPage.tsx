import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const PatientsPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" fontWeight={600} gutterBottom>
        Patient Management
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          Patient management features coming soon...
          This will include FHIR-compliant patient records, search, and PHI protection.
        </Typography>
      </Paper>
    </Box>
  );
};

export default PatientsPage;