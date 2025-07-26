import React, { useState } from 'react';
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Typography,
  Alert,
  Chip,
  Autocomplete,
  CircularProgress,
} from '@mui/material';
import {
  Storage as StorageIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';

interface DatabaseConfigProps {
  config: any;
  onChange: (config: any) => void;
}

const DatabaseConfig: React.FC<DatabaseConfigProps> = ({ config, onChange }) => {
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [availableTables, setAvailableTables] = useState<string[]>([]);

  const databaseTypes = [
    { value: 'sqlite', label: 'SQLite' },
    { value: 'mysql', label: 'MySQL' },
    { value: 'postgresql', label: 'PostgreSQL' },
    { value: 'oracle', label: 'Oracle' },
    { value: 'mongodb', label: 'MongoDB' },
    { value: 'cassandra', label: 'Cassandra' },
  ];

  const handleChange = (field: string, value: any) => {
    onChange({
      ...config,
      [field]: value,
    });
  };

  const getConnectionStringPlaceholder = (type: string) => {
    switch (type) {
      case 'sqlite':
        return 'sqlite:///path/to/database.db';
      case 'mysql':
        return 'mysql://username:password@host:port/database';
      case 'postgresql':
        return 'postgresql://username:password@host:port/database';
      case 'oracle':
        return 'oracle://username:password@host:port/service';
      case 'mongodb':
        return 'mongodb://username:password@host:port/database';
      case 'cassandra':
        return 'cassandra://username:password@host:port/keyspace';
      default:
        return 'Enter connection string';
    }
  };

  const testConnection = async () => {
    if (!config.type || !config.connection_string) {
      setTestResult({
        success: false,
        message: 'Please select database type and enter connection string',
      });
      return;
    }

    setTesting(true);
    setTestResult(null);

    try {
      // Call the backend API to test the connection
      const response = await fetch('/api/database/test-connection', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          db_type: config.type,
          connection_string: config.connection_string,
        }),
      });

      const result = await response.json();

      if (result.success) {
        setTestResult({
          success: true,
          message: 'Connection successful!',
        });

        // Set available tables from the response
        setAvailableTables(result.tables || []);
      } else {
        setTestResult({
          success: false,
          message: result.error || 'Connection failed. Please check your credentials.',
        });
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Connection failed. Please check your credentials.',
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Database Configuration
      </Typography>
      
      <Alert severity="info" sx={{ mb: 2 }}>
        Connect to your database to extract and process table data and schemas.
      </Alert>

      <FormControl fullWidth margin="normal">
        <InputLabel>Database Type</InputLabel>
        <Select
          value={config.type || ''}
          onChange={(e) => handleChange('type', e.target.value)}
          required
        >
          {databaseTypes.map((type) => (
            <MenuItem key={type.value} value={type.value}>
              {type.label}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <TextField
        fullWidth
        label="Connection String"
        value={config.connection_string || ''}
        onChange={(e) => handleChange('connection_string', e.target.value)}
        margin="normal"
        placeholder={getConnectionStringPlaceholder(config.type)}
        helperText="Enter the full connection string for your database"
        required
      />

      <Box sx={{ mt: 2, mb: 2 }}>
        <Button
          variant="outlined"
          startIcon={testing ? <CircularProgress size={20} /> : <StorageIcon />}
          onClick={testConnection}
          disabled={testing || !config.type || !config.connection_string}
          fullWidth
        >
          {testing ? 'Testing Connection...' : 'Test Connection'}
        </Button>
      </Box>

      {testResult && (
        <Alert
          severity={testResult.success ? 'success' : 'error'}
          icon={testResult.success ? <CheckCircleIcon /> : <ErrorIcon />}
          sx={{ mb: 2 }}
        >
          {testResult.message}
        </Alert>
      )}

      {testResult?.success && availableTables.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Select Tables to Process (optional)
          </Typography>
          <Autocomplete
            multiple
            options={availableTables}
            value={config.tables || []}
            onChange={(_, newValue) => handleChange('tables', newValue)}
            renderTags={(value, getTagProps) =>
              value.map((option, index) => (
                <Chip
                  variant="outlined"
                  label={option}
                  {...getTagProps({ index })}
                  key={option}
                />
              ))
            }
            renderInput={(params) => (
              <TextField
                {...params}
                placeholder="Select tables or leave empty to process all"
                helperText="Leave empty to process all tables in the database"
              />
            )}
          />
        </Box>
      )}

      <Alert severity="warning" sx={{ mt: 2 }}>
        <Typography variant="body2">
          <strong>Security Note:</strong> Your connection credentials are encrypted and stored securely. 
          We recommend using read-only database users for safety.
        </Typography>
      </Alert>

      <Alert severity="info" sx={{ mt: 1 }}>
        <Typography variant="body2">
          <strong>Processing:</strong> We'll extract table schemas, sample data, and relationships 
          to create a comprehensive knowledge base of your database structure.
        </Typography>
      </Alert>
    </Box>
  );
};

export default DatabaseConfig;
