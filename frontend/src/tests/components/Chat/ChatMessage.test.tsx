/**
 * Tests for ChatMessage component
 */

import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render, createMockMessage } from '../../utils/test-utils';
import ChatMessage from '../../../components/Chat/ChatMessage';

// Mock clipboard API
const mockWriteText = jest.fn();
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: mockWriteText,
  },
  writable: true,
});

describe('ChatMessage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders user message correctly', () => {
    const userMessage = createMockMessage({
      role: 'user',
      content: 'Hello, how are you?',
    });

    render(<ChatMessage message={userMessage} />);

    expect(screen.getByText('Hello, how are you?')).toBeInTheDocument();
    
    // User messages should have different styling
    const messageContainer = screen.getByText('Hello, how are you?').closest('[data-testid]');
    expect(messageContainer).toHaveStyle({ justifyContent: 'flex-end' });
  });

  it('renders assistant message correctly', () => {
    const assistantMessage = createMockMessage({
      role: 'assistant',
      content: 'I am doing well, thank you for asking!',
    });

    render(<ChatMessage message={assistantMessage} />);

    expect(screen.getByText('I am doing well, thank you for asking!')).toBeInTheDocument();
    
    // Assistant messages should be left-aligned
    const messageContainer = screen.getByText('I am doing well, thank you for asking!').closest('[data-testid]');
    expect(messageContainer).toHaveStyle({ justifyContent: 'flex-start' });
  });

  it('displays message timestamp', () => {
    const message = createMockMessage({
      created_at: '2023-01-01T12:00:00Z',
    });

    render(<ChatMessage message={message} />);

    // Should display formatted time
    expect(screen.getByText(/12:00/)).toBeInTheDocument();
  });

  it('shows copy button and copies message to clipboard', async () => {
    const user = userEvent.setup();
    const message = createMockMessage({
      content: 'This is a test message',
    });

    render(<ChatMessage message={message} />);

    const copyButton = screen.getByLabelText(/copy message/i);
    expect(copyButton).toBeInTheDocument();

    await user.click(copyButton);

    expect(mockWriteText).toHaveBeenCalledWith('This is a test message');
  });

  it('displays citations for assistant messages', async () => {
    const user = userEvent.setup();
    const assistantMessage = createMockMessage({
      role: 'assistant',
      content: 'Based on the documentation...',
      citations: [
        {
          context_name: 'Documentation',
          source: 'README.md',
          score: 0.95,
        },
        {
          context_name: 'Code',
          source: 'main.py',
          score: 0.87,
        },
      ],
    });

    render(<ChatMessage message={assistantMessage} />);

    // Should show sources section
    expect(screen.getByText(/sources \(2\)/i)).toBeInTheDocument();

    // Click to expand citations
    const sourcesButton = screen.getByText(/sources \(2\)/i);
    await user.click(sourcesButton);

    // Should show citation details
    expect(screen.getByText('Documentation')).toBeInTheDocument();
    expect(screen.getByText('README.md')).toBeInTheDocument();
    expect(screen.getByText('95.0%')).toBeInTheDocument();
    
    expect(screen.getByText('Code')).toBeInTheDocument();
    expect(screen.getByText('main.py')).toBeInTheDocument();
    expect(screen.getByText('87.0%')).toBeInTheDocument();
  });

  it('does not show citations for user messages', () => {
    const userMessage = createMockMessage({
      role: 'user',
      content: 'What is this about?',
      citations: [], // User messages shouldn't have citations anyway
    });

    render(<ChatMessage message={userMessage} />);

    expect(screen.queryByText(/sources/i)).not.toBeInTheDocument();
  });

  it('handles messages without citations', () => {
    const assistantMessage = createMockMessage({
      role: 'assistant',
      content: 'This is a response without citations',
      citations: [],
    });

    render(<ChatMessage message={assistantMessage} />);

    expect(screen.queryByText(/sources/i)).not.toBeInTheDocument();
  });

  it('formats code blocks in message content', () => {
    const message = createMockMessage({
      content: 'Here is some code: `console.log("hello")` and more text.',
    });

    render(<ChatMessage message={message} />);

    const codeElement = screen.getByText('console.log("hello")');
    expect(codeElement).toBeInTheDocument();
    expect(codeElement).toHaveStyle({
      fontFamily: 'monospace',
      backgroundColor: expect.any(String),
    });
  });

  it('handles multiline messages', () => {
    const message = createMockMessage({
      content: 'Line 1\nLine 2\nLine 3',
    });

    render(<ChatMessage message={message} />);

    expect(screen.getByText('Line 1')).toBeInTheDocument();
    expect(screen.getByText('Line 2')).toBeInTheDocument();
    expect(screen.getByText('Line 3')).toBeInTheDocument();
  });

  it('shows token count for assistant messages', () => {
    const assistantMessage = createMockMessage({
      role: 'assistant',
      content: 'This is an assistant response',
      tokens_used: 150,
    });

    render(<ChatMessage message={assistantMessage} />);

    expect(screen.getByText('150 tokens')).toBeInTheDocument();
  });

  it('does not show token count for user messages', () => {
    const userMessage = createMockMessage({
      role: 'user',
      content: 'This is a user message',
    });

    render(<ChatMessage message={userMessage} />);

    expect(screen.queryByText(/tokens/)).not.toBeInTheDocument();
  });

  it('handles citation expansion and collapse', async () => {
    const user = userEvent.setup();
    const assistantMessage = createMockMessage({
      role: 'assistant',
      content: 'Message with citations',
      citations: [
        {
          context_name: 'Test Context',
          source: 'test.txt',
          score: 0.9,
        },
      ],
    });

    render(<ChatMessage message={assistantMessage} />);

    const sourcesButton = screen.getByText(/sources \(1\)/i);
    
    // Initially collapsed
    expect(screen.queryByText('Test Context')).not.toBeInTheDocument();

    // Expand
    await user.click(sourcesButton);
    expect(screen.getByText('Test Context')).toBeInTheDocument();

    // Collapse
    await user.click(sourcesButton);
    await waitFor(() => {
      expect(screen.queryByText('Test Context')).not.toBeInTheDocument();
    });
  });

  it('handles copy failure gracefully', async () => {
    const user = userEvent.setup();
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    
    // Mock clipboard failure
    mockWriteText.mockRejectedValueOnce(new Error('Clipboard not available'));

    const message = createMockMessage({
      content: 'Test message',
    });

    render(<ChatMessage message={message} />);

    const copyButton = screen.getByLabelText(/copy message/i);
    await user.click(copyButton);

    expect(consoleSpy).toHaveBeenCalledWith('Failed to copy:', expect.any(Error));
    
    consoleSpy.mockRestore();
  });

  it('displays correct avatar icons', () => {
    const userMessage = createMockMessage({ role: 'user' });
    const assistantMessage = createMockMessage({ role: 'assistant' });

    const { rerender } = render(<ChatMessage message={userMessage} />);
    
    // User message should have person icon
    expect(screen.getByTestId('PersonIcon')).toBeInTheDocument();

    rerender(<ChatMessage message={assistantMessage} />);
    
    // Assistant message should have bot icon
    expect(screen.getByTestId('SmartToyIcon')).toBeInTheDocument();
  });
});
