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
})