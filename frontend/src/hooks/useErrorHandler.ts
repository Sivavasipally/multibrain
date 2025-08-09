/**
 * Error Handling Hook for RAG Chatbot PWA
 * 
 * This hook provides comprehensive error handling capabilities for React components,
 * including automatic error reporting, user-friendly error messages, and recovery
 * mechanisms. It integrates with the error boundary system and provides consistent
 * error handling patterns across the application.
 * 
 * Key Features:
 * - Automatic error logging and reporting
 * - User-friendly error message display
 * - API error handling with retry mechanisms
 * - Network error detection and handling
 * - Error context tracking and debugging
 * - Integration with snackbar notifications
 * 
 * Usage:
 *   const { handleError, handleApiError, withErrorHandler } = useErrorHandler();
 *   
 *   // Handle API errors
 *   try {
 *     await apiCall();
 *   } catch (error) {
 *     handleApiError(error, 'Failed to load data');
 *   }
 *   
 *   // Wrap async functions
 *   const safeApiCall = withErrorHandler(apiCall, 'Loading data failed');
 * 
 * Author: RAG Chatbot Development Team
 * Version: 1.0.0
 */

import { useCallback, useRef } from 'react';
import { useSnackbar } from '../contexts/SnackbarContext';

// Error types and interfaces
export interface ErrorContext {
  component?: string;
  action?: string;
  userId?: string;
  metadata?: Record<string, any>;
}

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: any;
}

export interface ErrorReport {
  message: string;
  stack?: string;
  url: string;
  userAgent: string;
  timestamp: string;
  context?: ErrorContext;
  errorType: 'api' | 'network' | 'runtime' | 'validation';
  severity: 'low' | 'medium' | 'high' | 'critical';
}

// Error classification patterns
const ERROR_PATTERNS = {
  network: [
    /network/i,
    /fetch/i,
    /connection/i,
    /timeout/i,
    /offline/i,
  ],
  authentication: [
    /unauthorized/i,
    /authentication/i,
    /token/i,
    /login/i,
  ],
  validation: [
    /validation/i,
    /required/i,
    /invalid/i,
    /format/i,
  ],
  permission: [
    /forbidden/i,
    /permission/i,
    /access denied/i,
  ],
  server: [
    /server error/i,
    /internal error/i,
    /service unavailable/i,
  ],
};

// User-friendly error messages
const ERROR_MESSAGES = {
  network: 'Network connection issue. Please check your internet connection and try again.',
  authentication: 'Authentication failed. Please log in again.',
  validation: 'Please check your input and try again.',
  permission: 'You don\'t have permission to perform this action.',
  server: 'Server error occurred. Please try again later.',
  default: 'An unexpected error occurred. Please try again.',
};

/**
 * Error Handler Hook
 * 
 * Provides comprehensive error handling capabilities with automatic
 * error classification, reporting, and user-friendly messaging.
 */
export function useErrorHandler(defaultContext?: ErrorContext) {
  const { showError, showWarning } = useSnackbar();
  const errorCountRef = useRef<Map<string, number>>(new Map());

  /**
   * Classify error type based on error message and properties
   */
  const classifyError = useCallback((error: any): string => {
    const message = error?.message?.toLowerCase() || '';
    const status = error?.response?.status || error?.status;

    // Check status codes first
    if (status >= 500) return 'server';
    if (status === 401 || status === 403) return 'authentication';
    if (status === 400) return 'validation';
    if (status === 429) return 'rate-limit';

    // Check error message patterns
    for (const [type, patterns] of Object.entries(ERROR_PATTERNS)) {
      if (patterns.some(pattern => pattern.test(message))) {
        return type;
      }
    }

    return 'unknown';
  }, []);

  /**
   * Determine error severity based on type and frequency
   */
  const getErrorSeverity = useCallback((errorType: string, message: string): 'low' | 'medium' | 'high' | 'critical' => {
    // Track error frequency
    const errorKey = `${errorType}:${message}`;
    const currentCount = errorCountRef.current.get(errorKey) || 0;
    errorCountRef.current.set(errorKey, currentCount + 1);

    // Critical errors
    if (['authentication', 'server'].includes(errorType)) {
      return 'critical';
    }

    // High severity for repeated errors
    if (currentCount > 3) {
      return 'high';
    }

    // Medium severity for network and permission errors
    if (['network', 'permission'].includes(errorType)) {
      return 'medium';
    }

    return 'low';
  }, []);

  /**
   * Get user-friendly error message based on error type
   */
  const getUserFriendlyMessage = useCallback((error: any, fallbackMessage?: string): string => {
    const errorType = classifyError(error);
    
    // Use specific error message if available and user-friendly
    if (error?.message && error.message.length < 200 && !error.message.includes('stack')) {
      return error.message;
    }

    // Use response message if available
    if (error?.response?.data?.message) {
      return error.response.data.message;
    }

    // Use error type specific message
    const typeMessage = ERROR_MESSAGES[errorType as keyof typeof ERROR_MESSAGES];
    if (typeMessage) {
      return typeMessage;
    }

    // Use fallback or default message
    return fallbackMessage || ERROR_MESSAGES.default;
  }, [classifyError]);

  /**
   * Report error to backend service
   */
  const reportError = useCallback(async (error: any, context?: ErrorContext) => {
    try {
      const errorReport: ErrorReport = {
        message: error.message || 'Unknown error',
        stack: error.stack,
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString(),
        context: { ...defaultContext, ...context },
        errorType: classifyError(error) as any,
        severity: getErrorSeverity(classifyError(error), error.message || ''),
      };

      // Only report medium+ severity errors to reduce noise
      if (['medium', 'high', 'critical'].includes(errorReport.severity)) {
        await fetch('/api/errors/report', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(errorReport),
        });
      }
    } catch (reportingError) {
      console.warn('Failed to report error:', reportingError);
      
      // Store in localStorage as fallback
      try {
        const storedErrors = JSON.parse(localStorage.getItem('pendingErrorReports') || '[]');
        storedErrors.push({
          error: error.message,
          context,
          timestamp: new Date().toISOString(),
        });
        
        // Keep only last 20 errors
        if (storedErrors.length > 20) {
          storedErrors.splice(0, storedErrors.length - 20);
        }
        
        localStorage.setItem('pendingErrorReports', JSON.stringify(storedErrors));
      } catch (storageError) {
        console.warn('Failed to store error in localStorage:', storageError);
      }
    }
  }, [defaultContext, classifyError, getErrorSeverity]);

  /**
   * Handle general errors with automatic classification and reporting
   */
  const handleError = useCallback((
    error: any,
    userMessage?: string,
    context?: ErrorContext,
    silent = false
  ) => {
    console.error('Error handled:', error, context);

    // Report error for monitoring
    reportError(error, context);

    // Show user notification unless silent
    if (!silent) {
      const message = getUserFriendlyMessage(error, userMessage);
      const severity = getErrorSeverity(classifyError(error), error.message || '');
      
      if (severity === 'critical') {
        showError(message);
      } else if (severity === 'medium' || severity === 'high') {
        showWarning(message);
      }
    }

    return {
      type: classifyError(error),
      severity: getErrorSeverity(classifyError(error), error.message || ''),
      message: getUserFriendlyMessage(error, userMessage),
    };
  }, [reportError, getUserFriendlyMessage, classifyError, getErrorSeverity, showError, showWarning]);

  /**
   * Handle API-specific errors with detailed context
   */
  const handleApiError = useCallback((
    error: any,
    userMessage?: string,
    apiContext?: string
  ) => {
    const context: ErrorContext = {
      ...defaultContext,
      action: apiContext,
      metadata: {
        status: error?.response?.status,
        statusText: error?.response?.statusText,
        url: error?.response?.config?.url,
        method: error?.response?.config?.method,
      },
    };

    return handleError(error, userMessage, context);
  }, [defaultContext, handleError]);

  /**
   * Wrap async functions with automatic error handling
   */
  const withErrorHandler = useCallback(<T extends any[], R>(
    fn: (...args: T) => Promise<R>,
    userMessage?: string,
    context?: ErrorContext
  ) => {
    return async (...args: T): Promise<R | null> => {
      try {
        return await fn(...args);
      } catch (error) {
        handleError(error, userMessage, context);
        return null;
      }
    };
  }, [handleError]);

  /**
   * Create an error handler for specific components
   */
  const createErrorHandler = useCallback((componentName: string) => {
    return {
      handleError: (error: any, userMessage?: string, action?: string) =>
        handleError(error, userMessage, { ...defaultContext, component: componentName, action }),
      
      handleApiError: (error: any, userMessage?: string, apiContext?: string) =>
        handleApiError(error, userMessage, `${componentName}.${apiContext}`),
      
      withErrorHandler: <T extends any[], R>(
        fn: (...args: T) => Promise<R>,
        userMessage?: string,
        action?: string
      ) => withErrorHandler(fn, userMessage, { ...defaultContext, component: componentName, action }),
    };
  }, [defaultContext, handleError, handleApiError, withErrorHandler]);

  /**
   * Validate input and throw user-friendly errors
   */
  const validateAndThrow = useCallback((
    condition: boolean,
    message: string,
    context?: ErrorContext
  ) => {
    if (!condition) {
      const error = new Error(message);
      error.name = 'ValidationError';
      handleError(error, message, context);
      throw error;
    }
  }, [handleError]);

  /**
   * Handle network connectivity errors
   */
  const handleNetworkError = useCallback((error: any) => {
    const isOffline = !navigator.onLine;
    const message = isOffline 
      ? 'You appear to be offline. Please check your internet connection.'
      : 'Network error occurred. Please try again.';
    
    return handleError(error, message, { action: 'network-request' });
  }, [handleError]);

  /**
   * Clear error count cache (useful for testing or reset scenarios)
   */
  const clearErrorCounts = useCallback(() => {
    errorCountRef.current.clear();
  }, []);

  return {
    handleError,
    handleApiError,
    withErrorHandler,
    createErrorHandler,
    validateAndThrow,
    handleNetworkError,
    clearErrorCounts,
    classifyError,
    getUserFriendlyMessage,
  };
}

export default useErrorHandler;