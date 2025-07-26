import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Avatar,
  IconButton,
  Collapse,
  Chip,
  Link,
  Tooltip,
} from '@mui/material';
import {
  Person as PersonIcon,
  SmartToy as BotIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  ContentCopy as CopyIcon,
  Source as SourceIcon,
} from '@mui/icons-material';
import type { Message } from '../../types/api';
import { useSnackbar } from '../../contexts/SnackbarContext';

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const [showCitations, setShowCitations] = useState(false);
  const { showSuccess } = useSnackbar();

  const isUser = message.role === 'user';

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      showSuccess('Message copied to clipboard');
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const formatContent = (content: string) => {
    // Simple markdown-like formatting
    return content
      .split('\n')
      .map((line, index) => {
        // Handle code blocks
        if (line.startsWith('```')) {
          return null; // Handle in a more sophisticated way if needed
        }
        
        // Handle inline code
        const codeRegex = /`([^`]+)`/g;
        const parts = line.split(codeRegex);
        
        return (
          <Typography
            key={index}
            variant="body1"
            component="div"
            sx={{ mb: index < content.split('\n').length - 1 ? 1 : 0 }}
          >
            {parts.map((part, partIndex) => {
              if (partIndex % 2 === 1) {
                // This is code
                return (
                  <Box
                    key={partIndex}
                    component="code"
                    sx={{
                      backgroundColor: 'grey.100',
                      px: 0.5,
                      py: 0.25,
                      borderRadius: 0.5,
                      fontFamily: 'monospace',
                      fontSize: '0.875rem',
                    }}
                  >
                    {part}
                  </Box>
                );
              }
              return part;
            })}
          </Typography>
        );
      })
      .filter(Boolean);
  };

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mb: 2,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: isUser ? 'row-reverse' : 'row',
          alignItems: 'flex-start',
          gap: 1,
          maxWidth: '80%',
        }}
      >
        <Avatar
          sx={{
            bgcolor: isUser ? 'primary.main' : 'secondary.main',
            width: 32,
            height: 32,
          }}
        >
          {isUser ? <PersonIcon /> : <BotIcon />}
        </Avatar>

        <Paper
          sx={{
            p: 2,
            backgroundColor: isUser ? 'primary.light' : 'background.paper',
            color: isUser ? 'primary.contrastText' : 'text.primary',
            borderRadius: 2,
            position: 'relative',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
            <Box sx={{ flexGrow: 1 }}>
              {formatContent(message.content)}
            </Box>
            
            <Tooltip title="Copy message">
              <IconButton
                size="small"
                onClick={copyToClipboard}
                sx={{
                  color: isUser ? 'primary.contrastText' : 'text.secondary',
                  opacity: 0.7,
                  '&:hover': { opacity: 1 },
                }}
              >
                <CopyIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>

          {/* Citations */}
          {!isUser && message.citations && message.citations.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  cursor: 'pointer',
                }}
                onClick={() => setShowCitations(!showCitations)}
              >
                <SourceIcon fontSize="small" />
                <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                  Sources ({message.citations.length})
                </Typography>
                {showCitations ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </Box>

              <Collapse in={showCitations}>
                <Box sx={{ mt: 1, display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {message.citations.map((citation, index) => (
                    <Paper
                      key={index}
                      variant="outlined"
                      sx={{
                        p: 1,
                        backgroundColor: 'background.default',
                        borderRadius: 1,
                      }}
                    >
                      <Box
                        sx={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          mb: 0.5,
                        }}
                      >
                        <Typography variant="caption" fontWeight="bold">
                          {citation.context_name}
                        </Typography>
                        <Chip
                          label={`${(citation.score * 100).toFixed(1)}%`}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        {citation.source}
                      </Typography>
                    </Paper>
                  ))}
                </Box>
              </Collapse>
            </Box>
          )}

          {/* Metadata */}
          <Box
            sx={{
              mt: 1,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <Typography
              variant="caption"
              sx={{
                color: isUser ? 'primary.contrastText' : 'text.secondary',
                opacity: 0.7,
              }}
            >
              {new Date(message.created_at).toLocaleTimeString()}
            </Typography>
            
            {!isUser && message.tokens_used && (
              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  opacity: 0.7,
                }}
              >
                {message.tokens_used} tokens
              </Typography>
            )}
          </Box>
        </Paper>
      </Box>
    </Box>
  );
};

export default ChatMessage;
