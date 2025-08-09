/**
 * Offline Page Component for RAG Chatbot PWA
 * 
 * Comprehensive offline experience page providing access to cached data,
 * offline functionality, and network status information. Shows available
 * offline features and guides users through offline capabilities.
 * 
 * Features:
 * - Offline functionality overview
 * - Cached data access
 * - Network reconnection assistance
 * - Sync queue management
 * - Local storage statistics
 * - Offline mode tutorials
 * 
 * Author: RAG Chatbot Development Team
 * Version: 2.0.0
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  LinearProgress,
  Chip,
  Tabs,
  Tab,
  Paper,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  CloudOff as CloudOffIcon,
  Refresh as RefreshIcon,
  Storage as StorageIcon,
  Chat as ChatIcon,
  Folder as FolderIcon,
  Sync as SyncIcon,
  Info as InfoIcon,
  Settings as SettingsIcon,
  WifiOff as WifiOffIcon,
  Router as RouterIcon,
  PhoneIphone as PhoneIcon,
  Computer as ComputerIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useOfflineStorage } from '../hooks/useOfflineStorage';
import { useOfflineQueue } from '../hooks/useOfflineQueue';
import OfflineQueueManager from '../components/Offline/OfflineQueueManager';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel({ children, value, index, ...other }: TabPanelProps) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`offline-tabpanel-${index}`}
      aria-labelledby={`offline-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const OfflinePage: React.FC = () => {
  const navigate = useNavigate();
  const offlineStorage = useOfflineStorage();
  const { queueStatus, networkStatus, processQueue } = useOfflineQueue();
  
  const [activeTab, setActiveTab] = useState(0);
  const [storageStats, setStorageStats] = useState<any>(null);
  const [cachedData, setCachedData] = useState<any>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    loadOfflineData();
    loadStorageStats();
  }, []);

  const loadOfflineData = async () => {
    try {
      const [contexts, sessions, messages] = await Promise.all([
        offlineStorage.getCachedContexts(),
        offlineStorage.getCachedSessions(),
        // Get messages for all sessions
        Promise.resolve([]), // This would need to aggregate messages from all sessions
      ]);

      setCachedData({
        contexts: contexts || [],
        sessions: sessions || [],
        messages: messages || [],
      });
    } catch (error) {
      console.error('Failed to load offline data:', error);
    }
  };

  const loadStorageStats = async () => {
    try {
      const cacheSize = await offlineStorage.getCacheSize();
      
      // Estimate storage usage
      let estimatedUsage = 0;
      if ('storage' in navigator && 'estimate' in navigator.storage) {
        const estimate = await navigator.storage.estimate();
        estimatedUsage = estimate.usage || 0;
      }

      setStorageStats({
        cacheSize,
        totalUsage: estimatedUsage,
        usageFormatted: formatBytes(estimatedUsage),
        cacheSizeFormatted: formatBytes(cacheSize),
      });
    } catch (error) {
      console.error('Failed to load storage stats:', error);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      // Check if we're back online
      if (navigator.onLine) {
        window.location.reload();
        return;
      }
      
      // Refresh offline data
      await loadOfflineData();
      await loadStorageStats();
    } catch (error) {
      console.error('Refresh failed:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleTroubleShoot = () => {
    setActiveTab(2); // Network tab
  };

  const handleGoHome = () => {
    navigate('/');
  };

  const handleOpenChat = () => {
    if (cachedData?.sessions?.length > 0) {
      navigate(`/chat/${cachedData.sessions[0].id}`);
    } else {
      navigate('/chat');
    }
  };

  const handleOpenContexts = () => {
    navigate('/contexts');
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const getNetworkIcon = () => {
    if (networkStatus.isOnline) return <RouterIcon />;
    return <WifiOffIcon />;
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box textAlign="center" mb={4}>
        <CloudOffIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
        <Typography variant="h3" gutterBottom>
          You're Offline
        </Typography>
        <Typography variant="h6" color="text.secondary" paragraph>
          Don't worry! The RAG Chatbot works offline too.
        </Typography>
        
        <Box display="flex" gap={2} justifyContent="center" mb={3}>
          <Button
            variant="contained"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            {isRefreshing ? 'Checking...' : 'Check Connection'}
          </Button>
          <Button
            variant="outlined"
            onClick={handleGoHome}
          >
            Go Home
          </Button>
        </Box>

        {isRefreshing && (
          <Box sx={{ width: '100%', maxWidth: 400, mx: 'auto' }}>
            <LinearProgress />
          </Box>
        )}
      </Box>

      {/* Network Status Alert */}
      <Alert 
        severity="info" 
        sx={{ mb: 3 }}
        action={
          <Button size="small" onClick={handleTroubleShoot}>
            Troubleshoot
          </Button>
        }
      >
        <Typography variant="body2">
          Your device is not connected to the internet. You can still access cached data and make changes that will sync when you're back online.
        </Typography>
      </Alert>

      {/* Sync Queue Status */}
      {queueStatus.total > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="body2">
            You have {queueStatus.total} pending changes that will sync when you're back online.
            {queueStatus.failed > 0 && ` ${queueStatus.failed} actions need attention.`}
          </Typography>
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange}
          variant="fullWidth"
        >
          <Tab label="Offline Features" icon={<StorageIcon />} />
          <Tab label="Your Data" icon={<FolderIcon />} />
          <Tab label="Network Help" icon={getNetworkIcon()} />
          <Tab label="Sync Queue" icon={<SyncIcon />} />
        </Tabs>

        <TabPanel value={activeTab} index={0}>
          {/* Offline Features */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2} mb={2}>
                    <ChatIcon color="primary" />
                    <Typography variant="h6">Chat History</Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Access your previous conversations and continue chatting with cached contexts.
                  </Typography>
                  <Chip 
                    label={`${cachedData?.sessions?.length || 0} sessions available`}
                    size="small" 
                    color="primary" 
                  />
                </CardContent>
                <CardActions>
                  <Button size="small" onClick={handleOpenChat}>
                    Open Chat
                  </Button>
                </CardActions>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2} mb={2}>
                    <FolderIcon color="primary" />
                    <Typography variant="h6">Cached Contexts</Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Browse and search through your cached contexts and documents.
                  </Typography>
                  <Chip 
                    label={`${cachedData?.contexts?.length || 0} contexts available`}
                    size="small" 
                    color="primary" 
                  />
                </CardContent>
                <CardActions>
                  <Button size="small" onClick={handleOpenContexts}>
                    Browse Contexts
                  </Button>
                </CardActions>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2} mb={2}>
                    <StorageIcon color="primary" />
                    <Typography variant="h6">Local Storage</Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Your data is stored locally and will remain available offline.
                  </Typography>
                  {storageStats && (
                    <Chip 
                      label={`${storageStats.cacheSizeFormatted} cached`}
                      size="small" 
                      color="primary" 
                    />
                  )}
                </CardContent>
                <CardActions>
                  <Button size="small" onClick={() => setActiveTab(1)}>
                    View Details
                  </Button>
                </CardActions>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2} mb={2}>
                    <SyncIcon color="primary" />
                    <Typography variant="h6">Auto Sync</Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Changes are automatically synced when connection is restored.
                  </Typography>
                  <Chip 
                    label={queueStatus.total > 0 ? `${queueStatus.total} pending` : 'Up to date'}
                    size="small" 
                    color={queueStatus.total > 0 ? 'warning' : 'success'} 
                  />
                </CardContent>
                <CardActions>
                  <Button size="small" onClick={() => setActiveTab(3)}>
                    View Queue
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          {/* Your Data */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Storage Usage</Typography>
                  {storageStats ? (
                    <Box>
                      <Typography variant="h4" color="primary.main">
                        {storageStats.cacheSizeFormatted}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Cached offline data
                      </Typography>
                      {storageStats.totalUsage > 0 && (
                        <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                          Total app storage: {storageStats.usageFormatted}
                        </Typography>
                      )}
                    </Box>
                  ) : (
                    <Typography>Loading...</Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Available Data</Typography>
                  <List>
                    <ListItem>
                      <ListItemIcon>
                        <ChatIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary={`${cachedData?.sessions?.length || 0} Chat Sessions`}
                        secondary="Previous conversations available offline"
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <FolderIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary={`${cachedData?.contexts?.length || 0} Contexts`}
                        secondary="Knowledge bases and document collections"
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <StorageIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary="User Preferences"
                        secondary="Settings and customizations stored locally"
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          {/* Network Help */}
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Alert severity="info" sx={{ mb: 3 }}>
                <Typography variant="body2">
                  Having trouble connecting? Try these troubleshooting steps.
                </Typography>
              </Alert>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2} mb={2}>
                    <PhoneIcon color="primary" />
                    <Typography variant="h6">Mobile Connection</Typography>
                  </Box>
                  <List dense>
                    <ListItem>
                      <ListItemText primary="Check cellular signal strength" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Try switching between WiFi and mobile data" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Restart your mobile connection" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Check airplane mode is off" />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2} mb={2}>
                    <RouterIcon color="primary" />
                    <Typography variant="h6">WiFi Connection</Typography>
                  </Box>
                  <List dense>
                    <ListItem>
                      <ListItemText primary="Check WiFi is enabled and connected" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Try reconnecting to your network" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Move closer to your router" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Restart your router if needed" />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2} mb={2}>
                    <ComputerIcon color="primary" />
                    <Typography variant="h6">Browser Issues</Typography>
                  </Box>
                  <List dense>
                    <ListItem>
                      <ListItemText primary="Check browser is up to date" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Clear browser cache and cookies" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Disable VPN or proxy temporarily" />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Try incognito/private mode" />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2} mb={2}>
                    <InfoIcon color="primary" />
                    <Typography variant="h6">Quick Checks</Typography>
                  </Box>
                  <List dense>
                    <ListItem>
                      <ListItemText 
                        primary="Network Status"
                        secondary={networkStatus.isOnline ? "Online" : "Offline"}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Connection Type"
                        secondary={networkStatus.connectionType || "Unknown"}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Last Online"
                        secondary={networkStatus.lastOnline.toLocaleString()}
                      />
                    </ListItem>
                  </List>
                </CardContent>
                <CardActions>
                  <Button size="small" onClick={handleRefresh} startIcon={<RefreshIcon />}>
                    Test Connection
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          {/* Sync Queue */}
          <OfflineQueueManager />
        </TabPanel>
      </Paper>

      {/* Footer Actions */}
      <Box textAlign="center" sx={{ mt: 4 }}>
        <Typography variant="body2" color="text.secondary" paragraph>
          The RAG Chatbot automatically saves your work and syncs when you're back online.
        </Typography>
        
        <Box display="flex" gap={2} justifyContent="center">
          <Button
            variant="outlined"
            startIcon={<ChatIcon />}
            onClick={handleOpenChat}
            disabled={!cachedData?.sessions?.length}
          >
            Continue Chatting
          </Button>
          <Button
            variant="outlined"
            startIcon={<FolderIcon />}
            onClick={handleOpenContexts}
          >
            Browse Contexts
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default OfflinePage;