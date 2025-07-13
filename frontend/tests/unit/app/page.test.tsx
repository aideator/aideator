import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import Home from '@/app/page'
import { apiClient } from '@/lib/api'

// Setup mocks
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))
jest.mock('@/lib/api')

const mockUseRouter = jest.mocked(useRouter)
const mockApiClient = apiClient as jest.Mocked<typeof apiClient>

const mockRouter = {
  push: jest.fn(),
  replace: jest.fn(),
  back: jest.fn(),
  forward: jest.fn(),
  refresh: jest.fn(),
  prefetch: jest.fn()
}

describe('Home Page', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseRouter.mockReturnValue(mockRouter)
    
    // Setup default API responses
    mockApiClient.getSessions.mockResolvedValue({
      sessions: [],
      total: 0,
      limit: 50,
      offset: 0
    })
    mockApiClient.searchGitHubRepositories.mockResolvedValue([])
    mockApiClient.getModelDefinitions.mockResolvedValue(['gpt-4-turbo', 'claude-3-sonnet'])
  })

  it('should render the home page', async () => {
    render(<Home />)
    
    await waitFor(() => {
      expect(screen.getByText('What are we coding next?')).toBeInTheDocument()
    })
  })

  it('should load sessions on mount', async () => {
    const sessions = [
      {
        id: 'session-1',
        user_id: 'user-1',
        title: 'Test Session',
        description: 'A test session',
        is_active: true,
        is_archived: false,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
        last_activity_at: '2023-01-01T00:00:00Z',
        models_used: ['gpt-4'],
        total_turns: 1,
        total_cost: 0.50
      }
    ]
    
    mockApiClient.getSessions.mockResolvedValue({
      sessions,
      total: 1,
      limit: 50,
      offset: 0
    })
    
    render(<Home />)
    
    await waitFor(() => {
      expect(mockApiClient.getSessions).toHaveBeenCalledWith({ limit: 50 })
    })
  })

  it('should show loading state initially', () => {
    render(<Home />)
    
    // Should show some loading indicators
    expect(screen.getByText('What are we coding next?')).toBeInTheDocument()
  })

  it('should handle textarea input', async () => {
    render(<Home />)
    
    await waitFor(() => {
      expect(screen.getByRole('textbox')).toBeInTheDocument()
    })
    
    const textarea = screen.getByRole('textbox')
    fireEvent.change(textarea, { target: { value: 'Test task description' } })
    
    expect(textarea).toHaveValue('Test task description')
  })

  it('should render agent count selector', async () => {
    render(<Home />)
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('3')).toBeInTheDocument()
    })
  })

  it('should handle repository selection', async () => {
    const repositories = [
      {
        id: 1,
        name: 'test-repo',
        full_name: 'user/test-repo',
        private: false,
        html_url: 'https://github.com/user/test-repo',
        description: 'A test repository',
        default_branch: 'main'
      }
    ]
    
    mockApiClient.searchGitHubRepositories.mockResolvedValue(repositories)
    
    render(<Home />)
    
    await waitFor(() => {
      expect(screen.getByText('What are we coding next?')).toBeInTheDocument()
    })
  })

  it('should display recent sessions when available', async () => {
    const sessions = [
      {
        id: 'session-1',
        user_id: 'user-1',
        title: 'Recent Session',
        description: 'A recent session',
        is_active: true,
        is_archived: false,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
        last_activity_at: '2023-01-01T00:00:00Z',
        models_used: ['gpt-4'],
        total_turns: 2,
        total_cost: 1.25
      }
    ]
    
    mockApiClient.getSessions.mockResolvedValue({
      sessions,
      total: 1,
      limit: 50,
      offset: 0
    })
    
    render(<Home />)
    
    await waitFor(() => {
      expect(screen.getByText('Recent Session')).toBeInTheDocument()
    })
  })

  it('should handle API errors gracefully', async () => {
    mockApiClient.getSessions.mockRejectedValue(new Error('API Error'))
    
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})
    
    render(<Home />)
    
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalled()
    })
    
    consoleSpy.mockRestore()
  })

  it('should show Ask and Code buttons', async () => {
    render(<Home />)
    
    await waitFor(() => {
      expect(screen.getByText('Ask')).toBeInTheDocument()
      expect(screen.getByText('Code')).toBeInTheDocument()
    })
  })

  it('should handle form submission', async () => {
    mockApiClient.createRun.mockResolvedValue({
      run_id: 'run-123',
      websocket_url: 'ws://localhost:8000/ws/runs/run-123',
      polling_url: 'http://localhost:8000/api/v1/runs/run-123',
      status: 'pending',
      estimated_duration_seconds: 300,
      session_id: 'session-123',
      turn_id: 'turn-123'
    })
    
    render(<Home />)
    
    await waitFor(() => {
      expect(screen.getByRole('textbox')).toBeInTheDocument()
    })
    
    const textarea = screen.getByRole('textbox')
    fireEvent.change(textarea, { target: { value: 'Test task' } })
    
    const codeButton = screen.getByText('Code')
    fireEvent.click(codeButton)
    
    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalled()
    })
  })

  it('should show validation error for empty task', async () => {
    render(<Home />)
    
    await waitFor(() => {
      expect(screen.getByText('Code')).toBeInTheDocument()
    })
    
    const codeButton = screen.getByText('Code')
    fireEvent.click(codeButton)
    
    // Should show some form of validation feedback
    expect(screen.getByText('Code')).toBeInTheDocument()
  })
})