/**
 * TypeScript API Client for RAG Chatbot PWA
 */

export interface Context {
  id: number;
  name: string;
  source_type: string;
  status: string;
  total_chunks?: number;
  total_tokens?: number;
  created_at?: string;
  updated_at?: string;
  description?: string;
}

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  session_id: number;
  created_at?: string;
  context_ids?: number[];
  citations?: Array<{
    context_id: number;
    context_name: string;
    source: string;
    score: number;
  }>;
}

export interface ChatSession {
  id: number;
  title?: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
}

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
}

export interface StreamingResponse {
  stream_id: string;
  message: string;
}

export class RagChatbotClient {
  private baseUrl: string;
  private token?: string;
  private headers: Record<string, string>;

  constructor(baseUrl: string, token?: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.token = token;
    this.headers = {
      'Content-Type': 'application/json',
    };

    if (token) {
      this.headers['Authorization'] = `Bearer ${token}`;
    }
  }

  private async request<T = any>(
    method: string,
    endpoint: string,
    data?: any,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      method,
      headers: { ...this.headers, ...options?.headers },
      ...options,
    };

    if (data && method !== 'GET') {
      if (data instanceof FormData) {
        // Remove Content-Type for FormData (browser will set it)
        delete config.headers!['Content-Type'];
        config.body = data;
      } else {
        config.body = JSON.stringify(data);
      }
    }

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return response.text() as any;
    } catch (error) {
      throw new Error(`API request failed: ${error instanceof Error ? error.message : error}`);
    }
  }

  // Authentication methods
  async authenticate(username: string, password: string): Promise<string> {
    const response = await this.request<{ access_token: string }>('POST', '/auth/login', {
      username,
      password,
    });

    const token = response.access_token;
    if (token) {
      this.token = token;
      this.headers['Authorization'] = `Bearer ${token}`;
    }

    return token;
  }

  async register(username: string, email: string, password: string): Promise<ApiResponse> {
    return this.request('POST', '/auth/register', {
      username,
      email,
      password,
    });
  }

  async getUserProfile(): Promise<any> {
    return this.request('GET', '/auth/profile');
  }

  // Context methods
  async createContext(data: {
    name: string;
    source_type: string;
    description?: string;
    [key: string]: any;
  }): Promise<Context> {
    return this.request('POST', '/contexts', data);
  }

  async getContexts(): Promise<Context[]> {
    return this.request('GET', '/contexts');
  }

  async getContext(contextId: number): Promise<Context> {
    return this.request('GET', `/contexts/${contextId}`);
  }

  async updateContext(contextId: number, data: Partial<Context>): Promise<Context> {
    return this.request('PUT', `/contexts/${contextId}`, data);
  }

  async deleteContext(contextId: number): Promise<ApiResponse> {
    return this.request('DELETE', `/contexts/${contextId}`);
  }

  async uploadFiles(contextId: number, files: File[]): Promise<ApiResponse> {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    return this.request('POST', `/upload/${contextId}`, formData);
  }

  // Chat methods
  async createChatSession(title?: string): Promise<ChatSession> {
    const data = title ? { title } : {};
    return this.request('POST', '/chat/sessions', data);
  }

  async getChatSessions(): Promise<ChatSession[]> {
    return this.request('GET', '/chat/sessions');
  }

  async getChatSession(sessionId: number): Promise<ChatSession> {
    return this.request('GET', `/chat/sessions/${sessionId}`);
  }

  async getChatMessages(sessionId: number): Promise<ChatMessage[]> {
    return this.request('GET', `/chat/sessions/${sessionId}/messages`);
  }

  async sendMessage(data: {
    session_id: number;
    message: string;
    context_ids?: number[];
    stream?: boolean;
  }): Promise<ChatMessage | StreamingResponse> {
    return this.request('POST', '/chat/query', data);
  }

  async sendStreamingMessage(data: {
    session_id: number;
    message: string;
    context_ids?: number[];
  }): Promise<ReadableStream<Uint8Array>> {
    const url = `${this.baseUrl}/chat/query`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ ...data, stream: true }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.body!;
  }

  // Utility methods
  async healthCheck(): Promise<{ status: string; timestamp: string; version: string }> {
    return this.request('GET', '/health');
  }

  // Helper method for streaming responses
  async *streamResponse(stream: ReadableStream<Uint8Array>): AsyncGenerator<string, void, unknown> {
    const reader = stream.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') return;
            
            try {
              const parsed = JSON.parse(data);
              if (parsed.content) {
                yield parsed.content;
              }
            } catch (e) {
              // Skip invalid JSON
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  // Set authentication token
  setToken(token: string): void {
    this.token = token;
    this.headers['Authorization'] = `Bearer ${token}`;
  }

  // Remove authentication
  logout(): void {
    this.token = undefined;
    delete this.headers['Authorization'];
  }
}

// Example usage
export const createClient = (baseUrl: string = 'http://localhost:5000/api', token?: string) => {
  return new RagChatbotClient(baseUrl, token);
};

// React hook for the client (if using React)
export const useRagChatbotClient = (baseUrl?: string, token?: string) => {
  const client = new RagChatbotClient(
    baseUrl || process.env.REACT_APP_API_URL || 'http://localhost:5000/api',
    token
  );
  
  return client;
};

export default RagChatbotClient;
