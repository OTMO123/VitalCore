import React from 'react';
import { Snackbar, Alert, AlertTitle } from '@mui/material';

import { useAppDispatch, useAppSelector } from '@/store';
import { hideSnackbar, selectSnackbar } from '@/store/slices/uiSlice';

// ============================================
// GLOBAL SNACKBAR COMPONENT
// ============================================

const GlobalSnackbar: React.FC = () => {
  const dispatch = useAppDispatch();
  const snackbar = useAppSelector(selectSnackbar);

  const handleClose = (_event?: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') {
      return;
    }
    dispatch(hideSnackbar());
  };

  return (
    <Snackbar
      open={snackbar.open}
      autoHideDuration={snackbar.autoHideDuration || 6000}
      onClose={handleClose}
      anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
    >
      <Alert 
        onClose={handleClose} 
        severity={snackbar.severity}
        variant="filled"
        sx={{ width: '100%' }}
      >
        {snackbar.message}
      </Alert>
    </Snackbar>
  );
};

export default GlobalSnackbar;