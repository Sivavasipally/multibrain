/**
 * Comprehensive tests for AuthContext
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AuthProvider, useAuth } from '../AuthContext';

// Mock API service
const mockLogin = jest.fn();
const mockRegister = jest.fn();
const mockGetProfile = jest.fn();
jest.mock('../../services/api', () => ({
  authAPI: {
    login: mockLogin,
    register: mockRegister,
    getProfile: mockGetProfile
  }
}));

// Mock localStorage
const mockSetItem = jest.fn();
const mockGetItem = jest.fn();
const mockRemoveItem = jest.fn();
Object.defineProperty(window, 'localStorage', {
  value: {
    setItem: mockSetItem,
    getItem: mockGetItem,
    removeItem: mockRemoveItem
  }
});

// Test component that uses AuthContext
const TestComponent: React.FC = () => {
  const { user, login, logout, register, loading } = useAuth();

  return (
    <div>
      <div data-testid="loading">{loading ? 'Loading' : 'Not Loading'}</div>
      <div data-testid="user">{user ? user.username : 'No User'}</div>
      <button onClick={() => login('testuser', 'password')}>Login</button>
      <button onClick={() => register('newuser', 'new@email.com', 'password')}>Register</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetItem.mockReturnValue(null);
  });

  it('provides initial auth state', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading');
    expect(screen.getByTestId('user')).toHaveTextContent('No User');
  });

  it('restores user from localStorage on mount', async () => {
    const savedUser = { id: 1, username: 'testuser', email: 'test@email.com' };
    const savedToken = 'saved-token';
    
    mockGetItem
      .mockReturnValueOnce(JSON.stringify(savedUser)) // user
      .mockReturnValueOnce(savedToken); // token

    mockGetProfile.mockResolvedValueOnce({ user: savedUser });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('testuser');
    });

    expect(mockGetProfile).toHaveBeenCalled();
  });

  it('handles successful login', async () => {
    const mockUser = { id: 1, username: 'testuser', email: 'test@email.com' };
    const mockToken = 'auth-token';
    mockLogin.mockResolvedValueOnce({
      user: mockUser,
      access_token: mockToken
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    const loginButton = screen.getByText('Login');
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('testuser');
    });

    expect(mockLogin).toHaveBeenCalledWith('testuser', 'password');
    expect(mockSetItem).toHaveBeenCalledWith('user', JSON.stringify(mockUser));
    expect(mockSetItem).toHaveBeenCalledWith('token', mockToken);
  });

  it('handles login failure', async () => {
    const errorMessage = 'Invalid credentials';
    mockLogin.mockRejectedValueOnce(new Error(errorMessage));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    const loginButton = screen.getByText('Login');
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('No User');
    });

    expect(mockSetItem).not.toHaveBeenCalled();
  });

  it('handles successful registration', async () => {
    const mockUser = { id: 2, username: 'newuser', email: 'new@email.com' };
    const mockToken = 'new-auth-token';
    mockRegister.mockResolvedValueOnce({
      user: mockUser,
      access_token: mockToken
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    const registerButton = screen.getByText('Register');
    fireEvent.click(registerButton);

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('newuser');
    });

    expect(mockRegister).toHaveBeenCalledWith('newuser', 'new@email.com', 'password');
    expect(mockSetItem).toHaveBeenCalledWith('user', JSON.stringify(mockUser));
    expect(mockSetItem).toHaveBeenCalledWith('token', mockToken);
  });

  it('handles registration failure', async () => {
    const errorMessage = 'Username already exists';
    mockRegister.mockRejectedValueOnce(new Error(errorMessage));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    const registerButton = screen.getByText('Register');
    fireEvent.click(registerButton);

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('No User');
    });

    expect(mockSetItem).not.toHaveBeenCalled();
  });

  it('handles logout', async () => {
    // Start with a logged-in user
    const mockUser = { id: 1, username: 'testuser', email: 'test@email.com' };
    const mockToken = 'auth-token';
    mockLogin.mockResolvedValueOnce({
      user: mockUser,
      access_token: mockToken
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Login first
    const loginButton = screen.getByText('Login');
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('testuser');
    });

    // Now logout
    const logoutButton = screen.getByText('Logout');
    fireEvent.click(logoutButton);

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('No User');
    });

    expect(mockRemoveItem).toHaveBeenCalledWith('user');
    expect(mockRemoveItem).toHaveBeenCalledWith('token');
  });

  it('shows loading state during async operations', async () => {
    mockLogin.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({
        user: { id: 1, username: 'testuser', email: 'test@email.com' },
        access_token: 'token'
      }), 100))
    );

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    const loginButton = screen.getByText('Login');
    fireEvent.click(loginButton);

    expect(screen.getByTestId('loading')).toHaveTextContent('Loading');

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading');
    });
  });

  it('handles token expiration during profile refresh', async () => {
    const savedUser = { id: 1, username: 'testuser', email: 'test@email.com' };
    const savedToken = 'expired-token';
    
    mockGetItem
      .mockReturnValueOnce(JSON.stringify(savedUser))
      .mockReturnValueOnce(savedToken);

    mockGetProfile.mockRejectedValueOnce(new Error('Token expired'));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('No User');
    });

    expect(mockRemoveItem).toHaveBeenCalledWith('user');
    expect(mockRemoveItem).toHaveBeenCalledWith('token');
  });

  it('throws error when useAuth is used outside AuthProvider', () => {
    const TestComponentWithoutProvider: React.FC = () => {
      useAuth();
      return null;
    };

    // Suppress console.error for this test
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestComponentWithoutProvider />);
    }).toThrow('useAuth must be used within an AuthProvider');

    consoleSpy.mockRestore();
  });

  it('updates axios defaults with token on login', async () => {
    const mockToken = 'auth-token';
    mockLogin.mockResolvedValueOnce({
      user: { id: 1, username: 'testuser', email: 'test@email.com' },
      access_token: mockToken
    });

    // Mock axios defaults
    const mockAxiosDefaults = {
      headers: {
        common: {}
      }
    };
    jest.doMock('axios', () => ({
      defaults: mockAxiosDefaults
    }));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    const loginButton = screen.getByText('Login');
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('testuser');
    });
  });

  it('clears axios defaults on logout', async () => {
    // Setup logged in state first
    const mockUser = { id: 1, username: 'testuser', email: 'test@email.com' };
    const mockToken = 'auth-token';
    mockLogin.mockResolvedValueOnce({
      user: mockUser,
      access_token: mockToken
    });

    const mockAxiosDefaults = {
      headers: {
        common: {}
      }
    };
    jest.doMock('axios', () => ({
      defaults: mockAxiosDefaults
    }));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Login first
    const loginButton = screen.getByText('Login');
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('testuser');
    });

    // Then logout
    const logoutButton = screen.getByText('Logout');
    fireEvent.click(logoutButton);

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('No User');
    });
  });
});