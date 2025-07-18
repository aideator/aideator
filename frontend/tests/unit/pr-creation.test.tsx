import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PRCreation } from '@/components/pr-creation'
import { useAuth } from '@/components/auth/auth-provider'

// Mock the auth provider
jest.mock('@/components/auth/auth-provider')
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>

// Mock the DiffViewer component
jest.mock('@/components/diff-viewer', () => {
  return function MockDiffViewer({ xmlData }: { xmlData: string }) {
    return <div data-testid="diff-viewer">{xmlData}</div>
  }
})

describe('PRCreation', () => {
  const defaultProps = {
    taskId: '123',
    variationId: 0,
    summary: 'Test summary',
    diffContent: '<diff>test diff</diff>',
    changedFiles: [
      { name: 'test.js', additions: 5, deletions: 2 }
    ],
    githubUrl: 'https://github.com/test/repo'
  }

  beforeEach(() => {
    mockUseAuth.mockReturnValue({
      user: { id: '1', name: 'Test User' },
      token: 'test-token',
      isLoading: false,
      login: jest.fn(),
      logout: jest.fn()
    })

    // Mock fetch
    global.fetch = jest.fn()
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  it('renders the component with all required data', () => {
    render(<PRCreation {...defaultProps} />)
    
    expect(screen.getByText('Create Pull Request')).toBeInTheDocument()
    expect(screen.getByText('Create a GitHub pull request with the changes from this variation')).toBeInTheDocument()
    expect(screen.getByDisplayValue('AIdeator – Task 123 Variation 1')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Test summary')).toBeInTheDocument()
  })

  it('shows repository URL', () => {
    render(<PRCreation {...defaultProps} />)
    
    expect(screen.getByText('Repository:')).toBeInTheDocument()
    expect(screen.getByText('https://github.com/test/repo')).toBeInTheDocument()
  })

  it('shows changed files', () => {
    render(<PRCreation {...defaultProps} />)
    
    expect(screen.getByText('Files to be changed')).toBeInTheDocument()
    expect(screen.getByText('test.js')).toBeInTheDocument()
    expect(screen.getByText('+5')).toBeInTheDocument()
    expect(screen.getByText('-2')).toBeInTheDocument()
  })

  it('shows diff preview', () => {
    render(<PRCreation {...defaultProps} />)
    
    expect(screen.getByText('Preview Changes')).toBeInTheDocument()
    expect(screen.getByTestId('diff-viewer')).toBeInTheDocument()
  })

  it('creates PR successfully', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ pr_url: 'https://github.com/test/repo/pull/123' })
    } as Response)

    render(<PRCreation {...defaultProps} />)
    
    const createButton = screen.getByText('Create Pull Request')
    fireEvent.click(createButton)

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/tasks/123/variations/0/pull-request',
        {
          method: 'POST',
          headers: {
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            title: 'AIdeator – Task 123 Variation 1',
            description: 'Test summary',
          }),
        }
      )
    })

    await waitFor(() => {
      expect(screen.getByText('Pull Request Created')).toBeInTheDocument()
      expect(screen.getByText('View on GitHub')).toBeInTheDocument()
    })
  })

  it('handles PR creation error', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>
    mockFetch.mockResolvedValueOnce({
      ok: false,
      text: async () => 'GitHub API error'
    } as Response)

    render(<PRCreation {...defaultProps} />)
    
    const createButton = screen.getByText('Create Pull Request')
    fireEvent.click(createButton)

    await waitFor(() => {
      expect(screen.getByText('Failed to create PR: GitHub API error')).toBeInTheDocument()
    })
  })

  it('shows error when no token available', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      token: null,
      isLoading: false,
      login: jest.fn(),
      logout: jest.fn()
    })

    render(<PRCreation {...defaultProps} />)
    
    const createButton = screen.getByText('Create Pull Request')
    expect(createButton).toBeDisabled()
    expect(screen.getByText('Please log in with GitHub to create pull requests')).toBeInTheDocument()
  })

  it('shows error when no GitHub URL', () => {
    render(<PRCreation {...defaultProps} githubUrl={undefined} />)
    
    const createButton = screen.getByText('Create Pull Request')
    expect(createButton).toBeDisabled()
    expect(screen.getByText('No GitHub repository associated with this task')).toBeInTheDocument()
  })

  it('shows error when no diff content', () => {
    render(<PRCreation {...defaultProps} diffContent="" />)
    
    const createButton = screen.getByText('Create Pull Request')
    expect(createButton).toBeDisabled()
    expect(screen.getByText('No changes available to create a pull request')).toBeInTheDocument()
  })

  it('allows editing PR title and description', () => {
    render(<PRCreation {...defaultProps} />)
    
    const titleInput = screen.getByDisplayValue('AIdeator – Task 123 Variation 1')
    const descriptionInput = screen.getByDisplayValue('Test summary')
    
    fireEvent.change(titleInput, { target: { value: 'Custom PR Title' } })
    fireEvent.change(descriptionInput, { target: { value: 'Custom description' } })
    
    expect(titleInput).toHaveValue('Custom PR Title')
    expect(descriptionInput).toHaveValue('Custom description')
  })

  it('validates PR title length', () => {
    render(<PRCreation {...defaultProps} />)
    
    const titleInput = screen.getByDisplayValue('AIdeator – Task 123 Variation 1')
    
    // Test too short title
    fireEvent.change(titleInput, { target: { value: 'Hi' } })
    expect(screen.getByText('PR title must be at least 5 characters')).toBeInTheDocument()
    
    // Test valid title
    fireEvent.change(titleInput, { target: { value: 'Valid Title' } })
    expect(screen.queryByText('PR title must be at least 5 characters')).not.toBeInTheDocument()
  })

  it('validates PR description length', () => {
    render(<PRCreation {...defaultProps} />)
    
    const descriptionInput = screen.getByDisplayValue('Test summary')
    const longDescription = 'a'.repeat(2001)
    
    fireEvent.change(descriptionInput, { target: { value: longDescription } })
    expect(screen.getByText('PR description must be less than 2000 characters')).toBeInTheDocument()
  })

  it('shows character count for title and description', () => {
    render(<PRCreation {...defaultProps} />)
    
    expect(screen.getByText('25/100 characters')).toBeInTheDocument()
    expect(screen.getByText('12/2000 characters')).toBeInTheDocument()
  })

  it('handles rate limiting with retry logic', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>
    
    // Mock rate limit response first, then success
    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 429,
        text: async () => 'Rate limit exceeded'
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ pr_url: 'https://github.com/test/repo/pull/123' })
      } as Response)

    render(<PRCreation {...defaultProps} />)
    
    const createButton = screen.getByText('Create Pull Request')
    fireEvent.click(createButton)

    // Should show retrying message
    await waitFor(() => {
      expect(screen.getByText('Retrying... (1/3)')).toBeInTheDocument()
    })

    // Should eventually succeed
    await waitFor(() => {
      expect(screen.getByText('Pull Request Created')).toBeInTheDocument()
    })
  })

  it('handles specific HTTP error codes', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>
    
    // Test 403 error
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      text: async () => 'Forbidden'
    } as Response)

    render(<PRCreation {...defaultProps} />)
    
    const createButton = screen.getByText('Create Pull Request')
    fireEvent.click(createButton)

    await waitFor(() => {
      expect(screen.getByText('Access denied. Please check your repository permissions.')).toBeInTheDocument()
    })
  })

  it('shows validation errors in form fields', () => {
    render(<PRCreation {...defaultProps} />)
    
    const titleInput = screen.getByDisplayValue('AIdeator – Task 123 Variation 1')
    
    // Make title too short
    fireEvent.change(titleInput, { target: { value: 'Hi' } })
    
    // Check that input has error styling
    expect(titleInput).toHaveClass('border-red-500')
    expect(titleInput).toHaveAttribute('aria-invalid', 'true')
  })

  it('disables button when form is invalid', () => {
    render(<PRCreation {...defaultProps} />)
    
    const titleInput = screen.getByDisplayValue('AIdeator – Task 123 Variation 1')
    const createButton = screen.getByText('Create Pull Request')
    
    // Make title too short
    fireEvent.change(titleInput, { target: { value: 'Hi' } })
    
    expect(createButton).toBeDisabled()
  })

  it('shows ready state when all requirements are met', () => {
    render(<PRCreation {...defaultProps} />)
    
    expect(screen.getByText('Ready to create PR:')).toBeInTheDocument()
    expect(screen.getByText('• GitHub repository: test/repo')).toBeInTheDocument()
    expect(screen.getByText('• 1 file modified')).toBeInTheDocument()
    expect(screen.getByText('• Diff content available')).toBeInTheDocument()
  })

  it('shows requirements not met when missing data', () => {
    render(<PRCreation {...defaultProps} githubUrl={undefined} />)
    
    expect(screen.getByText('Requirements not met:')).toBeInTheDocument()
    expect(screen.getByText('• No GitHub repository associated with this task')).toBeInTheDocument()
  })

  it('trims whitespace from title and description', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ pr_url: 'https://github.com/test/repo/pull/123' })
    } as Response)

    render(<PRCreation {...defaultProps} />)
    
    const titleInput = screen.getByDisplayValue('AIdeator – Task 123 Variation 1')
    const descriptionInput = screen.getByDisplayValue('Test summary')
    
    // Add whitespace
    fireEvent.change(titleInput, { target: { value: '  Title with spaces  ' } })
    fireEvent.change(descriptionInput, { target: { value: '  Description with spaces  ' } })
    
    const createButton = screen.getByText('Create Pull Request')
    fireEvent.click(createButton)

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: JSON.stringify({
            title: 'Title with spaces',
            description: 'Description with spaces',
          }),
        })
      )
    })
  })

  it('tracks analytics events when available', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>
    const mockAnalytics = {
      track: jest.fn()
    }
    
    // Mock analytics
    Object.defineProperty(window, 'analytics', {
      value: mockAnalytics,
      writable: true
    })
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ pr_url: 'https://github.com/test/repo/pull/123' })
    } as Response)

    render(<PRCreation {...defaultProps} />)
    
    const createButton = screen.getByText('Create Pull Request')
    fireEvent.click(createButton)

    await waitFor(() => {
      expect(mockAnalytics.track).toHaveBeenCalledWith('pr_creation_success', {
        taskId: '123',
        variationId: 0,
        prUrl: 'https://github.com/test/repo/pull/123',
        timestamp: expect.any(String)
      })
    })
  })

  it('handles keyboard navigation', () => {
    render(<PRCreation {...defaultProps} />)
    
    const titleInput = screen.getByDisplayValue('AIdeator – Task 123 Variation 1')
    const descriptionInput = screen.getByDisplayValue('Test summary')
    
    // Test tab navigation
    titleInput.focus()
    expect(titleInput).toHaveFocus()
    
    // Tab to description
    fireEvent.keyDown(titleInput, { key: 'Tab' })
    expect(descriptionInput).toHaveFocus()
  })

  it('provides proper ARIA labels and descriptions', () => {
    render(<PRCreation {...defaultProps} />)
    
    const titleInput = screen.getByDisplayValue('AIdeator – Task 123 Variation 1')
    const descriptionInput = screen.getByDisplayValue('Test summary')
    const createButton = screen.getByText('Create Pull Request')
    
    expect(titleInput).toHaveAttribute('id', 'pr-title')
    expect(descriptionInput).toHaveAttribute('id', 'pr-description')
    expect(createButton).toHaveAttribute('aria-describedby', 'pr-button-description')
  })
})