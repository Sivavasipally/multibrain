/**
 * Settings Page for RAG Chatbot PWA
 * 
 * Comprehensive user preferences and settings management interface.
 * Organized by categories with search, import/export, and templates.
 * 
 * Features:
 * - Categorized settings organization
 * - Real-time preference updates
 * - Import/export functionality
 * - Preference templates
 * - Search and filtering
 * - Reset to defaults
 * - Offline support with sync status
 * 
 * Author: RAG Chatbot Development Team
 * Version: 2.0.0
 */

import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Tabs,
  Tab,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Switch,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  TextField,
  Alert,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  IconButton,
  Badge,
  LinearProgress,
} from '@mui/material';
import {
  Palette as PaletteIcon,
  Chat as ChatIcon,
  Search as SearchIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Refresh as RefreshIcon,
  Save as SaveIcon,
  Settings as SettingsIcon,
  ExpandMore as ExpandMoreIcon,
  Info as InfoIcon,
  Sync as SyncIcon,
  Dashboard as TemplateIcon,
} from '@mui/icons-material';
import { usePreferences } from '../contexts/PreferencesContext';
import { useSnackbar } from '../contexts/SnackbarContext';
import { preferencesAPI } from '../services/api';

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
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const Settings: React.FC = () => {
  const {
    preferences,
    loading,
    hasChanges,
    lastSyncTime,
    updatePreference,
    updateCategoryPreferences,
    resetCategory,
    resetAllPreferences,
    exportPreferences,
    importPreferences,
    applyTemplate,
  } = usePreferences();
  
  const { showSuccess, showError, showWarning } = useSnackbar();
  
  const [activeTab, setActiveTab] = useState(0);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [templatesDialogOpen, setTemplatesDialogOpen] = useState(false);
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [resetTarget, setResetTarget] = useState<string | null>(null);
  const [templates, setTemplates] = useState<any[]>([]);
  const [importData, setImportData] = useState('');

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await preferencesAPI.getTemplates();
      if (response.success) {
        setTemplates(response.templates);
      }
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleExport = async (format: 'json' | 'csv') => {
    try {
      await exportPreferences(format);
    } catch (error) {
      showError('Failed to export preferences');
    }
  };

  const handleImport = async () => {
    try {
      const data = JSON.parse(importData);
      await importPreferences(data, true); // Merge mode
      setImportDialogOpen(false);
      setImportData('');
    } catch (error: any) {
      if (error.name === 'SyntaxError') {
        showError('Invalid JSON format');
      } else {
        showError('Failed to import preferences');
      }
    }
  };

  const handleReset = async () => {
    try {
      if (resetTarget === 'all') {
        await resetAllPreferences();
      } else if (resetTarget) {
        await resetCategory(resetTarget as any);
      }
      setResetDialogOpen(false);
      setResetTarget(null);
    } catch (error) {
      showError('Failed to reset preferences');
    }
  };

  const handleApplyTemplate = async (templateId: number) => {
    try {
      await applyTemplate(templateId);
      setTemplatesDialogOpen(false);
    } catch (error) {
      showError('Failed to apply template');
    }
  };

  const openResetDialog = (target: string) => {
    setResetTarget(target);
    setResetDialogOpen(true);
  };

  const categoryIcons = {
    appearance: <PaletteIcon />,
    chat: <ChatIcon />,
    search: <SearchIcon />,
    privacy: <SecurityIcon />,
    performance: <SpeedIcon />,
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={4}>
        <Box display="flex" alignItems="center" gap={2}>
          <SettingsIcon sx={{ fontSize: 32 }} />
          <Typography variant="h4">Settings</Typography>
          {hasChanges && (
            <Badge color="warning" variant="dot">
              <Chip label="Unsaved Changes" size="small" color="warning" />
            </Badge>
          )}
        </Box>
        
        <Box display="flex" gap={1}>
          <Tooltip title="Import Settings">
            <IconButton onClick={() => setImportDialogOpen(true)}>
              <UploadIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Export Settings">
            <Button
              startIcon={<DownloadIcon />}
              variant="outlined"
              size="small"
              onClick={() => handleExport('json')}
            >
              Export
            </Button>
          </Tooltip>
          <Tooltip title="Browse Templates">
            <Button
              startIcon={<TemplateIcon />}
              variant="outlined"
              size="small"
              onClick={() => setTemplatesDialogOpen(true)}
            >
              Templates
            </Button>
          </Tooltip>
        </Box>
      </Box>

      {/* Sync Status */}
      {(loading || hasChanges || lastSyncTime) && (
        <Alert 
          severity={hasChanges ? 'warning' : 'info'} 
          sx={{ mb: 3 }}
          icon={hasChanges ? <SyncIcon /> : <InfoIcon />}
        >
          <Box display="flex" alignItems="center" gap={2} width="100%">
            <Typography variant="body2">
              {loading ? 'Loading preferences...' : 
               hasChanges ? 'You have unsaved changes that will sync automatically' :
               `Last synced: ${lastSyncTime?.toLocaleString()}`}
            </Typography>
            {loading && <LinearProgress sx={{ flexGrow: 1, ml: 2 }} />}
          </Box>
        </Alert>
      )}

      {/* Settings Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<PaletteIcon />} label="Appearance" />
          <Tab icon={<ChatIcon />} label="Chat" />
          <Tab icon={<SearchIcon />} label="Search" />
          <Tab icon={<SecurityIcon />} label="Privacy" />
          <Tab icon={<SpeedIcon />} label="Performance" />
        </Tabs>

        {/* Appearance Settings */}
        <TabPanel value={activeTab} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Theme</Typography>
                  <FormControl fullWidth margin="normal">
                    <InputLabel>Theme</InputLabel>
                    <Select
                      value={preferences.appearance.theme}
                      onChange={(e) => updatePreference('appearance', 'theme', e.target.value)}
                    >
                      <MenuItem value="light">Light</MenuItem>
                      <MenuItem value="dark">Dark</MenuItem>
                      <MenuItem value="system">System</MenuItem>
                    </Select>
                  </FormControl>
                  
                  <FormControl fullWidth margin="normal">
                    <InputLabel>Font Size</InputLabel>
                    <Select
                      value={preferences.appearance.fontSize}
                      onChange={(e) => updatePreference('appearance', 'fontSize', e.target.value)}
                    >
                      <MenuItem value="small">Small</MenuItem>
                      <MenuItem value="medium">Medium</MenuItem>
                      <MenuItem value="large">Large</MenuItem>
                    </Select>
                  </FormControl>

                  <Box display="flex" alignItems="center" justifyContent="space-between" mt={2}>
                    <Typography>Compact Mode</Typography>
                    <Switch
                      checked={preferences.appearance.compactMode}
                      onChange={(e) => updatePreference('appearance', 'compactMode', e.target.checked)}
                    />
                  </Box>
                </CardContent>
                <CardActions>
                  <Button 
                    size="small" 
                    onClick={() => openResetDialog('appearance')}
                    startIcon={<RefreshIcon />}
                  >
                    Reset to Defaults
                  </Button>
                </CardActions>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Localization</Typography>
                  
                  <TextField
                    fullWidth
                    label="Language"
                    value={preferences.appearance.language}
                    onChange={(e) => updatePreference('appearance', 'language', e.target.value)}
                    margin="normal"
                  />
                  
                  <TextField
                    fullWidth
                    label="Timezone"
                    value={preferences.appearance.timezone}
                    onChange={(e) => updatePreference('appearance', 'timezone', e.target.value)}
                    margin="normal"
                  />
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Chat Settings */}
        <TabPanel value={activeTab} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Chat Behavior</Typography>
                  
                  <FormControl fullWidth margin="normal">
                    <InputLabel>Default Model</InputLabel>
                    <Select
                      value={preferences.chat.defaultModel}
                      onChange={(e) => updatePreference('chat', 'defaultModel', e.target.value)}
                    >
                      <MenuItem value="gemini-pro">Gemini Pro</MenuItem>
                      <MenuItem value="gemini-pro-vision">Gemini Pro Vision</MenuItem>
                    </Select>
                  </FormControl>

                  <Typography gutterBottom>Message History Limit</Typography>
                  <Slider
                    value={preferences.chat.messageLimit}
                    onChange={(e, value) => updatePreference('chat', 'messageLimit', value)}
                    min={10}
                    max={1000}
                    step={10}
                    valueLabelDisplay="auto"
                    marks={[
                      { value: 50, label: '50' },
                      { value: 200, label: '200' },
                      { value: 500, label: '500' }
                    ]}
                  />

                  <Box display="flex" alignItems="center" justifyContent="space-between" mt={2}>
                    <Typography>Auto-save Conversations</Typography>
                    <Switch
                      checked={preferences.chat.autoSave}
                      onChange={(e) => updatePreference('chat', 'autoSave', e.target.checked)}
                    />
                  </Box>

                  <Box display="flex" alignItems="center" justifyContent="space-between" mt={1}>
                    <Typography>Show Timestamps</Typography>
                    <Switch
                      checked={preferences.chat.showTimestamps}
                      onChange={(e) => updatePreference('chat', 'showTimestamps', e.target.checked)}
                    />
                  </Box>
                </CardContent>
                <CardActions>
                  <Button 
                    size="small" 
                    onClick={() => openResetDialog('chat')}
                    startIcon={<RefreshIcon />}
                  >
                    Reset to Defaults
                  </Button>
                </CardActions>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Notifications & Effects</Typography>

                  <Box display="flex" alignItems="center" justifyContent="space-between" mt={2}>
                    <Typography>Enable Notifications</Typography>
                    <Switch
                      checked={preferences.chat.enableNotifications}
                      onChange={(e) => updatePreference('chat', 'enableNotifications', e.target.checked)}
                    />
                  </Box>

                  <Box display="flex" alignItems="center" justifyContent="space-between" mt={1}>
                    <Typography>Sound Effects</Typography>
                    <Switch
                      checked={preferences.chat.soundEffects}
                      onChange={(e) => updatePreference('chat', 'soundEffects', e.target.checked)}
                    />
                  </Box>

                  <Box display="flex" alignItems="center" justifyContent="space-between" mt={1}>
                    <Typography>Typing Indicator</Typography>
                    <Switch
                      checked={preferences.chat.typingIndicator}
                      onChange={(e) => updatePreference('chat', 'typingIndicator', e.target.checked)}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Search Settings */}
        <TabPanel value={activeTab} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Search Behavior</Typography>
                  
                  <FormControl fullWidth margin="normal">
                    <InputLabel>Default Search Type</InputLabel>
                    <Select
                      value={preferences.search.defaultSearchType}
                      onChange={(e) => updatePreference('search', 'defaultSearchType', e.target.value)}
                    >
                      <MenuItem value="semantic">Semantic Search</MenuItem>
                      <MenuItem value="keyword">Keyword Search</MenuItem>
                      <MenuItem value="hybrid">Hybrid Search</MenuItem>
                    </Select>
                  </FormControl>

                  <Typography gutterBottom>Maximum Results</Typography>
                  <Slider
                    value={preferences.search.maxResults}
                    onChange={(e, value) => updatePreference('search', 'maxResults', value)}
                    min={5}
                    max={100}
                    step={5}
                    valueLabelDisplay="auto"
                    marks={[
                      { value: 10, label: '10' },
                      { value: 50, label: '50' },
                      { value: 100, label: '100' }
                    ]}
                  />

                  <Box display="flex" alignItems="center" justifyContent="space-between" mt={2}>
                    <Typography>Auto-complete</Typography>
                    <Switch
                      checked={preferences.search.enableAutoComplete}
                      onChange={(e) => updatePreference('search', 'enableAutoComplete', e.target.checked)}
                    />
                  </Box>

                  <Box display="flex" alignItems="center" justifyContent="space-between" mt={1}>
                    <Typography>Search History</Typography>
                    <Switch
                      checked={preferences.search.searchHistory}
                      onChange={(e) => updatePreference('search', 'searchHistory', e.target.checked)}
                    />
                  </Box>
                </CardContent>
                <CardActions>
                  <Button 
                    size="small" 
                    onClick={() => openResetDialog('search')}
                    startIcon={<RefreshIcon />}
                  >
                    Reset to Defaults
                  </Button>
                </CardActions>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Indexing</Typography>

                  <Box display="flex" alignItems="center" justifyContent="space-between" mt={2}>
                    <Typography>Enable Background Indexing</Typography>
                    <Switch
                      checked={preferences.search.indexingEnabled}
                      onChange={(e) => updatePreference('search', 'indexingEnabled', e.target.checked)}
                    />
                  </Box>

                  <Alert severity="info" sx={{ mt: 2 }}>
                    Background indexing improves search performance but may use more system resources.
                  </Alert>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Privacy Settings */}
        <TabPanel value={activeTab} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Data Sharing</Typography>

                  <Box display="flex" alignItems="center" justifyContent="space-between" mt={2}>
                    <Typography>Share Usage Data</Typography>
                    <Switch
                      checked={preferences.privacy.shareUsageData}
                      onChange={(e) => updatePreference('privacy', 'shareUsageData', e.target.checked)}
                    />
                  </Box>

                  <Box display="flex" alignItems="center" justifyContent="space-between" mt={1}>
                    <Typography>Enable Analytics</Typography>
                    <Switch
                      checked={preferences.privacy.enableAnalytics}
                      onChange={(e) => updatePreference('privacy', 'enableAnalytics', e.target.checked)}
                    />
                  </Box>

                  <Typography gutterBottom sx={{ mt: 3 }}>Data Retention (Days)</Typography>
                  <Slider
                    value={preferences.privacy.dataRetentionDays}
                    onChange={(e, value) => updatePreference('privacy', 'dataRetentionDays', value)}
                    min={7}
                    max={365}
                    step={7}
                    valueLabelDisplay="auto"
                    marks={[
                      { value: 30, label: '30' },
                      { value: 90, label: '90' },
                      { value: 365, label: '365' }
                    ]}
                  />
                </CardContent>
                <CardActions>
                  <Button 
                    size="small" 
                    onClick={() => openResetDialog('privacy')}
                    startIcon={<RefreshIcon />}
                  >
                    Reset to Defaults
                  </Button>
                </CardActions>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Export Format</Typography>
                  
                  <FormControl fullWidth margin="normal">
                    <InputLabel>Default Export Format</InputLabel>
                    <Select
                      value={preferences.privacy.exportFormat}
                      onChange={(e) => updatePreference('privacy', 'exportFormat', e.target.value)}
                    >
                      <MenuItem value="json">JSON</MenuItem>
                      <MenuItem value="csv">CSV</MenuItem>
                      <MenuItem value="markdown">Markdown</MenuItem>
                    </Select>
                  </FormControl>

                  <Alert severity="warning" sx={{ mt: 2 }}>
                    Your data is processed locally and never sent to third parties without your consent.
                  </Alert>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Performance Settings */}
        <TabPanel value={activeTab} index={4}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Caching</Typography>

                  <Typography gutterBottom>Cache Size (MB)</Typography>
                  <Slider
                    value={preferences.performance.cacheSize}
                    onChange={(e, value) => updatePreference('performance', 'cacheSize', value)}
                    min={10}
                    max={1000}
                    step={10}
                    valueLabelDisplay="auto"
                    marks={[
                      { value: 50, label: '50' },
                      { value: 200, label: '200' },
                      { value: 500, label: '500' }
                    ]}
                  />

                  <Box display="flex" alignItems="center" justifyContent="space-between" mt={2}>
                    <Typography>Enable Prefetching</Typography>
                    <Switch
                      checked={preferences.performance.prefetchEnabled}
                      onChange={(e) => updatePreference('performance', 'prefetchEnabled', e.target.checked)}
                    />
                  </Box>

                  <Typography gutterBottom sx={{ mt: 3 }}>Compression Level</Typography>
                  <Slider
                    value={preferences.performance.compressionLevel}
                    onChange={(e, value) => updatePreference('performance', 'compressionLevel', value)}
                    min={0}
                    max={9}
                    step={1}
                    valueLabelDisplay="auto"
                    marks={[
                      { value: 0, label: 'None' },
                      { value: 6, label: 'Default' },
                      { value: 9, label: 'Max' }
                    ]}
                  />
                </CardContent>
                <CardActions>
                  <Button 
                    size="small" 
                    onClick={() => openResetDialog('performance')}
                    startIcon={<RefreshIcon />}
                  >
                    Reset to Defaults
                  </Button>
                </CardActions>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Processing</Typography>

                  <Typography gutterBottom>Batch Size</Typography>
                  <Slider
                    value={preferences.performance.batchSize}
                    onChange={(e, value) => updatePreference('performance', 'batchSize', value)}
                    min={1}
                    max={100}
                    step={1}
                    valueLabelDisplay="auto"
                    marks={[
                      { value: 10, label: '10' },
                      { value: 50, label: '50' },
                      { value: 100, label: '100' }
                    ]}
                  />

                  <Alert severity="info" sx={{ mt: 2 }}>
                    Higher cache sizes and compression levels improve performance but use more memory.
                  </Alert>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>

      {/* Global Actions */}
      <Box display="flex" gap={2} justifyContent="center">
        <Button
          variant="contained"
          color="error"
          onClick={() => openResetDialog('all')}
          startIcon={<RefreshIcon />}
        >
          Reset All Settings
        </Button>
      </Box>

      {/* Import Dialog */}
      <Dialog open={importDialogOpen} onClose={() => setImportDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Import Settings</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={10}
            label="Paste JSON settings data"
            value={importData}
            onChange={(e) => setImportData(e.target.value)}
            sx={{ mt: 2 }}
          />
          <Alert severity="info" sx={{ mt: 2 }}>
            Importing will merge with your existing settings. Invalid settings will be ignored.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImportDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleImport} variant="contained" disabled={!importData.trim()}>
            Import
          </Button>
        </DialogActions>
      </Dialog>

      {/* Templates Dialog */}
      <Dialog open={templatesDialogOpen} onClose={() => setTemplatesDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Preference Templates</DialogTitle>
        <DialogContent>
          <List>
            {templates.map((template, index) => (
              <React.Fragment key={template.id}>
                <ListItem>
                  <ListItemText
                    primary={template.name}
                    secondary={
                      <Box>
                        <Typography variant="body2">{template.description}</Typography>
                        <Chip label={template.category} size="small" sx={{ mt: 1 }} />
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <Button
                      size="small"
                      onClick={() => handleApplyTemplate(template.id)}
                    >
                      Apply
                    </Button>
                  </ListItemSecondaryAction>
                </ListItem>
                {index < templates.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
          {templates.length === 0 && (
            <Typography color="textSecondary" align="center" sx={{ py: 4 }}>
              No templates available
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTemplatesDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Reset Confirmation Dialog */}
      <Dialog open={resetDialogOpen} onClose={() => setResetDialogOpen(false)}>
        <DialogTitle>Confirm Reset</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to reset {resetTarget === 'all' ? 'all settings' : `${resetTarget} settings`} to defaults?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResetDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleReset} color="error" variant="contained">
            Reset
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Settings;