/**
 * Offline Queue Manager Component for RAG Chatbot PWA
 * 
 * Provides visual management interface for offline actions and sync operations.
 * Shows queue status, conflict resolution, and network connectivity information.
 * 
 * Features:
 * - Real-time queue status display
 * - Action retry and removal controls
 * - Conflict resolution interface
 * - Network connectivity indicator
 * - Batch operations support
 * - Progress visualization
 * 
 * Author: RAG Chatbot Development Team
 * Version: 2.0.0
 */

import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  IconButton,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  LinearProgress,
  Tooltip,
  Badge,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Sync as SyncIcon,
  SyncDisabled as SyncDisabledIcon,
  NetworkCheck as NetworkCheckIcon,
  ExpandMore as ExpandMoreIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import type { QueueAction, ConflictItem } from '../../hooks/useOfflineQueue';
import { useOfflineQueue } from '../../hooks/useOfflineQueue';
import { useSnackbar } from '../../contexts/SnackbarContext';

interface OfflineQueueManagerProps {
  compact?: boolean;
  maxHeight?: number;
  onClose?: () => void;
}

const OfflineQueueManager: React.FC<OfflineQueueManagerProps> = ({
  compact = false,
  maxHeight = 400,
  onClose,
}) => {
  const {
    queueActions,
    queueStatus,
    networkStatus,
    isProcessing,
    conflicts,
    processQueue,
    retryFailed,
    clearCompleted,
    removeAction,
    resolveConflict,
    getActionsByStatus,
    stats,
  } = useOfflineQueue();

  const { showSuccess, showError } = useSnackbar();
  
  const [selectedConflict, setSelectedConflict] = useState<ConflictItem | null>(null);
  const [conflictDialogOpen, setConflictDialogOpen] = useState(false);
  const [expandedSections, setExpandedSections] = useState<string[]>(['status']);

  const handleSectionExpand = (section: string) => (event: React.SyntheticEvent, expanded: boolean) => {
    setExpandedSections(prev => 
      expanded 
        ? [...prev, section]
        : prev.filter(s => s !== section)
    );
  };

  const handleRetryAction = async (actionId: string) => {
    try {
      const action = queueActions.find(a => a.id === actionId);
      if (action) {
        // Re-queue the specific action
        await processQueue();
        showSuccess('Action retried');
      }
    } catch (error) {
      showError('Failed to retry action');
    }
  };

  const handleRemoveAction = async (actionId: string) => {
    try {
      await removeAction(actionId);
    } catch (error) {
      showError('Failed to remove action');
    }
  };

  const handleConflictResolve = (conflict: ConflictItem) => {
    setSelectedConflict(conflict);
    setConflictDialogOpen(true);
  };

  const handleConflictResolution = async (resolution: 'client' | 'server' | 'merge') => {
    if (!selectedConflict) return;

    try {
      await resolveConflict(selectedConflict.id, resolution);
      setConflictDialogOpen(false);
      setSelectedConflict(null);
    } catch (error) {
      showError('Failed to resolve conflict');
    }
  };

  const getStatusIcon = (status: QueueAction['status']) => {
    switch (status) {
      case 'queued':
        return <ScheduleIcon color="primary" fontSize="small" />;
      case 'processing':
        return <SyncIcon 
          color="primary" 
          fontSize="small" 
          sx={{ 
            animation: 'rotation 1s infinite linear',
            '@keyframes rotation': {
              from: { transform: 'rotate(0deg)' },
              to: { transform: 'rotate(359deg)' }
            }
          }} 
        />;
      case 'completed':
        return <CheckCircleIcon color="success" fontSize="small" />;
      case 'failed':
        return <ErrorIcon color="error" fontSize="small" />;
      case 'conflict':
        return <WarningIcon color="warning" fontSize="small" />;
      default:
        return <ScheduleIcon fontSize="small" />;
    }
  };

  const getStatusColor = (status: QueueAction['status']) => {
    switch (status) {
      case 'queued': return 'primary';
      case 'processing': return 'info';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'conflict': return 'warning';
      default: return 'default';
    }
  };

  const formatActionLabel = (action: QueueAction) => {
    const operations = {
      create: 'Create',
      update: 'Update',
      delete: 'Delete',
    };
    
    const types = {
      contexts: 'Context',
      sessions: 'Session',
      messages: 'Message',
      documents: 'Document',
    };

    return `${operations[action.operation]} ${types[action.type as keyof typeof types] || action.type}`;
  };

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  if (compact) {
    return (
      <Paper sx={{ p: 2, maxHeight, overflow: 'auto' }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Typography variant="h6">Sync Status</Typography>
          <Box display="flex" alignItems="center" gap={1}>
            <Chip
              icon={networkStatus.isOnline ? <NetworkCheckIcon /> : <SyncDisabledIcon />}
              label={networkStatus.isOnline ? 'Online' : 'Offline'}
              color={networkStatus.isOnline ? 'success' : 'warning'}
              size="small"
            />
            {onClose && (
              <IconButton size="small" onClick={onClose}>
                <ClearIcon />
              </IconButton>
            )}
          </Box>
        </Box>

        {queueStatus.total === 0 ? (
          <Typography color="textSecondary" align="center">
            All changes are synced
          </Typography>
        ) : (
          <Box>
            <Grid container spacing={2} mb={2}>
              <Grid item xs={6}>
                <Card>
                  <CardContent sx={{ py: 1, '&:last-child': { pb: 1 } }}>
                    <Typography variant="body2" color="textSecondary">Pending</Typography>
                    <Typography variant="h6">{queueStatus.pending}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card>
                  <CardContent sx={{ py: 1, '&:last-child': { pb: 1 } }}>
                    <Typography variant="body2" color="textSecondary">Failed</Typography>
                    <Typography variant="h6" color="error.main">{queueStatus.failed}</Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {isProcessing && <LinearProgress sx={{ mb: 2 }} />}

            <Box display="flex" gap={1}>
              <Button
                size="small"
                variant="outlined"
                startIcon={<SyncIcon />}
                onClick={processQueue}
                disabled={isProcessing || !networkStatus.isOnline}
              >
                Sync Now
              </Button>
              {queueStatus.failed > 0 && (
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={retryFailed}
                >
                  Retry Failed
                </Button>
              )}
            </Box>
          </Box>
        )}
      </Paper>
    );
  }

  return (
    <Box>
      {/* Status Overview */}
      <Accordion 
        expanded={expandedSections.includes('status')} 
        onChange={handleSectionExpand('status')}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box display="flex" alignItems="center" gap={2} width="100%">
            <Typography variant="h6">Queue Status</Typography>
            <Chip
              icon={networkStatus.isOnline ? <NetworkCheckIcon /> : <SyncDisabledIcon />}
              label={networkStatus.isOnline ? 'Online' : 'Offline'}
              color={networkStatus.isOnline ? 'success' : 'warning'}
              size="small"
            />
            {queueStatus.total > 0 && (
              <Badge badgeContent={queueStatus.total} color="primary">
                <SyncIcon />
              </Badge>
            )}
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent>
                  <Typography variant="body2" color="textSecondary">Total Actions</Typography>
                  <Typography variant="h5">{queueStatus.total}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent>
                  <Typography variant="body2" color="textSecondary">Pending</Typography>
                  <Typography variant="h5" color="primary.main">{queueStatus.pending}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent>
                  <Typography variant="body2" color="textSecondary">Failed</Typography>
                  <Typography variant="h5" color="error.main">{queueStatus.failed}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent>
                  <Typography variant="body2" color="textSecondary">Conflicts</Typography>
                  <Typography variant="h5" color="warning.main">{queueStatus.conflicts}</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {isProcessing && (
            <Box mt={2}>
              <Typography variant="body2" mb={1}>Syncing...</Typography>
              <LinearProgress />
            </Box>
          )}

          <Box display="flex" gap={1} mt={2}>
            <Button
              variant="contained"
              startIcon={<SyncIcon />}
              onClick={processQueue}
              disabled={isProcessing || !networkStatus.isOnline || queueStatus.pending === 0}
            >
              Sync All ({queueStatus.pending})
            </Button>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={retryFailed}
              disabled={isProcessing || queueStatus.failed === 0}
            >
              Retry Failed ({queueStatus.failed})
            </Button>
            <Button
              variant="outlined"
              startIcon={<DeleteIcon />}
              onClick={clearCompleted}
              disabled={queueStatus.completed === 0}
            >
              Clear Completed ({queueStatus.completed})
            </Button>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Queue Actions */}
      {queueActions.length > 0 && (
        <Accordion 
          expanded={expandedSections.includes('actions')} 
          onChange={handleSectionExpand('actions')}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">
              Queue Actions ({queueActions.length})
            </Typography>
          </AccordionSummary>
          <AccordionDetails sx={{ maxHeight: 300, overflow: 'auto' }}>
            <List>
              {queueActions.map((action, index) => (
                <React.Fragment key={action.id}>
                  <ListItem>
                    <Box display="flex" alignItems="center" gap={1} mr={2}>
                      {getStatusIcon(action.status)}
                    </Box>
                    <ListItemText
                      primary={formatActionLabel(action)}
                      secondary={
                        <Box>
                          <Typography variant="caption" color="textSecondary">
                            {formatTimestamp(action.timestamp)}
                            {action.retryCount > 0 && ` • ${action.retryCount} retries`}
                          </Typography>
                          {action.error && (
                            <Typography variant="caption" color="error.main" display="block">
                              {action.error}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                    <Box display="flex" gap={1}>
                      <Chip
                        label={action.status}
                        color={getStatusColor(action.status) as any}
                        size="small"
                      />
                      <Chip
                        label={`Priority: ${action.priority}`}
                        variant="outlined"
                        size="small"
                      />
                    </Box>
                    <ListItemSecondaryAction>
                      <Box display="flex" gap={1}>
                        {action.status === 'failed' && (
                          <Tooltip title="Retry">
                            <IconButton
                              size="small"
                              onClick={() => handleRetryAction(action.id)}
                              disabled={isProcessing}
                            >
                              <RefreshIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                        {action.status !== 'processing' && (
                          <Tooltip title="Remove">
                            <IconButton
                              size="small"
                              onClick={() => handleRemoveAction(action.id)}
                              disabled={isProcessing}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Box>
                    </ListItemSecondaryAction>
                  </ListItem>
                  {index < queueActions.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </AccordionDetails>
        </Accordion>
      )}

      {/* Conflicts */}
      {conflicts.length > 0 && (
        <Accordion 
          expanded={expandedSections.includes('conflicts')} 
          onChange={handleSectionExpand('conflicts')}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6" color="warning.main">
              Conflicts ({conflicts.length})
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Alert severity="warning" sx={{ mb: 2 }}>
              These items have conflicts that need manual resolution
            </Alert>
            <List>
              {conflicts.map((conflict, index) => (
                <React.Fragment key={conflict.id}>
                  <ListItem>
                    <Box display="flex" alignItems="center" gap={1} mr={2}>
                      <WarningIcon color="warning" />
                    </Box>
                    <ListItemText
                      primary={`${conflict.type} Conflict`}
                      secondary={formatTimestamp(conflict.timestamp)}
                    />
                    <ListItemSecondaryAction>
                      <Button
                        size="small"
                        variant="outlined"
                        color="warning"
                        onClick={() => handleConflictResolve(conflict)}
                      >
                        Resolve
                      </Button>
                    </ListItemSecondaryAction>
                  </ListItem>
                  {index < conflicts.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </AccordionDetails>
        </Accordion>
      )}

      {/* Statistics */}
      <Accordion 
        expanded={expandedSections.includes('stats')} 
        onChange={handleSectionExpand('stats')}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Statistics</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography variant="body2" color="textSecondary">
                Failure Rate
              </Typography>
              <Typography variant="h6">
                {(stats.failureRate * 100).toFixed(1)}%
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body2" color="textSecondary">
                Avg Retries
              </Typography>
              <Typography variant="h6">
                {stats.avgRetryCount.toFixed(1)}
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <Typography variant="body2" color="textSecondary">
                Connection Type
              </Typography>
              <Typography variant="body1">
                {networkStatus.connectionType}
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <Typography variant="body2" color="textSecondary">
                Last Online
              </Typography>
              <Typography variant="body1">
                {networkStatus.lastOnline.toLocaleString()}
              </Typography>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Conflict Resolution Dialog */}
      <Dialog 
        open={conflictDialogOpen} 
        onClose={() => setConflictDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Resolve Conflict</DialogTitle>
        <DialogContent>
          {selectedConflict && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedConflict.type} Conflict
              </Typography>
              <Typography variant="body2" color="textSecondary" paragraph>
                Your local changes conflict with server data. Choose how to resolve:
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="subtitle1" color="primary">
                      Your Changes (Client)
                    </Typography>
                    <Box mt={1}>
                      <pre style={{ fontSize: '12px', overflow: 'auto' }}>
                        {JSON.stringify(selectedConflict.clientData, null, 2)}
                      </pre>
                    </Box>
                  </Paper>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="subtitle1" color="secondary">
                      Server Version
                    </Typography>
                    <Box mt={1}>
                      <pre style={{ fontSize: '12px', overflow: 'auto' }}>
                        {JSON.stringify(selectedConflict.serverData, null, 2)}
                      </pre>
                    </Box>
                  </Paper>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConflictDialogOpen(false)}>
            Cancel
          </Button>
          <Button 
            onClick={() => handleConflictResolution('server')}
            color="secondary"
          >
            Use Server Version
          </Button>
          <Button 
            onClick={() => handleConflictResolution('client')}
            color="primary"
          >
            Use My Changes
          </Button>
          <Button 
            onClick={() => handleConflictResolution('merge')}
            variant="contained"
          >
            Auto Merge
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default OfflineQueueManager;