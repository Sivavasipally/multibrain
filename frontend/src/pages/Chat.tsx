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
import ChatMessage from '../components/Chat/ChatMessage';
import ContextSelector from '../components/Chat/ContextSelector';

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
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { showError, showSuccess } = useSnackbar();

  useEffect(() => {
    loadSessions();
    loadContexts();
  }, []);

  useEffect(() => {
    if (sessionId) {
      loadSession(parseInt(sessionId));
    }
  }, [sessionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadSessions = async () => {
    try {
      const response = await chatAPI.getChatSessions();
      setSessions(response.sessions);
    } catch (error: any) {
      showError('Failed to load chat sessions');
    }
  };

  const loadContexts = async () => {
    try {
      const response = await contextsAPI.getContexts();
      const readyContexts = response.contexts.filter(c => c.status === 'ready');
      setContexts(readyContexts);
    } catch (error: any) {
      showError('Failed to load contexts');
    }
  };

  const loadSession = async (id: number) => {
    try {
      const response = await chatAPI.getChatSession(id);
      setCurrentSession(response.session);
      setMessages(response.session.messages || []);
    } catch (error: any) {
      showError('Failed to load chat session');
    }
  };

  const createNewSession = async () => {
    try {
      const response = await chatAPI.createChatSession();
      setSessions(prev => [response.session, ...prev]);
      navigate(`/chat/${response.session.id}`);
    } catch (error: any) {
      showError('Failed to create new session');
    }
  };

  const deleteSession = async (id: number) => {
    try {
      await chatAPI.deleteChatSession(id);
      setSessions(prev => prev.filter(s => s.id !== id));
      
      if (currentSession?.id === id) {
        navigate('/chat');
        setCurrentSession(null);
        setMessages([]);
      }
      
      showSuccess('Session deleted');
    } catch (error: any) {
      showError('Failed to delete session');
    }
  };

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
      showError('Failed to send message');
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
            <Button
              variant="outlined"
              size="small"
              startIcon={<StorageIcon />}
              onClick={() => setContextSelectorOpen(true)}
            >
              Contexts ({selectedContexts.length})
            </Button>
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
                      onClick={() => setContextSelectorOpen(true)}
                    >
                      Select Contexts
                    </Button>
                  </Box>
                </Box>
              ) : (
                <>
                  {messages.map((msg, index) => (
                    <ChatMessage key={msg.id || index} message={msg} />
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

      {/* Context Selector */}
      <ContextSelector
        open={contextSelectorOpen}
        contexts={contexts}
        selectedContexts={selectedContexts}
        onSelectionChange={setSelectedContexts}
        onClose={() => setContextSelectorOpen(false)}
      />

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
