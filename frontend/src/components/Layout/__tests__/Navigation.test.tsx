/**
 * Comprehensive tests for Navigation component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import Navigation from '../Navigation';
import { AuthProvider } from '../../../contexts/AuthContext';

// Mock AuthContext
const mockLogout = jest.fn();
const mockAuthContextLoggedIn = {
  user: { id: 1, username: 'testuser', email: 'test@example.com' },
  login: jest.fn(),
  logout: mockLogout,
  register: jest.fn(),
  loading: false
};

const mockAuthContextLoggedOut = {
  user: null,
  login: jest.fn(),
  logout: jest.fn(),
  register: jest.fn(),
  loading: false
};

jest.mock('../../../contexts/AuthContext', () => ({
  ...jest.requireActual('../../../contexts/AuthContext'),
  useAuth: jest.fn()
}));

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useLocation: () => ({ pathname: '/dashboard' })
}));

// Test wrapper
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
);

describe('Navigation Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('When logged in', () => {
    beforeEach(() => {
      const { useAuth } = require('../../../contexts/AuthContext');
      useAuth.mockReturnValue(mockAuthContextLoggedIn);
    });

    it('renders navigation menu with all links', () => {
      render(
        <TestWrapper>
          <Navigation />
        </TestWrapper>
      );

      expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
      expect(screen.getByText(/contexts/i)).toBeInTheDocument();
      expect(screen.getByText(/chat/i)).toBeInTheDocument();
      expect(screen.getByText(/settings/i)).toBeInTheDocument();
    });

    it('displays user information', () => {
      render(
        <TestWrapper>
          <Navigation />
        </TestWrapper>
      );

      expect(screen.getByText('testuser')).toBeInTheDocument();
    });

    it('navigates to correct routes when menu items are clicked', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <Navigation />
        </TestWrapper>
      );

      const contextsLink = screen.getByText(/contexts/i);
      await user.click(contextsLink);

      expect(mockNavigate).toHaveBeenCalledWith('/contexts');
    });

    it('shows logout option in user menu', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <Navigation />
        </TestWrapper>
      );

      const userMenuButton = screen.getByText('testuser');
      await user.click(userMenuButton);

      expect(screen.getByText(/logout/i)).toBeInTheDocument();
    });

    it('calls logout function when logout is clicked', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <Navigation />
        </TestWrapper>
      );

      const userMenuButton = screen.getByText('testuser');
      await user.click(userMenuButton);

      const logoutButton = screen.getByText(/logout/i);
      await user.click(logoutButton);

      expect(mockLogout).toHaveBeenCalled();
    });

    it('highlights active navigation item', () => {
      render(
        <TestWrapper>
          <Navigation />
        </TestWrapper>
      );

      const dashboardLink = screen.getByText(/dashboard/i);
      expect(dashboardLink.closest('a')).toHaveClass('active');
    });

    it('toggles mobile menu on small screens', async () => {
      const user = userEvent.setup();

      // Mock window.innerWidth for mobile
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 600,
      });

      render(
        <TestWrapper>
          <Navigation />
        </TestWrapper>
      );

      const menuToggle = screen.getByLabelText(/toggle menu/i);
      await user.click(menuToggle);

      // Menu should be visible after toggle
      expect(screen.getByRole('navigation')).toHaveClass('mobile-menu-open');
    });
  });

  describe('When logged out', () => {
    beforeEach(() => {
      const { useAuth } = require('../../../contexts/AuthContext');
      useAuth.mockReturnValue(mockAuthContextLoggedOut);
    });

    it('shows login and register links', () => {
      render(
        <TestWrapper>
          <Navigation />
        </TestWrapper>
      );

      expect(screen.getByText(/login/i)).toBeInTheDocument();
      expect(screen.getByText(/register/i)).toBeInTheDocument();
    });

    it('does not show protected navigation items', () => {
      render(
        <TestWrapper>
          <Navigation />
        </TestWrapper>
      );

      expect(screen.queryByText(/dashboard/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/contexts/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/chat/i)).not.toBeInTheDocument();
    });

    it('navigates to login when login link is clicked', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <Navigation />
        </TestWrapper>
      );

      const loginLink = screen.getByText(/login/i);
      await user.click(loginLink);

      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });

    it('navigates to register when register link is clicked', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <Navigation />
        </TestWrapper>
      );

      const registerLink = screen.getByText(/register/i);
      await user.click(registerLink);

      expect(mockNavigate).toHaveBeenCalledWith('/register');
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      const { useAuth } = require('../../../contexts/AuthContext');
      useAuth.mockReturnValue(mockAuthContextLoggedIn);
    });

    it('supports keyboard navigation', async () => {
      render(
        <TestWrapper>
          <Navigation />
        </TestWrapper>
      );

      const dashboardLink = screen.getByText(/dashboard/i);
      const contextsLink = screen.getByText(/contexts/i);

      dashboardLink.focus();
      expect(dashboardLink).toHaveFocus();

      fireEvent.keyDown(dashboardLink, { key: 'Tab' });
      expect(contextsLink).toHaveFocus();
    });

    it('has proper ARIA labels', () => {
      render(
        <TestWrapper>
          <Navigation />
        </TestWrapper>
      );

      expect(screen.getByRole('navigation')).toHaveAttribute('aria-label', 'Main navigation');
    });

    it('indicates current page for screen readers', () => {
      render(
        <TestWrapper>
          <Navigation />
        </TestWrapper>
      );

      const activeLink = screen.getByText(/dashboard/i).closest('a');
      expect(activeLink).toHaveAttribute('aria-current', 'page');
    });
  });

  describe('Responsive Behavior', () => {
    beforeEach(() => {
      const { useAuth } = require('../../../contexts/AuthContext');
      useAuth.mockReturnValue(mockAuthContextLoggedIn);
    });

    it('shows mobile menu toggle on small screens', () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      });

      render(
        <TestWrapper>
          <Navigation />
        </TestWrapper>
      );

      expect(screen.getByLabelText(/toggle menu/i)).toBeInTheDocument();
    });

    it('hides mobile menu toggle on large screens', () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1200,
      });

      render(
        <TestWrapper>
          <Navigation />
        </TestWrapper>
      );

      expect(screen.queryByLabelText(/toggle menu/i)).not.toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('shows loading state when auth is loading', () => {
      const { useAuth } = require('../../../contexts/AuthContext');
      useAuth.mockReturnValue({
        ...mockAuthContextLoggedOut,
        loading: true
      });

      render(
        <TestWrapper>
          <Navigation />
        </TestWrapper>
      );

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });
});