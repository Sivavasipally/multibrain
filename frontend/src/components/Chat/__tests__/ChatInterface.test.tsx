/**
 * Comprehensive tests for ChatInterface component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import ChatInterface from '../ChatInterface';
import { AuthProvider } from '../../../contexts/AuthContext';

// Mock API service
const mockSendMessage = jest.fn();
const mockGetChatHistory = jest.fn();
jest.mock('../../../services/api', () => ({
  chatAPI: {
    sendMessage: mockSendMessage,
    getChatHistory: mockGetChatHistory,
    createSession: jest.fn().mockResolvedValue({ session: { id: 1, title: 'Test Session' } })
  },
  contextsAPI: {
    getContexts: jest.fn().mockResolvedValue({ contexts: [] })
  }
}));

// Mock AuthContext
const mockAuthContext = {
  user: { id: 1, username: 'testuser', email: 'test@example.com' },
  login: jest.fn(),
  logout: jest.fn(),
  register: jest.fn(),
  loading: false
};

jest.mock('../../../contexts/AuthContext', () => ({
  ...jest.requireActual('../../../contexts/AuthContext'),
  useAuth: () => mockAuthContext
}));

// Test wrapper
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
);

describe('ChatInterface Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetChatHistory.mockResolvedValue({ messages: [] });
  });

  it('renders chat interface with message input', () => {
    render(
      <TestWrapper>
        <ChatInterface sessionId={1} />
      </TestWrapper>
    );

    expect(screen.getByPlaceholderText(/type your message/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  it('sends message when send button is clicked', async () => {
    const user = userEvent.setup();
    const mockResponse = {
      message: {
        id: 1,
        content: 'AI response',
        role: 'assistant',
        citations: []
      }
    };
    mockSendMessage.mockResolvedValueOnce(mockResponse);

    render(
      <TestWrapper>
        <ChatInterface sessionId={1} />
      </TestWrapper>
    );

    const messageInput = screen.getByPlaceholderText(/type your message/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    await user.type(messageInput, 'Hello, AI!');
    await user.click(sendButton);

    await waitFor(() => {
      expect(mockSendMessage).toHaveBeenCalledWith(1, {
        message: 'Hello, AI!',
        context_ids: [],
        stream: false
      });
    });
  });

  it('sends message on Enter key press', async () => {
    const user = userEvent.setup();
    const mockResponse = {
      message: {
        id: 1,
        content: 'AI response',
        role: 'assistant',
        citations: []
      }
    };
    mockSendMessage.mockResolvedValueOnce(mockResponse);

    render(
      <TestWrapper>
        <ChatInterface sessionId={1} />
      </TestWrapper>
    );

    const messageInput = screen.getByPlaceholderText(/type your message/i);

    await user.type(messageInput, 'Hello, AI!');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(mockSendMessage).toHaveBeenCalled();
    });
  });

  it('prevents sending empty messages', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <ChatInterface sessionId={1} />
      </TestWrapper>
    );

    const sendButton = screen.getByRole('button', { name: /send/i });
    expect(sendButton).toBeDisabled();

    const messageInput = screen.getByPlaceholderText(/type your message/i);
    await user.type(messageInput, '   '); // Whitespace only

    expect(sendButton).toBeDisabled();
  });

  it('displays messages in chat history', async () => {
    const mockMessages = [
      {
        id: 1,
        content: 'Hello, AI!',
        role: 'user',
        created_at: '2024-01-01T10:00:00Z'
      },
      {
        id: 2,
        content: 'Hello! How can I help you today?',
        role: 'assistant',
        created_at: '2024-01-01T10:00:05Z',
        citations: []
      }
    ];
    mockGetChatHistory.mockResolvedValue({ messages: mockMessages });

    render(
      <TestWrapper>
        <ChatInterface sessionId={1} />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Hello, AI!')).toBeInTheDocument();
      expect(screen.getByText('Hello! How can I help you today?')).toBeInTheDocument();
    });
  });

  it('shows loading indicator while sending message', async () => {
    const user = userEvent.setup();
    mockSendMessage.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({
        message: { id: 1, content: 'Response', role: 'assistant', citations: [] }
      }), 100))
    );

    render(
      <TestWrapper>
        <ChatInterface sessionId={1} />
      </TestWrapper>
    );

    const messageInput = screen.getByPlaceholderText(/type your message/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    await user.type(messageInput, 'Hello, AI!');
    await user.click(sendButton);

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('displays error message when send fails', async () => {
    const user = userEvent.setup();
    const errorMessage = 'Failed to send message';
    mockSendMessage.mockRejectedValueOnce(new Error(errorMessage));

    render(
      <TestWrapper>
        <ChatInterface sessionId={1} />
      </TestWrapper>
    );

    const messageInput = screen.getByPlaceholderText(/type your message/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    await user.type(messageInput, 'Hello, AI!');
    await user.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText(/failed to send message/i)).toBeInTheDocument();
    });
  });

  it('scrolls to bottom when new message is added', async () => {
    const mockScrollIntoView = jest.fn();
    Element.prototype.scrollIntoView = mockScrollIntoView;

    const user = userEvent.setup();
    mockSendMessage.mockResolvedValue({
      message: {
        id: 1,
        content: 'AI response',
        role: 'assistant',
        citations: []
      }
    });

    render(
      <TestWrapper>
        <ChatInterface sessionId={1} />
      </TestWrapper>
    );

    const messageInput = screen.getByPlaceholderText(/type your message/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    await user.type(messageInput, 'Hello, AI!');
    await user.click(sendButton);

    await waitFor(() => {
      expect(mockScrollIntoView).toHaveBeenCalled();
    });
  });

  it('supports multiline messages', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <ChatInterface sessionId={1} />
      </TestWrapper>
    );

    const messageInput = screen.getByPlaceholderText(/type your message/i);

    await user.type(messageInput, 'Line 1{Shift>}{Enter}{/Shift}Line 2');

    expect(messageInput).toHaveValue('Line 1\nLine 2');
  });

  it('displays citations for AI responses', async () => {
    const mockMessages = [
      {
        id: 1,
        content: 'Based on the documentation, here is the answer.',
        role: 'assistant',
        created_at: '2024-01-01T10:00:00Z',
        citations: [
          {
            source: 'documentation.md',
            content: 'Relevant excerpt from documentation',
            score: 0.95
          }
        ]
      }
    ];
    mockGetChatHistory.mockResolvedValue({ messages: mockMessages });

    render(
      <TestWrapper>
        <ChatInterface sessionId={1} />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Based on the documentation, here is the answer.')).toBeInTheDocument();
      expect(screen.getByText('documentation.md')).toBeInTheDocument();
    });
  });

  it('handles streaming responses', async () => {
    const user = userEvent.setup();
    
    // Mock streaming response
    const mockStreamingResponse = {
      message: {
        id: 1,
        content: '',
        role: 'assistant',
        citations: [],
        streaming: true
      }
    };
    
    mockSendMessage.mockResolvedValue(mockStreamingResponse);

    render(
      <TestWrapper>
        <ChatInterface sessionId={1} />
      </TestWrapper>
    );

    const messageInput = screen.getByPlaceholderText(/type your message/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    await user.type(messageInput, 'Tell me about streaming');
    await user.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText(/typing/i)).toBeInTheDocument();
    });
  });
});