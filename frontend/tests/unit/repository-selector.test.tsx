import { render, screen, fireEvent } from '@testing-library/react'
import { RepositorySelector } from '@/components/repository-selector'

// Mock the GitHubRepo interface
const mockRepos = [
  {
    id: 1,
    name: 'test-repo',
    full_name: 'test-org/test-repo',
    html_url: 'https://github.com/test-org/test-repo',
    description: 'A test repository',
    private: false,
    default_branch: 'main',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 2,
    name: 'another-repo',
    full_name: 'test-org/another-repo',
    html_url: 'https://github.com/test-org/another-repo',
    description: 'Another test repository',
    private: true,
    default_branch: 'main',
    updated_at: '2024-01-01T00:00:00Z'
  }
]

describe('RepositorySelector', () => {
  const mockOnRepoSelect = jest.fn()

  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()
    mockOnRepoSelect.mockClear()
  })

  it('renders the selector button', () => {
    render(
      <RepositorySelector
        repos={mockRepos}
        selectedRepo=""
        onRepoSelect={mockOnRepoSelect}
        loading={false}
        token="test-token"
      />
    )

    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('shows loading state when loading is true', () => {
    render(
      <RepositorySelector
        repos={mockRepos}
        selectedRepo=""
        onRepoSelect={mockOnRepoSelect}
        loading={true}
        token="test-token"
      />
    )

    expect(screen.getByText('Loading repos...')).toBeInTheDocument()
  })

  it('opens dropdown when clicked', () => {
    render(
      <RepositorySelector
        repos={mockRepos}
        selectedRepo=""
        onRepoSelect={mockOnRepoSelect}
        loading={false}
        token="test-token"
      />
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    expect(screen.getByPlaceholderText('Search repositories...')).toBeInTheDocument()
  })

  it('displays repositories grouped by organization', () => {
    render(
      <RepositorySelector
        repos={mockRepos}
        selectedRepo=""
        onRepoSelect={mockOnRepoSelect}
        loading={false}
        token="test-token"
      />
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    // Check for organization header
    expect(screen.getAllByText('test-org')[0]).toBeInTheDocument()
    expect(screen.getByText('test-repo')).toBeInTheDocument()
    expect(screen.getByText('another-repo')).toBeInTheDocument()
  })

  it('filters repositories when searching', () => {
    render(
      <RepositorySelector
        repos={mockRepos}
        selectedRepo=""
        onRepoSelect={mockOnRepoSelect}
        loading={false}
        token="test-token"
      />
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    const searchInput = screen.getByPlaceholderText('Search repositories...')
    fireEvent.change(searchInput, { target: { value: 'test-repo' } })

    expect(screen.getByText('test-repo')).toBeInTheDocument()
    expect(screen.queryByText('another-repo')).not.toBeInTheDocument()
  })

  it('calls onRepoSelect when a repository is clicked', () => {
    render(
      <RepositorySelector
        repos={mockRepos}
        selectedRepo=""
        onRepoSelect={mockOnRepoSelect}
        loading={false}
        token="test-token"
      />
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    const repoButton = screen.getByText('test-repo')
    fireEvent.click(repoButton)

    expect(mockOnRepoSelect).toHaveBeenCalledWith(
      'https://github.com/test-org/test-repo'
    )
  })

  it('shows demo repository for unauthenticated users', () => {
    render(
      <RepositorySelector
        repos={mockRepos}
        selectedRepo=""
        onRepoSelect={mockOnRepoSelect}
        loading={false}
        token={null}
      />
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    expect(screen.getByText('helloworld')).toBeInTheDocument()
    expect(screen.getByText('aideator')).toBeInTheDocument()
  })
})