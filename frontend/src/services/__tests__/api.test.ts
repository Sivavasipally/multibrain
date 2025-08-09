/**
 * Comprehensive tests for API service
 */

import axios from 'axios';
import { authAPI, contextsAPI, chatAPI, uploadAPI } from '../api';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock axios instance
const mockAxiosInstance = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  interceptors: {
    request: { use: jest.fn() },
    response: { use: jest.fn() }
  }
};

mockedAxios.create.mockReturnValue(mockAxiosInstance as any);

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('authAPI', () => {
    it('handles successful login', async () => {
      const mockResponse = {
        data: {
          user: { id: 1, username: 'testuser', email: 'test@email.com' },
          access_token: 'auth-token'
        }
      };
      mockAxiosInstance.post.mockResolvedValueOnce(mockResponse);

      const result = await authAPI.login('testuser', 'password');

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/login', {
        username: 'testuser',
        password: 'password'
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('handles login failure', async () => {
      const mockError = new Error('Invalid credentials');
      mockAxiosInstance.post.mockRejectedValueOnce(mockError);

      await expect(authAPI.login('testuser', 'wrong')).rejects.toThrow('Invalid credentials');
    });

    it('handles successful registration', async () => {
      const mockResponse = {
        data: {
          user: { id: 2, username: 'newuser', email: 'new@email.com' },
          access_token: 'new-token'
        }
      };
      mockAxiosInstance.post.mockResolvedValueOnce(mockResponse);

      const result = await authAPI.register('newuser', 'new@email.com', 'password');

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/register', {
        username: 'newuser',
        email: 'new@email.com',
        password: 'password'
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('gets user profile', async () => {
      const mockResponse = {
        data: {
          user: { id: 1, username: 'testuser', email: 'test@email.com' }
        }
      };
      mockAxiosInstance.get.mockResolvedValueOnce(mockResponse);

      const result = await authAPI.getProfile();

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/auth/profile');
      expect(result).toEqual(mockResponse.data);
    });

    it('handles logout', async () => {
      const mockResponse = { data: { message: 'Logged out successfully' } };
      mockAxiosInstance.post.mockResolvedValueOnce(mockResponse);

      const result = await authAPI.logout();

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/logout');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('contextsAPI', () => {
    it('gets contexts list', async () => {
      const mockResponse = {
        data: {
          contexts: [
            { id: 1, name: 'Context 1', source_type: 'files' },
            { id: 2, name: 'Context 2', source_type: 'repo' }
          ]
        }
      };
      mockAxiosInstance.get.mockResolvedValueOnce(mockResponse);

      const result = await contextsAPI.getContexts();

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/contexts');
      expect(result).toEqual(mockResponse.data);
    });

    it('gets contexts with query parameters', async () => {
      const mockResponse = { data: { contexts: [] } };
      mockAxiosInstance.get.mockResolvedValueOnce(mockResponse);

      await contextsAPI.getContexts({ status: 'ready', source_type: 'files' });

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/contexts?status=ready&source_type=files');
    });

    it('gets single context', async () => {
      const mockResponse = {
        data: {
          context: { id: 1, name: 'Test Context', source_type: 'files' }
        }
      };
      mockAxiosInstance.get.mockResolvedValueOnce(mockResponse);

      const result = await contextsAPI.getContext(1);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/contexts/1');
      expect(result).toEqual(mockResponse.data);
    });

    it('creates new context', async () => {
      const contextData = {
        name: 'New Context',
        description: 'Test context',
        source_type: 'files'
      };
      const mockResponse = {
        data: {
          context: { id: 3, ...contextData, status: 'pending' }
        }
      };
      mockAxiosInstance.post.mockResolvedValueOnce(mockResponse);

      const result = await contextsAPI.createContext(contextData);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/contexts', contextData);
      expect(result).toEqual(mockResponse.data);
    });

    it('updates existing context', async () => {
      const updateData = { name: 'Updated Context' };
      const mockResponse = {
        data: {
          context: { id: 1, name: 'Updated Context', source_type: 'files' }
        }
      };
      mockAxiosInstance.put.mockResolvedValueOnce(mockResponse);

      const result = await contextsAPI.updateContext(1, updateData);

      expect(mockAxiosInstance.put).toHaveBeenCalledWith('/contexts/1', updateData);
      expect(result).toEqual(mockResponse.data);
    });

    it('deletes context', async () => {
      const mockResponse = { data: { message: 'Context deleted successfully' } };
      mockAxiosInstance.delete.mockResolvedValueOnce(mockResponse);

      const result = await contextsAPI.deleteContext(1);

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/contexts/1');
      expect(result).toEqual(mockResponse.data);
    });

    it('searches contexts', async () => {
      const mockResponse = {
        data: {
          results: [{ id: 1, name: 'Search Result' }],
          total: 1
        }
      };
      mockAxiosInstance.get.mockResolvedValueOnce(mockResponse);

      const result = await contextsAPI.searchContexts('test query');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/contexts/search?q=test%20query');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('chatAPI', () => {
    it('creates chat session', async () => {
      const mockResponse = {
        data: {
          session: { id: 1, title: 'New Chat', message_count: 0 }
        }
      };
      mockAxiosInstance.post.mockResolvedValueOnce(mockResponse);

      const result = await chatAPI.createSession();

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/chat/sessions');
      expect(result).toEqual(mockResponse.data);
    });

    it('gets chat sessions', async () => {
      const mockResponse = {
        data: {
          sessions: [
            { id: 1, title: 'Session 1', message_count: 5 },
            { id: 2, title: 'Session 2', message_count: 3 }
          ]
        }
      };
      mockAxiosInstance.get.mockResolvedValueOnce(mockResponse);

      const result = await chatAPI.getSessions();

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/chat/sessions');
      expect(result).toEqual(mockResponse.data);
    });

    it('sends message', async () => {
      const messageData = {
        message: 'Hello, AI!',
        context_ids: [1, 2],
        stream: false
      };
      const mockResponse = {
        data: {
          message: {
            id: 1,
            content: 'Hello! How can I help you?',
            role: 'assistant',
            citations: []
          }
        }
      };
      mockAxiosInstance.post.mockResolvedValueOnce(mockResponse);

      const result = await chatAPI.sendMessage(1, messageData);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/chat/1', messageData);
      expect(result).toEqual(mockResponse.data);
    });

    it('gets chat history', async () => {
      const mockResponse = {
        data: {
          messages: [
            { id: 1, content: 'Hello', role: 'user' },
            { id: 2, content: 'Hi there!', role: 'assistant' }
          ]
        }
      };
      mockAxiosInstance.get.mockResolvedValueOnce(mockResponse);

      const result = await chatAPI.getChatHistory(1);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/chat/1/history');
      expect(result).toEqual(mockResponse.data);
    });

    it('deletes chat session', async () => {
      const mockResponse = { data: { message: 'Session deleted' } };
      mockAxiosInstance.delete.mockResolvedValueOnce(mockResponse);

      const result = await chatAPI.deleteSession(1);

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/chat/sessions/1');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('uploadAPI', () => {
    it('uploads file', async () => {
      const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
      const mockResponse = {
        data: {
          document: {
            id: 1,
            filename: 'test.txt',
            file_type: 'text/plain'
          }
        }
      };
      mockAxiosInstance.post.mockResolvedValueOnce(mockResponse);

      const result = await uploadAPI.uploadFile(1, mockFile);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/upload/1',
        expect.any(FormData),
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: undefined
        }
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('uploads file with progress callback', async () => {
      const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
      const mockResponse = { data: { document: { id: 1 } } };
      const mockProgressCallback = jest.fn();
      
      mockAxiosInstance.post.mockResolvedValueOnce(mockResponse);

      await uploadAPI.uploadFile(1, mockFile, mockProgressCallback);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/upload/1',
        expect.any(FormData),
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: mockProgressCallback
        }
      );
    });

    it('uploads multiple files', async () => {
      const mockFiles = [
        new File(['content 1'], 'test1.txt', { type: 'text/plain' }),
        new File(['content 2'], 'test2.txt', { type: 'text/plain' })
      ];
      const mockResponse = {
        data: {
          documents: [
            { id: 1, filename: 'test1.txt' },
            { id: 2, filename: 'test2.txt' }
          ]
        }
      };
      mockAxiosInstance.post.mockResolvedValueOnce(mockResponse);

      const result = await uploadAPI.uploadFiles(1, mockFiles);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/upload/1/multiple',
        expect.any(FormData),
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: undefined
        }
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('handles upload errors', async () => {
      const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
      const mockError = new Error('Upload failed');
      mockAxiosInstance.post.mockRejectedValueOnce(mockError);

      await expect(uploadAPI.uploadFile(1, mockFile)).rejects.toThrow('Upload failed');
    });
  });

  describe('Error Handling', () => {
    it('handles network errors', async () => {
      const networkError = new Error('Network Error');
      mockAxiosInstance.get.mockRejectedValueOnce(networkError);

      await expect(authAPI.getProfile()).rejects.toThrow('Network Error');
    });

    it('handles HTTP error responses', async () => {
      const httpError = {
        response: {
          status: 401,
          data: { error: 'Unauthorized' }
        }
      };
      mockAxiosInstance.post.mockRejectedValueOnce(httpError);

      await expect(authAPI.login('user', 'pass')).rejects.toEqual(httpError);
    });
  });

  describe('Request Interceptors', () => {
    it('sets up request interceptor for authentication', () => {
      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalled();
    });

    it('sets up response interceptor for error handling', () => {
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled();
    });
  });
});