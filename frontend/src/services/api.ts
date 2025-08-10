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

export interface SearchResult {
  context: Context;
  relevance_score?: number;
  highlights?: Array<{
    field: string;
    fragment: string;
    positions: number[];
  }>;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  filters: any;
  execution_time_ms: number;
  suggestions?: string[];
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
  searchContexts: async (
    query?: string,
    filters?: {
      status?: string;
      source_type?: string;
      date_from?: string;
      date_to?: string;
      chunks_min?: number;
      chunks_max?: number;
    },
    sort?: {
      field?: string;
      order?: string;
    },
    limit?: number,
    offset?: number
  ): Promise<SearchResponse> => {
    const params = new URLSearchParams();
    
    if (query) params.append('q', query);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.source_type) params.append('source_type', filters.source_type);
    if (filters?.date_from) params.append('date_from', filters.date_from);
    if (filters?.date_to) params.append('date_to', filters.date_to);
    if (filters?.chunks_min !== undefined) params.append('chunks_min', filters.chunks_min.toString());
    if (filters?.chunks_max !== undefined) params.append('chunks_max', filters.chunks_max.toString());
    if (sort?.field) params.append('sort_by', sort.field);
    if (sort?.order) params.append('sort_order', sort.order);
    if (limit !== undefined) params.append('limit', limit.toString());
    if (offset !== undefined) params.append('offset', offset.toString());
    
    const response = await api.get(`/contexts/search?${params.toString()}`);
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
  uploadFiles: async (contextId: number, files: FileList | File[]): Promise<{ files: any[] }> => {
    const formData = new FormData();
    formData.append('context_id', contextId.toString());
    
    const fileArray = Array.isArray(files) ? files : Array.from(files);
    fileArray.forEach((file) => {
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

// Preferences API
export const preferencesAPI = {
  // Get all preferences
  getPreferences: async () => {
    const response = await api.get('/preferences');
    return response.data;
  },
  
  // Get category preferences
  getCategoryPreferences: async (category: string) => {
    const response = await api.get(`/preferences/${category}`);
    return response.data;
  },
  
  // Update all preferences
  updatePreferences: async (preferences: any) => {
    const response = await api.put('/preferences', { preferences });
    return response.data;
  },
  
  // Update category preferences
  updateCategoryPreferences: async (category: string, preferences: any) => {
    const response = await api.put(`/preferences/${category}`, { preferences });
    return response.data;
  },
  
  // Reset preferences
  resetPreferences: async (category?: string) => {
    const response = await api.post('/preferences/reset', category ? { category } : {});
    return response.data;
  },
  
  // Export preferences
  exportPreferences: async (format: 'json' | 'csv' = 'json') => {
    const response = await api.get(`/preferences/export?format=${format}`, {
      responseType: 'text'
    });
    return response.data;
  },
  
  // Import preferences
  importPreferences: async (preferences: any, merge: boolean = false) => {
    const response = await api.post('/preferences/import', { preferences, merge });
    return response.data;
  },
  
  // Get preference templates
  getTemplates: async (category?: string, publicOnly: boolean = true) => {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    params.append('public_only', publicOnly.toString());
    
    const response = await api.get(`/preferences/templates?${params}`);
    return response.data;
  },
  
  // Create preference template
  createTemplate: async (template: any) => {
    const response = await api.post('/preferences/templates', template);
    return response.data;
  },
  
  // Apply preference template
  applyTemplate: async (templateId: number) => {
    const response = await api.post(`/preferences/templates/${templateId}/apply`);
    return response.data;
  },
  
  // Get preference schemas
  getSchemas: async () => {
    const response = await api.get('/preferences/schema');
    return response.data;
  },
};

export default api;
