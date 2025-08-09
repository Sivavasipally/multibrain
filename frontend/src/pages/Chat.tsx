import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Paper,
  Typography,
  TextField,
  Button,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Drawer,
  useTheme,
  useMediaQuery,
  Fab,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  OutlinedInput,
  Checkbox,
  ListItemIcon,
} from '@mui/material';
import {
  Send as SendIcon,
  Add as AddIcon,
  Menu as MenuIcon,
  Delete as DeleteIcon,
  Storage as StorageIcon,
} from '@mui/icons-material';
import { chatAPI, contextsAPI } from '../services/api';
import type { ChatSession, Message, Context } from '../types/api';
import { useSnackbar } from '../contexts/SnackbarContext';
import useErrorHandler from '../hooks/useErrorHandler';
import { ComponentErrorBoundary } from '../components/ErrorBoundary/ErrorBoundary';
import ChatMessage from '../components/Chat/ChatMessage';
import ContextSelector from '../components/Chat/ContextSelector';
import ContextSwitcher from '../components/Chat/ContextSwitcher';

const Chat: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [contexts, setContexts] = useState<Context[]>([]);
  const [selectedContexts, setSelectedContexts] = useState<number[]>([]);
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile);
  const [contextSelectorOpen, setContextSelectorOpen] = useState(false);
  const [contextSwitcherOpen, setContextSwitcherOpen] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { showError, showSuccess } = useSnackbar();
  const errorHandler = useErrorHandler({ component: 'ChatPage' });

  // Load initial data only once
  useEffect(() => {
    let mounted = true;
    
    const loadInitialData = async () => {
      try {
        await Promise.all([
          loadSessions(),
          loadContexts()
        ]);
      } catch (error) {
        if (mounted) {
          console.error('Failed to load initial chat data:', error);
        }
      }
    };
    
    loadInitialData();
    
    return () => {
      mounted = false;
    };
  }, []); // Empty dependency array - only run once

  // Load specific session when sessionId changes
  useEffect(() => {
    if (sessionId && !isNaN(parseInt(sessionId))) {
      loadSession(parseInt(sessionId));
    }
  }, [sessionId]); // Only depend on sessionId

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadSessions = errorHandler.withErrorHandler(
    async () => {
      const response = await chatAPI.getChatSessions();
      setSessions(response.sessions);
    },
    'Failed to load chat sessions',
    'loadSessions'
  );

  const loadContexts = errorHandler.withErrorHandler(
    async () => {
      const response = await contextsAPI.getContexts();
      const readyContexts = response.contexts.filter(c => c.status === 'ready');
      setContexts(readyContexts);
    },
    'Failed to load contexts',
    'loadContexts'
  );

  const loadSession = errorHandler.withErrorHandler(
    async (id: number) => {
      const response = await chatAPI.getChatSession(id);
      setCurrentSession(response.session);
      setMessages(response.session.messages || []);
    },
    'Failed to load chat session',
    'loadSession'
  );

  const createNewSession = errorHandler.withErrorHandler(
    async () => {
      const response = await chatAPI.createChatSession();
      setSessions(prev => [response.session, ...prev]);
      navigate(`/chat/${response.session.id}`);
    },
    'Failed to create new session',
    'createNewSession'
  );

  const deleteSession = errorHandler.withErrorHandler(
    async (id: number) => {
      await chatAPI.deleteChatSession(id);
      setSessions(prev => prev.filter(s => s.id !== id));
      
      if (currentSession?.id === id) {
        navigate('/chat');
        setCurrentSession(null);
        setMessages([]);
      }
      
      showSuccess('Session deleted');
    },
    'Failed to delete session',
    'deleteSession'
  );

  const sendMessage = async () => {
    if (!message.trim() || !currentSession || selectedContexts.length === 0) {
      if (selectedContexts.length === 0) {
        setContextSelectorOpen(true);
        return;
      }
      return;
    }

    const userMessage = message.trim();
    setMessage('');
    setSending(true);

    // Add user message immediately
    const tempUserMessage: Message = {
      id: Date.now(),
      role: 'user',
      content: userMessage,
      context_ids: selectedContexts,
      citations: [],
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, tempUserMessage]);

    try {
      const response = await chatAPI.sendMessage(
        currentSession.id,
        userMessage,
        selectedContexts
      );

      // Replace temp message with actual response
      setMessages(prev => [
        ...prev.slice(0, -1),
        tempUserMessage,
        response.message,
      ]);

      // Update session in sidebar
      setSessions(prev =>
        prev.map(s =>
          s.id === currentSession.id
            ? { ...s, message_count: s.message_count + 2, updated_at: new Date().toISOString() }
            : s
        )
      );
    } catch (error: any) {
      errorHandler.handleApiError(error, 'Failed to send message', 'sendMessage');
      // Remove the temp user message on error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setSending(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleContextsChange = (contextIds: number[]) => {
    setSelectedContexts(contextIds);
    
    // Show feedback about context switch
    if (contextIds.length > 0) {
      const contextNames = contexts
        .filter(ctx => contextIds.includes(ctx.id))
        .map(ctx => ctx.name)
        .join(', ');
      
      showSuccess(`Switched to context${contextIds.length > 1 ? 's' : ''}: ${contextNames}`);
    }
  };

  const handleQuickContextSwitch = (contextId: number) => {
    const isSelected = selectedContexts.includes(contextId);
    
    if (isSelected) {
      // Remove context
      if (selectedContexts.length > 1) {
        setSelectedContexts(prev => prev.filter(id => id !== contextId));
      } else {
        showError('At least one context must be selected');
      }
    } else {
      // Add context (up to 3 for quick switch)
      if (selectedContexts.length < 3) {
        setSelectedContexts(prev => [...prev, contextId]);
      } else {
        showError('Maximum 3 contexts can be active. Use the context switcher for more options.');
      }
    }
  };

  const sidebarContent = (
    <Box sx={{ width: 300, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Button
          fullWidth
          variant="contained"
          startIcon={<AddIcon />}
          onClick={createNewSession}
        >
          New Chat
        </Button>
      </Box>
      
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        <List>
          {sessions.map((session) => (
            <ListItem
              key={session.id}
              component="button"
              selected={currentSession?.id === session.id}
              onClick={() => navigate(`/chat/${session.id}`)}
              sx={{ cursor: 'pointer' }}
            >
              <ListItemText
                primary={session.title}
                secondary={`${session.message_count} messages`}
                primaryTypographyProps={{
                  noWrap: true,
                  sx: { fontSize: '0.875rem' }
                }}
                secondaryTypographyProps={{
                  sx: { fontSize: '0.75rem' }
                }}
              />
              <ListItemSecondaryAction>
                <IconButton
                  edge="end"
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteSession(session.id);
                  }}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
        
        {sessions.length === 0 && (
          <Box sx={{ p: 2, textAlign: 'center' }}>
            <Typography color="text.secondary">
              No chat sessions yet
            </Typography>
          </Box>
        )}
      </Box>
    </Box>
  );

  return (
    <Box sx={{ height: 'calc(100vh - 64px)', display: 'flex' }}>
      {/* Sidebar */}
      <Drawer
        variant={isMobile ? 'temporary' : 'permanent'}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        sx={{
          '& .MuiDrawer-paper': {
            position: 'relative',
            height: '100%',
            borderRight: 1,
            borderColor: 'divider',
          },
        }}
      >
        {sidebarContent}
      </Drawer>

      {/* Main Chat Area */}
      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Paper
          sx={{
            p: 2,
            borderBottom: 1,
            borderColor: 'divider',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Box display="flex" alignItems="center" gap={1}>
            {isMobile && (
              <IconButton onClick={() => setSidebarOpen(true)}>
                <MenuIcon />
              </IconButton>
            )}
            <Typography variant="h6">
              {currentSession?.title || 'Select a chat session'}
            </Typography>
          </Box>
          
          {currentSession && (
            <Box display="flex" alignItems="center" gap={1}>
              {/* Quick Context Pills */}
              {selectedContexts.slice(0, 2).map(contextId => {
                const context = contexts.find(c => c.id === contextId);
                return context ? (
                  <Chip
                    key={contextId}
                    label={context.name}
                    size="small"
                    onDelete={() => handleQuickContextSwitch(contextId)}
                    clickable
                    onClick={() => handleQuickContextSwitch(contextId)}
                    color="primary"
                    variant="outlined"
                  />
                ) : null;
              })}
              
              {selectedContexts.length > 2 && (
                <Chip
                  label={`+${selectedContexts.length - 2} more`}
                  size="small"
                  variant="outlined"
                  clickable
                  onClick={() => setContextSwitcherOpen(true)}
                />
              )}
              
              <Button
                variant="outlined"
                size="small"
                startIcon={<StorageIcon />}
                onClick={() => setContextSwitcherOpen(true)}
              >
                {selectedContexts.length === 0 
                  ? 'Select Contexts' 
                  : `${selectedContexts.length} Context${selectedContexts.length > 1 ? 's' : ''}`
                }
              </Button>
            </Box>
          )}
        </Paper>

        {currentSession ? (
          <>
            {/* Messages */}
            <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
              {messages.length === 0 ? (
                <Box
                  sx={{
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    textAlign: 'center',
                  }}
                >
                  <Box>
                    <Typography variant="h5" gutterBottom>
                      Start a conversation
                    </Typography>
                    <Typography color="text.secondary" paragraph>
                      Select contexts and ask questions about your data
                    </Typography>
                    <Button
                      variant="contained"
                      onClick={() => setContextSwitcherOpen(true)}
                    >
                      Select Contexts
                    </Button>
                  </Box>
                </Box>
              ) : (
                <>
                  {messages.map((msg, index) => (
                    <ComponentErrorBoundary 
                      key={msg.id || index} 
                      componentName="ChatMessage"
                      fallback={
                        <Box sx={{ p: 2, bgcolor: 'error.light', borderRadius: 1, mb: 1 }}>
                          <Typography color="error.contrastText">
                            Error displaying message
                          </Typography>
                        </Box>
                      }
                    >
                      <ChatMessage message={msg} />
                    </ComponentErrorBoundary>
                  ))}
                  <div ref={messagesEndRef} />
                </>
              )}
            </Box>

            {/* Input */}
            <Paper sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
              {selectedContexts.length > 0 && (
                <Box sx={{ mb: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {selectedContexts.map((contextId) => {
                    const context = contexts.find(c => c.id === contextId);
                    return context ? (
                      <Chip
                        key={contextId}
                        label={context.name}
                        size="small"
                        onDelete={() => setSelectedContexts(prev => prev.filter(id => id !== contextId))}
                      />
                    ) : null;
                  })}
                </Box>
              )}
              
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  multiline
                  maxRows={4}
                  placeholder="Type your message..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={sending}
                />
                <Button
                  variant="contained"
                  onClick={sendMessage}
                  disabled={sending || !message.trim() || selectedContexts.length === 0}
                  sx={{ minWidth: 'auto', px: 2 }}
                >
                  <SendIcon />
                </Button>
              </Box>
            </Paper>
          </>
        ) : (
          <Box
            sx={{
              flexGrow: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
            }}
          >
            <Box>
              <Typography variant="h4" gutterBottom>
                Welcome to RAG Chatbot
              </Typography>
              <Typography color="text.secondary" paragraph>
                Create a new chat session or select an existing one to start
              </Typography>
              <Button variant="contained" onClick={createNewSession}>
                Start New Chat
              </Button>
            </Box>
          </Box>
        )}
      </Box>

      {/* Context Selector (Legacy) */}
      <ComponentErrorBoundary componentName="ContextSelector">
        <ContextSelector
          open={contextSelectorOpen}
          contexts={contexts}
          selectedContexts={selectedContexts}
          onSelectionChange={setSelectedContexts}
          onClose={() => setContextSelectorOpen(false)}
        />
      </ComponentErrorBoundary>

      {/* Advanced Context Switcher */}
      <ComponentErrorBoundary componentName="ContextSwitcher">
        {contextSwitcherOpen && (
          <Box
            sx={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              bgcolor: 'rgba(0, 0, 0, 0.5)',
              zIndex: 1300,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              p: 2,
            }}
            onClick={() => setContextSwitcherOpen(false)}
          >
            <Paper
              sx={{
                maxWidth: 800,
                width: '100%',
                maxHeight: '90vh',
                overflow: 'auto',
                p: 3,
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <ContextSwitcher
                sessionId={currentSession?.id}
                selectedContexts={selectedContexts}
                onContextsChange={handleContextsChange}
                maxContexts={5}
                showMetrics={true}
                showSearch={true}
                showFilters={true}
                allowEmpty={false}
                onClose={() => setContextSwitcherOpen(false)}
              />
            </Paper>
          </Box>
        )}
      </ComponentErrorBoundary>

      {/* Mobile FAB */}
      {isMobile && (
        <Fab
          color="primary"
          sx={{ position: 'fixed', bottom: 16, right: 16 }}
          onClick={() => setSidebarOpen(true)}
        >
          <MenuIcon />
        </Fab>
      )}
    </Box>
  );
};

export default Chat;
