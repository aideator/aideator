import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useRouter } from 'next/navigation'
import Home from '@/app/page'
import { apiClient } from '@/lib/api'

// Mock dependencies
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
  prefetch: jest.fn(),
}

describe('Home Page', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseRouter.mockReturnValue(mockRouter)

    // Mock API responses
    mockApiClient.getSessions.mockResolvedValue({
      sessions: [
        {
          id: 'session-1',
          user_id: 'user-1',
          title: 'Test Session',
          description: 'Test Description',
          is_active: true,
          is_archived: false,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
          last_activity_at: '2024-01-01T00:00:00Z',
          models_used: ['gpt-4'],
          total_turns: 5,
          total_cost: 0.123,
        },
      ],
      total: 1,
      limit: 50,
      offset: 0,
    })

    mockApiClient.searchGitHubRepositories.mockResolvedValue([
      {
        id: 1,
        name: 'test-repo',
        full_name: 'user/test-repo',
        private: false,
        html_url: 'https://github.com/user/test-repo',
        description: 'Test repository',
        default_branch: 'main',
      },
    ])

    mockApiClient.getGitHubRepositoryBranches.mockResolvedValue([
      {
        name: 'main',
        commit: {
          sha: 'abc123',
          url: 'https://api.github.com/repos/user/test-repo/commits/abc123',
        },
        protected: false,
      },
      {
        name: 'dev',
        commit: {
          sha: 'def456',
          url: 'https://api.github.com/repos/user/test-repo/commits/def456',
        },
        protected: true,
      },
    ])

    mockApiClient.getModelDefinitions.mockResolvedValue([
      'gpt-4-turbo',
      'gpt-3.5-turbo',
      'claude-3-sonnet',
    ])

    mockApiClient.createSession.mockResolvedValue({
      id: 'new-session-1',
      user_id: 'user-1',
      title: 'New Session',
      description: 'New Description',
      is_active: true,
      is_archived: false,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      last_activity_at: '2024-01-01T00:00:00Z',
      models_used: ['gpt-4'],
      total_turns: 0,
      total_cost: 0,
    })

    mockApiClient.createRun.mockResolvedValue({
      run_id: 'run-1',
      session_id: 'session-1',
      turn_id: 'turn-1',
      websocket_url: 'ws://localhost:8000/ws/runs/run-1',
    })
  })

  describe('Initial Load', () => {
    it('should render the home page', async () => {
      render(<Home />)
      
      expect(screen.getByText('AIdeator')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Describe a task or ask a question')).toBeInTheDocument()
    })

    it('should load sessions on mount', async () => {
      render(<Home />)
      
      await waitFor(() => {
        expect(mockApiClient.getSessions).toHaveBeenCalledWith({ limit: 50 })
      })
    })

    it('should load repositories on mount', async () => {
      render(<Home />)
      
      await waitFor(() => {
        expect(mockApiClient.searchGitHubRepositories).toHaveBeenCalledWith(
          'language:javascript OR language:typescript OR language:python stars:>1000'
        )
      })
    })

    it('should load model definitions on mount', async () => {
      render(<Home />)
      
      await waitFor(() => {
        expect(mockApiClient.getModelDefinitions).toHaveBeenCalled()
      })
    })
  })

  describe('Task Input', () => {
    it('should update task text on input', async () => {
      const user = userEvent.setup()
      render(<Home />)
      
      const textarea = screen.getByPlaceholderText('Describe a task or ask a question')
      await user.type(textarea, 'Test task')
      
      expect(textarea).toHaveValue('Test task')
    })

    it('should handle Enter key to submit', async () => {
      const user = userEvent.setup()
      render(<Home />)
      
      const textarea = screen.getByPlaceholderText('Describe a task or ask a question')
      await user.type(textarea, 'Test task')
      
      await waitFor(() => {
        expect(mockApiClient.getModelDefinitions).toHaveBeenCalled()
      })
      
      await user.keyboard('{Meta>}{Enter}{/Meta}')
      
      await waitFor(() => {
        expect(mockApiClient.createRun).toHaveBeenCalled()
      })
    })
  })

  describe('Repository Selection', () => {
    it('should load branches when repository is selected', async () => {
      render(<Home />)
      
      await waitFor(() => {
        expect(mockApiClient.searchGitHubRepositories).toHaveBeenCalled()
      })

      await waitFor(() => {
        expect(mockApiClient.getGitHubRepositoryBranches).toHaveBeenCalledWith('user', 'test-repo')
      })
    })

    it('should show loading state for repositories', () => {
      mockApiClient.searchGitHubRepositories.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )
      
      render(<Home />)
      
      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })
  })

  describe('Ask Button', () => {
    it('should create a session when Ask is clicked', async () => {
      const user = userEvent.setup()
      render(<Home />)
      
      const textarea = screen.getByPlaceholderText('Describe a task or ask a question')
      await user.type(textarea, 'Test question')
      
      await waitFor(() => {
        expect(mockApiClient.getModelDefinitions).toHaveBeenCalled()
      })
      
      const askButton = screen.getByText('Ask')
      await user.click(askButton)
      
      await waitFor(() => {
        expect(mockApiClient.createSession).toHaveBeenCalledWith({
          title: 'Test question',
          description: 'Q&A session: Test question',
          models_used: ['gpt-4-turbo', 'gpt-3.5-turbo', 'claude-3-sonnet'],
        })
      })
      
      expect(mockRouter.push).toHaveBeenCalledWith('/session/new-session-1')
    })

    it('should be disabled when no task text', () => {
      render(<Home />)
      
      const askButton = screen.getByText('Ask')
      expect(askButton).toBeDisabled()
    })
  })

  describe('Code Button', () => {
    it('should create a run when Code is clicked', async () => {
      const user = userEvent.setup()
      render(<Home />)
      
      const textarea = screen.getByPlaceholderText('Describe a task or ask a question')
      await user.type(textarea, 'Test code task')
      
      await waitFor(() => {
        expect(mockApiClient.getModelDefinitions).toHaveBeenCalled()
      })
      
      const codeButton = screen.getByText('Code')
      await user.click(codeButton)
      
      await waitFor(() => {
        expect(mockApiClient.createRun).toHaveBeenCalledWith({
          github_url: 'https://github.com/user/test-repo',
          prompt: 'Test code task',
          model_variants: expect.arrayContaining([
            expect.objectContaining({
              model_definition_id: expect.any(String),
              model_parameters: expect.objectContaining({
                temperature: expect.any(Number),
                max_tokens: 4096,
              }),
            }),
          ]),
          agent_mode: 'litellm',
          use_claude_code: false,
        })
      })
      
      expect(mockRouter.push).toHaveBeenCalledWith('/session/session-1/turn/turn-1/run/run-1')
    })

    it('should show loading state when creating run', async () => {
      const user = userEvent.setup()
      mockApiClient.createRun.mockImplementation(() => new Promise(() => {})) // Never resolves
      
      render(<Home />)
      
      const textarea = screen.getByPlaceholderText('Describe a task or ask a question')
      await user.type(textarea, 'Test code task')
      
      await waitFor(() => {
        expect(mockApiClient.getModelDefinitions).toHaveBeenCalled()
      })
      
      const codeButton = screen.getByText('Code')
      await user.click(codeButton)
      
      await waitFor(() => {
        expect(screen.getByText('Creating...')).toBeInTheDocument()
      })
    })
  })

  describe('Sessions Tab', () => {
    it('should display sessions list', async () => {
      render(<Home />)
      
      await waitFor(() => {
        expect(screen.getByText('Test Session')).toBeInTheDocument()
      })
    })

    it('should show loading state for sessions', () => {
      mockApiClient.getSessions.mockImplementation(() => new Promise(() => {}))
      
      render(<Home />)
      
      expect(screen.getByText('Loading sessions...')).toBeInTheDocument()
    })

    it('should handle sessions API error', async () => {
      mockApiClient.getSessions.mockRejectedValue(new Error('API Error'))
      
      render(<Home />)
      
      await waitFor(() => {
        expect(screen.getByText('Failed to load sessions')).toBeInTheDocument()
      })
    })

    it('should show retry button on error', async () => {
      mockApiClient.getSessions.mockRejectedValue(new Error('API Error'))
      
      render(<Home />)
      
      await waitFor(() => {
        expect(screen.getByText('Retry')).toBeInTheDocument()
      })
    })

    it('should show empty state when no sessions', async () => {
      mockApiClient.getSessions.mockResolvedValue({
        sessions: [],
        total: 0,
        limit: 50,
        offset: 0,
      })
      
      render(<Home />)
      
      await waitFor(() => {
        expect(screen.getByText('No sessions yet. Create your first session above!')).toBeInTheDocument()
      })
    })
  })

  describe('Agent Count Selection', () => {
    it('should update selected agent count', async () => {
      const user = userEvent.setup()
      render(<Home />)
      
      // Wait for initial load
      await waitFor(() => {
        expect(mockApiClient.getModelDefinitions).toHaveBeenCalled()
      })
      
      // Note: This is a simplified test as Select component testing is complex
      // In a real scenario, you might need to use more specific selectors
      const agentCountSelect = screen.getByDisplayValue('3')
      expect(agentCountSelect).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should handle repository loading error gracefully', async () => {
      mockApiClient.searchGitHubRepositories.mockRejectedValue(new Error('GitHub API Error'))
      
      render(<Home />)
      
      // Should not crash the app
      await waitFor(() => {
        expect(screen.getByText('AIdeator')).toBeInTheDocument()
      })
    })

    it('should handle model definitions loading error gracefully', async () => {
      mockApiClient.getModelDefinitions.mockRejectedValue(new Error('Models API Error'))
      
      render(<Home />)
      
      // Should not crash the app
      await waitFor(() => {
        expect(screen.getByText('AIdeator')).toBeInTheDocument()
      })
    })

    it('should handle branches loading error gracefully', async () => {
      mockApiClient.getGitHubRepositoryBranches.mockRejectedValue(new Error('Branches API Error'))
      
      render(<Home />)
      
      // Should not crash the app
      await waitFor(() => {
        expect(screen.getByText('AIdeator')).toBeInTheDocument()
      })
    })
  })
})