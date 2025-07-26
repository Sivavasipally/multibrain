/**
 * API Types for RAG Chatbot PWA
 */

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
  source_type: 'files' | 'repo' | 'database';
  status: 'pending' | 'processing' | 'ready' | 'error';
  progress: number;
  total_chunks: number;
  total_tokens: number;
  config: Record<string, any>;
  created_at: string;
  updated_at: string;
  error_message?: string;
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
  created_at: string;
  tokens_used?: number;
}

export interface Citation {
  context_name: string;
  source: string;
  score: number;
  content?: string;
}

export interface AuthResponse {
  access_token: string;
  user: User;
}

export interface ApiError {
  error: string;
  details?: string;
}

export interface UploadResponse {
  files: {
    filename: string;
    size: number;
    path: string;
  }[];
}

export interface SupportedExtensions {
  extensions: {
    documents: string[];
    code: string[];
    data: string[];
    archives: string[];
  };
  total_count: number;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
}
