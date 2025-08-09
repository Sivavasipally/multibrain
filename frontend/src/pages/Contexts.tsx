import React, { useState, useEffect, useMemo, useCallback } from 'react';
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
  TextField,
  FormControl,
  InputLabel,
  Select,
  InputAdornment,
  Collapse,
  Paper,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Badge,
  List,
  ListItem,
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
  Search as SearchIcon,
  Clear as ClearIcon,
  FilterList as FilterListIcon,
  Sort as SortIcon,
  ViewModule as GridViewIcon,
  ViewList as ListViewIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { contextsAPI } from '../services/api';
import type { Context, SearchResult } from '../types/api';
import { contextSearchService } from '../services/contextSearchService';
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
  
  // Search and filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'ready' | 'processing' | 'error'>('all');
  const [sourceTypeFilter, setSourceTypeFilter] = useState<'all' | 'repo' | 'database' | 'files'>('all');
  const [sortBy, setSortBy] = useState<'name' | 'created_at' | 'chunks' | 'status'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [filtersExpanded, setFiltersExpanded] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [searchSuggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const { showSuccess, showError, showWarning } = useSnackbar();
  const { user, token } = useAuth();

  // Utility function to clear API cache
  const clearAPICache = async (endpoint: string) => {
    if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
      try {
        const cacheNames = await caches.keys();
        for (const cacheName of cacheNames) {
          if (cacheName.includes('api')) {
            const cache = await caches.open(cacheName);
            await cache.delete(endpoint);
            console.log(`🧹 Cleared cache for ${endpoint}`);
          }
        }
      } catch (error) {
        console.warn('Failed to clear cache:', error);
      }
    }
  };

  useEffect(() => {
    // Only load data when user is authenticated and token is available
    // Use a ref to prevent loops when user/token objects change but values are same
    if (user?.id && token) {
      loadContexts();
    }
  }, [user?.id, token]); // Only depend on user ID, not entire user object

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
      await clearAPICache('/api/contexts');
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
      
      // Clear service worker cache for contexts to ensure fresh data
      await clearAPICache('/api/contexts');
      
      // Optimistically remove from local state first for immediate UI update
      setContexts(prev => prev.filter(ctx => ctx.id !== contextToDelete.id));
      
      showSuccess('Context deleted successfully');
      
      // Still reload from server to be safe
      loadContexts();
    } catch (error: any) {
      showError('Failed to delete context');
      // Reload contexts on error to ensure consistency
      loadContexts();
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

  // Filter and sort contexts
  const filteredAndSortedContexts = useMemo(() => {
    let filtered = contexts.filter(context => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        if (!context.name.toLowerCase().includes(query) && 
            !context.description?.toLowerCase().includes(query)) {
          return false;
        }
      }
      
      // Status filter
      if (statusFilter !== 'all' && context.status !== statusFilter) {
        return false;
      }
      
      // Source type filter
      if (sourceTypeFilter !== 'all' && context.source_type !== sourceTypeFilter) {
        return false;
      }
      
      return true;
    });

    // Sort contexts
    filtered.sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'created_at':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'chunks':
          comparison = (a.total_chunks || 0) - (b.total_chunks || 0);
          break;
        case 'status':
          comparison = a.status.localeCompare(b.status);
          break;
        default:
          comparison = 0;
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }, [contexts, searchQuery, statusFilter, sourceTypeFilter, sortBy, sortOrder]);

  const handleClearSearch = () => {
    setSearchQuery('');
    setStatusFilter('all');
    setSourceTypeFilter('all');
    setIsSearchMode(false);
    setSearchResults([]);
    setShowSuggestions(false);
  };

  const handleSortToggle = () => {
    setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
  };

  const getStatusCount = (status: string) => {
    return contexts.filter(c => c.status === status).length;
  };

  const getSourceTypeCount = (sourceType: string) => {
    return contexts.filter(c => c.source_type === sourceType).length;
  };

  // Search timeout ref
  const searchTimeout = React.useRef<NodeJS.Timeout>();
  
  // Enhanced search functionality with proper cleanup
  const performAdvancedSearch = React.useCallback(async () => {
    if (!searchQuery.trim()) {
      setIsSearchMode(false);
      setSearchResults([]);
      return;
    }

    try {
      const filters = {
        status: statusFilter !== 'all' ? statusFilter : undefined,
        source_type: sourceTypeFilter !== 'all' ? sourceTypeFilter : undefined,
      };

      const sort = {
        field: sortBy === 'chunks' ? 'chunks' : sortBy,
        order: sortOrder,
      };

      const response = await contextSearchService.searchContexts(
        searchQuery,
        filters,
        sort,
        50, // limit
        0   // offset
      );

      setSearchResults(response.results);
      setIsSearchMode(true);
      
      if (response.results.length === 0) {
        showWarning('No contexts match your search criteria');
      }
    } catch (error) {
      showError('Search failed. Please try again.');
      console.error('Search error:', error);
    }
  }, [searchQuery, statusFilter, sourceTypeFilter, sortBy, sortOrder, showWarning, showError]);

  const handleSearchChange = React.useCallback(async (value: string) => {
    setSearchQuery(value);
    
    if (!value.trim()) {
      setIsSearchMode(false);
      setSearchResults([]);
      setShowSuggestions(false);
      return;
    }

    // Get search suggestions (don't await to avoid blocking)
    contextSearchService.getSearchSuggestions(value)
      .then(suggestions => {
        setSuggestions(suggestions);
        setShowSuggestions(suggestions.length > 0);
      })
      .catch(error => {
        console.error('Failed to get search suggestions:', error);
      });

    // Debounce search execution
    if (searchTimeout.current) {
      clearTimeout(searchTimeout.current);
    }
    
    searchTimeout.current = setTimeout(() => {
      if (value.trim()) {
        performAdvancedSearch();
      }
    }, 500);
  }, [performAdvancedSearch]);

  // Cleanup search timeout on unmount
  React.useEffect(() => {
    return () => {
      if (searchTimeout.current) {
        clearTimeout(searchTimeout.current);
      }
    };
  }, []);

  const handleSuggestionClick = (suggestion: string) => {
    setSearchQuery(suggestion);
    setShowSuggestions(false);
    performAdvancedSearch();
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
        <Box>
          <Typography variant="h4">
            Contexts
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {filteredAndSortedContexts.length} of {contexts.length} contexts
            {isSearchMode && (
              <Chip 
                label={`Search: "${searchQuery}"`} 
                size="small" 
                color="primary" 
                variant="outlined"
                sx={{ ml: 1 }}
                onDelete={() => {
                  setSearchQuery('');
                  setIsSearchMode(false);
                  setSearchResults([]);
                }}
              />
            )}
          </Typography>
        </Box>
        <Box display="flex" gap={1} alignItems="center">
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(e, newView) => newView && setViewMode(newView)}
            size="small"
          >
            <ToggleButton value="grid">
              <GridViewIcon fontSize="small" />
            </ToggleButton>
            <ToggleButton value="list">
              <ListViewIcon fontSize="small" />
            </ToggleButton>
          </ToggleButtonGroup>
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

      {/* Search and Filter Section */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box display="flex" gap={2} alignItems="center" mb={2}>
          <Box sx={{ position: 'relative', flexGrow: 1 }}>
            <TextField
              placeholder="Search contexts..."
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
                endAdornment: searchQuery && (
                  <InputAdornment position="end">
                    <IconButton size="small" onClick={() => {
                      setSearchQuery('');
                      setIsSearchMode(false);
                      setSearchResults([]);
                      setShowSuggestions(false);
                    }}>
                      <ClearIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              fullWidth
              size="small"
            />
            
            {/* Search Suggestions */}
            {showSuggestions && searchSuggestions.length > 0 && (
              <Paper
                sx={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  zIndex: 1000,
                  maxHeight: 200,
                  overflow: 'auto',
                  mt: 1,
                }}
              >
                <List dense>
                  {searchSuggestions.map((suggestion, index) => (
                    <ListItem
                      key={index}
                      button
                      onClick={() => handleSuggestionClick(suggestion)}
                    >
                      <ListItemIcon>
                        <SearchIcon fontSize="small" />
                      </ListItemIcon>
                      <ListItemText primary={suggestion} />
                    </ListItem>
                  ))}
                </List>
              </Paper>
            )}
          </Box>
          <Button
            startIcon={<FilterListIcon />}
            onClick={() => setFiltersExpanded(!filtersExpanded)}
            endIcon={filtersExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            variant="outlined"
            size="small"
          >
            Filters
          </Button>
          <Tooltip title={`Sort by ${sortBy} (${sortOrder === 'asc' ? 'ascending' : 'descending'})`}>
            <Button
              startIcon={<SortIcon />}
              onClick={handleSortToggle}
              variant="outlined"
              size="small"
            >
              {sortBy} {sortOrder === 'asc' ? '↑' : '↓'}
            </Button>
          </Tooltip>
        </Box>

        {/* Advanced Filters */}
        <Collapse in={filtersExpanded}>
          <Box display="flex" gap={2} alignItems="center" pt={2}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as any)}
                label="Status"
              >
                <MenuItem value="all">All ({contexts.length})</MenuItem>
                <MenuItem value="ready">
                  <Box display="flex" alignItems="center" justifyContent="space-between" width="100%">
                    <span>Ready</span>
                    <Badge badgeContent={getStatusCount('ready')} color="success" />
                  </Box>
                </MenuItem>
                <MenuItem value="processing">
                  <Box display="flex" alignItems="center" justifyContent="space-between" width="100%">
                    <span>Processing</span>
                    <Badge badgeContent={getStatusCount('processing')} color="warning" />
                  </Box>
                </MenuItem>
                <MenuItem value="error">
                  <Box display="flex" alignItems="center" justifyContent="space-between" width="100%">
                    <span>Error</span>
                    <Badge badgeContent={getStatusCount('error')} color="error" />
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>
            
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Source</InputLabel>
              <Select
                value={sourceTypeFilter}
                onChange={(e) => setSourceTypeFilter(e.target.value as any)}
                label="Source"
              >
                <MenuItem value="all">All ({contexts.length})</MenuItem>
                <MenuItem value="repo">
                  <Box display="flex" alignItems="center" gap={1}>
                    <CodeIcon fontSize="small" />
                    Repository ({getSourceTypeCount('repo')})
                  </Box>
                </MenuItem>
                <MenuItem value="database">
                  <Box display="flex" alignItems="center" gap={1}>
                    <DatabaseIcon fontSize="small" />
                    Database ({getSourceTypeCount('database')})
                  </Box>
                </MenuItem>
                <MenuItem value="files">
                  <Box display="flex" alignItems="center" gap={1}>
                    <FolderIcon fontSize="small" />
                    Files ({getSourceTypeCount('files')})
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>
            
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Sort By</InputLabel>
              <Select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                label="Sort By"
              >
                <MenuItem value="name">Name</MenuItem>
                <MenuItem value="created_at">Created Date</MenuItem>
                <MenuItem value="chunks">Chunks</MenuItem>
                <MenuItem value="status">Status</MenuItem>
              </Select>
            </FormControl>
            
            <Button
              size="small"
              variant="outlined"
              onClick={handleClearSearch}
              startIcon={<ClearIcon />}
              disabled={searchQuery === '' && statusFilter === 'all' && sourceTypeFilter === 'all'}
            >
              Clear All
            </Button>
          </Box>
        </Collapse>
      </Paper>

      {filteredAndSortedContexts.length === 0 ? (
        searchQuery || statusFilter !== 'all' || sourceTypeFilter !== 'all' ? (
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 6 }}>
              <SearchIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                No contexts match your search
              </Typography>
              <Typography color="text.secondary" paragraph>
                Try adjusting your search criteria or filters
              </Typography>
              <Button
                variant="outlined"
                onClick={handleClearSearch}
                startIcon={<ClearIcon />}
              >
                Clear Search
              </Button>
            </CardContent>
          </Card>
        ) : contexts.length === 0 ? (
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
      ) : null
      ) : (
        <Grid container spacing={viewMode === 'grid' ? 3 : 2}>
          {filteredAndSortedContexts.map((context) => (
            <Grid xs={12} sm={viewMode === 'grid' ? 6 : 12} md={viewMode === 'grid' ? 4 : 12} key={context.id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: viewMode === 'list' ? 'row' : 'column',
                  minHeight: viewMode === 'grid' ? 280 : 120,
                  '&:hover': {
                    boxShadow: 3,
                    transform: 'translateY(-2px)',
                  },
                  transition: 'all 0.2s ease-in-out',
                }}
              >
                <CardContent sx={{ 
                  flexGrow: 1, 
                  display: 'flex', 
                  flexDirection: viewMode === 'list' ? 'row' : 'column',
                  alignItems: viewMode === 'list' ? 'center' : 'stretch',
                  p: viewMode === 'list' ? 2 : 3,
                  gap: viewMode === 'list' ? 2 : 0,
                }}>
                  <Box 
                    display="flex" 
                    justifyContent="space-between" 
                    alignItems={viewMode === 'list' ? 'center' : 'flex-start'} 
                    mb={viewMode === 'list' ? 0 : 2}
                    minWidth={viewMode === 'list' ? 300 : 'auto'}
                  >
                    <Box display="flex" alignItems="center" gap={1}>
                      {getSourceIcon(context.source_type)}
                      <Typography variant={viewMode === 'list' ? 'body1' : 'h6'} noWrap>
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

                  {viewMode === 'grid' ? (
                    <>
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
                    </>
                  ) : (
                    <>
                      <Box display="flex" flexDirection="column" flexGrow={1} minWidth={0}>
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            mb: 1,
                          }}
                        >
                          {context.description || 'No description'}
                        </Typography>
                        
                        <Box display="flex" gap={1} alignItems="center">
                          <Chip
                            label={context.status}
                            color={getStatusColor(context.status) as any}
                            size="small"
                          />
                          <Typography variant="caption" color="text.secondary">
                            {context.total_chunks || 0} chunks
                          </Typography>
                          <Typography variant="caption" color="text.secondary">•</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {getSourceLabel(context.source_type)}
                          </Typography>
                        </Box>
                      </Box>
                      
                      {context.status === 'processing' && (
                        <Box sx={{ minWidth: 100 }}>
                          <LinearProgress
                            variant="determinate"
                            value={context.progress}
                            size="small"
                          />
                          <Typography variant="caption" color="text.secondary" align="center" display="block">
                            {context.progress}%
                          </Typography>
                        </Box>
                      )}
                      
                      <Button
                        size="small"
                        onClick={() => handleViewDetails(context)}
                        sx={{ whiteSpace: 'nowrap' }}
                      >
                        Details
                      </Button>
                    </>
                  )}

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
        onSuccess={async () => {
          setWizardOpen(false);
          await clearAPICache('/api/contexts');
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
        onUpdate={async () => {
          await clearAPICache('/api/contexts');
          loadContexts();
        }}
      />
    </Box>
  );
};

export default Contexts;
