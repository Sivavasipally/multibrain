import React, { useState, useEffect } from 'react';
import {
  Alert,
  Snackbar,
  Chip,
  Box,
  Typography,
  Button,
  Collapse,
  IconButton,
} from '@mui/material';
import {
  WifiOff as OfflineIcon,
  Wifi as OnlineIcon,
  Sync as SyncIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { usePWA } from '../../hooks/usePWA';
import { useOfflineStorage } from '../../hooks/useOfflineStorage';

const OfflineIndicator: React.FC = () => {
  const [showOfflineAlert, setShowOfflineAlert] = useState(false);
  const [showOnlineAlert, setShowOnlineAlert] = useState(false);
  const [wasOffline, setWasOffline] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [offlineMessageCount, setOfflineMessageCount] = useState(0);
  
  const { isOnline, getNetworkStatus } = usePWA();
  const { getOfflineMessages, getCacheSize } = useOfflineStorage();

  useEffect(() => {
    if (!isOnline && !wasOffline) {
      setShowOfflineAlert(true);
      setWasOffline(true);
    } else if (isOnline && wasOffline) {
      setShowOnlineAlert(true);
      setShowOfflineAlert(false);
      setWasOffline(false);
      // Trigger sync of offline messages
      syncOfflineData();
    }
  }, [isOnline, wasOffline]);

  useEffect(() => {
    // Update offline message count
    const updateOfflineCount = async () => {
      const messages = await getOfflineMessages();
      setOfflineMessageCount(messages.length);
    };

    updateOfflineCount();
    const interval = setInterval(updateOfflineCount, 5000); // Check every 5 seconds

    return () => clearInterval(interval);
  }, [getOfflineMessages]);

  const syncOfflineData = async () => {
    try {
      // Trigger background sync
      if ('serviceWorker' in navigator) {
        const registration = await navigator.serviceWorker.ready;
        if ('sync' in registration) {
          await (registration as any).sync.register('background-sync-messages');
        }
      }
    } catch (error) {
      console.error('Failed to trigger background sync:', error);
    }
  };

  const getConnectionInfo = () => {
    const networkStatus = getNetworkStatus();
    if (networkStatus) {
      return {
        type: networkStatus.effectiveType,
        speed: `${networkStatus.downlink} Mbps`,
        latency: `${networkStatus.rtt}ms`,
        saveData: networkStatus.saveData,
      };
    }
    return null;
  };

  const connectionInfo = getConnectionInfo();

  return (
    <>
      {/* Offline Alert */}
      <Snackbar
        open={showOfflineAlert}
        onClose={() => setShowOfflineAlert(false)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert
          severity="warning"
          onClose={() => setShowOfflineAlert(false)}
          sx={{ width: '100%', minWidth: 300 }}
        >
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              You're offline
            </Typography>
            <Typography variant="body2">
              You can continue using the app with limited functionality.
              {offlineMessageCount > 0 && (
                <> {offlineMessageCount} message(s) will sync when you're back online.</>
              )}
            </Typography>
            
            <Box mt={1}>
              <Button
                size="small"
                onClick={() => setShowDetails(!showDetails)}
                endIcon={showDetails ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              >
                Details
              </Button>
            </Box>
            
            <Collapse in={showDetails}>
              <Box mt={1} p={1} bgcolor="rgba(0,0,0,0.1)" borderRadius={1}>
                <Typography variant="caption" display="block">
                  • Chat messages will be saved locally
                </Typography>
                <Typography variant="caption" display="block">
                  • Context creation is disabled
                </Typography>
                <Typography variant="caption" display="block">
                  • Cached data is available for viewing
                </Typography>
              </Box>
            </Collapse>
          </Box>
        </Alert>
      </Snackbar>

      {/* Back Online Alert */}
      <Snackbar
        open={showOnlineAlert}
        autoHideDuration={4000}
        onClose={() => setShowOnlineAlert(false)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert
          severity="success"
          onClose={() => setShowOnlineAlert(false)}
          icon={<OnlineIcon />}
        >
          <Typography variant="subtitle2">
            You're back online!
          </Typography>
          {offlineMessageCount > 0 && (
            <Typography variant="body2">
              Syncing {offlineMessageCount} offline message(s)...
            </Typography>
          )}
        </Alert>
      </Snackbar>

      {/* Connection Status Chip (always visible) */}
      <Box
        sx={{
          position: 'fixed',
          top: 80,
          right: 16,
          zIndex: 1200,
        }}
      >
        <Chip
          icon={isOnline ? <OnlineIcon /> : <OfflineIcon />}
          label={
            <Box display="flex" alignItems="center" gap={0.5}>
              {isOnline ? 'Online' : 'Offline'}
              {connectionInfo && isOnline && (
                <Typography variant="caption" sx={{ opacity: 0.7 }}>
                  ({connectionInfo.type})
                </Typography>
              )}
              {offlineMessageCount > 0 && (
                <Box
                  component="span"
                  sx={{
                    backgroundColor: 'warning.main',
                    color: 'warning.contrastText',
                    borderRadius: '50%',
                    width: 16,
                    height: 16,
                    fontSize: '0.75rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    ml: 0.5,
                  }}
                >
                  {offlineMessageCount}
                </Box>
              )}
            </Box>
          }
          color={isOnline ? 'success' : 'warning'}
          variant={isOnline ? 'outlined' : 'filled'}
          size="small"
          sx={{
            backgroundColor: isOnline ? 'transparent' : 'warning.main',
            '& .MuiChip-label': {
              fontSize: '0.75rem',
            },
          }}
        />
      </Box>
    </>
  );
};

export default OfflineIndicator;
