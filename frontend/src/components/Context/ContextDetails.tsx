import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  Card,
  CardContent,
  Grid,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Storage as StorageIcon,
  Code as CodeIcon,
  Storage as DatabaseIcon,
  Folder as FolderIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material';
import { contextsAPI } from '../../services/api';
import type { Context, Document } from '../../types/api';
import { useSnackbar } from '../../contexts/SnackbarContext';

interface ContextDetailsProps {
  open: boolean;
  context: Context | null;
  onClose: () => void;
  onUpdate: () => void;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`context-tabpanel-${index}`}
      aria-labelledby={`context-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const ContextDetails: React.FC<ContextDetailsProps> = ({ open, context, onClose, onUpdate }) => {
  const [tabValue, setTabValue] = useState(0);
  const [contextDetails, setContextDetails] = useState<Context | null>(null);
  const [loading, setLoading] = useState(false);
  const { showError } = useSnackbar();

  useEffect(() => {
    if (open && context) {
      loadContextDetails();
    }
  }, [open, context]);

  const loadContextDetails = async () => {
    if (!context) return;

    try {
      setLoading(true);
      const response = await contextsAPI.getContext(context.id);
      setContextDetails(response.context);
    } catch (error: any) {
      showError('Failed to load context details');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'success';
      case 'processing':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getSourceIcon = (sourceType: string) => {
    switch (sourceType) {
      case 'repo':
        return <CodeIcon />;
      case 'database':
        return <DatabaseIcon />;
      case 'files':
        return <FolderIcon />;
      default:
        return <StorageIcon />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (!context) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={1}>
            {getSourceIcon(context.source_type)}
            <Typography variant="h6">{context.name}</Typography>
          </Box>
          <Tooltip title="Refresh">
            <span>
              <IconButton onClick={loadContextDetails} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {loading && <LinearProgress sx={{ mb: 2 }} />}
        
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
            <Tab label="Overview" />
            <Tab label="Documents" />
            <Tab label="Configuration" />
            <Tab label="Statistics" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Basic Information
                  </Typography>
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      Status
                    </Typography>
                    <Chip
                      label={context.status}
                      color={getStatusColor(context.status) as any}
                      size="small"
                    />
                  </Box>
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      Description
                    </Typography>
                    <Typography variant="body1">
                      {context.description || 'No description'}
                    </Typography>
                  </Box>
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      Source Type
                    </Typography>
                    <Typography variant="body1">{context.source_type}</Typography>
                  </Box>
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      Created
                    </Typography>
                    <Typography variant="body1">
                      {formatDate(context.created_at)}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Processing Status
                  </Typography>
                  {context.status === 'processing' && (
                    <Box mb={2}>
                      <LinearProgress
                        variant="determinate"
                        value={context.progress}
                        sx={{ mb: 1 }}
                      />
                      <Typography variant="body2" color="text.secondary">
                        {context.progress}% complete
                      </Typography>
                    </Box>
                  )}
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      Total Chunks
                    </Typography>
                    <Typography variant="h4">{context.total_chunks || 0}</Typography>
                  </Box>
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      Total Tokens
                    </Typography>
                    <Typography variant="h4">
                      {(context.total_tokens || 0).toLocaleString()}
                    </Typography>
                  </Box>
                  {context.error_message && (
                    <Box mb={2}>
                      <Typography variant="body2" color="error">
                        Error: {context.error_message}
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {contextDetails?.documents && contextDetails.documents.length > 0 ? (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Filename</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Size</TableCell>
                    <TableCell>Chunks</TableCell>
                    <TableCell>Tokens</TableCell>
                    <TableCell>Language</TableCell>
                    <TableCell>Processed</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {contextDetails.documents.map((doc) => (
                    <TableRow key={doc.id}>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          <DescriptionIcon fontSize="small" />
                          {doc.filename}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip label={doc.file_type} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>{formatFileSize(doc.file_size)}</TableCell>
                      <TableCell>{doc.chunks_count}</TableCell>
                      <TableCell>{doc.tokens_count?.toLocaleString()}</TableCell>
                      <TableCell>{doc.language || '-'}</TableCell>
                      <TableCell>
                        {doc.processed_at ? formatDate(doc.processed_at) : 'Pending'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Typography color="text.secondary" textAlign="center" py={4}>
              No documents found
            </Typography>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Configuration
              </Typography>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <Typography variant="body2" color="text.secondary">
                    Chunk Strategy
                  </Typography>
                  <Typography variant="body1">{context.chunk_strategy}</Typography>
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <Typography variant="body2" color="text.secondary">
                    Embedding Model
                  </Typography>
                  <Typography variant="body1">{context.embedding_model}</Typography>
                </Grid>
                <Grid size={{ xs: 12 }}>
                  <Typography variant="body2" color="text.secondary">
                    Source Configuration
                  </Typography>
                  <Paper sx={{ p: 2, mt: 1, backgroundColor: 'grey.50' }}>
                    <pre style={{ margin: 0, fontSize: '0.875rem' }}>
                      {JSON.stringify(context.config, null, 2)}
                    </pre>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 4 }}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <StorageIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
                  <Typography variant="h4">{context.total_chunks || 0}</Typography>
                  <Typography color="text.secondary">Total Chunks</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <DescriptionIcon sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
                  <Typography variant="h4">
                    {contextDetails?.documents?.length || 0}
                  </Typography>
                  <Typography color="text.secondary">Documents</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <CodeIcon sx={{ fontSize: 48, color: 'warning.main', mb: 1 }} />
                  <Typography variant="h4">
                    {(context.total_tokens || 0).toLocaleString()}
                  </Typography>
                  <Typography color="text.secondary">Total Tokens</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default ContextDetails;
