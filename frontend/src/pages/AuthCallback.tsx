import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Box, CircularProgress, Typography, Alert } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import { useSnackbar } from '../contexts/SnackbarContext';

const AuthCallback: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { showSuccess, showError } = useSnackbar();

  useEffect(() => {
    const token = searchParams.get('token');
    const error = searchParams.get('error');

    if (error) {
      showError(`Authentication failed: ${error}`);
      navigate('/login');
      return;
    }

    if (token) {
      // Store token and redirect
      localStorage.setItem('token', token);
      showSuccess('Successfully signed in with GitHub!');
      navigate('/dashboard');
    } else {
      showError('No authentication token received');
      navigate('/login');
    }
  }, [searchParams, navigate, showSuccess, showError]);

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="100vh"
      gap={2}
    >
      <CircularProgress size={60} />
      <Typography variant="h6" color="text.secondary">
        Completing authentication...
      </Typography>
    </Box>
  );
};

export default AuthCallback;
