import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Stepper,
  Step,
  StepLabel,
  Box,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  CardActionArea,
  Grid,
  Alert,
} from '@mui/material';
import {
  Code as CodeIcon,
  Storage as DatabaseIcon,
  Folder as FolderIcon,
} from '@mui/icons-material';
import { contextsAPI } from '../../services/api';
import { useSnackbar } from '../../contexts/SnackbarContext';
import RepositoryConfig from './RepositoryConfig';
import DatabaseConfig from './DatabaseConfig';
import FileUploadConfig from './FileUploadConfig';

interface ContextWizardProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

interface ContextData {
  name: string;
  description: string;
  source_type: 'repo' | 'database' | 'files' | '';
  chunk_strategy: string;
  embedding_model: string;
  repo_config?: any;
  database_config?: any;
  file_config?: any;
}

const steps = ['Basic Info', 'Source Type', 'Configuration', 'Review'];

const ContextWizard: React.FC<ContextWizardProps> = ({ open, onClose, onSuccess }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { showSuccess, showError } = useSnackbar();

  const [contextData, setContextData] = useState<ContextData>({
    name: '',
    description: '',
    source_type: '',
    chunk_strategy: 'language-specific',
    embedding_model: 'text-embedding-004',
  });

  const handleNext = () => {
    if (validateStep(activeStep)) {
      setActiveStep((prevStep) => prevStep + 1);
      setError('');
    }
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
    setError('');
  };

  const handleReset = () => {
    setActiveStep(0);
    setContextData({
      name: '',
      description: '',
      source_type: '',
      chunk_strategy: 'language-specific',
      embedding_model: 'text-embedding-004',
    });
    setError('');
  };

  const validateStep = (step: number): boolean => {
    switch (step) {
      case 0:
        if (!contextData.name.trim()) {
          setError('Context name is required');
          return false;
        }
        return true;
      case 1:
        if (!contextData.source_type) {
          setError('Please select a source type');
          return false;
        }
        return true;
      case 2:
        // Validation will be handled by individual config components
        return true;
      default:
        return true;
    }
  };

  const handleCreate = async () => {
    try {
      setLoading(true);
      setError('');

      // First create the context
      const response = await contextsAPI.createContext(contextData);
      const createdContext = response.context;

      // If files were selected, upload them
      if (contextData.source_type === 'files' && contextData.file_config?.files?.length > 0) {
        try {
          const formData = new FormData();
          formData.append('context_id', createdContext.id.toString());

          // Add all selected files to FormData
          contextData.file_config.files.forEach((file: File) => {
            formData.append('files', file);
          });

          // Upload files and process them
          await fetch('http://localhost:5000/api/upload/files', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
            },
            body: formData,
          });

          showSuccess('Context created and files uploaded successfully!');
        } catch (uploadErr) {
          console.error('File upload failed:', uploadErr);
          showError('Context created but file upload failed. You can upload files later.');
        }
      } else {
        showSuccess('Context created successfully!');
      }

      onSuccess();
      handleReset();
    } catch (err: any) {
      const errorMessage = err.response?.data?.error || 'Failed to create context';
      setError(errorMessage);
      showError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    handleReset();
    onClose();
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box>
            <TextField
              fullWidth
              label="Context Name"
              value={contextData.name}
              onChange={(e) => setContextData({ ...contextData, name: e.target.value })}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Description"
              value={contextData.description}
              onChange={(e) => setContextData({ ...contextData, description: e.target.value })}
              margin="normal"
              multiline
              rows={3}
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Chunk Strategy</InputLabel>
              <Select
                value={contextData.chunk_strategy}
                onChange={(e) => setContextData({ ...contextData, chunk_strategy: e.target.value })}
              >
                <MenuItem value="language-specific">Language-Specific</MenuItem>
                <MenuItem value="fixed-size">Fixed Size</MenuItem>
                <MenuItem value="semantic">Semantic</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth margin="normal">
              <InputLabel>Embedding Model</InputLabel>
              <Select
                value={contextData.embedding_model}
                onChange={(e) => setContextData({ ...contextData, embedding_model: e.target.value })}
              >
                <MenuItem value="text-embedding-004">Gemini Text Embedding 004</MenuItem>
                <MenuItem value="sentence-transformers">Sentence Transformers</MenuItem>
              </Select>
            </FormControl>
          </Box>
        );

      case 1:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Choose your data source
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 4 }}>
                <Card
                  sx={{
                    border: contextData.source_type === 'repo' ? 2 : 1,
                    borderColor: contextData.source_type === 'repo' ? 'primary.main' : 'divider',
                  }}
                >
                  <CardActionArea
                    onClick={() => setContextData({ ...contextData, source_type: 'repo' })}
                    sx={{ p: 2 }}
                  >
                    <CardContent sx={{ textAlign: 'center' }}>
                      <CodeIcon sx={{ fontSize: 48, mb: 1 }} />
                      <Typography variant="h6">Repository</Typography>
                      <Typography variant="body2" color="text.secondary">
                        GitHub or Bitbucket repository
                      </Typography>
                    </CardContent>
                  </CardActionArea>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <Card
                  sx={{
                    border: contextData.source_type === 'database' ? 2 : 1,
                    borderColor: contextData.source_type === 'database' ? 'primary.main' : 'divider',
                  }}
                >
                  <CardActionArea
                    onClick={() => setContextData({ ...contextData, source_type: 'database' })}
                    sx={{ p: 2 }}
                  >
                    <CardContent sx={{ textAlign: 'center' }}>
                      <DatabaseIcon sx={{ fontSize: 48, mb: 1 }} />
                      <Typography variant="h6">Database</Typography>
                      <Typography variant="body2" color="text.secondary">
                        SQL or NoSQL database
                      </Typography>
                    </CardContent>
                  </CardActionArea>
                </Card>
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <Card
                  sx={{
                    border: contextData.source_type === 'files' ? 2 : 1,
                    borderColor: contextData.source_type === 'files' ? 'primary.main' : 'divider',
                  }}
                >
                  <CardActionArea
                    onClick={() => setContextData({ ...contextData, source_type: 'files' })}
                    sx={{ p: 2 }}
                  >
                    <CardContent sx={{ textAlign: 'center' }}>
                      <FolderIcon sx={{ fontSize: 48, mb: 1 }} />
                      <Typography variant="h6">Files</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Upload documents and files
                      </Typography>
                    </CardContent>
                  </CardActionArea>
                </Card>
              </Grid>
            </Grid>
          </Box>
        );

      case 2:
        return (
          <Box>
            {contextData.source_type === 'repo' && (
              <RepositoryConfig
                config={contextData.repo_config || {}}
                onChange={(config) => setContextData({ ...contextData, repo_config: config })}
              />
            )}
            {contextData.source_type === 'database' && (
              <DatabaseConfig
                config={contextData.database_config || {}}
                onChange={(config) => setContextData({ ...contextData, database_config: config })}
              />
            )}
            {contextData.source_type === 'files' && (
              <FileUploadConfig
                config={contextData.file_config || {}}
                onChange={(config) => setContextData({ ...contextData, file_config: config })}
              />
            )}
          </Box>
        );

      case 3:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Review Configuration
            </Typography>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  <strong>Name:</strong> {contextData.name}
                </Typography>
                <Typography variant="body2" gutterBottom>
                  <strong>Description:</strong> {contextData.description || 'No description'}
                </Typography>
                <Typography variant="body2" gutterBottom>
                  <strong>Source Type:</strong> {contextData.source_type}
                </Typography>
                <Typography variant="body2" gutterBottom>
                  <strong>Chunk Strategy:</strong> {contextData.chunk_strategy}
                </Typography>
                <Typography variant="body2" gutterBottom>
                  <strong>Embedding Model:</strong> {contextData.embedding_model}
                </Typography>
              </CardContent>
            </Card>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>Create New Context</DialogTitle>
      <DialogContent>
        <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {renderStepContent(activeStep)}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Box sx={{ flex: '1 1 auto' }} />
        <Button disabled={activeStep === 0} onClick={handleBack}>
          Back
        </Button>
        {activeStep === steps.length - 1 ? (
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={loading}
          >
            {loading ? 'Creating...' : 'Create Context'}
          </Button>
        ) : (
          <Button variant="contained" onClick={handleNext}>
            Next
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default ContextWizard;
