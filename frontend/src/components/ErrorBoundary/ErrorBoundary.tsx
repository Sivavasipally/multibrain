/**
 * Comprehensive Error Boundary System for RAG Chatbot PWA
 * 
 * This module provides robust error boundaries to catch JavaScript errors anywhere
 * in the component tree, log errors, and display fallback UI components. The system
 * includes different types of error boundaries for various use cases and provides
 * detailed error reporting and recovery mechanisms.
 * 
 * Key Features:
 * - Global error boundary for application-wide error catching
 * - Page-specific error boundaries for route-level isolation
 * - Component-specific error boundaries for granular error handling
 * - Error logging and reporting to backend services
 * - User-friendly error messages and recovery options
 * - Development vs production error display modes
 * 
 * Usage:
 *   <ErrorBoundary>
 *     <ComponentThatMightThrow />
 *   </ErrorBoundary>
 * 
 * Author: RAG Chatbot Development Team
 * Version: 1.0.0
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Container,
  Alert,
  AlertTitle,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Stack,
  Divider,
} from '@mui/material';
import {
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Home as HomeIcon,
  BugReport as BugReportIcon,
  ExpandMore as ExpandMoreIcon,
  ContentCopy as CopyIcon,
} from '@mui/icons-material';

// Error boundary props interface
interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  level?: 'global' | 'page' | 'component';
  context?: string;
  showErrorDetails?: boolean;
}

// Error boundary state interface
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
  retryCount: number;
}

// Error details interface for reporting
interface ErrorDetails {
  message: string;
  stack?: string;
  componentStack: string;
  url: string;
  userAgent: string;
  timestamp: string;
  userId?: string;
  context?: string;
  level: string;
  errorId: string;
}

/**
 * Main Error Boundary Component
 * 
 * Catches JavaScript errors in child components and displays appropriate
 * fallback UI while logging error details for debugging and monitoring.
 */
class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private retryTimeoutId: NodeJS.Timeout | null = null;

  constructor(props: ErrorBoundaryProps) {
    super(props);
    
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Update state to show fallback UI
    return {
      hasError: true,
      error,
      errorId: generateErrorId(),
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Capture error details
    this.setState({
      error,
      errorInfo,
    });

    // Log error details
    this.logError(error, errorInfo);

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  componentWillUnmount() {
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId);
    }
  }

  private logError = async (error: Error, errorInfo: ErrorInfo) => {
    const errorDetails: ErrorDetails = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
      context: this.props.context,
      level: this.props.level || 'component',
      errorId: this.state.errorId || generateErrorId(),
    };

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.group('🚨 Error Boundary Caught Error');
      console.error('Error:', error);
      console.error('Error Info:', errorInfo);
      console.error('Error Details:', errorDetails);
      console.groupEnd();
    }

    // Log to external service (if available)
    try {
      await this.reportError(errorDetails);
    } catch (reportError) {
      console.error('Failed to report error:', reportError);
    }
  };

  private reportError = async (errorDetails: ErrorDetails) => {
    try {
      // Send error to backend logging service
      const response = await fetch('/api/errors/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorDetails),
      });

      if (!response.ok) {
        throw new Error(`Error reporting failed: ${response.status}`);
      }
    } catch (error) {
      // Fallback to local storage for offline scenarios
      const errors = JSON.parse(localStorage.getItem('errorReports') || '[]');
      errors.push(errorDetails);
      
      // Keep only last 50 errors to prevent storage bloat
      if (errors.length > 50) {
        errors.splice(0, errors.length - 50);
      }
      
      localStorage.setItem('errorReports', JSON.stringify(errors));
    }
  };

  private handleRetry = () => {
    const { retryCount } = this.state;
    const maxRetries = 3;

    if (retryCount < maxRetries) {
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null,
        retryCount: retryCount + 1,
      });

      // Auto-retry after a delay to prevent infinite loops
      this.retryTimeoutId = setTimeout(() => {
        if (this.state.hasError) {
          this.setState({ retryCount: retryCount + 1 });
        }
      }, 1000 * Math.pow(2, retryCount)); // Exponential backoff
    }
  };

  private handleGoHome = () => {
    window.location.href = '/dashboard';
  };

  private handleReload = () => {
    window.location.reload();
  };

  private copyErrorToClipboard = async () => {
    const { error, errorInfo, errorId } = this.state;
    const errorText = `Error ID: ${errorId}\nMessage: ${error?.message}\nStack: ${error?.stack}\nComponent Stack: ${errorInfo?.componentStack}`;
    
    try {
      await navigator.clipboard.writeText(errorText);
    } catch (err) {
      console.error('Failed to copy error to clipboard:', err);
    }
  };

  render() {
    const { hasError, error, errorInfo, errorId, retryCount } = this.state;
    const { children, fallback, level = 'component', showErrorDetails = process.env.NODE_ENV === 'development' } = this.props;

    if (hasError) {
      // Use custom fallback if provided
      if (fallback) {
        return fallback;
      }

      // Render appropriate error UI based on level
      return this.renderErrorUI(level, error, errorInfo, errorId, retryCount, showErrorDetails);
    }

    return children;
  }

  private renderErrorUI(
    level: string,
    error: Error | null,
    errorInfo: ErrorInfo | null,
    errorId: string | null,
    retryCount: number,
    showErrorDetails: boolean
  ) {
    const maxRetries = 3;
    const canRetry = retryCount < maxRetries;

    // Global application error
    if (level === 'global') {
      return (
        <Container maxWidth="md" sx={{ mt: 4 }}>
          <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
            <ErrorIcon sx={{ fontSize: 64, color: 'error.main', mb: 2 }} />
            <Typography variant="h4" gutterBottom>
              Application Error
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              We're sorry, but something went wrong with the application.
              Our team has been notified and is working on a fix.
            </Typography>
            
            <Stack direction="row" spacing={2} justifyContent="center" sx={{ mt: 3 }}>
              <Button
                variant="contained"
                startIcon={<RefreshIcon />}
                onClick={this.handleReload}
              >
                Reload Application
              </Button>
              <Button
                variant="outlined"
                startIcon={<HomeIcon />}
                onClick={this.handleGoHome}
              >
                Go to Dashboard
              </Button>
            </Stack>

            {errorId && (
              <Box sx={{ mt: 3 }}>
                <Chip
                  label={`Error ID: ${errorId}`}
                  variant="outlined"
                  size="small"
                  icon={<BugReportIcon />}
                />
              </Box>
            )}

            {showErrorDetails && error && (
              <Box sx={{ mt: 3, textAlign: 'left' }}>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle2">Technical Details</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Stack spacing={2}>
                      <Alert severity="error">
                        <AlertTitle>Error Message</AlertTitle>
                        {error.message}
                      </Alert>
                      
                      {error.stack && (
                        <Box>
                          <Typography variant="subtitle2" gutterBottom>
                            Stack Trace:
                          </Typography>
                          <Paper
                            variant="outlined"
                            sx={{ p: 2, backgroundColor: 'grey.50', fontFamily: 'monospace', fontSize: '0.75rem' }}
                          >
                            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                              {error.stack}
                            </pre>
                          </Paper>
                        </Box>
                      )}

                      <Button
                        size="small"
                        startIcon={<CopyIcon />}
                        onClick={this.copyErrorToClipboard}
                      >
                        Copy Error Details
                      </Button>
                    </Stack>
                  </AccordionDetails>
                </Accordion>
              </Box>
            )}
          </Paper>
        </Container>
      );
    }

    // Page-level error
    if (level === 'page') {
      return (
        <Container maxWidth="sm" sx={{ mt: 4 }}>
          <Alert severity="error" sx={{ mb: 3 }}>
            <AlertTitle>Page Error</AlertTitle>
            This page encountered an error and couldn't be displayed properly.
          </Alert>
          
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h6" gutterBottom>
              Something went wrong
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              {error?.message || 'An unexpected error occurred on this page.'}
            </Typography>

            <Stack direction="row" spacing={2} justifyContent="center">
              {canRetry && (
                <Button
                  variant="contained"
                  startIcon={<RefreshIcon />}
                  onClick={this.handleRetry}
                >
                  Try Again ({maxRetries - retryCount} left)
                </Button>
              )}
              <Button
                variant="outlined"
                startIcon={<HomeIcon />}
                onClick={this.handleGoHome}
              >
                Go Home
              </Button>
            </Stack>

            {showErrorDetails && errorId && (
              <Box sx={{ mt: 2 }}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="caption" color="text.secondary">
                  Error ID: {errorId}
                </Typography>
              </Box>
            )}
          </Paper>
        </Container>
      );
    }

    // Component-level error
    return (
      <Alert severity="error" sx={{ m: 1 }}>
        <AlertTitle>Component Error</AlertTitle>
        {error?.message || 'This component encountered an error.'}
        {canRetry && (
          <Button
            size="small"
            startIcon={<RefreshIcon />}
            onClick={this.handleRetry}
            sx={{ mt: 1 }}
          >
            Retry
          </Button>
        )}
      </Alert>
    );
  }
}

/**
 * Generate unique error ID for tracking
 */
function generateErrorId(): string {
  return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Global Error Boundary for application-wide error catching
 */
export const GlobalErrorBoundary: React.FC<{ children: ReactNode }> = ({ children }) => (
  <ErrorBoundary level="global" context="global">
    {children}
  </ErrorBoundary>
);

/**
 * Page Error Boundary for route-level error isolation
 */
export const PageErrorBoundary: React.FC<{ children: ReactNode; pageName: string }> = ({ 
  children, 
  pageName 
}) => (
  <ErrorBoundary level="page" context={`page:${pageName}`}>
    {children}
  </ErrorBoundary>
);

/**
 * Component Error Boundary for granular error handling
 */
export const ComponentErrorBoundary: React.FC<{ 
  children: ReactNode; 
  componentName: string;
  fallback?: ReactNode;
}> = ({ children, componentName, fallback }) => (
  <ErrorBoundary 
    level="component" 
    context={`component:${componentName}`}
    fallback={fallback}
  >
    {children}
  </ErrorBoundary>
);

export default ErrorBoundary;