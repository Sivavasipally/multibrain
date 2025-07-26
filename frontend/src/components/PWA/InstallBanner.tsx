import React, { useState } from 'react';
import {
  Alert,
  AlertTitle,
  Button,
  Box,
  IconButton,
  Slide,
  Paper,
  Typography,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Close as CloseIcon,
  GetApp as InstallIcon,
  PhoneIphone as PhoneIcon,
  Share as ShareIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { usePWA } from '../../hooks/usePWA';

const InstallBanner: React.FC = () => {
  const [dismissed, setDismissed] = useState(false);
  const [installing, setInstalling] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const { isInstallable, isInstalled, installApp, addToHomeScreen } = usePWA();

  // Don't show if already installed or dismissed
  if (isInstalled || dismissed || !isInstallable) {
    return null;
  }

  const handleInstall = async () => {
    setInstalling(true);
    const success = await installApp();
    
    if (success) {
      setDismissed(true);
    }
    setInstalling(false);
  };

  const handleDismiss = () => {
    setDismissed(true);
    // Store dismissal in localStorage to persist across sessions
    localStorage.setItem('pwa-install-dismissed', 'true');
  };

  // Check if user previously dismissed
  React.useEffect(() => {
    const wasDismissed = localStorage.getItem('pwa-install-dismissed');
    if (wasDismissed) {
      setDismissed(true);
    }
  }, []);

  // iOS-specific install instructions
  const iosInstructions = addToHomeScreen();

  if (iosInstructions?.isIOS) {
    return (
      <Slide direction="up" in={!dismissed} mountOnEnter unmountOnExit>
        <Paper
          sx={{
            position: 'fixed',
            bottom: 0,
            left: 0,
            right: 0,
            zIndex: 1300,
            p: 2,
            borderRadius: '16px 16px 0 0',
            backgroundColor: 'primary.main',
            color: 'primary.contrastText',
          }}
        >
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box display="flex" alignItems="center" gap={2}>
              <PhoneIcon />
              <Box>
                <Typography variant="subtitle1" fontWeight="bold">
                  Install RAG Chatbot
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Tap <ShareIcon sx={{ fontSize: 16, mx: 0.5 }} /> then "Add to Home Screen"
                </Typography>
              </Box>
            </Box>
            <IconButton
              onClick={handleDismiss}
              sx={{ color: 'primary.contrastText' }}
            >
              <CloseIcon />
            </IconButton>
          </Box>
        </Paper>
      </Slide>
    );
  }

  return (
    <Slide direction="up" in={!dismissed} mountOnEnter unmountOnExit>
      <Alert
        severity="info"
        sx={{
          position: 'fixed',
          bottom: 16,
          left: 16,
          right: 16,
          zIndex: 1300,
          borderRadius: 2,
          boxShadow: theme.shadows[8],
          maxWidth: isMobile ? 'none' : 400,
          margin: isMobile ? 0 : 'auto',
        }}
        action={
          <Box display="flex" gap={1}>
            <Button
              color="inherit"
              size="small"
              onClick={handleInstall}
              disabled={installing}
              startIcon={<InstallIcon />}
            >
              {installing ? 'Installing...' : 'Install'}
            </Button>
            <IconButton
              size="small"
              onClick={handleDismiss}
              color="inherit"
            >
              <CloseIcon />
            </IconButton>
          </Box>
        }
      >
        <AlertTitle>Install RAG Chatbot</AlertTitle>
        Get the full app experience with offline support and faster loading.
      </Alert>
    </Slide>
  );
};

export default InstallBanner;
