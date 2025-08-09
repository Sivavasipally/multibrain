/**
 * API Error Handler for RAG Chatbot PWA
 * 
 * This service provides specialized error handling for API calls and HTTP requests.
 * It integrates with the error boundary system and provides automatic error recovery,
 * retry mechanisms, and user-friendly error reporting for network-related issues.
 * 
 * Key Features:
 * - Automatic request/response interceptors
 * - Intelligent retry logic with exponential backoff
 * - Network connectivity monitoring
 * - Token refresh handling
 * - Request queuing during offline periods
 * - Error classification and user messaging
 * 
 * Usage:
 *   import { apiErrorHandler } from '../services/apiErrorHandler';
 *   
 *   // Wrap API client
 *   const client = apiErrorHandler.wrapApiClient(apiClient);
 *   
 *   // Handle individual requests
 *   const data = await apiErrorHandler.executeRequest(
 *     () => api.getData(),
 *     'Failed to load data'
 *   );
 * 
 * Author: RAG Chatbot Development Team
 * Version: 1.0.0
 */

import { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { errorService } from './errorService';

// API Error interfaces
export interface ApiErrorContext {
  endpoint?: string;
  method?: string;
  status?: number;
  requestId?: string;
  retry?: number;
}

export interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  retryCondition: (error: AxiosError) => boolean;
}

export interface OfflineRequest {
  id: string;
  config: AxiosRequestConfig;
  timestamp: number;
  context?: ApiErrorContext;
}

// Default retry configuration
const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000, // 1 second
  maxDelay: 10000, // 10 seconds
  retryCondition: (error: AxiosError) => {
    const status = error.response?.status;
    return !status || status >= 500 || status === 408 || status === 429;
  },
};

// Request queue for offline scenarios
class OfflineRequestQueue {
  private queue: OfflineRequest[] = [];
  private isProcessing = false;

  add(config: AxiosRequestConfig, context?: ApiErrorContext): string {
    const request: OfflineRequest = {
      id: `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      config,
      timestamp: Date.now(),
      context,
    };

    this.queue.push(request);
    return request.id;
  }

  async processQueue(apiClient: AxiosInstance): Promise<void> {
    if (this.isProcessing || this.queue.length === 0) return;

    this.isProcessing = true;

    try {
      while (this.queue.length > 0) {
        const request = this.queue.shift();
        if (!request) break;

        try {
          await apiClient(request.config);
          console.log(`✅ Offline request processed: ${request.id}`);
        } catch (error) {
          console.warn(`❌ Failed to process offline request: ${request.id}`, error);
          // Re-queue if still retryable
          if (this.shouldRetryRequest(error as AxiosError)) {
            this.queue.unshift(request);
            break; // Stop processing to avoid infinite loops
          }
        }
      }
    } finally {
      this.isProcessing = false;
    }
  }

  private shouldRetryRequest(error: AxiosError): boolean {
    return DEFAULT_RETRY_CONFIG.retryCondition(error);
  }

  getQueueSize(): number {
    return this.queue.length;
  }

  clear(): void {
    this.queue = [];
  }
}

/**
 * API Error Handler Class
 * 
 * Provides comprehensive error handling for HTTP requests with retry logic,
 * offline support, and integration with the error boundary system.
 */
class ApiErrorHandler {
  private offlineQueue = new OfflineRequestQueue();
  private isOnline = navigator.onLine;
  private tokenRefreshPromise: Promise<string> | null = null;

  constructor() {
    this.setupNetworkListeners();
  }

  /**
   * Wrap an Axios instance with error handling interceptors
   */
  wrapApiClient(client: AxiosInstance, config?: Partial<RetryConfig>): AxiosInstance {
    const retryConfig = { ...DEFAULT_RETRY_CONFIG, ...config };

    // Request interceptor
    client.interceptors.request.use(
      (requestConfig) => {
        // Add request ID for tracking
        requestConfig.metadata = {
          ...requestConfig.metadata,
          requestId: `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          startTime: Date.now(),
        };

        // Add breadcrumb
        errorService.addBreadcrumb('http', `${requestConfig.method?.toUpperCase()} ${requestConfig.url}`, {
          requestId: requestConfig.metadata.requestId,
          method: requestConfig.method,
          url: requestConfig.url,
        });

        return requestConfig;
      },
      (error) => {
        this.handleRequestError(error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    client.interceptors.response.use(
      (response) => {
        this.handleSuccessResponse(response);
        return response;
      },
      async (error: AxiosError) => {
        return this.handleResponseError(error, client, retryConfig);
      }
    );

    return client;
  }

  /**
   * Execute a request with error handling
   */
  async executeRequest<T>(
    requestFn: () => Promise<T>,
    userMessage?: string,
    context?: ApiErrorContext
  ): Promise<T | null> {
    try {
      return await requestFn();
    } catch (error) {
      this.handleApiError(error as AxiosError, userMessage, context);
      return null;
    }
  }

  /**
   * Handle request errors
   */
  private handleRequestError(error: any): void {
    console.error('Request setup error:', error);
    
    errorService.reportError(error, {
      component: 'ApiErrorHandler',
      action: 'request_setup',
    }, 'medium');
  }

  /**
   * Handle successful responses
   */
  private handleSuccessResponse(response: AxiosResponse): void {
    const duration = Date.now() - (response.config.metadata?.startTime || Date.now());
    
    // Log successful requests in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`✅ ${response.config.method?.toUpperCase()} ${response.config.url} (${duration}ms)`);
    }

    // Add success breadcrumb
    errorService.addBreadcrumb('http', `Success: ${response.config.method?.toUpperCase()} ${response.config.url}`, {
      status: response.status,
      duration,
      requestId: response.config.metadata?.requestId,
    });

    // Process offline queue if we're back online
    if (this.isOnline && this.offlineQueue.getQueueSize() > 0) {
      // Note: We would need the client instance here, which could be passed via context
      // For now, we'll trigger queue processing when network comes back online
    }
  }

  /**
   * Handle response errors with retry logic
   */
  private async handleResponseError(
    error: AxiosError,
    client: AxiosInstance,
    retryConfig: RetryConfig
  ): Promise<AxiosResponse> {
    const config = error.config as AxiosRequestConfig & { _retry?: number };
    
    // Initialize retry count
    if (!config._retry) {
      config._retry = 0;
    }

    // Handle token refresh for 401 errors
    if (error.response?.status === 401) {
      try {
        const newToken = await this.handleTokenRefresh();
        if (newToken && config.headers) {
          config.headers.Authorization = `Bearer ${newToken}`;
          return client(config);
        }
      } catch (refreshError) {
        // Token refresh failed, redirect to login
        this.handleAuthenticationFailure();
        return Promise.reject(error);
      }
    }

    // Check if we should retry
    if (config._retry < retryConfig.maxRetries && retryConfig.retryCondition(error)) {
      config._retry++;
      
      // Calculate delay with exponential backoff
      const delay = Math.min(
        retryConfig.baseDelay * Math.pow(2, config._retry - 1),
        retryConfig.maxDelay
      );

      // Add jitter to prevent thundering herd
      const jitteredDelay = delay + Math.random() * 1000;

      console.warn(`⏳ Retrying request (${config._retry}/${retryConfig.maxRetries}) after ${jitteredDelay}ms`);

      // Add retry breadcrumb
      errorService.addBreadcrumb('http', `Retrying: ${config.method?.toUpperCase()} ${config.url}`, {
        attempt: config._retry,
        maxRetries: retryConfig.maxRetries,
        delay: jitteredDelay,
        error: error.message,
      });

      await this.delay(jitteredDelay);
      return client(config);
    }

    // Handle offline scenarios
    if (!this.isOnline && this.isQueueableRequest(config)) {
      const requestId = this.offlineQueue.add(config, {
        endpoint: config.url,
        method: config.method,
      });

      console.log(`📱 Request queued for offline processing: ${requestId}`);
      
      // Return a rejected promise with a specific offline error
      const offlineError = new Error('Request queued for offline processing');
      offlineError.name = 'OfflineError';
      return Promise.reject(offlineError);
    }

    // Final error handling
    this.handleApiError(error);
    return Promise.reject(error);
  }

  /**
   * Handle API errors with classification and reporting
   */
  private handleApiError(error: AxiosError, userMessage?: string, context?: ApiErrorContext): void {
    const status = error.response?.status;
    const method = error.config?.method?.toUpperCase();
    const url = error.config?.url;

    // Create error context
    const errorContext: ApiErrorContext = {
      endpoint: url,
      method,
      status,
      requestId: (error.config as any)?.metadata?.requestId,
      ...context,
    };

    // Classify error
    const errorType = this.classifyApiError(error);
    const severity = this.getErrorSeverity(error);

    // Report error
    errorService.reportError(error, {
      component: 'ApiClient',
      action: 'http_request',
      metadata: errorContext,
    }, severity);

    // Add error breadcrumb
    errorService.addBreadcrumb('error', `HTTP Error: ${method} ${url}`, {
      status,
      statusText: error.response?.statusText,
      message: error.message,
      requestId: errorContext.requestId,
    });

    // Log error details
    console.error(`🚨 API Error [${status}]: ${method} ${url}`, {
      error: error.message,
      response: error.response?.data,
      context: errorContext,
    });
  }

  /**
   * Classify API error type
   */
  private classifyApiError(error: AxiosError): string {
    const status = error.response?.status;

    if (!status || error.code === 'NETWORK_ERROR') return 'network';
    if (status === 401 || status === 403) return 'authentication';
    if (status >= 400 && status < 500) return 'client';
    if (status >= 500) return 'server';
    if (error.code === 'ECONNABORTED') return 'timeout';

    return 'unknown';
  }

  /**
   * Get error severity based on status and type
   */
  private getErrorSeverity(error: AxiosError): 'low' | 'medium' | 'high' | 'critical' {
    const status = error.response?.status;

    if (status === 500 || status === 502 || status === 503) return 'critical';
    if (status === 401 || status === 403) return 'high';
    if (status && status >= 400 && status < 500) return 'medium';
    if (!status || error.code === 'NETWORK_ERROR') return 'high';

    return 'medium';
  }

  /**
   * Handle token refresh for authentication errors
   */
  private async handleTokenRefresh(): Promise<string | null> {
    // Prevent multiple simultaneous token refresh attempts
    if (this.tokenRefreshPromise) {
      return this.tokenRefreshPromise;
    }

    this.tokenRefreshPromise = this.performTokenRefresh();

    try {
      const token = await this.tokenRefreshPromise;
      return token;
    } finally {
      this.tokenRefreshPromise = null;
    }
  }

  /**
   * Perform actual token refresh
   */
  private async performTokenRefresh(): Promise<string | null> {
    try {
      // Get refresh token from localStorage or secure storage
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      // Make refresh request (adjust endpoint as needed)
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refreshToken }),
      });

      if (!response.ok) {
        throw new Error(`Token refresh failed: ${response.status}`);
      }

      const data = await response.json();
      const newToken = data.accessToken;

      // Store new token
      localStorage.setItem('accessToken', newToken);
      if (data.refreshToken) {
        localStorage.setItem('refreshToken', data.refreshToken);
      }

      return newToken;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return null;
    }
  }

  /**
   * Handle authentication failure
   */
  private handleAuthenticationFailure(): void {
    console.warn('Authentication failed, redirecting to login');
    
    // Clear stored tokens
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');

    // Add breadcrumb
    errorService.addBreadcrumb('user', 'Authentication failed, redirecting to login');

    // Redirect to login (adjust path as needed)
    window.location.href = '/login';
  }

  /**
   * Check if a request should be queued for offline processing
   */
  private isQueueableRequest(config: AxiosRequestConfig): boolean {
    const method = config.method?.toLowerCase();
    
    // Only queue certain types of requests
    const queueableMethods = ['post', 'put', 'patch', 'delete'];
    if (!method || !queueableMethods.includes(method)) {
      return false;
    }

    // Don't queue auth requests or very large payloads
    if (config.url?.includes('/auth/') || config.url?.includes('/login')) {
      return false;
    }

    return true;
  }

  /**
   * Setup network connectivity listeners
   */
  private setupNetworkListeners(): void {
    window.addEventListener('online', () => {
      console.log('🌐 Network connectivity restored');
      this.isOnline = true;
      
      errorService.addBreadcrumb('info', 'Network connectivity restored');
      
      // Process offline queue
      // Note: Would need access to the client instance here
      // This could be improved by storing client references
    });

    window.addEventListener('offline', () => {
      console.log('📱 Network connectivity lost');
      this.isOnline = false;
      
      errorService.addBreadcrumb('info', 'Network connectivity lost');
    });
  }

  /**
   * Utility function for delays
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Get offline queue statistics
   */
  public getOfflineQueueStats(): { size: number; isOnline: boolean } {
    return {
      size: this.offlineQueue.getQueueSize(),
      isOnline: this.isOnline,
    };
  }

  /**
   * Clear offline queue
   */
  public clearOfflineQueue(): void {
    this.offlineQueue.clear();
  }
}

// Create singleton instance
export const apiErrorHandler = new ApiErrorHandler();

export default apiErrorHandler;