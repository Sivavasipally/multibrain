import React, { useState, useCallback } from 'react';
import {
  Box,
  Typography,
  Alert,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Button,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  InsertDriveFile as FileIcon,
  Delete as DeleteIcon,
  Archive as ArchiveIcon,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { uploadAPI } from '../../services/api';
import { useSnackbar } from '../../contexts/SnackbarContext';

interface FileUploadConfigProps {
  config: any;
  onChange: (config: any) => void;
}

const FileUploadConfig: React.FC<FileUploadConfigProps> = ({ config, onChange }) => {
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const { showSuccess, showError } = useSnackbar();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = [...uploadedFiles, ...acceptedFiles];
    setUploadedFiles(newFiles);

    // Update config with actual File objects and file paths
    onChange({
      ...config,
      files: newFiles,
      file_paths: newFiles.map(f => f.name),
    });
  }, [uploadedFiles, config, onChange]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
    accept: {
      'text/*': ['.txt', '.md', '.rst'],
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/csv': ['.csv'],
      'application/json': ['.json'],
      'text/yaml': ['.yml', '.yaml'],
      'text/xml': ['.xml'],
      'text/html': ['.html', '.htm'],
      'text/css': ['.css'],
      'text/javascript': ['.js'],
      'text/typescript': ['.ts'],
      'text/x-python': ['.py'],
      'text/x-java-source': ['.java'],
      'text/x-c': ['.c', '.h'],
      'text/x-c++': ['.cpp', '.hpp'],
      'text/x-go': ['.go'],
      'text/x-rust': ['.rs'],
      'text/x-ruby': ['.rb'],
      'text/x-php': ['.php'],
      'text/x-csharp': ['.cs'],
      'text/x-kotlin': ['.kt'],
      'text/x-swift': ['.swift'],
      'application/sql': ['.sql'],
      'application/zip': ['.zip'],
      'application/x-tar': ['.tar'],
      'application/gzip': ['.gz'],
    },
  });

  const removeFile = (index: number) => {
    const newFiles = uploadedFiles.filter((_, i) => i !== index);
    setUploadedFiles(newFiles);

    // Update config with remaining files
    onChange({
      ...config,
      files: newFiles,
      file_paths: newFiles.map(f => f.name),
    });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    
    if (['zip', 'tar', 'gz', 'rar'].includes(extension || '')) {
      return <ArchiveIcon />;
    }
    
    return <FileIcon />;
  };

  const getFileTypeChip = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    
    const typeMap: { [key: string]: { label: string; color: any } } = {
      'pdf': { label: 'PDF', color: 'error' },
      'docx': { label: 'Word', color: 'primary' },
      'doc': { label: 'Word', color: 'primary' },
      'xlsx': { label: 'Excel', color: 'success' },
      'xls': { label: 'Excel', color: 'success' },
      'csv': { label: 'CSV', color: 'success' },
      'json': { label: 'JSON', color: 'warning' },
      'yaml': { label: 'YAML', color: 'warning' },
      'yml': { label: 'YAML', color: 'warning' },
      'xml': { label: 'XML', color: 'warning' },
      'py': { label: 'Python', color: 'info' },
      'js': { label: 'JavaScript', color: 'info' },
      'ts': { label: 'TypeScript', color: 'info' },
      'java': { label: 'Java', color: 'info' },
      'cpp': { label: 'C++', color: 'info' },
      'c': { label: 'C', color: 'info' },
      'go': { label: 'Go', color: 'info' },
      'rs': { label: 'Rust', color: 'info' },
      'zip': { label: 'Archive', color: 'secondary' },
      'tar': { label: 'Archive', color: 'secondary' },
      'gz': { label: 'Archive', color: 'secondary' },
    };
    
    const type = typeMap[extension || ''] || { label: extension?.toUpperCase() || 'File', color: 'default' };
    
    return (
      <Chip
        label={type.label}
        color={type.color}
        size="small"
        variant="outlined"
      />
    );
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        File Upload Configuration
      </Typography>
      
      <Alert severity="info" sx={{ mb: 2 }}>
        Upload documents, code files, and archives to create your knowledge base. 
        Supported formats include PDF, Word, Excel, CSV, code files, and more.
      </Alert>

      <Paper
        {...getRootProps()}
        sx={{
          p: 3,
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          textAlign: 'center',
          mb: 2,
        }}
      >
        <input {...getInputProps()} />
        <CloudUploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
        <Typography variant="h6" gutterBottom>
          {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
        </Typography>
        <Typography color="text.secondary">
          or click to select files
        </Typography>
        <Button variant="outlined" sx={{ mt: 2 }}>
          Choose Files
        </Button>
      </Paper>

      {uploadedFiles.length > 0 && (
        <Box>
          <Typography variant="subtitle1" gutterBottom>
            Selected Files ({uploadedFiles.length})
          </Typography>
          <List>
            {uploadedFiles.map((file, index) => (
              <ListItem key={index} divider>
                <ListItemIcon>
                  {getFileIcon(file.name)}
                </ListItemIcon>
                <ListItemText
                  primary={file.name}
                  secondary={formatFileSize(file.size)}
                  secondaryTypographyProps={{
                    component: 'div'
                  }}
                />
                <Box display="flex" alignItems="center" gap={1}>
                  {getFileTypeChip(file.name)}
                </Box>
                <ListItemSecondaryAction>
                  <IconButton
                    edge="end"
                    onClick={() => removeFile(index)}
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      <Alert severity="success" sx={{ mt: 2 }}>
        <Typography variant="body2">
          <strong>Supported formats:</strong> PDF, Word (DOC/DOCX), Excel (XLS/XLSX), 
          CSV, JSON, YAML, XML, HTML, CSS, JavaScript, TypeScript, Python, Java, C/C++, 
          Go, Rust, Ruby, PHP, C#, Kotlin, Swift, SQL, Markdown, Text files, and ZIP archives.
        </Typography>
      </Alert>

      <Alert severity="warning" sx={{ mt: 1 }}>
        <Typography variant="body2">
          <strong>File size limit:</strong> Maximum 100MB per file. 
          For larger files, consider using ZIP compression or splitting into smaller files.
        </Typography>
      </Alert>
    </Box>
  );
};

export default FileUploadConfig;
