import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  LinearProgress,
  Chip,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import {
  Add as AddIcon,
  Storage as StorageIcon,
  Chat as ChatIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
} from '@mui/icons-material';
import { contextsAPI, chatAPI } from '../services/api';
import type { Context, ChatSession } from '../types/api';
import { useSnackbar } from '../contexts/SnackbarContext';
import { useAuth } from '../contexts/AuthContext';

const Dashboard: React.FC = () => {
  const [contexts, setContexts] = useState<Context[]>([]);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { showError } = useSnackbar();
  const { user, token } = useAuth();

  useEffect(() => {
    // Only load data when user is authenticated and token is available
    // Use a ref to prevent loops when user/token objects change but values are same
    if (user?.id && token) {
      loadDashboardData();
    }
  }, [user?.id, token]); // Only depend on user ID, not entire user object

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [contextsResponse, sessionsResponse] = await Promise.all([
        contextsAPI.getContexts(),
        chatAPI.getChatSessions(),
      ]);
      
      setContexts(contextsResponse.contexts);
      setChatSessions(sessionsResponse.sessions);
    } catch (error: any) {
      showError('Failed to load dashboard data');
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

  const getStatusText = (status: string) => {
    switch (status) {
      case 'ready':
        return 'Ready';
      case 'processing':
        return 'Processing';
      case 'error':
        return 'Error';
      case 'pending':
        return 'Pending';
      default:
        return status;
    }
  };

  const handleStartChat = async () => {
    try {
      const response = await chatAPI.createChatSession();
      navigate(`/chat/${response.session.id}`);
    } catch (error: any) {
      showError('Failed to create chat session');
    }
  };

  if (loading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  const readyContexts = contexts.filter(c => c.status === 'ready');
  const processingContexts = contexts.filter(c => c.status === 'processing');
  const recentSessions = chatSessions.slice(0, 5);

  return (
    <Box>
      <Box display="flex" justifyContent="between" alignItems="center" mb={3}>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>
        <IconButton onClick={loadDashboardData}>
          <RefreshIcon />
        </IconButton>
      </Box>

      <Grid container spacing={3}>
        {/* Quick Stats */}
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <StorageIcon color="primary" />
                <Box>
                  <Typography variant="h4">{contexts.length}</Typography>
                  <Typography color="text.secondary">Total Contexts</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <StorageIcon color="success" />
                <Box>
                  <Typography variant="h4">{readyContexts.length}</Typography>
                  <Typography color="text.secondary">Ready Contexts</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <ChatIcon color="primary" />
                <Box>
                  <Typography variant="h4">{chatSessions.length}</Typography>
                  <Typography color="text.secondary">Chat Sessions</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <StorageIcon color="warning" />
                <Box>
                  <Typography variant="h4">
                    {contexts.reduce((sum, c) => sum + (c.total_chunks || 0), 0)}
                  </Typography>
                  <Typography color="text.secondary">Total Chunks</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid size={{ xs: 12 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box display="flex" gap={2} flexWrap="wrap">
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => navigate('/contexts')}
                >
                  Create Context
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<ChatIcon />}
                  onClick={handleStartChat}
                  disabled={readyContexts.length === 0}
                >
                  Start Chat
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<StorageIcon />}
                  onClick={() => navigate('/contexts')}
                >
                  Manage Contexts
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Processing Contexts */}
        {processingContexts.length > 0 && (
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Processing Contexts
                </Typography>
                <List>
                  {processingContexts.map((context) => (
                    <ListItem key={context.id}>
                      <ListItemText
                        primary={context.name}
                        secondary={
                          <Box>
                            <LinearProgress
                              variant="determinate"
                              value={context.progress}
                              sx={{ mt: 1, mb: 1 }}
                            />
                            <Typography variant="caption">
                              {context.progress}% complete
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Recent Contexts */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Contexts
              </Typography>
              <List>
                {contexts.slice(0, 5).map((context) => (
                  <ListItem key={context.id}>
                    <ListItemText
                      primary={context.name}
                      secondary={`${context.total_chunks || 0} chunks`}
                      secondaryTypographyProps={{
                        component: 'div'
                      }}
                    />
                    <Box display="flex" alignItems="center" gap={1} mt={1}>
                      <Chip
                        label={getStatusText(context.status)}
                        color={getStatusColor(context.status) as any}
                        size="small"
                      />
                    </Box>
                    <ListItemSecondaryAction>
                      <IconButton
                        edge="end"
                        onClick={() => navigate('/contexts')}
                      >
                        <PlayIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
              {contexts.length === 0 && (
                <Typography color="text.secondary" textAlign="center" py={2}>
                  No contexts created yet
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Chat Sessions */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Chat Sessions
              </Typography>
              <List>
                {recentSessions.map((session) => (
                  <ListItem key={session.id}>
                    <ListItemText
                      primary={session.title}
                      secondary={
                        <Typography variant="caption">
                          {session.message_count} messages • {' '}
                          {new Date(session.updated_at).toLocaleDateString()}
                        </Typography>
                      }
                    />
                    <ListItemSecondaryAction>
                      <IconButton
                        edge="end"
                        onClick={() => navigate(`/chat/${session.id}`)}
                      >
                        <ChatIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
              {chatSessions.length === 0 && (
                <Typography color="text.secondary" textAlign="center" py={2}>
                  No chat sessions yet
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
