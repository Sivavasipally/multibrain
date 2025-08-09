/**
 * Comprehensive tests for OfflineIndicator component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import OfflineIndicator from '../OfflineIndicator';

// Mock network status
const mockOnlineStatus = {
  isOnline: true,
  wasOffline: false
};

// Mock useNetworkStatus hook
jest.mock('../../../hooks/useNetworkStatus', () => ({
  useNetworkStatus: () => mockOnlineStatus
}));

describe('OfflineIndicator Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset to default online state
    mockOnlineStatus.isOnline = true;
    mockOnlineStatus.wasOffline = false;
  });

  it('does not render when online', () => {
    render(<OfflineIndicator />);

    expect(screen.queryByText(/offline/i)).not.toBeInTheDocument();
  });

  it('shows offline indicator when offline', () => {
    mockOnlineStatus.isOnline = false;

    render(<OfflineIndicator />);

    expect(screen.getByText(/you are currently offline/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/offline status/i)).toBeInTheDocument();
  });

  it('shows reconnection message when coming back online', async () => {
    mockOnlineStatus.isOnline = true;
    mockOnlineStatus.wasOffline = true;

    render(<OfflineIndicator />);

    expect(screen.getByText(/connection restored/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/connection restored/i)).toBeInTheDocument();
  });

  it('auto-hides reconnection message after delay', async () => {
    jest.useFakeTimers();
    
    mockOnlineStatus.isOnline = true;
    mockOnlineStatus.wasOffline = true;

    render(<OfflineIndicator />);

    expect(screen.getByText(/connection restored/i)).toBeInTheDocument();

    // Fast forward time
    jest.advanceTimersByTime(5000);

    await waitFor(() => {
      expect(screen.queryByText(/connection restored/i)).not.toBeInTheDocument();
    });

    jest.useRealTimers();
  });

  it('shows retry button when offline', () => {
    mockOnlineStatus.isOnline = false;

    render(<OfflineIndicator />);

    expect(screen.getByRole('button', { name: /retry connection/i })).toBeInTheDocument();
  });

  it('handles retry button click', async () => {
    const mockCheckConnection = jest.fn();
    mockOnlineStatus.isOnline = false;

    // Mock the retry functionality
    jest.spyOn(navigator, 'onLine', 'get').mockReturnValue(false);
    
    render(<OfflineIndicator onRetry={mockCheckConnection} />);

    const retryButton = screen.getByRole('button', { name: /retry connection/i });
    fireEvent.click(retryButton);

    expect(mockCheckConnection).toHaveBeenCalled();
  });

  it('displays offline mode features', () => {
    mockOnlineStatus.isOnline = false;

    render(<OfflineIndicator showFeatures />);

    expect(screen.getByText(/offline features available/i)).toBeInTheDocument();
  });

  it('shows pending sync count when offline', () => {
    mockOnlineStatus.isOnline = false;
    const pendingCount = 3;

    render(<OfflineIndicator pendingSyncCount={pendingCount} />);

    expect(screen.getByText(new RegExp(`${pendingCount}.*pending`, 'i'))).toBeInTheDocument();
  });

  it('supports custom messages', () => {
    mockOnlineStatus.isOnline = false;
    const customMessage = 'Custom offline message';

    render(<OfflineIndicator message={customMessage} />);

    expect(screen.getByText(customMessage)).toBeInTheDocument();
  });

  it('applies custom styling', () => {
    mockOnlineStatus.isOnline = false;
    const customClassName = 'custom-offline-indicator';

    render(<OfflineIndicator className={customClassName} />);

    const indicator = screen.getByLabelText(/offline status/i);
    expect(indicator).toHaveClass(customClassName);
  });

  it('handles different severity levels', () => {
    mockOnlineStatus.isOnline = false;

    render(<OfflineIndicator severity="error" />);

    const indicator = screen.getByLabelText(/offline status/i);
    expect(indicator).toHaveClass('severity-error');
  });

  it('shows connection quality indicator', () => {
    mockOnlineStatus.isOnline = true;
    const connectionQuality = 'slow';

    render(<OfflineIndicator connectionQuality={connectionQuality} />);

    expect(screen.getByText(/slow connection/i)).toBeInTheDocument();
  });

  it('is dismissible when configured', async () => {
    mockOnlineStatus.isOnline = true;
    mockOnlineStatus.wasOffline = true;

    render(<OfflineIndicator dismissible />);

    const dismissButton = screen.getByRole('button', { name: /dismiss/i });
    fireEvent.click(dismissButton);

    await waitFor(() => {
      expect(screen.queryByText(/connection restored/i)).not.toBeInTheDocument();
    });
  });

  it('provides accessibility features', () => {
    mockOnlineStatus.isOnline = false;

    render(<OfflineIndicator />);

    const indicator = screen.getByLabelText(/offline status/i);
    expect(indicator).toHaveAttribute('role', 'status');
    expect(indicator).toHaveAttribute('aria-live', 'polite');
  });

  it('announces status changes to screen readers', () => {
    mockOnlineStatus.isOnline = false;

    const { rerender } = render(<OfflineIndicator />);

    expect(screen.getByText(/you are currently offline/i)).toBeInTheDocument();

    // Simulate coming back online
    mockOnlineStatus.isOnline = true;
    mockOnlineStatus.wasOffline = true;

    rerender(<OfflineIndicator />);

    expect(screen.getByText(/connection restored/i)).toBeInTheDocument();
  });

  it('handles network status transitions smoothly', () => {
    const { rerender } = render(<OfflineIndicator />);

    // Go offline
    mockOnlineStatus.isOnline = false;
    rerender(<OfflineIndicator />);
    
    expect(screen.getByText(/you are currently offline/i)).toBeInTheDocument();

    // Come back online
    mockOnlineStatus.isOnline = true;
    mockOnlineStatus.wasOffline = true;
    rerender(<OfflineIndicator />);
    
    expect(screen.getByText(/connection restored/i)).toBeInTheDocument();

    // Stable online state
    mockOnlineStatus.wasOffline = false;
    rerender(<OfflineIndicator />);
    
    expect(screen.queryByText(/offline/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/connection restored/i)).not.toBeInTheDocument();
  });

  it('supports compact mode', () => {
    mockOnlineStatus.isOnline = false;

    render(<OfflineIndicator compact />);

    const indicator = screen.getByLabelText(/offline status/i);
    expect(indicator).toHaveClass('compact');
  });
});