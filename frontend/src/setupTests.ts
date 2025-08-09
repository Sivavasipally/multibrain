/**
 * Jest setup file for frontend tests
 */

import '@testing-library/jest-dom';

// Mock IntersectionObserver for components that use it
global.IntersectionObserver = class IntersectionObserver {
  observe() {
    return null;
  }
  disconnect() {
    return null;
  }
  unobserve() {
    return null;
  }
};

// Mock ResizeObserver for components that use it
global.ResizeObserver = class ResizeObserver {
  observe() {
    return null;
  }
  disconnect() {
    return null;
  }
  unobserve() {
    return null;
  }
};

// Mock matchMedia for responsive components
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  length: 0,
  key: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  length: 0,
  key: jest.fn(),
};

Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock
});

// Mock window.location
delete (window as any).location;
(window as any).location = {
  href: 'http://localhost:3000',
  origin: 'http://localhost:3000',
  hostname: 'localhost',
  port: '3000',
  protocol: 'http:',
  search: '',
  hash: '',
  pathname: '/',
  reload: jest.fn(),
  assign: jest.fn(),
  replace: jest.fn(),
};

// Mock window.navigator
Object.defineProperty(window, 'navigator', {
  value: {
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    onLine: true,
    language: 'en-US',
    languages: ['en-US', 'en'],
    cookieEnabled: true,
    platform: 'Win32',
    serviceWorker: {
      register: jest.fn(),
      ready: Promise.resolve({
        unregister: jest.fn()
      })
    }
  },
  writable: true
});

// Mock window.history
Object.defineProperty(window, 'history', {
  value: {
    pushState: jest.fn(),
    replaceState: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    go: jest.fn(),
    length: 1,
    state: null,
  },
  writable: true
});

// Mock URL.createObjectURL for file uploads
global.URL.createObjectURL = jest.fn(() => 'mocked-url');
global.URL.revokeObjectURL = jest.fn();

// Mock File Reader for file uploads
global.FileReader = class FileReader {
  result: string | ArrayBuffer | null = null;
  error: any = null;
  readyState: number = 0;
  
  onload: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  onerror: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  onloadstart: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  onloadend: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  onprogress: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  onabort: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  
  readAsText(file: File | Blob) {
    setTimeout(() => {
      this.result = 'mocked file content';
      this.readyState = 2;
      if (this.onload) {
        this.onload({} as ProgressEvent<FileReader>);
      }
    }, 0);
  }
  
  readAsDataURL(file: File | Blob) {
    setTimeout(() => {
      this.result = 'data:text/plain;base64,bW9ja2VkIGZpbGUgY29udGVudA==';
      this.readyState = 2;
      if (this.onload) {
        this.onload({} as ProgressEvent<FileReader>);
      }
    }, 0);
  }
  
  abort() {
    this.readyState = 2;
    if (this.onabort) {
      this.onabort({} as ProgressEvent<FileReader>);
    }
  }
  
  addEventListener = jest.fn();
  removeEventListener = jest.fn();
  dispatchEvent = jest.fn();
  
  EMPTY = 0;
  LOADING = 1;
  DONE = 2;
};

// Mock fetch for API calls
global.fetch = jest.fn();

// Mock WebSocket for real-time features
global.WebSocket = class WebSocket {
  url: string;
  readyState: number = 1;
  
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
  
  constructor(url: string) {
    this.url = url;
  }
  
  send = jest.fn();
  close = jest.fn();
  addEventListener = jest.fn();
  removeEventListener = jest.fn();
  dispatchEvent = jest.fn();
  
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
};

// Mock Notification API
global.Notification = class Notification {
  static permission: NotificationPermission = 'default';
  
  static requestPermission = jest.fn().mockResolvedValue('granted');
  
  constructor(title: string, options?: NotificationOptions) {}
  
  close = jest.fn();
  addEventListener = jest.fn();
  removeEventListener = jest.fn();
  dispatchEvent = jest.fn();
  
  onclick: ((event: Event) => void) | null = null;
  onshow: ((event: Event) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: Event) => void) | null = null;
};

// Suppress console warnings during tests
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

beforeEach(() => {
  console.error = jest.fn();
  console.warn = jest.fn();
});

afterEach(() => {
  console.error = originalConsoleError;
  console.warn = originalConsoleWarn;
});

// Global test timeout
jest.setTimeout(10000);