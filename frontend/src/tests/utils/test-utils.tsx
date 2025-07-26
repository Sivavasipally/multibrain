/**
 * Custom render utilities for testing React components
 */

import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { AuthProvider } from '../../contexts/AuthContext';
import { ThemeProvider as CustomThemeProvider } from '../../contexts/ThemeContext';
import { SnackbarProvider } from '../../contexts/SnackbarContext';

// Mock theme
const mockTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

// All providers wrapper
const AllTheProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <BrowserRouter>
      <CustomThemeProvider>
        <ThemeProvider theme={mockTheme}>
          <CssBaseline />
          <SnackbarProvider>
            <AuthProvider>
              {children}
            </AuthProvider>
          </SnackbarProvider>
        </ThemeProvider>
      </CustomThemeProvider>
    </BrowserRouter>
  );
};

// Custom render function
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

// Re-export everything
export * from '@testing-library/react';
export { customRender as render };

// Helper functions for testing
export const createMockUser = () => ({
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  created_at: '2023-01-01T00:00:00Z',
  is_active: true,
});

export const createMockContext = (overrides = {}) => ({
  id: 1,
  name: 'Test Context',
  description: 'A test context',
  source_type: 'files',
  status: 'ready',
  progress: 100,
  total_chunks: 50,
  total_tokens: 1000,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
  config: {},
  ...overrides,
});

export const createMockChatSession = (overrides = {}) => ({
  id: 1,
  title: 'Test Chat Session',
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
  message_count: 0,
  ...overrides,
});

export const createMockMessage = (overrides = {}) => ({
  id: 1,
  role: 'user' as const,
  content: 'Test message',
  context_ids: [1],
  citations: [],
  created_at: '2023-01-01T00:00:00Z',
  ...overrides,
});

// Mock localStorage helpers
export const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

// Mock API response helpers
export const createMockApiResponse = <T>(data: T, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: () => Promise.resolve(data),
  text: () => Promise.resolve(JSON.stringify(data)),
});

// Wait for async operations
export const waitForAsync = () => new Promise(resolve => setTimeout(resolve, 0));

// Mock file for upload testing
export const createMockFile = (name = 'test.txt', content = 'test content', type = 'text/plain') => {
  const file = new File([content], name, { type });
  return file;
};

// Mock drag and drop events
export const createMockDragEvent = (files: File[]) => {
  const event = new Event('drop', { bubbles: true });
  Object.defineProperty(event, 'dataTransfer', {
    value: {
      files,
      items: files.map(file => ({
        kind: 'file',
        type: file.type,
        getAsFile: () => file,
      })),
      types: ['Files'],
    },
  });
  return event;
};

// Mock intersection observer for testing
export const mockIntersectionObserver = () => {
  const mockIntersectionObserver = jest.fn();
  mockIntersectionObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  });
  window.IntersectionObserver = mockIntersectionObserver;
};

// Mock resize observer for testing
export const mockResizeObserver = () => {
  const mockResizeObserver = jest.fn();
  mockResizeObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  });
  window.ResizeObserver = mockResizeObserver;
};

// Mock match media for responsive testing
export const mockMatchMedia = (matches = false) => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
      matches,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
};

// Mock service worker for PWA testing
export const mockServiceWorker = () => {
  Object.defineProperty(navigator, 'serviceWorker', {
    value: {
      register: jest.fn(() => Promise.resolve({
        installing: null,
        waiting: null,
        active: null,
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
      })),
      ready: Promise.resolve({
        installing: null,
        waiting: null,
        active: null,
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        unregister: jest.fn(() => Promise.resolve(true)),
      }),
      controller: null,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    },
    writable: true,
  });
};

// Mock notifications for PWA testing
export const mockNotifications = (permission: NotificationPermission = 'default') => {
  Object.defineProperty(Notification, 'permission', {
    value: permission,
    writable: true,
  });

  Object.defineProperty(Notification, 'requestPermission', {
    value: jest.fn(() => Promise.resolve(permission)),
    writable: true,
  });

  global.Notification = jest.fn().mockImplementation((title, options) => ({
    title,
    ...options,
    close: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
  })) as any;
};

// Mock clipboard API
export const mockClipboard = () => {
  Object.defineProperty(navigator, 'clipboard', {
    value: {
      writeText: jest.fn(() => Promise.resolve()),
      readText: jest.fn(() => Promise.resolve('mock clipboard content')),
    },
    writable: true,
  });
};

// Mock geolocation API
export const mockGeolocation = () => {
  Object.defineProperty(navigator, 'geolocation', {
    value: {
      getCurrentPosition: jest.fn((success) => 
        success({
          coords: {
            latitude: 40.7128,
            longitude: -74.0060,
            accuracy: 10,
          },
        })
      ),
      watchPosition: jest.fn(),
      clearWatch: jest.fn(),
    },
    writable: true,
  });
};

// Test data generators
export const generateTestContexts = (count = 3) => {
  return Array.from({ length: count }, (_, index) => 
    createMockContext({
      id: index + 1,
      name: `Test Context ${index + 1}`,
      source_type: ['files', 'repo', 'database'][index % 3],
      status: ['ready', 'processing', 'error'][index % 3],
    })
  );
};

export const generateTestMessages = (count = 5) => {
  return Array.from({ length: count }, (_, index) => 
    createMockMessage({
      id: index + 1,
      role: index % 2 === 0 ? 'user' : 'assistant',
      content: `Test message ${index + 1}`,
    })
  );
};
