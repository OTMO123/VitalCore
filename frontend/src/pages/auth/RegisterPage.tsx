import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Button,
  Avatar,
} from '@mui/material';
import { HealthAndSafety as HealthIcon } from '@mui/icons-material';

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: 3,
      }}
    >
      <Paper
        elevation={10}
        sx={{
          width: '100%',
          maxWidth: 400,
          padding: 4,
          borderRadius: 3,
          textAlign: 'center',
        }}
      >
        <Avatar
          sx={{
            bgcolor: 'primary.main',
            width: 64,
            height: 64,
            margin: '0 auto',
            mb: 2,
          }}
        >
          <HealthIcon sx={{ fontSize: 40 }} />
        </Avatar>
        
        <Typography variant="h4" fontWeight={700} color="primary.main" gutterBottom>
          Registration
        </Typography>
        
        <Typography variant="body1" color="text.secondary" mb={4}>
          Please contact your system administrator to create a new account.
          Healthcare AI Platform requires proper authorization for access.
        </Typography>
        
        <Button
          variant="contained"
          fullWidth
          onClick={() => navigate('/login')}
          sx={{ mb: 2 }}
        >
          Back to Login
        </Button>
        
        <Typography variant="caption" color="text.secondary">
          🔒 Account creation is restricted for security compliance
        </Typography>
      </Paper>
    </Box>
  );
};

export default RegisterPage;