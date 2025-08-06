import { createTheme, Theme } from '@mui/material/styles';
import { alpha } from '@mui/material/styles';

// ============================================
// HEALTHCARE COLOR PALETTE
// ============================================

const healthcareColors = {
  primary: {
    50: '#e3f2fd',
    100: '#bbdefb',
    200: '#90caf9',
    300: '#64b5f6',
    400: '#42a5f5',
    500: '#2196f3',
    600: '#1e88e5',
    700: '#1976d2',
    800: '#1565c0',
    900: '#0d47a1',
  },
  secondary: {
    50: '#f3e5f5',
    100: '#e1bee7',
    200: '#ce93d8',
    300: '#ba68c8',
    400: '#ab47bc',
    500: '#9c27b0',
    600: '#8e24aa',
    700: '#7b1fa2',
    800: '#6a1b9a',
    900: '#4a148c',
  },
  success: {
    50: '#e8f5e8',
    100: '#c8e6c9',
    200: '#a5d6a7',
    300: '#81c784',
    400: '#66bb6a',
    500: '#4caf50',
    600: '#43a047',
    700: '#388e3c',
    800: '#2e7d32',
    900: '#1b5e20',
  },
  warning: {
    50: '#fff8e1',
    100: '#ffecb3',
    200: '#ffe082',
    300: '#ffd54f',
    400: '#ffca28',
    500: '#ffc107',
    600: '#ffb300',
    700: '#ffa000',
    800: '#ff8f00',
    900: '#ff6f00',
  },
  error: {
    50: '#ffebee',
    100: '#ffcdd2',
    200: '#ef9a9a',
    300: '#e57373',
    400: '#ef5350',
    500: '#f44336',
    600: '#e53935',
    700: '#d32f2f',
    800: '#c62828',
    900: '#b71c1c',
  },
  grey: {
    50: '#fafafa',
    100: '#f5f5f5',
    200: '#eeeeee',
    300: '#e0e0e0',
    400: '#bdbdbd',
    500: '#9e9e9e',
    600: '#757575',
    700: '#616161',
    800: '#424242',
    900: '#212121',
  },
};

// ============================================
// LIGHT THEME
// ============================================

const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: healthcareColors.primary[600],
      light: healthcareColors.primary[400],
      dark: healthcareColors.primary[800],
      contrastText: '#ffffff',
    },
    secondary: {
      main: healthcareColors.secondary[600],
      light: healthcareColors.secondary[400],
      dark: healthcareColors.secondary[800],
      contrastText: '#ffffff',
    },
    success: {
      main: healthcareColors.success[600],
      light: healthcareColors.success[400],
      dark: healthcareColors.success[800],
      contrastText: '#ffffff',
    },
    warning: {
      main: healthcareColors.warning[600],
      light: healthcareColors.warning[400],
      dark: healthcareColors.warning[800],
      contrastText: '#000000',
    },
    error: {
      main: healthcareColors.error[600],
      light: healthcareColors.error[400],
      dark: healthcareColors.error[800],
      contrastText: '#ffffff',
    },
    background: {
      default: '#fafafa',
      paper: '#ffffff',
    },
    text: {
      primary: healthcareColors.grey[900],
      secondary: healthcareColors.grey[700],
    },
    divider: healthcareColors.grey[200],
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.125rem',
      fontWeight: 600,
      lineHeight: 1.235,
    },
    h2: {
      fontSize: '1.75rem',
      fontWeight: 600,
      lineHeight: 1.2,
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.167,
    },
    h4: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.235,
    },
    h5: {
      fontSize: '1.125rem',
      fontWeight: 600,
      lineHeight: 1.334,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.6,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.43,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 24px',
          fontSize: '0.875rem',
          fontWeight: 500,
          textTransform: 'none',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          },
        },
        contained: {
          boxShadow: '0 1px 3px rgba(0,0,0,0.12)',
          '&:hover': {
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
          border: `1px solid ${healthcareColors.grey[200]}`,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
        elevation1: {
          boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            '& fieldset': {
              borderColor: healthcareColors.grey[300],
            },
            '&:hover fieldset': {
              borderColor: healthcareColors.primary[400],
            },
            '&.Mui-focused fieldset': {
              borderColor: healthcareColors.primary[600],
              borderWidth: 2,
            },
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          color: healthcareColors.grey[900],
          boxShadow: '0 1px 3px rgba(0,0,0,0.12)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: `1px solid ${healthcareColors.grey[200]}`,
          backgroundColor: '#ffffff',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          margin: '2px 8px',
          '&.Mui-selected': {
            backgroundColor: alpha(healthcareColors.primary[600], 0.08),
            color: healthcareColors.primary[600],
            '&:hover': {
              backgroundColor: alpha(healthcareColors.primary[600], 0.12),
            },
          },
          '&:hover': {
            backgroundColor: alpha(healthcareColors.grey[500], 0.04),
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          fontWeight: 500,
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          '& .MuiAlert-icon': {
            marginRight: 12,
          },
        },
      },
    },
  },
});

// ============================================
// DARK THEME
// ============================================

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: healthcareColors.primary[400],
      light: healthcareColors.primary[300],
      dark: healthcareColors.primary[600],
      contrastText: '#000000',
    },
    secondary: {
      main: healthcareColors.secondary[400],
      light: healthcareColors.secondary[300],
      dark: healthcareColors.secondary[600],
      contrastText: '#000000',
    },
    success: {
      main: healthcareColors.success[400],
      light: healthcareColors.success[300],
      dark: healthcareColors.success[600],
      contrastText: '#000000',
    },
    warning: {
      main: healthcareColors.warning[400],
      light: healthcareColors.warning[300],
      dark: healthcareColors.warning[600],
      contrastText: '#000000',
    },
    error: {
      main: healthcareColors.error[400],
      light: healthcareColors.error[300],
      dark: healthcareColors.error[600],
      contrastText: '#000000',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
    text: {
      primary: '#ffffff',
      secondary: '#b3b3b3',
    },
    divider: '#333333',
  },
  typography: lightTheme.typography,
  shape: lightTheme.shape,
  components: {
    ...lightTheme.components,
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#1e1e1e',
          color: '#ffffff',
          boxShadow: '0 1px 3px rgba(0,0,0,0.12)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: '1px solid #333333',
          backgroundColor: '#1e1e1e',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
          border: '1px solid #333333',
          backgroundColor: '#1e1e1e',
        },
      },
    },
  },
});

// ============================================
// THEME FACTORY
// ============================================

export const createAppTheme = (mode: 'light' | 'dark'): Theme => {
  return mode === 'light' ? lightTheme : darkTheme;
};

export { healthcareColors };
export default lightTheme;