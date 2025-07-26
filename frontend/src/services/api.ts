import axios from 'axios';
import type { AxiosInstance, AxiosResponse } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    // Always read token fresh from localStorage to avoid race conditions
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('Adding Authorization header:', `Bearer ${token.substring(0, 20)}...`);
    } else {
      console.log('No token found in localStorage');
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Types
export interface User {
  id: number;
  username: string;
  email: string;
  created_at: string;
  is_active: boolean;
}

export interface Context {
  id: number;
  name: string;
  description: string;
  source_type: 'repo' | 'database' | 'files';
  config: any;
  chunk_strategy: string;
  embedding_model: string;
  status: 'pending' | 'processing' | 'ready' | 'error';
  progress: number;
  error_message?: string;
  total_chunks: number;
  total_tokens: number;
  created_at: string;
  updated_at: string;
  documents?: Document[];
}

export interface Document {
  id: number;
  filename: string;
  file_type: string;
  file_size: number;
  chunks_count: number;
  tokens_count: number;
  language?: string;
  created_at: string;
  processed_at?: string;
}

export interface ChatSession {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  messages?: Message[];
}

export interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  context_ids: number[];
  citations: Citation[];
  tokens_used?: number;
  model_used?: string;
  created_at: string;
}

export interface Citation {
  context_id: number;
  context_name: string;
  source: string;
  score: number;
}

// Auth API
export const authAPI = {
  login: async (username: string, password: string): Promise<{ access_token: string; user: User }> => {
    const response = await api.post('/auth/login', { username, password });
    return response.data;
  },

  register: async (username: string, email: string, password: string): Promise<{ access_token: string; user: User }> => {
    const response = await api.post('/auth/register', { username, email, password });
    return response.data;
  },

  getProfile: async (token?: string): Promise<{ user: User }> => {
    const config = token ? { headers: { Authorization: `Bearer ${token}` } } : {};
    const response = await api.get('/auth/profile', config);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },
};

// Contexts API
export const contextsAPI = {
  getContexts: async (): Promise<{ contexts: Context[] }> => {
    const response = await api.get('/contexts');
    return response.data;
  },

  getContext: async (id: number): Promise<{ context: Context }> => {
    const response = await api.get(`/contexts/${id}`);
    return response.data;
  },

  createContext: async (contextData: Partial<Context>): Promise<{ context: Context }> => {
    const response = await api.post('/contexts', contextData);
    return response.data;
  },

  updateContext: async (id: number, contextData: Partial<Context>): Promise<{ context: Context }> => {
    const response = await api.put(`/contexts/${id}`, contextData);
    return response.data;
  },

  deleteContext: async (id: number): Promise<void> => {
    await api.delete(`/contexts/${id}`);
  },

  reprocessContext: async (id: number): Promise<{ context: Context }> => {
    const response = await api.post(`/contexts/${id}/reprocess`);
    return response.data;
  },

  getContextStatus: async (id: number): Promise<{
    status: string;
    progress: number;
    error_message?: string;
    total_chunks: number;
    total_tokens: number;
  }> => {
    const response = await api.get(`/contexts/${id}/status`);
    return response.data;
  },
};

// Chat API
export const chatAPI = {
  getChatSessions: async (): Promise<{ sessions: ChatSession[] }> => {
    const response = await api.get('/chat/sessions');
    return response.data;
  },

  getChatSession: async (id: number): Promise<{ session: ChatSession }> => {
    const response = await api.get(`/chat/sessions/${id}`);
    return response.data;
  },

  createChatSession: async (title?: string): Promise<{ session: ChatSession }> => {
    const response = await api.post('/chat/sessions', { title });
    return response.data;
  },

  deleteChatSession: async (id: number): Promise<void> => {
    await api.delete(`/chat/sessions/${id}`);
  },

  sendMessage: async (
    sessionId: number,
    message: string,
    contextIds: number[],
    stream: boolean = false
  ): Promise<{ message: Message; citations: Citation[] }> => {
    const response = await api.post('/chat/query', {
      session_id: sessionId,
      message,
      context_ids: contextIds,
      stream,
    });
    return response.data;
  },

  // Streaming chat (returns EventSource for SSE)
  streamMessage: (
    sessionId: number,
    message: string,
    contextIds: number[]
  ): EventSource => {
    const token = localStorage.getItem('token');
    const url = new URL(`${API_BASE_URL}/api/chat/query`);
    
    // Create EventSource with POST data (this is a simplified approach)
    // In a real implementation, you might need to use fetch with streaming
    const eventSource = new EventSource(url.toString());
    
    // Send the actual POST request
    api.post('/chat/query', {
      session_id: sessionId,
      message,
      context_ids: contextIds,
      stream: true,
    });
    
    return eventSource;
  },
};

// Upload API
export const uploadAPI = {
  uploadFiles: async (contextId: number, files: FileList): Promise<{ files: any[] }> => {
    const formData = new FormData();
    formData.append('context_id', contextId.toString());
    
    Array.from(files).forEach((file) => {
      formData.append('files', file);
    });

    const response = await api.post('/upload/files', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  extractZip: async (contextId: number, zipFile: File): Promise<{ files: any[] }> => {
    const formData = new FormData();
    formData.append('context_id', contextId.toString());
    formData.append('file', zipFile);

    const response = await api.post('/upload/extract-zip', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getSupportedExtensions: async (): Promise<{ extensions: any; total_count: number }> => {
    const response = await api.get('/upload/supported-extensions');
    return response.data;
  },
};

export default api;
