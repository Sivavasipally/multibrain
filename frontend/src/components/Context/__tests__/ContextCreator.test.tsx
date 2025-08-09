/**
 * Comprehensive tests for ContextCreator component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import ContextCreator from '../ContextCreator';
import { AuthProvider } from '../../../contexts/AuthContext';

// Mock API service
const mockCreateContext = jest.fn();
jest.mock('../../../services/api', () => ({
  contextsAPI: {
    createContext: mockCreateContext
  }
}));

// Mock AuthContext
const mockAuthContext = {
  user: { id: 1, username: 'testuser', email: 'test@example.com' },
  login: jest.fn(),
  logout: jest.fn(),
  register: jest.fn(),
  loading: false
};

jest.mock('../../../contexts/AuthContext', () => ({
  ...jest.requireActual('../../../contexts/AuthContext'),
  useAuth: () => mockAuthContext
}));

// Test wrapper
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
);

describe('ContextCreator Component', () => {
  const mockOnContextCreated = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders context creation form', () => {
    render(
      <TestWrapper>
        <ContextCreator onContextCreated={mockOnContextCreated} />
      </TestWrapper>
    );

    expect(screen.getByLabelText(/context name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    expect(screen.getByText(/source type/i)).toBeInTheDocument();
  });

  it('shows different config fields based on source type', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <ContextCreator onContextCreated={mockOnContextCreated} />
      </TestWrapper>
    );

    // Default should be files
    expect(screen.getByText(/files/i)).toBeInTheDocument();

    // Change to repository
    const sourceTypeSelect = screen.getByRole('button', { name: /source type/i });
    await user.click(sourceTypeSelect);
    
    const repoOption = screen.getByText(/repository/i);
    await user.click(repoOption);

    // Should show repository URL field
    await waitFor(() => {
      expect(screen.getByLabelText(/repository url/i)).toBeInTheDocument();
    });

    // Change to database
    await user.click(sourceTypeSelect);
    const dbOption = screen.getByText(/database/i);
    await user.click(dbOption);

    // Should show database connection field
    await waitFor(() => {
      expect(screen.getByLabelText(/connection string/i)).toBeInTheDocument();
    });
  });

  it('validates required fields', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <ContextCreator onContextCreated={mockOnContextCreated} />
      </TestWrapper>
    );

    const createButton = screen.getByRole('button', { name: /create context/i });
    await user.click(createButton);

    await waitFor(() => {
      expect(screen.getByText(/context name is required/i)).toBeInTheDocument();
    });
  });

  it('creates file-based context successfully', async () => {
    const user = userEvent.setup();
    const mockContext = {
      id: 1,
      name: 'Test Files Context',
      description: 'A test context',
      source_type: 'files'
    };
    mockCreateContext.mockResolvedValueOnce({ context: mockContext });

    render(
      <TestWrapper>
        <ContextCreator onContextCreated={mockOnContextCreated} />
      </TestWrapper>
    );

    const nameInput = screen.getByLabelText(/context name/i);
    const descriptionInput = screen.getByLabelText(/description/i);
    const createButton = screen.getByRole('button', { name: /create context/i });

    await user.type(nameInput, 'Test Files Context');
    await user.type(descriptionInput, 'A test context');
    await user.click(createButton);

    await waitFor(() => {
      expect(mockCreateContext).toHaveBeenCalledWith({
        name: 'Test Files Context',
        description: 'A test context',
        source_type: 'files',
        chunk_strategy: 'language-specific',
        embedding_model: 'text-embedding-004'
      });
      expect(mockOnContextCreated).toHaveBeenCalledWith(mockContext);
    });
  });

  it('creates repository-based context successfully', async () => {
    const user = userEvent.setup();
    const mockContext = {
      id: 1,
      name: 'Test Repo Context',
      source_type: 'repo'
    };
    mockCreateContext.mockResolvedValueOnce({ context: mockContext });

    render(
      <TestWrapper>
        <ContextCreator onContextCreated={mockOnContextCreated} />
      </TestWrapper>
    );

    const nameInput = screen.getByLabelText(/context name/i);
    const sourceTypeSelect = screen.getByRole('button', { name: /source type/i });
    
    await user.type(nameInput, 'Test Repo Context');
    await user.click(sourceTypeSelect);
    
    const repoOption = screen.getByText(/repository/i);
    await user.click(repoOption);

    await waitFor(async () => {
      const repoUrlInput = screen.getByLabelText(/repository url/i);
      await user.type(repoUrlInput, 'https://github.com/test/repo.git');
    });

    const createButton = screen.getByRole('button', { name: /create context/i });
    await user.click(createButton);

    await waitFor(() => {
      expect(mockCreateContext).toHaveBeenCalledWith({
        name: 'Test Repo Context',
        description: '',
        source_type: 'repo',
        config: {
          repo_url: 'https://github.com/test/repo.git',
          branch: 'main',
          include_patterns: [],
          exclude_patterns: []
        },
        chunk_strategy: 'language-specific',
        embedding_model: 'text-embedding-004'
      });
    });
  });

  it('handles creation errors gracefully', async () => {
    const user = userEvent.setup();
    const errorMessage = 'Context creation failed';
    mockCreateContext.mockRejectedValueOnce(new Error(errorMessage));

    render(
      <TestWrapper>
        <ContextCreator onContextCreated={mockOnContextCreated} />
      </TestWrapper>
    );

    const nameInput = screen.getByLabelText(/context name/i);
    const createButton = screen.getByRole('button', { name: /create context/i });

    await user.type(nameInput, 'Test Context');
    await user.click(createButton);

    await waitFor(() => {
      expect(screen.getByText(/context creation failed/i)).toBeInTheDocument();
    });
  });

  it('disables form during creation', async () => {
    const user = userEvent.setup();
    mockCreateContext.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({ context: {} }), 100))
    );

    render(
      <TestWrapper>
        <ContextCreator onContextCreated={mockOnContextCreated} />
      </TestWrapper>
    );

    const nameInput = screen.getByLabelText(/context name/i);
    const createButton = screen.getByRole('button', { name: /create context/i });

    await user.type(nameInput, 'Test Context');
    await user.click(createButton);

    expect(createButton).toBeDisabled();
    expect(nameInput).toBeDisabled();
  });

  it('validates repository URL format', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <ContextCreator onContextCreated={mockOnContextCreated} />
      </TestWrapper>
    );

    const nameInput = screen.getByLabelText(/context name/i);
    const sourceTypeSelect = screen.getByRole('button', { name: /source type/i });
    
    await user.type(nameInput, 'Test Repo Context');
    await user.click(sourceTypeSelect);
    
    const repoOption = screen.getByText(/repository/i);
    await user.click(repoOption);

    await waitFor(async () => {
      const repoUrlInput = screen.getByLabelText(/repository url/i);
      await user.type(repoUrlInput, 'invalid-url');
    });

    const createButton = screen.getByRole('button', { name: /create context/i });
    await user.click(createButton);

    await waitFor(() => {
      expect(screen.getByText(/please enter a valid repository url/i)).toBeInTheDocument();
    });
  });

  it('allows customization of chunk strategy', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <ContextCreator onContextCreated={mockOnContextCreated} />
      </TestWrapper>
    );

    const chunkStrategySelect = screen.getByRole('button', { name: /chunk strategy/i });
    await user.click(chunkStrategySelect);

    const fixedSizeOption = screen.getByText(/fixed size/i);
    await user.click(fixedSizeOption);

    expect(screen.getByText(/fixed size/i)).toBeInTheDocument();
  });

  it('allows customization of embedding model', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <ContextCreator onContextCreated={mockOnContextCreated} />
      </TestWrapper>
    );

    const embeddingModelSelect = screen.getByRole('button', { name: /embedding model/i });
    await user.click(embeddingModelSelect);

    const altModel = screen.getByText(/text-embedding-ada-002/i);
    await user.click(altModel);

    expect(screen.getByText(/text-embedding-ada-002/i)).toBeInTheDocument();
  });

  it('supports keyboard navigation', async () => {
    render(
      <TestWrapper>
        <ContextCreator onContextCreated={mockOnContextCreated} />
      </TestWrapper>
    );

    const nameInput = screen.getByLabelText(/context name/i);
    const descriptionInput = screen.getByLabelText(/description/i);

    nameInput.focus();
    expect(nameInput).toHaveFocus();

    fireEvent.keyDown(nameInput, { key: 'Tab' });
    expect(descriptionInput).toHaveFocus();
  });
});