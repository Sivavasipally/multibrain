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
  InputAdornment,
  IconButton,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  GitHub as GitHubIcon,
} from '@mui/icons-material';

interface RepositoryConfigProps {
  config: any;
  onChange: (config: any) => void;
}

const RepositoryConfig: React.FC<RepositoryConfigProps> = ({ config, onChange }) => {
  const [showToken, setShowToken] = useState(false);

  const handleChange = (field: string, value: string) => {
    onChange({
      ...config,
      [field]: value,
    });
  };

  const handleGitHubAuth = () => {
    // Redirect to GitHub OAuth for repository access
    window.location.href = `${import.meta.env.VITE_API_URL}/api/auth/github/login`;
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Repository Configuration
      </Typography>
      
      <Alert severity="info" sx={{ mb: 2 }}>
        Connect your GitHub or Bitbucket repository to automatically process code files and documentation.
      </Alert>

      <TextField
        fullWidth
        label="Repository URL"
        value={config.url || ''}
        onChange={(e) => handleChange('url', e.target.value)}
        margin="normal"
        placeholder="https://github.com/username/repository"
        helperText="Enter the full URL of your GitHub or Bitbucket repository"
        required
      />

      <TextField
        fullWidth
        label="Branch"
        value={config.branch || 'main'}
        onChange={(e) => handleChange('branch', e.target.value)}
        margin="normal"
        helperText="Branch to process (default: main)"
      />

      <TextField
        fullWidth
        label="Access Token"
        type={showToken ? 'text' : 'password'}
        value={config.access_token || ''}
        onChange={(e) => handleChange('access_token', e.target.value)}
        margin="normal"
        helperText="Personal access token for private repositories (optional for public repos)"
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <IconButton
                aria-label="toggle token visibility"
                onClick={() => setShowToken(!showToken)}
                edge="end"
              >
                {showToken ? <VisibilityOff /> : <Visibility />}
              </IconButton>
            </InputAdornment>
          ),
        }}
      />

      <Box sx={{ mt: 2, mb: 2 }}>
        <Button
          variant="outlined"
          startIcon={<GitHubIcon />}
          onClick={handleGitHubAuth}
          fullWidth
        >
          Authenticate with GitHub
        </Button>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          This will redirect you to GitHub to authorize access to your repositories
        </Typography>
      </Box>

      <Alert severity="warning" sx={{ mt: 2 }}>
        <Typography variant="body2">
          <strong>Supported file types:</strong> Python, JavaScript, TypeScript, Java, C/C++, Go, 
          Kotlin, Rust, Ruby, PHP, C#, Swift, HTML, CSS, SQL, JSON, YAML, Markdown, and more.
        </Typography>
      </Alert>
    </Box>
  );
};

export default RepositoryConfig;
