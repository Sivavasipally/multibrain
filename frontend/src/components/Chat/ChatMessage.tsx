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
    // Enhanced markdown-like formatting for richer content display
    const lines = content.split('\n');
    const elements: React.ReactElement[] = [];
    let inCodeBlock = false;
    let codeBlockContent: string[] = [];
    let codeBlockLanguage = '';
    let inTable = false;
    let tableRows: string[] = [];
    
    lines.forEach((line, index) => {
      // Handle code blocks
      if (line.startsWith('```')) {
        if (!inCodeBlock) {
          // Start code block
          inCodeBlock = true;
          codeBlockLanguage = line.substring(3).trim();
          codeBlockContent = [];
        } else {
          // End code block
          inCodeBlock = false;
          elements.push(
            <Paper
              key={`code-${index}`}
              variant="outlined"
              sx={{
                p: 2,
                backgroundColor: 'grey.50',
                borderRadius: 1,
                mb: 2,
                overflow: 'auto',
              }}
            >
              {codeBlockLanguage && (
                <Typography
                  variant="caption"
                  sx={{
                    color: 'text.secondary',
                    textTransform: 'uppercase',
                    fontWeight: 'bold',
                    mb: 1,
                    display: 'block',
                  }}
                >
                  {codeBlockLanguage}
                </Typography>
              )}
              <Typography
                component="code"
                sx={{
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                  whiteSpace: 'pre-wrap',
                  display: 'block',
                }}
              >
                {codeBlockContent.join('\n')}
              </Typography>
            </Paper>
          );
        }
        return;
      }
      
      if (inCodeBlock) {
        codeBlockContent.push(line);
        return;
      }
      
      // Handle tables
      if (line.includes('|') && line.trim().startsWith('|') && line.trim().endsWith('|')) {
        if (!inTable) {
          inTable = true;
          tableRows = [];
        }
        tableRows.push(line);
        return;
      } else if (inTable) {
        // End table
        inTable = false;
        elements.push(
          <Paper
            key={`table-${index}`}
            variant="outlined"
            sx={{ mb: 2, overflow: 'auto' }}
          >
            <Box component="table" sx={{ width: '100%', borderCollapse: 'collapse' }}>
              {tableRows.map((row, rowIndex) => {
                const cells = row.split('|').slice(1, -1).map(cell => cell.trim());
                const isHeader = rowIndex === 0;
                const isSeparator = row.includes('---');
                
                if (isSeparator) return null;
                
                return (
                  <Box
                    key={rowIndex}
                    component="tr"
                    sx={{
                      borderBottom: '1px solid',
                      borderColor: 'divider',
                    }}
                  >
                    {cells.map((cell, cellIndex) => (
                      <Box
                        key={cellIndex}
                        component={isHeader ? 'th' : 'td'}
                        sx={{
                          p: 1,
                          textAlign: 'left',
                          fontWeight: isHeader ? 'bold' : 'normal',
                          backgroundColor: isHeader ? 'grey.50' : 'transparent',
                        }}
                      >
                        <Typography variant={isHeader ? 'subtitle2' : 'body2'}>
                          {cell}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                );
              })}
            </Box>
          </Paper>
        );
      }
      
      // Handle headers
      if (line.startsWith('#')) {
        const level = line.match(/^#+/)?.[0].length || 1;
        const text = line.substring(level).trim();
        const variant = level === 1 ? 'h5' : level === 2 ? 'h6' : 'subtitle1';
        
        elements.push(
          <Typography
            key={index}
            variant={variant}
            sx={{
              fontWeight: 'bold',
              mt: level === 1 ? 2 : 1.5,
              mb: 1,
              color: 'text.primary',
            }}
          >
            {text}
          </Typography>
        );
        return;
      }
      
      // Handle bold and italic text
      if (line.includes('**') || line.includes('*')) {
        const formatInlineText = (text: string) => {
          // Handle bold text
          let parts = text.split(/\*\*([^*]+)\*\*/g);
          const elements = parts.map((part, i) => 
            i % 2 === 1 ? <strong key={i}>{part}</strong> : part
          );
          
          // Handle italic text
          return elements.map((element, i) => {
            if (typeof element === 'string' && element.includes('*')) {
              const italicParts = element.split(/\*([^*]+)\*/g);
              return italicParts.map((part, j) => 
                j % 2 === 1 ? <em key={`${i}-${j}`}>{part}</em> : part
              );
            }
            return element;
          }).flat();
        };
        
        elements.push(
          <Typography
            key={index}
            variant="body1"
            component="div"
            sx={{ mb: 1 }}
          >
            {formatInlineText(line)}
          </Typography>
        );
        return;
      }
      
      // Handle inline code and regular text
      const codeRegex = /`([^`]+)`/g;
      const parts = line.split(codeRegex);
      
      if (line.trim() === '') {
        elements.push(<Box key={index} sx={{ height: 8 }} />);
        return;
      }
      
      elements.push(
        <Typography
          key={index}
          variant="body1"
          component="div"
          sx={{ mb: 1 }}
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
    });
    
    return elements;
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
                        p: 2,
                        backgroundColor: 'background.default',
                        borderRadius: 1,
                        border: '1px solid',
                        borderColor: 'divider',
                      }}
                    >
                      <Box
                        sx={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'flex-start',
                          mb: 1,
                        }}
                      >
                        <Box sx={{ flexGrow: 1 }}>
                          <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 0.5 }}>
                            {citation.context_name}
                          </Typography>
                          {citation.source && (
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                              📄 {citation.source}
                            </Typography>
                          )}
                          
                          {/* Enhanced metadata display */}
                          {citation.metadata && (
                            <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                              {citation.metadata.file_type && (
                                <Chip
                                  label={citation.metadata.file_type.toUpperCase()}
                                  size="small"
                                  variant="outlined"
                                  color="secondary"
                                  sx={{ height: 18, fontSize: '0.65rem' }}
                                />
                              )}
                              {citation.metadata.document_type && (
                                <Chip
                                  label={citation.metadata.document_type.replace('_', ' ')}
                                  size="small"
                                  variant="outlined"
                                  color="info"
                                  sx={{ height: 18, fontSize: '0.65rem' }}
                                />
                              )}
                              {citation.metadata.section_title && (
                                <Chip
                                  label={`§ ${citation.metadata.section_title}`}
                                  size="small"
                                  variant="outlined"
                                  color="default"
                                  sx={{ height: 18, fontSize: '0.65rem' }}
                                />
                              )}
                              {citation.metadata.has_tables && (
                                <Chip
                                  label={`📊 Tables: ${citation.metadata.table_count || 1}`}
                                  size="small"
                                  variant="outlined"
                                  color="success"
                                  sx={{ height: 18, fontSize: '0.65rem' }}
                                />
                              )}
                              {citation.metadata.processing_method && (
                                <Chip
                                  label={citation.metadata.processing_method}
                                  size="small"
                                  variant="outlined"
                                  color="default"
                                  sx={{ height: 18, fontSize: '0.65rem' }}
                                />
                              )}
                            </Box>
                          )}
                          
                          {/* Document properties */}
                          {citation.metadata?.document_properties && (
                            <Box sx={{ mt: 1 }}>
                              {citation.metadata.document_properties.title && (
                                <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                                  <strong>Title:</strong> {citation.metadata.document_properties.title}
                                </Typography>
                              )}
                              {citation.metadata.document_properties.creator && (
                                <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                                  <strong>Author:</strong> {citation.metadata.document_properties.creator}
                                </Typography>
                              )}
                            </Box>
                          )}
                        </Box>
                        
                        <Chip
                          label={`${(citation.score * 100).toFixed(1)}%`}
                          size="small"
                          color="primary"
                          sx={{ ml: 1, flexShrink: 0 }}
                        />
                      </Box>
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
