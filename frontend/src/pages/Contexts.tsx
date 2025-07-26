import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  Typography,
  Chip,
  IconButton,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Add as AddIcon,
  MoreVert as MoreVertIcon,
  Refresh as RefreshIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as PlayIcon,
  Storage as StorageIcon,
  Code as CodeIcon,
  Storage as DatabaseIcon,
  Folder as FolderIcon,
} from '@mui/icons-material';
import { contextsAPI } from '../services/api';
import type { Context } from '../types/api';
import { useSnackbar } from '../contexts/SnackbarContext';
import { useAuth } from '../contexts/AuthContext';
import ContextWizard from '../components/Context/ContextWizard';
import ContextDetails from '../components/Context/ContextDetails';

const Contexts: React.FC = () => {
  const [contexts, setContexts] = useState<Context[]>([]);
  const [loading, setLoading] = useState(true);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [selectedContext, setSelectedContext] = useState<Context | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [contextToDelete, setContextToDelete] = useState<Context | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [menuContext, setMenuContext] = useState<Context | null>(null);

  const { showSuccess, showError } = useSnackbar();
  const { user, token } = useAuth();

  useEffect(() => {
    // Only load data when user is authenticated and token is available
    if (user && token) {
      loadContexts();
    }
  }, [user, token]);

  const loadContexts = async () => {
    try {
      setLoading(true);
      const response = await contextsAPI.getContexts();
      setContexts(response.contexts);
    } catch (error: any) {
      showError('Failed to load contexts');
    } finally {
      setLoading(false);
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, context: Context) => {
    setAnchorEl(event.currentTarget);
    setMenuContext(context);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setMenuContext(null);
  };

  const handleViewDetails = (context: Context) => {
    setSelectedContext(context);
    setDetailsOpen(true);
    handleMenuClose();
  };

  const handleReprocess = async (context: Context) => {
    try {
      await contextsAPI.reprocessContext(context.id);
      showSuccess('Context reprocessing started');
      loadContexts();
    } catch (error: any) {
      showError('Failed to start reprocessing');
    }
    handleMenuClose();
  };

  const handleDeleteClick = (context: Context) => {
    setContextToDelete(context);
    setDeleteDialogOpen(true);
    handleMenuClose();
  };

  const handleDeleteConfirm = async () => {
    if (!contextToDelete) return;

    try {
      await contextsAPI.deleteContext(contextToDelete.id);
      showSuccess('Context deleted successfully');
      loadContexts();
    } catch (error: any) {
      showError('Failed to delete context');
    } finally {
      setDeleteDialogOpen(false);
      setContextToDelete(null);
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

  const getSourceLabel = (sourceType: string) => {
    switch (sourceType) {
      case 'repo':
        return 'Repository';
      case 'database':
        return 'Database';
      case 'files':
        return 'Files';
      default:
        return sourceType;
    }
  };

  if (loading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Contexts
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, height: '100%', overflow: 'auto' }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Contexts
        </Typography>
        <Box display="flex" gap={1}>
          <IconButton onClick={loadContexts}>
            <RefreshIcon />
          </IconButton>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setWizardOpen(true)}
          >
            Create Context
          </Button>
        </Box>
      </Box>

      {contexts.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <StorageIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              No contexts created yet
            </Typography>
            <Typography color="text.secondary" paragraph>
              Create your first context to start building your knowledge base
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setWizardOpen(true)}
            >
              Create Context
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {contexts.map((context) => (
            <Grid xs={12} sm={6} md={4} key={context.id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  minHeight: 280
                }}
              >
                <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                    <Box display="flex" alignItems="center" gap={1}>
                      {getSourceIcon(context.source_type)}
                      <Typography variant="h6" noWrap>
                        {context.name}
                      </Typography>
                    </Box>
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenuOpen(e, context)}
                    >
                      <MoreVertIcon />
                    </IconButton>
                  </Box>

                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{
                      mb: 2,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                    }}
                  >
                    {context.description || 'No description'}
                  </Typography>

                  <Box display="flex" gap={1} mb={2} flexWrap="wrap">
                    <Chip
                      label={context.status}
                      color={getStatusColor(context.status) as any}
                      size="small"
                    />
                    <Chip
                      label={getSourceLabel(context.source_type)}
                      variant="outlined"
                      size="small"
                    />
                  </Box>

                  {context.status === 'processing' && (
                    <Box mb={2}>
                      <LinearProgress
                        variant="determinate"
                        value={context.progress}
                        sx={{ mb: 1 }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        {context.progress}% complete
                      </Typography>
                    </Box>
                  )}

                  <Box
                    display="flex"
                    justifyContent="space-between"
                    alignItems="center"
                    mt="auto"
                    pt={1}
                  >
                    <Typography variant="caption" color="text.secondary">
                      {context.total_chunks || 0} chunks
                    </Typography>
                    <Button
                      size="small"
                      onClick={() => handleViewDetails(context)}
                    >
                      View Details
                    </Button>
                  </Box>

                  {context.error_message && (
                    <Typography
                      variant="caption"
                      color="error"
                      sx={{
                        mt: 1,
                        display: 'block',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      Error: {context.error_message}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => menuContext && handleViewDetails(menuContext)}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Details</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => menuContext && handleReprocess(menuContext)}
          disabled={menuContext?.status === 'processing'}
        >
          <ListItemIcon>
            <PlayIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Reprocess</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => menuContext && handleDeleteClick(menuContext)}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Delete</ListItemText>
        </MenuItem>
      </Menu>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Context</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{contextToDelete?.name}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Context Creation Wizard */}
      <ContextWizard
        open={wizardOpen}
        onClose={() => setWizardOpen(false)}
        onSuccess={() => {
          setWizardOpen(false);
          loadContexts();
        }}
      />

      {/* Context Details Dialog */}
      <ContextDetails
        open={detailsOpen}
        context={selectedContext}
        onClose={() => {
          setDetailsOpen(false);
          setSelectedContext(null);
        }}
        onUpdate={loadContexts}
      />
    </Box>
  );
};

export default Contexts;
