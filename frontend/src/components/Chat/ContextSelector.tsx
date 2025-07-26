import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Checkbox,
  Typography,
  Box,
  Chip,
  Alert,
} from '@mui/material';
import {
  Storage as StorageIcon,
  Code as CodeIcon,
  Storage as DatabaseIcon,
  Folder as FolderIcon,
} from '@mui/icons-material';
import type { Context } from '../../types/api';

interface ContextSelectorProps {
  open: boolean;
  contexts: Context[];
  selectedContexts: number[];
  onSelectionChange: (contextIds: number[]) => void;
  onClose: () => void;
}

const ContextSelector: React.FC<ContextSelectorProps> = ({
  open,
  contexts,
  selectedContexts,
  onSelectionChange,
  onClose,
}) => {
  const handleToggle = (contextId: number) => {
    const currentIndex = selectedContexts.indexOf(contextId);
    const newSelected = [...selectedContexts];

    if (currentIndex === -1) {
      newSelected.push(contextId);
    } else {
      newSelected.splice(currentIndex, 1);
    }

    onSelectionChange(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedContexts.length === contexts.length) {
      onSelectionChange([]);
    } else {
      onSelectionChange(contexts.map(c => c.id));
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

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Select Contexts</Typography>
          <Button
            size="small"
            onClick={handleSelectAll}
            disabled={contexts.length === 0}
          >
            {selectedContexts.length === contexts.length ? 'Deselect All' : 'Select All'}
          </Button>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {contexts.length === 0 ? (
          <Alert severity="info">
            No ready contexts available. Create and process contexts first to use them in chat.
          </Alert>
        ) : (
          <>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Select one or more contexts to provide knowledge for your chat session.
            </Typography>
            
            <List>
              {contexts.map((context) => (
                <ListItem
                  key={context.id}
                  button
                  onClick={() => handleToggle(context.id)}
                  sx={{
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 1,
                    mb: 1,
                    '&:hover': {
                      backgroundColor: 'action.hover',
                    },
                  }}
                >
                  <ListItemIcon>
                    <Checkbox
                      edge="start"
                      checked={selectedContexts.indexOf(context.id) !== -1}
                      tabIndex={-1}
                      disableRipple
                    />
                  </ListItemIcon>
                  
                  <ListItemIcon>
                    {getSourceIcon(context.source_type)}
                  </ListItemIcon>
                  
                  <ListItemText
                    primary={context.name}
                    secondary={context.description || 'No description'}
                    secondaryTypographyProps={{
                      component: 'div'
                    }}
                  />
                  <Box display="flex" gap={1} mt={0.5}>
                    <Chip
                      label={getSourceLabel(context.source_type)}
                      size="small"
                      variant="outlined"
                    />
                    <Chip
                      label={`${context.total_chunks || 0} chunks`}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  </Box>
                </ListItem>
              ))}
            </List>
          </>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={onClose}
          disabled={selectedContexts.length === 0}
        >
          Use Selected ({selectedContexts.length})
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ContextSelector;
