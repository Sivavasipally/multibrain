/**
 * Offline Indicator Component for RAG Chatbot PWA
 * 
 * Provides persistent offline status indication with connection quality monitoring,
 * sync status, and user feedback. Shows detailed connectivity information and
 * quick access to offline functionality.
 * 
 * Features:
 * - Real-time network status monitoring
 * - Connection quality indication
 * - Sync queue status
 * - Quick actions for offline mode
 * - Expandable details panel
 * 
 * Author: RAG Chatbot Development Team
 * Version: 2.0.0
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Chip,
  IconButton,
  Popover,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Alert,
  LinearProgress,
  Tooltip,
  Badge,
} from '@mui/material';
import {
  CloudOff as CloudOffIcon,
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon,
  NetworkCheck as NetworkCheckIcon,
  Sync as SyncIcon,
  SyncDisabled as SyncDisabledIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { useOfflineQueue } from '../../hooks/useOfflineQueue';
import OfflineQueueManager from './OfflineQueueManager';

interface OfflineIndicatorProps {
  position?: 'fixed' | 'static';
  anchorOrigin?: {
    vertical: 'top' | 'bottom';
    horizontal: 'left' | 'right';
  };
  showOnlineStatus?: boolean;
  compact?: boolean;
}

const OfflineIndicator: React.FC<OfflineIndicatorProps> = ({
  position = 'fixed',
  anchorOrigin = { vertical: 'bottom', horizontal: 'right' },
  showOnlineStatus = false,
  compact = false,
}) => {
  const {
    queueStatus,
    networkStatus,
    isProcessing,
    stats,
    processQueue,
  } = useOfflineQueue();

  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [showQueueManager, setShowQueueManager] = useState(false);
  const [connectionDetails, setConnectionDetails] = useState<any>(null);

  useEffect(() => {
    // Monitor connection details if available
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      
      const updateDetails = () => {
        setConnectionDetails({
          effectiveType: connection.effectiveType,
          downlink: connection.downlink,
          rtt: connection.rtt,
          saveData: connection.saveData,
        });
      };
      
      updateDetails();
      connection.addEventListener('change', updateDetails);
      
      return () => {
        connection.removeEventListener('change', updateDetails);
      };
    }
  }, []);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleSyncNow = async () => {
    await processQueue();
    handleClose();
  };

  const handleOpenQueueManager = () => {
    setShowQueueManager(true);
    handleClose();
  };

  const getConnectionIcon = () => {
    if (!networkStatus.isOnline) {
      return <WifiOffIcon />;
    }
    
    if (connectionDetails) {
      const { effectiveType } = connectionDetails;
      if (['slow-2g', '2g'].includes(effectiveType)) {
        return <SpeedIcon />;
      } else if (['3g'].includes(effectiveType)) {
        return <WifiIcon />;
      } else {
        return <NetworkCheckIcon />;
      }
    }
    
    return <WifiIcon />;
  };

  const getConnectionColor = (): 'success' | 'warning' | 'error' | 'default' => {
    if (!networkStatus.isOnline) return 'error';
    
    if (connectionDetails) {
      const { effectiveType } = connectionDetails;
      if (['slow-2g', '2g'].includes(effectiveType)) return 'warning';
      if (['3g'].includes(effectiveType)) return 'default';
      return 'success';
    }
    
    return 'success';
  };

  const getConnectionLabel = () => {
    if (!networkStatus.isOnline) return 'Offline';
    
    if (connectionDetails) {
      const { effectiveType } = connectionDetails;
      return effectiveType?.toUpperCase() || 'Online';
    }
    
    return 'Online';
  };

  const formatSpeed = (speed: number) => {
    if (speed >= 1) return `${speed.toFixed(1)} Mbps`;
    return `${(speed * 1000).toFixed(0)} kbps`;
  };

  const formatLatency = (rtt: number) => {
    return `${rtt}ms`;
  };

  // Don't show indicator if online and no queue items (unless explicitly shown)
  if (networkStatus.isOnline && queueStatus.total === 0 && !showOnlineStatus) {
    return null;
  }

  const open = Boolean(anchorEl);
  const id = open ? 'offline-indicator-popover' : undefined;

  const chipLabel = networkStatus.isOnline 
    ? (queueStatus.total > 0 ? `${queueStatus.pending} pending` : getConnectionLabel())
    : 'Offline';

  if (compact) {
    return (
      <Chip
        icon={getConnectionIcon()}
        label={chipLabel}
        color={getConnectionColor()}
        size="small"
        onClick={handleClick}
        sx={{ cursor: 'pointer' }}
      />
    );
  }

  return (
    <>
      <Box
        sx={{
          position,
          ...(position === 'fixed' && {
            [anchorOrigin.vertical]: 20,
            [anchorOrigin.horizontal]: 20,
            zIndex: 1300,
          }),
        }}
      >
        <Tooltip title="Network & Sync Status">
          <Badge
            badgeContent={queueStatus.total > 0 ? queueStatus.total : undefined}
            color="primary"
          >
            <Chip
              icon={isProcessing ? <SyncIcon 
                sx={{ 
                  animation: 'rotation 1s infinite linear',
                  '@keyframes rotation': {
                    from: { transform: 'rotate(0deg)' },
                    to: { transform: 'rotate(359deg)' }
                  }
                }} 
              /> : getConnectionIcon()}
              label={chipLabel}
              color={getConnectionColor()}
              onClick={handleClick}
              sx={{ 
                cursor: 'pointer',
                boxShadow: 2,
              }}
            />
          </Badge>
        </Tooltip>
      </Box>

      <Popover
        id={id}
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'top',
          horizontal: 'center',
        }}
        transformOrigin={{
          vertical: 'bottom',
          horizontal: 'center',
        }}
        sx={{ mt: -1 }}
      >
        <Box sx={{ p: 2, minWidth: 300 }}>
          {/* Connection Status */}
          <Box display="flex" alignItems="center" gap={2} mb={2}>
            <Box display="flex" alignItems="center" gap={1}>
              {getConnectionIcon()}
              <Typography variant="h6">
                {networkStatus.isOnline ? 'Online' : 'Offline'}
              </Typography>
            </Box>
            <Chip
              label={getConnectionLabel()}
              color={getConnectionColor()}
              size="small"
            />
          </Box>

          {/* Connection Details */}
          {networkStatus.isOnline && connectionDetails && (
            <Box mb={2}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Connection Quality
              </Typography>
              <List dense>
                <ListItem sx={{ py: 0 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    <SpeedIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary={`${formatSpeed(connectionDetails.downlink)} downlink`}
                    secondary={`${formatLatency(connectionDetails.rtt)} latency`}
                  />
                </ListItem>
                {connectionDetails.saveData && (
                  <ListItem sx={{ py: 0 }}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <InfoIcon fontSize="small" color="warning" />
                    </ListItemIcon>
                    <ListItemText primary="Data saver mode active" />
                  </ListItem>
                )}
              </List>
            </Box>
          )}

          {/* Sync Status */}
          {queueStatus.total > 0 && (
            <>
              <Divider sx={{ my: 2 }} />
              <Box>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Sync Status
                </Typography>
                <List dense>
                  <ListItem sx={{ py: 0 }}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <ScheduleIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={`${queueStatus.pending} pending actions`} />
                  </ListItem>
                  {queueStatus.failed > 0 && (
                    <ListItem sx={{ py: 0 }}>
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        <WarningIcon fontSize="small" color="error" />
                      </ListItemIcon>
                      <ListItemText
                        primary={`${queueStatus.failed} failed actions`}
                        secondary={`${stats.failureRate * 100}% failure rate`}
                      />
                    </ListItem>
                  )}
                  {queueStatus.conflicts > 0 && (
                    <ListItem sx={{ py: 0 }}>
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        <WarningIcon fontSize="small" color="warning" />
                      </ListItemIcon>
                      <ListItemText primary={`${queueStatus.conflicts} conflicts`} />
                    </ListItem>
                  )}
                </List>

                {isProcessing && (
                  <Box mt={1}>
                    <Typography variant="caption" color="textSecondary">
                      Syncing...
                    </Typography>
                    <LinearProgress size="small" sx={{ mt: 0.5 }} />
                  </Box>
                )}

                <Box display="flex" gap={1} mt={2}>
                  <Button
                    size="small"
                    variant="contained"
                    startIcon={<SyncIcon />}
                    onClick={handleSyncNow}
                    disabled={isProcessing || !networkStatus.isOnline || queueStatus.pending === 0}
                  >
                    Sync Now
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<StorageIcon />}
                    onClick={handleOpenQueueManager}
                  >
                    Manage Queue
                  </Button>
                </Box>
              </Box>
            </>
          )}

          {/* Offline Alert */}
          {!networkStatus.isOnline && (
            <>
              <Divider sx={{ my: 2 }} />
              <Alert severity="info" size="small">
                You're working offline. Changes will sync when you're back online.
              </Alert>
            </>
          )}

          {/* Poor Connection Warning */}
          {networkStatus.isOnline && 
           connectionDetails && 
           ['slow-2g', '2g'].includes(connectionDetails.effectiveType) && (
            <>
              <Divider sx={{ my: 2 }} />
              <Alert severity="warning" size="small">
                Slow connection detected. Sync may be delayed.
              </Alert>
            </>
          )}

          {/* Last Online Status */}
          {!networkStatus.isOnline && (
            <Box mt={2}>
              <Typography variant="caption" color="textSecondary">
                Last online: {networkStatus.lastOnline.toLocaleString()}
              </Typography>
            </Box>
          )}
        </Box>
      </Popover>

      {/* Queue Manager Dialog */}
      {showQueueManager && (
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            bgcolor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 1400,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            p: 2,
          }}
          onClick={() => setShowQueueManager(false)}
        >
          <Box
            sx={{
              bgcolor: 'background.paper',
              borderRadius: 2,
              maxWidth: '90vw',
              maxHeight: '90vh',
              overflow: 'auto',
              p: 2,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <OfflineQueueManager onClose={() => setShowQueueManager(false)} />
          </Box>
        </Box>
      )}
    </>
  );
};

export default OfflineIndicator;