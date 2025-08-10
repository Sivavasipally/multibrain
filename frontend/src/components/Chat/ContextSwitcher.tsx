/**
 * Context Switcher Component for RAG Chatbot PWA
 * 
 * Advanced context switching interface for chat sessions with multi-context support,
 * context search, filtering, and real-time switching capabilities.
 * 
 * Features:
 * - Multi-context selection and switching
 * - Real-time context search and filtering
 * - Context status indicators
 * - Quick context suggestions
 * - Context performance metrics
 * - Session-specific context management
 * 
 * Usage:
 *   <ContextSwitcher
 *     sessionId={sessionId}
 *     selectedContexts={selectedContexts}
 *     onContextsChange={handleContextsChange}
 *     showMetrics={true}
 *   />
 * 
 * Author: RAG Chatbot Development Team
 * Version: 2.0.0
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  TextField,
  Chip,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Checkbox,
  IconButton,
  Button,
  Paper,
  InputAdornment,
  Tooltip,
  Badge,
  Collapse,
  Alert,
  LinearProgress,
  Grid,
  Card,
  CardContent,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear as ClearIcon,
  Folder as FolderIcon,
  FolderOpen as FolderOpenIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Speed as SpeedIcon,
  Storage as StorageIcon,
  Refresh as RefreshIcon,
  FilterList as FilterListIcon,
  Sort as SortIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { contextsAPI } from '../../services/api';
import { useSnackbar } from '../../contexts/SnackbarContext';
import { usePreferences } from '../../contexts/PreferencesContext';
import type { Context } from '../../types/api';

interface ContextSwitcherProps {
  sessionId?: number;
  selectedContexts: number[];
  onContextsChange: (contextIds: number[]) => void;
  maxContexts?: number;
  showMetrics?: boolean;
  showSearch?: boolean;
  showFilters?: boolean;
  allowEmpty?: boolean;
  onClose?: () => void;
}

interface ContextMetrics {
  documentsCount: number;
  chunksCount: number;
  lastUsed?: Date;
  queryCount?: number;
  avgResponseTime?: number;
  errorRate?: number;
}

interface ContextWithMetrics extends Context {
  metrics?: ContextMetrics;
}

const ContextSwitcher: React.FC<ContextSwitcherProps> = ({
  sessionId,
  selectedContexts,
  onContextsChange,
  maxContexts = 5,
  showMetrics = true,
  showSearch = true,
  showFilters = true,
  allowEmpty = false,
  onClose,
}) => {
  const [contexts, setContexts] = useState<ContextWithMetrics[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'created_at' | 'last_used' | 'performance'>('name');
  const [filterStatus, setFilterStatus] = useState<'all' | 'ready' | 'processing' | 'failed'>('ready');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [metricsExpanded, setMetricsExpanded] = useState(false);
  
  const { showError, showWarning } = useSnackbar();
  const { preferences } = usePreferences();

  useEffect(() => {
    loadContexts();
  }, []);

  const loadContexts = async () => {
    try {
      setLoading(true);
      const response = await contextsAPI.getContexts();
      
      // Load contexts with metrics
      const contextsWithMetrics = await Promise.all(
        response.contexts.map(async (context: Context) => {
          let metrics: ContextMetrics | undefined;
          
          if (showMetrics) {
            try {
              // Load context metrics (this would be a separate API endpoint)
              metrics = await loadContextMetrics(context.id);
            } catch (error) {
              console.warn(`Failed to load metrics for context ${context.id}`);
            }
          }
          
          return { ...context, metrics };
        })
      );
      
      setContexts(contextsWithMetrics);
    } catch (error: any) {
      console.error('Failed to load contexts:', error);
      showError('Failed to load contexts');
    } finally {
      setLoading(false);
    }
  };

  const loadContextMetrics = async (contextId: number): Promise<ContextMetrics> => {
    // This would be implemented as a real API endpoint
    // For now, return mock data
    return {
      documentsCount: Math.floor(Math.random() * 50) + 1,
      chunksCount: Math.floor(Math.random() * 1000) + 100,
      lastUsed: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000),
      queryCount: Math.floor(Math.random() * 100),
      avgResponseTime: Math.random() * 2000 + 500,
      errorRate: Math.random() * 0.1,
    };
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
      if (filterStatus !== 'all' && context.status !== filterStatus) {
        return false;
      }
      
      return true;
    });

    // Sort contexts
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'created_at':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'last_used':
          const aLastUsed = a.metrics?.lastUsed?.getTime() || 0;
          const bLastUsed = b.metrics?.lastUsed?.getTime() || 0;
          return bLastUsed - aLastUsed;
        case 'performance':
          const aPerf = (a.metrics?.avgResponseTime || Infinity);
          const bPerf = (b.metrics?.avgResponseTime || Infinity);
          return aPerf - bPerf;
        default:
          return 0;
      }
    });

    return filtered;
  }, [contexts, searchQuery, sortBy, filterStatus]);

  const handleContextToggle = (contextId: number) => {
    const isSelected = selectedContexts.includes(contextId);
    
    if (isSelected) {
      // Remove context
      if (selectedContexts.length === 1 && !allowEmpty) {
        showWarning('At least one context must be selected');
        return;
      }
      onContextsChange(selectedContexts.filter(id => id !== contextId));
    } else {
      // Add context
      if (selectedContexts.length >= maxContexts) {
        showWarning(`Maximum ${maxContexts} contexts allowed`);
        return;
      }
      onContextsChange([...selectedContexts, contextId]);
    }
  };

  const handleSelectAll = () => {
    const availableContexts = filteredAndSortedContexts
      .filter(context => context.status === 'ready')
      .slice(0, maxContexts)
      .map(context => context.id);
    
    onContextsChange(availableContexts);
  };

  const handleClearAll = () => {
    if (allowEmpty) {
      onContextsChange([]);
    } else {
      showWarning('At least one context must be selected');
    }
  };

  const getContextIcon = (context: ContextWithMetrics) => {
    const isSelected = selectedContexts.includes(context.id);
    
    if (context.status === 'processing') {
      return <RefreshIcon 
        sx={{ 
          animation: 'rotation 1s infinite linear',
          '@keyframes rotation': {
            from: { transform: 'rotate(0deg)' },
            to: { transform: 'rotate(359deg)' }
          }
        }} 
      />;
    } else if (context.status === 'failed') {
      return <ErrorIcon color="error" />;
    } else if (context.status === 'ready') {
      return isSelected ? <FolderOpenIcon color="primary" /> : <FolderIcon />;
    }
    
    return <FolderIcon />;
  };

  const getContextStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'success';
      case 'processing': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const formatDate = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  const selectedContextsList = contexts.filter(context => 
    selectedContexts.includes(context.id)
  );

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Typography variant="h6">
          Context Selection
        </Typography>
        <Box display="flex" alignItems="center" gap={1}>
          <Typography variant="body2" color="textSecondary">
            {selectedContexts.length}/{maxContexts}
          </Typography>
          {onClose && (
            <IconButton size="small" onClick={onClose}>
              <ClearIcon />
            </IconButton>
          )}
        </Box>
      </Box>

      {/* Selected Contexts Summary */}
      {selectedContexts.length > 0 && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Selected Contexts ({selectedContexts.length})
          </Typography>
          <Box display="flex" flexWrap="wrap" gap={1}>
            {selectedContextsList.map(context => (
              <Chip
                key={context.id}
                label={context.name}
                onDelete={() => handleContextToggle(context.id)}
                color="primary"
                variant="outlined"
                icon={getContextIcon(context)}
              />
            ))}
          </Box>
        </Paper>
      )}

      {/* Search and Filters */}
      {(showSearch || showFilters) && (
        <Box mb={2}>
          {showSearch && (
            <TextField
              fullWidth
              placeholder="Search contexts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
                endAdornment: searchQuery && (
                  <InputAdornment position="end">
                    <IconButton size="small" onClick={() => setSearchQuery('')}>
                      <ClearIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              sx={{ mb: showFilters ? 2 : 0 }}
            />
          )}
          
          {showFilters && (
            <Box display="flex" gap={2} alignItems="center">
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Status</InputLabel>
                <Select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value as any)}
                  label="Status"
                >
                  <MenuItem value="all">All</MenuItem>
                  <MenuItem value="ready">Ready</MenuItem>
                  <MenuItem value="processing">Processing</MenuItem>
                  <MenuItem value="failed">Failed</MenuItem>
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
                  <MenuItem value="created_at">Created</MenuItem>
                  <MenuItem value="last_used">Last Used</MenuItem>
                  {showMetrics && <MenuItem value="performance">Performance</MenuItem>}
                </Select>
              </FormControl>
              
              <Button
                size="small"
                startIcon={<FilterListIcon />}
                onClick={() => setShowAdvanced(!showAdvanced)}
              >
                Advanced
              </Button>
            </Box>
          )}
          
          {/* Advanced Filters */}
          <Collapse in={showAdvanced}>
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Grid container spacing={2}>
                <Grid size={6}>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={handleSelectAll}
                    disabled={filteredAndSortedContexts.length === 0}
                  >
                    Select All ({Math.min(filteredAndSortedContexts.length, maxContexts)})
                  </Button>
                </Grid>
                <Grid size={6}>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={handleClearAll}
                    disabled={selectedContexts.length === 0}
                  >
                    Clear All
                  </Button>
                </Grid>
              </Grid>
            </Box>
          </Collapse>
        </Box>
      )}

      {/* Loading State */}
      {loading && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress />
          <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
            Loading contexts...
          </Typography>
        </Box>
      )}

      {/* Context List */}
      <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
        <List>
          {filteredAndSortedContexts.map((context, index) => {
            const isSelected = selectedContexts.includes(context.id);
            const canSelect = context.status === 'ready';
            
            return (
              <React.Fragment key={context.id}>
                <ListItem
                  component={canSelect ? 'button' : 'div'}
                  selected={isSelected}
                  onClick={() => canSelect && handleContextToggle(context.id)}
                  disabled={!canSelect}
                  sx={{
                    borderRadius: 1,
                    mb: 0.5,
                    cursor: canSelect ? 'pointer' : 'default',
                    ...(isSelected && {
                      bgcolor: 'primary.light',
                      '&:hover': { bgcolor: 'primary.light' },
                    }),
                  }}
                >
                  <ListItemIcon>
                    <Badge
                      badgeContent={context.metrics?.documentsCount}
                      color="primary"
                      invisible={!context.metrics?.documentsCount}
                    >
                      {getContextIcon(context)}
                    </Badge>
                  </ListItemIcon>
                  
                  <ListItemText
                    primary={
                      <Box component="span" display="inline-flex" alignItems="center" gap={1}>
                        <Box component="span" variant="body1">
                          {context.name}
                        </Box>
                        <Chip
                          label={context.status}
                          size="small"
                          color={getContextStatusColor(context.status) as any}
                          variant="outlined"
                        />
                      </Box>
                    }
                    secondary={
                      <Box component="span">
                        <Box component="span" variant="body2" color="textSecondary" display="block">
                          {context.description || 'No description'}
                        </Box>
                        {context.metrics && showMetrics && (
                          <Box component="span" variant="caption" color="textSecondary" display="block">
                            {context.metrics.chunksCount} chunks • 
                            Last used {formatDate(context.metrics.lastUsed!)}
                          </Box>
                        )}
                      </Box>
                    }
                  />
                  
                  {canSelect && (
                    <ListItemSecondaryAction>
                      <Checkbox
                        checked={isSelected}
                        onChange={() => handleContextToggle(context.id)}
                      />
                    </ListItemSecondaryAction>
                  )}
                </ListItem>
                
                {/* Context Metrics (expanded) */}
                {isSelected && showMetrics && context.metrics && (
                  <Collapse in={metricsExpanded}>
                    <Card sx={{ ml: 4, mr: 2, mb: 1 }}>
                      <CardContent sx={{ py: 1 }}>
                        <Grid container spacing={2}>
                          <Grid size={6}>
                            <Box display="flex" alignItems="center" gap={1}>
                              <StorageIcon fontSize="small" />
                              <Typography variant="caption">
                                {context.metrics.documentsCount} docs, {context.metrics.chunksCount} chunks
                              </Typography>
                            </Box>
                          </Grid>
                          <Grid size={6}>
                            <Box display="flex" alignItems="center" gap={1}>
                              <SpeedIcon fontSize="small" />
                              <Typography variant="caption">
                                {context.metrics.avgResponseTime?.toFixed(0)}ms avg
                              </Typography>
                            </Box>
                          </Grid>
                        </Grid>
                      </CardContent>
                    </Card>
                  </Collapse>
                )}
                
                {index < filteredAndSortedContexts.length - 1 && <Divider />}
              </React.Fragment>
            );
          })}
        </List>
      </Box>

      {/* No Results */}
      {!loading && filteredAndSortedContexts.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <FolderIcon sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
          <Typography variant="body1" color="textSecondary">
            {searchQuery ? 'No contexts match your search' : 'No contexts available'}
          </Typography>
          {searchQuery && (
            <Button
              size="small"
              onClick={() => setSearchQuery('')}
              sx={{ mt: 1 }}
            >
              Clear Search
            </Button>
          )}
        </Box>
      )}

      {/* Metrics Toggle */}
      {showMetrics && selectedContexts.length > 0 && (
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Button
            size="small"
            onClick={() => setMetricsExpanded(!metricsExpanded)}
            endIcon={metricsExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          >
            {metricsExpanded ? 'Hide' : 'Show'} Metrics
          </Button>
        </Box>
      )}

      {/* Warning Messages */}
      {selectedContexts.length === maxContexts && (
        <Alert severity="info" sx={{ mt: 2 }}>
          Maximum number of contexts selected. Unselect a context to add another.
        </Alert>
      )}
      
      {selectedContexts.length === 0 && !allowEmpty && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          At least one context must be selected to continue chatting.
        </Alert>
      )}

    </Box>
  );
};

export default ContextSwitcher;