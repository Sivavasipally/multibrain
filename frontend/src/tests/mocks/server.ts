/**
 * Mock Service Worker (MSW) server for API mocking in tests
 */

import { setupServer } from 'msw/node';
import { rest } from 'msw';

// Mock data
const mockUser = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  created_at: '2023-01-01T00:00:00Z',
  is_active: true,
};

const mockContexts = [
  {
    id: 1,
    name: 'Test Context 1',
    description: 'A test context for files',
    source_type: 'files',
    status: 'ready',
    progress: 100,
    total_chunks: 50,
    total_tokens: 1000,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z',
    config: { file_paths: ['test1.txt', 'test2.py'] },
  },
  {
    id: 2,
    name: 'Test Context 2',
    description: 'A test context for repository',
    source_type: 'repo',
    status: 'processing',
    progress: 75,
    total_chunks: 0,
    total_tokens: 0,
    created_at: '2023-01-02T00:00:00Z',
    updated_at: '2023-01-02T00:00:00Z',
    config: { repo_url: 'https://github.com/test/repo' },
  },
];

const mockChatSessions = [
  {
    id: 1,
    title: 'Test Chat Session 1',
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z',
    message_count: 4,
  },
  {
    id: 2,
    title: 'Test Chat Session 2',
    created_at: '2023-01-02T00:00:00Z',
    updated_at: '2023-01-02T00:00:00Z',
    message_count: 2,
  },
];

const mockMessages = [
  {
    id: 1,
    role: 'user',
    content: 'What is this codebase about?',
    context_ids: [1],
    citations: [],
    created_at: '2023-01-01T00:00:00Z',
  },
  {
    id: 2,
    role: 'assistant',
    content: 'This codebase is a RAG chatbot PWA that allows users to create contexts from various sources and chat with their data.',
    context_ids: [1],
    citations: [
      {
        context_name: 'Test Context 1',
        source: 'README.md',
        score: 0.95,
      },
    ],
    created_at: '2023-01-01T00:00:01Z',
  },
];

// Request handlers
const handlers = [
  // Auth endpoints
  rest.post('http://localhost:5000/api/auth/register', (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        access_token: 'mock-access-token',
        user: mockUser,
      })
    );
  }),

  rest.post('http://localhost:5000/api/auth/login', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        access_token: 'mock-access-token',
        user: mockUser,
      })
    );
  }),

  rest.get('http://localhost:5000/api/auth/profile', (req, res, ctx) => {
    const authHeader = req.headers.get('Authorization');
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res(ctx.status(401), ctx.json({ error: 'Unauthorized' }));
    }

    return res(
      ctx.status(200),
      ctx.json({
        user: mockUser,
      })
    );
  }),

  rest.post('http://localhost:5000/api/auth/logout', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ message: 'Logged out successfully' })
    );
  }),

  // Context endpoints
  rest.get('http://localhost:5000/api/contexts', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        contexts: mockContexts,
      })
    );
  }),

  rest.post('http://localhost:5000/api/contexts', (req, res, ctx) => {
    const newContext = {
      id: mockContexts.length + 1,
      ...req.body,
      status: 'pending',
      progress: 0,
      total_chunks: 0,
      total_tokens: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    return res(
      ctx.status(201),
      ctx.json({
        context: newContext,
      })
    );
  }),

  rest.get('http://localhost:5000/api/contexts/:id', (req, res, ctx) => {
    const { id } = req.params;
    const context = mockContexts.find(c => c.id === parseInt(id as string));

    if (!context) {
      return res(ctx.status(404), ctx.json({ error: 'Context not found' }));
    }

    return res(
      ctx.status(200),
      ctx.json({
        context: {
          ...context,
          documents: [
            {
              id: 1,
              filename: 'test1.txt',
              file_type: 'text',
              file_size: 1024,
              chunks_count: 5,
              tokens_count: 100,
              language: 'text',
              processed_at: '2023-01-01T00:00:00Z',
            },
          ],
        },
      })
    );
  }),

  rest.put('http://localhost:5000/api/contexts/:id', (req, res, ctx) => {
    const { id } = req.params;
    const context = mockContexts.find(c => c.id === parseInt(id as string));

    if (!context) {
      return res(ctx.status(404), ctx.json({ error: 'Context not found' }));
    }

    const updatedContext = {
      ...context,
      ...req.body,
      updated_at: new Date().toISOString(),
    };

    return res(
      ctx.status(200),
      ctx.json({
        context: updatedContext,
      })
    );
  }),

  rest.delete('http://localhost:5000/api/contexts/:id', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ message: 'Context deleted successfully' })
    );
  }),

  rest.post('http://localhost:5000/api/contexts/:id/reprocess', (req, res, ctx) => {
    const { id } = req.params;
    const context = mockContexts.find(c => c.id === parseInt(id as string));

    if (!context) {
      return res(ctx.status(404), ctx.json({ error: 'Context not found' }));
    }

    return res(
      ctx.status(200),
      ctx.json({
        context: {
          ...context,
          status: 'processing',
          progress: 0,
        },
      })
    );
  }),

  // Chat endpoints
  rest.get('http://localhost:5000/api/chat/sessions', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        sessions: mockChatSessions,
      })
    );
  }),

  rest.post('http://localhost:5000/api/chat/sessions', (req, res, ctx) => {
    const newSession = {
      id: mockChatSessions.length + 1,
      title: `Chat Session ${mockChatSessions.length + 1}`,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      message_count: 0,
    };

    return res(
      ctx.status(201),
      ctx.json({
        session: newSession,
      })
    );
  }),

  rest.get('http://localhost:5000/api/chat/sessions/:id', (req, res, ctx) => {
    const { id } = req.params;
    const session = mockChatSessions.find(s => s.id === parseInt(id as string));

    if (!session) {
      return res(ctx.status(404), ctx.json({ error: 'Session not found' }));
    }

    return res(
      ctx.status(200),
      ctx.json({
        session: {
          ...session,
          messages: mockMessages,
        },
      })
    );
  }),

  rest.delete('http://localhost:5000/api/chat/sessions/:id', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ message: 'Session deleted successfully' })
    );
  }),

  rest.post('http://localhost:5000/api/chat/query', (req, res, ctx) => {
    const newMessage = {
      id: mockMessages.length + 1,
      role: 'assistant',
      content: 'This is a mock response to your question.',
      context_ids: [1],
      citations: [
        {
          context_name: 'Test Context 1',
          source: 'mock-source.txt',
          score: 0.85,
        },
      ],
      created_at: new Date().toISOString(),
    };

    return res(
      ctx.status(200),
      ctx.json({
        message: newMessage,
        citations: newMessage.citations,
      })
    );
  }),

  // Upload endpoints
  rest.post('http://localhost:5000/api/upload/files', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        files: [
          {
            filename: 'test-upload.txt',
            size: 1024,
            path: '/uploads/test-upload.txt',
          },
        ],
      })
    );
  }),

  rest.get('http://localhost:5000/api/upload/supported-extensions', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        extensions: {
          documents: ['.pdf', '.docx', '.doc', '.txt', '.md'],
          code: ['.py', '.js', '.ts', '.java', '.cpp'],
          data: ['.csv', '.json', '.yaml', '.xml'],
          archives: ['.zip', '.tar', '.gz'],
        },
        total_count: 50,
      })
    );
  }),

  // Health check
  rest.get('http://localhost:5000/health', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: 'test',
      })
    );
  }),
];

// Create server
export const server = setupServer(...handlers);
