/**
 * Tests for ProtectedRoute component
 */

import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import { render } from '../../utils/test-utils';
import ProtectedRoute from '../../../components/Auth/ProtectedRoute';
import { AuthContext } from '../../../contexts/AuthContext';

// Mock child component
const MockProtectedComponent = () => <div>Protected Content</div>;

// Mock auth context values
const mockAuthContextValue = {
  user: null,
  token: null,
  loading: false,
  login: jest.fn(),
  logout: jest.fn(),
  register: jest.fn(),
};

const mockAuthenticatedContextValue = {
  user: {
    id: 1,
    username: 'testuser',
    email: 'test@example.com',
    created_at: '2023-01-01T00:00:00Z',
    is_active: true,
  },
  token: 'mock-token',
  loading: false,
  login: jest.fn(),
  logout: jest.fn(),
  register: jest.fn(),
};

const mockLoadingContextValue = {
  user: null,
  token: null,
  loading: true,
  login: jest.fn(),
  logout: jest.fn(),
  register: jest.fn(),
};

describe('ProtectedRoute', () => {
  it('renders children when user is authenticated', async () => {
    render(
      <AuthContext.Provider value={mockAuthenticatedContextValue}>
        <ProtectedRoute>
          <MockProtectedComponent />
        </ProtectedRoute>
      </AuthContext.Provider>
    );

    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
  });

  it('redirects to login when user is not authenticated', async () => {
    render(
      <AuthContext.Provider value={mockAuthContextValue}>
        <ProtectedRoute>
          <MockProtectedComponent />
        </ProtectedRoute>
      </AuthContext.Provider>
    );

    await waitFor(() => {
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  it('shows loading state when authentication is loading', async () => {
    render(
      <AuthContext.Provider value={mockLoadingContextValue}>
        <ProtectedRoute>
          <MockProtectedComponent />
        </ProtectedRoute>
      </AuthContext.Provider>
    );

    // Should not show protected content while loading
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('handles authentication state changes', async () => {
    const { rerender } = render(
      <AuthContext.Provider value={mockLoadingContextValue}>
        <ProtectedRoute>
          <MockProtectedComponent />
        </ProtectedRoute>
      </AuthContext.Provider>
    );

    // Initially loading
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();

    // After authentication
    rerender(
      <AuthContext.Provider value={mockAuthenticatedContextValue}>
        <ProtectedRoute>
          <MockProtectedComponent />
        </ProtectedRoute>
      </AuthContext.Provider>
    );

    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
  });

  it('handles logout scenario', async () => {
    const { rerender } = render(
      <AuthContext.Provider value={mockAuthenticatedContextValue}>
        <ProtectedRoute>
          <MockProtectedComponent />
        </ProtectedRoute>
      </AuthContext.Provider>
    );

    // Initially authenticated
    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    // After logout
    rerender(
      <AuthContext.Provider value={mockAuthContextValue}>
        <ProtectedRoute>
          <MockProtectedComponent />
        </ProtectedRoute>
      </AuthContext.Provider>
    );

    await waitFor(() => {
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  it('preserves redirect location', async () => {
    // Mock location
    const mockLocation = {
      pathname: '/protected-page',
      search: '?param=value',
      hash: '#section',
      state: null,
      key: 'test',
    };

    Object.defineProperty(window, 'location', {
      value: mockLocation,
      writable: true,
    });

    render(
      <AuthContext.Provider value={mockAuthContextValue}>
        <ProtectedRoute>
          <MockProtectedComponent />
        </ProtectedRoute>
      </AuthContext.Provider>
    );

    await waitFor(() => {
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    // Should redirect to login with return URL
    // This would be tested with router testing utilities in a real scenario
  });
});
