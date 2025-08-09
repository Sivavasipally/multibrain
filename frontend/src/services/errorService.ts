/**
 * Error Reporting Service for RAG Chatbot PWA
 * 
 * This service provides centralized error reporting and monitoring capabilities
 * for the frontend application. It handles error collection, batching, and
 * transmission to backend services for analysis and debugging.
 * 
 * Key Features:
 * - Automatic error collection and batching
 * - Offline error storage with sync on reconnect
 * - Error deduplication and rate limiting
 * - User session and context tracking
 * - Privacy-aware error sanitization
 * - Performance impact monitoring
 * 
 * Usage:
 *   import { errorService } from '../services/errorService';
 *   
 *   // Report an error
 *   errorService.reportError(error, { component: 'ChatPage', action: 'sendMessage' });
 *   
 *   // Start monitoring
 *   errorService.initialize();
 * 
 * Author: RAG Chatbot Development Team
 * Version: 1.0.0
 */

// Error reporting interfaces
export interface ErrorContext {
  component?: string;
  action?: string;
  userId?: string;
  sessionId?: string;
  metadata?: Record<string, any>;
}

export interface ErrorReport {
  id: string;
  message: string;
  stack?: string;
  url: string;
  userAgent: string;
  timestamp: string;
  context?: ErrorContext;
  errorType: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  fingerprint: string;
  breadcrumbs: Breadcrumb[];
  userFeedback?: string;
}

export interface Breadcrumb {
  timestamp: string;
  type: 'navigation' | 'user' | 'http' | 'error' | 'info';
  message: string;
  data?: Record<string, any>;
}

export interface ErrorServiceConfig {
  maxBreadcrumbs: number;
  maxBatchSize: number;
  batchTimeout: number;
  maxRetries: number;
  enableAutoReporting: boolean;
  enableBreadcrumbs: boolean;
  apiEndpoint: string;
  rateLimitWindow: number;
  maxErrorsPerWindow: number;
}

/**
 * Error Reporting Service Class
 * 
 * Manages error collection, processing, and reporting to backend services
 * with offline support and performance optimization.
 */
class ErrorService {
  private config: ErrorServiceConfig;
  private breadcrumbs: Breadcrumb[] = [];
  private errorQueue: ErrorReport[] = [];
  private rateLimitMap: Map<string, number> = new Map();
  private batchTimer: NodeJS.Timeout | null = null;
  private isOnline = navigator.onLine;
  private sessionId: string;

  constructor(config: Partial<ErrorServiceConfig> = {}) {
    this.config = {
      maxBreadcrumbs: 50,
      maxBatchSize: 10,
      batchTimeout: 5000,
      maxRetries: 3,
      enableAutoReporting: true,
      enableBreadcrumbs: true,
      apiEndpoint: '/api/errors/report',
      rateLimitWindow: 60000, // 1 minute
      maxErrorsPerWindow: 10,
      ...config,
    };

    this.sessionId = this.generateSessionId();
    this.setupEventListeners();
  }

  /**
   * Initialize the error service
   */
  public initialize(): void {
    if (this.config.enableAutoReporting) {
      this.setupGlobalErrorHandlers();
    }

    if (this.config.enableBreadcrumbs) {
      this.setupBreadcrumbTracking();
    }

    // Process any stored offline errors
    this.processOfflineErrors();
  }

  /**
   * Report an error with context
   */
  public reportError(
    error: Error | string,
    context: ErrorContext = {},
    severity: ErrorReport['severity'] = 'medium'
  ): string {
    const errorReport = this.createErrorReport(error, context, severity);
    
    // Check rate limiting
    if (this.isRateLimited(errorReport.fingerprint)) {
      console.warn('Error reporting rate limited for:', errorReport.fingerprint);
      return errorReport.id;
    }

    // Add to queue
    this.errorQueue.push(errorReport);
    
    // Schedule batch processing
    this.scheduleBatch();
    
    // Log in development
    if (process.env.NODE_ENV === 'development') {
      console.group('🚨 Error Reported');
      console.error('Error:', error);
      console.log('Context:', context);
      console.log('Report:', errorReport);
      console.groupEnd();
    }

    return errorReport.id;
  }

  /**
   * Add a breadcrumb for tracking user actions
   */
  public addBreadcrumb(
    type: Breadcrumb['type'],
    message: string,
    data?: Record<string, any>
  ): void {
    if (!this.config.enableBreadcrumbs) return;

    const breadcrumb: Breadcrumb = {
      timestamp: new Date().toISOString(),
      type,
      message,
      data: this.sanitizeData(data),
    };

    this.breadcrumbs.push(breadcrumb);

    // Maintain breadcrumb limit
    if (this.breadcrumbs.length > this.config.maxBreadcrumbs) {
      this.breadcrumbs = this.breadcrumbs.slice(-this.config.maxBreadcrumbs);
    }
  }

  /**
   * Get current error statistics
   */
  public getStats(): {
    queueSize: number;
    breadcrumbsCount: number;
    sessionId: string;
    isOnline: boolean;
  } {
    return {
      queueSize: this.errorQueue.length,
      breadcrumbsCount: this.breadcrumbs.length,
      sessionId: this.sessionId,
      isOnline: this.isOnline,
    };
  }

  /**
   * Clear error queue and breadcrumbs
   */
  public clear(): void {
    this.errorQueue = [];
    this.breadcrumbs = [];
    this.rateLimitMap.clear();
  }

  /**
   * Create an error report from error and context
   */
  private createErrorReport(
    error: Error | string,
    context: ErrorContext,
    severity: ErrorReport['severity']
  ): ErrorReport {
    const errorObj = typeof error === 'string' ? new Error(error) : error;
    const message = errorObj.message || 'Unknown error';
    const stack = errorObj.stack;

    // Create fingerprint for deduplication
    const fingerprint = this.createFingerprint(message, stack, context);

    return {
      id: this.generateErrorId(),
      message: this.sanitizeMessage(message),
      stack: this.sanitizeStack(stack),
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
      context: {
        ...context,
        sessionId: this.sessionId,
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight,
        },
        connection: this.getConnectionInfo(),
      },
      errorType: this.classifyError(errorObj),
      severity,
      fingerprint,
      breadcrumbs: [...this.breadcrumbs], // Copy current breadcrumbs
    };
  }

  /**
   * Create a unique fingerprint for error deduplication
   */
  private createFingerprint(
    message: string,
    stack?: string,
    context?: ErrorContext
  ): string {
    const stackLines = stack?.split('\n').slice(0, 3).join('\n') || '';
    const contextKey = context?.component || context?.action || 'unknown';
    const content = `${message}:${stackLines}:${contextKey}`;
    
    // Simple hash function
    let hash = 0;
    for (let i = 0; i < content.length; i++) {
      const char = content.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    
    return Math.abs(hash).toString(36);
  }

  /**
   * Check if error reporting is rate limited
   */
  private isRateLimited(fingerprint: string): boolean {
    const now = Date.now();
    const windowStart = now - this.config.rateLimitWindow;
    
    // Clean old entries
    for (const [fp, timestamp] of this.rateLimitMap.entries()) {
      if (timestamp < windowStart) {
        this.rateLimitMap.delete(fp);
      }
    }

    // Check current fingerprint
    const entries = Array.from(this.rateLimitMap.entries())
      .filter(([fp]) => fp === fingerprint)
      .length;

    if (entries >= this.config.maxErrorsPerWindow) {
      return true;
    }

    // Record this error
    this.rateLimitMap.set(`${fingerprint}:${now}`, now);
    return false;
  }

  /**
   * Schedule batch processing of errors
   */
  private scheduleBatch(): void {
    if (this.batchTimer) return;

    this.batchTimer = setTimeout(() => {
      this.processBatch();
      this.batchTimer = null;
    }, this.config.batchTimeout);

    // Process immediately if batch is full
    if (this.errorQueue.length >= this.config.maxBatchSize) {
      if (this.batchTimer) {
        clearTimeout(this.batchTimer);
        this.batchTimer = null;
      }
      this.processBatch();
    }
  }

  /**
   * Process batch of errors
   */
  private async processBatch(): Promise<void> {
    if (this.errorQueue.length === 0) return;

    const batch = this.errorQueue.splice(0, this.config.maxBatchSize);
    
    if (!this.isOnline) {
      this.storeOfflineErrors(batch);
      return;
    }

    try {
      await this.sendErrorBatch(batch);
    } catch (error) {
      console.warn('Failed to send error batch:', error);
      this.storeOfflineErrors(batch);
    }
  }

  /**
   * Send error batch to server
   */
  private async sendErrorBatch(errors: ErrorReport[]): Promise<void> {
    const response = await fetch(this.config.apiEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ errors }),
    });

    if (!response.ok) {
      throw new Error(`Error reporting failed: ${response.status} ${response.statusText}`);
    }
  }

  /**
   * Store errors offline for later transmission
   */
  private storeOfflineErrors(errors: ErrorReport[]): void {
    try {
      const stored = JSON.parse(localStorage.getItem('offlineErrors') || '[]');
      stored.push(...errors);
      
      // Keep only last 100 errors to prevent storage bloat
      if (stored.length > 100) {
        stored.splice(0, stored.length - 100);
      }
      
      localStorage.setItem('offlineErrors', JSON.stringify(stored));
    } catch (error) {
      console.warn('Failed to store offline errors:', error);
    }
  }

  /**
   * Process stored offline errors
   */
  private async processOfflineErrors(): Promise<void> {
    try {
      const stored = JSON.parse(localStorage.getItem('offlineErrors') || '[]');
      if (stored.length === 0) return;

      if (this.isOnline) {
        await this.sendErrorBatch(stored);
        localStorage.removeItem('offlineErrors');
      }
    } catch (error) {
      console.warn('Failed to process offline errors:', error);
    }
  }

  /**
   * Set up global error handlers
   */
  private setupGlobalErrorHandlers(): void {
    // Handle uncaught JavaScript errors
    window.addEventListener('error', (event) => {
      this.reportError(event.error || event.message, {
        component: 'global',
        action: 'uncaught_error',
        metadata: {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
        },
      }, 'high');
    });

    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.reportError(event.reason, {
        component: 'global',
        action: 'unhandled_rejection',
      }, 'high');
    });
  }

  /**
   * Set up breadcrumb tracking
   */
  private setupBreadcrumbTracking(): void {
    // Track navigation
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;

    history.pushState = (...args) => {
      this.addBreadcrumb('navigation', `Navigation to ${args[2]}`, { state: args[0] });
      return originalPushState.apply(history, args);
    };

    history.replaceState = (...args) => {
      this.addBreadcrumb('navigation', `Replace state ${args[2]}`, { state: args[0] });
      return originalReplaceState.apply(history, args);
    };

    // Track clicks on important elements
    document.addEventListener('click', (event) => {
      const target = event.target as HTMLElement;
      if (target.tagName === 'BUTTON' || target.closest('button')) {
        const button = target.closest('button') || target;
        this.addBreadcrumb('user', 'Button clicked', {
          text: button.textContent?.trim() || 'Unknown button',
          id: button.id,
          className: button.className,
        });
      }
    });
  }

  /**
   * Set up network connectivity listeners
   */
  private setupEventListeners(): void {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.processOfflineErrors();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
    });
  }

  /**
   * Classify error type
   */
  private classifyError(error: Error): string {
    const message = error.message.toLowerCase();
    const name = error.name.toLowerCase();

    if (name.includes('network') || message.includes('fetch')) return 'network';
    if (name.includes('syntax')) return 'syntax';
    if (name.includes('reference')) return 'reference';
    if (name.includes('type')) return 'type';
    if (message.includes('permission')) return 'permission';
    if (message.includes('quota')) return 'storage';

    return 'runtime';
  }

  /**
   * Sanitize error message to remove sensitive data
   */
  private sanitizeMessage(message: string): string {
    // Remove potential sensitive information
    return message
      .replace(/token[=:]\s*[^\s]+/gi, 'token=***')
      .replace(/password[=:]\s*[^\s]+/gi, 'password=***')
      .replace(/key[=:]\s*[^\s]+/gi, 'key=***')
      .replace(/bearer\s+[^\s]+/gi, 'bearer ***');
  }

  /**
   * Sanitize stack trace
   */
  private sanitizeStack(stack?: string): string | undefined {
    if (!stack) return undefined;

    return stack
      .replace(/token[=:]\s*[^\s]+/gi, 'token=***')
      .replace(/password[=:]\s*[^\s]+/gi, 'password=***');
  }

  /**
   * Sanitize data object
   */
  private sanitizeData(data?: Record<string, any>): Record<string, any> | undefined {
    if (!data) return undefined;

    const sanitized: Record<string, any> = {};
    
    for (const [key, value] of Object.entries(data)) {
      if (typeof value === 'string' && (
        key.toLowerCase().includes('token') ||
        key.toLowerCase().includes('password') ||
        key.toLowerCase().includes('key')
      )) {
        sanitized[key] = '***';
      } else if (typeof value === 'object' && value !== null) {
        sanitized[key] = this.sanitizeData(value);
      } else {
        sanitized[key] = value;
      }
    }

    return sanitized;
  }

  /**
   * Get connection information
   */
  private getConnectionInfo(): Record<string, any> {
    const connection = (navigator as any).connection;
    if (!connection) return {};

    return {
      effectiveType: connection.effectiveType,
      downlink: connection.downlink,
      rtt: connection.rtt,
    };
  }

  /**
   * Generate unique session ID
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Generate unique error ID
   */
  private generateErrorId(): string {
    return `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Create singleton instance
export const errorService = new ErrorService();

export default errorService;