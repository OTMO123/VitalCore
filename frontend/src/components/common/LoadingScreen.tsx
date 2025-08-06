import React from 'react';
import {
  Box,
  CircularProgress,
  Typography,
  Paper,
} from '@mui/material';
import { HealthAndSafety as HealthIcon } from '@mui/icons-material';

// ============================================
// LOADING SCREEN COMPONENT
// ============================================

interface LoadingScreenProps {
  message?: string;
  fullScreen?: boolean;
}

const LoadingScreen: React.FC<LoadingScreenProps> = ({
  message = 'Loading Healthcare AI Platform...',
  fullScreen = true,
}) => {
  const content = (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight={fullScreen ? '100vh' : '200px'}
      bgcolor="background.default"
    >
      <Paper
        elevation={3}
        sx={{
          p: 4,
          borderRadius: 3,
          textAlign: 'center',
          minWidth: 300,
        }}
      >
        <Box mb={3}>
          <HealthIcon
            sx={{
              fontSize: 64,
              color: 'primary.main',
              mb: 2,
            }}
          />
        </Box>

        <CircularProgress
          size={40}
          thickness={4}
          sx={{ mb: 3 }}
        />

        <Typography
          variant="h6"
          fontWeight={600}
          color="primary.main"
          gutterBottom
        >
          Healthcare AI Platform
        </Typography>

        <Typography
          variant="body2"
          color="text.secondary"
        >
          {message}
        </Typography>

        <Box mt={2}>
          <Typography
            variant="caption"
            color="text.secondary"
          >
            HIPAA Compliant • SOC2 Certified • FHIR R4
          </Typography>
        </Box>
      </Paper>
    </Box>
  );

  return content;
};

export default LoadingScreen;