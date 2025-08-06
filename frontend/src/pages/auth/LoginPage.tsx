import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  Avatar,
  Link,
  Divider,
  Checkbox,
  FormControlLabel,
  CircularProgress,
} from '@mui/material';
import {
  HealthAndSafety as HealthIcon,
  Visibility,
  VisibilityOff,
  Security as SecurityIcon,
  Shield as ShieldIcon,
} from '@mui/icons-material';
import { IconButton, InputAdornment } from '@mui/material';

import { useAppDispatch, useAppSelector } from '@/store';
import { loginUser, selectAuthLoading, selectAuthError } from '@/store/slices/authSlice';
import { showSnackbar } from '@/store/slices/uiSlice';

// SOC2 Type II & HIPAA Compliance - Audit logging
import { auditLogger } from '@/utils/auditLogger';
import { sanitizeInput, rateLimiter, secureClearString } from '@/utils/security';

// ============================================
// LOGIN PAGE COMPONENT
// ============================================

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useAppDispatch();
  
  const loading = useAppSelector(selectAuthLoading);
  const error = useAppSelector(selectAuthError);
  
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const from = location.state?.from?.pathname || '/dashboard';

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    // SOC2 Type II - Input validation and sanitization
    const sanitizedUsername = sanitizeInput(formData.username.trim());
    const password = formData.password; // Don't sanitize password to preserve special chars
    
    if (!sanitizedUsername || !password) {
      dispatch(showSnackbar({
        message: 'Please fill in all fields',
        severity: 'warning',
      }));
      
      // HIPAA Audit - Failed login attempt
      await auditLogger.logLoginAttempt(sanitizedUsername, false, 'Empty credentials');
      return;
    }

    // Rate limiting for security
    const clientIP = 'CLIENT_IP'; // Backend will resolve actual IP
    if (!rateLimiter.isAllowed(`login_${clientIP}`, 5)) {
      dispatch(showSnackbar({
        message: 'Too many login attempts. Please try again in 15 minutes.',
        severity: 'error'
      }));
      
      await auditLogger.logSecurityEvent('RATE_LIMIT_EXCEEDED', 'HIGH', {
        action: 'LOGIN_ATTEMPT',
        username: sanitizedUsername
      });
      return;
    }

    try {
      const result = await dispatch(loginUser({
        username: sanitizedUsername,
        password: password,
        rememberMe
      }));
      
      if (loginUser.fulfilled.match(result)) {
        // SOC2 & HIPAA - Successful authentication audit
        await auditLogger.logLoginAttempt(sanitizedUsername, true, 'Valid credentials');
        
        dispatch(showSnackbar({
          message: 'Login successful!',
          severity: 'success',
        }));
        
        // Clear password from memory (security best practice)
        secureClearString(password);
        setFormData(prev => ({ ...prev, password: '' }));
        
        navigate(from, { replace: true });
      }
    } catch (error: any) {
      // HIPAA & SOC2 - Failed authentication audit
      await auditLogger.logLoginAttempt(sanitizedUsername, false, error.message || 'Authentication failed');
      
      // Security event logging
      await auditLogger.logSecurityEvent('LOGIN_FAILURE', 'MEDIUM', {
        username: sanitizedUsername,
        error: error.message || 'Unknown error',
        timestamp: new Date().toISOString()
      });
      
      // Clear password on failure
      setFormData(prev => ({ ...prev, password: '' }));
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

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
        }}
      >
        {/* Logo and Title */}
        <Box textAlign="center" mb={4}>
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
            Healthcare AI Platform
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Secure • HIPAA Compliant • AI-Powered
          </Typography>
        </Box>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Login Form */}
        <Box component="form" onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Username or Email"
            name="username"
            value={formData.username}
            onChange={handleInputChange}
            margin="normal"
            required
            autoComplete="username"
            autoFocus
            disabled={loading === 'loading'}
          />

          <TextField
            fullWidth
            label="Password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            value={formData.password}
            onChange={handleInputChange}
            margin="normal"
            required
            autoComplete="current-password"
            disabled={loading === 'loading'}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={togglePasswordVisibility}
                    edge="end"
                    disabled={loading === 'loading'}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <FormControlLabel
            control={
              <Checkbox
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                disabled={loading === 'loading'}
              />
            }
            label="Remember me"
            sx={{ mt: 1, mb: 2 }}
          />

          <Button
            type="submit"
            fullWidth
            variant="contained"
            size="large"
            disabled={loading === 'loading'}
            sx={{
              mt: 2,
              mb: 2,
              py: 1.5,
              fontSize: '1rem',
              fontWeight: 600,
            }}
          >
            {loading === 'loading' ? 'Signing In...' : 'Sign In'}
          </Button>

          <Box textAlign="center">
            <Link
              href="#"
              variant="body2"
              sx={{ textDecoration: 'none' }}
              onClick={(e) => {
                e.preventDefault();
                dispatch(showSnackbar({
                  message: 'Password reset feature coming soon',
                  severity: 'info',
                }));
              }}
            >
              Forgot your password?
            </Link>
          </Box>
        </Box>

        <Divider sx={{ my: 3 }}>
          <Typography variant="body2" color="text.secondary">
            Demo Access
          </Typography>
        </Divider>

        {/* Demo Credentials */}
        <Box bgcolor="grey.50" p={2} borderRadius={1} mb={2}>
          <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
            Demo Credentials:
          </Typography>
          <Typography variant="body2" fontFamily="monospace">
            <strong>Admin:</strong> admin / admin123
          </Typography>
          <Typography variant="body2" fontFamily="monospace">
            <strong>Operator:</strong> operator / operator123
          </Typography>
          <Typography variant="body2" fontFamily="monospace">
            <strong>Viewer:</strong> viewer / viewer123
          </Typography>
        </Box>

        {/* Security Notice */}
        <Box textAlign="center" mt={3}>
          <Typography variant="caption" color="text.secondary">
            🔒 This system is protected by enterprise-grade security
            <br />
            SOC2 Type II Certified • HIPAA Compliant • FHIR R4
          </Typography>
        </Box>

        {/* Footer */}
        <Box textAlign="center" mt={4}>
          <Typography variant="body2" color="text.secondary">
            Don't have an account?{' '}
            <Link
              href="#"
              onClick={(e) => {
                e.preventDefault();
                navigate('/register');
              }}
              sx={{ textDecoration: 'none' }}
            >
              Contact Administrator
            </Link>
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
};

export default LoginPage;