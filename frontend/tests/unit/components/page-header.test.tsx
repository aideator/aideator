import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import { usePathname, useRouter } from 'next/navigation'
import { PageHeader } from '@/components/page-header'
import { apiClient } from '@/lib/api'
import { AuthProvider } from '@/lib/auth-context'

// Setup mocks
const mockPush = jest.fn()
const mockReplace = jest.fn()

jest.mock('next/navigation', () => ({
  usePathname: jest.fn(() => '/'),
  useRouter: jest.fn(() => ({
    push: mockPush,
    replace: mockReplace,
  })),
}))
jest.mock('@/lib/api')

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

const mockUsePathname = jest.mocked(usePathname)
const mockApiClient = apiClient as jest.Mocked<typeof apiClient>

// Test wrapper component
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <AuthProvider>{children}</AuthProvider>
)

describe('PageHeader', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    localStorageMock.getItem.mockReturnValue(null)
  })

  it('should render default header for home page', () => {
    mockUsePathname.mockReturnValue('/')
    
    render(<PageHeader />, { wrapper: TestWrapper })
    
    expect(screen.getByText('AIdeator')).toBeInTheDocument()
    expect(screen.getByText('API Docs')).toBeInTheDocument()
  })

  it('should render session header when on session page', async () => {
    mockUsePathname.mockReturnValue('/session/test-session-id')
    mockApiClient.getSession.mockResolvedValue({
      id: 'test-session-id',
      user_id: 'user-123',
      title: 'Test Session Title',
      description: 'A test session',
      is_active: true,
      is_archived: false,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
      last_activity_at: '2023-01-01T00:00:00Z',
      models_used: ['gpt-4'],
      total_turns: 1,
      total_cost: 0.50
    })
    
    await act(async () => {
      render(<PageHeader />, { wrapper: TestWrapper })
    })
    
    await waitFor(() => {
      expect(screen.getByText('Test Session Title')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Archive')).toBeInTheDocument()
    expect(screen.getByText('Share')).toBeInTheDocument()
    expect(screen.getByText('Create PR')).toBeInTheDocument()
  })

  it('should handle session loading error gracefully', async () => {
    mockUsePathname.mockReturnValue('/session/invalid-session-id')
    mockApiClient.getSession.mockRejectedValue(new Error('Session not found'))
    
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})
    
    await act(async () => {
      render(<PageHeader />, { wrapper: TestWrapper })
    })
    
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Failed to load session:', expect.any(Error))
    })
    
    // Should still render default header when session fails to load
    expect(screen.getByText('AIdeator')).toBeInTheDocument()
    
    consoleSpy.mockRestore()
  })

  it('should extract session ID from pathname correctly', () => {
    mockUsePathname.mockReturnValue('/session/abc-123-def')
    mockApiClient.getSession.mockResolvedValue({
      id: 'abc-123-def',
      user_id: 'user-456',
      title: 'Session with Complex ID',
      description: undefined,
      is_active: true,
      is_archived: false,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
      last_activity_at: '2023-01-01T00:00:00Z',
      models_used: ['claude-3'],
      total_turns: 2,
      total_cost: 1.25
    })
    
    render(<PageHeader />, { wrapper: TestWrapper })
    
    expect(mockApiClient.getSession).toHaveBeenCalledWith('abc-123-def')
  })

  it('should not match invalid session paths', () => {
    mockUsePathname.mockReturnValue('/session/test-id/turn/123')
    
    render(<PageHeader />, { wrapper: TestWrapper })
    
    expect(mockApiClient.getSession).not.toHaveBeenCalled()
    expect(screen.getByText('AIdeator')).toBeInTheDocument()
  })

  it('should include API docs link with correct URL', () => {
    mockUsePathname.mockReturnValue('/')
    
    render(<PageHeader />, { wrapper: TestWrapper })
    
    const apiDocsLink = screen.getByText('API Docs').closest('a')
    expect(apiDocsLink).toHaveAttribute('href', 'http://localhost:8000/docs')
    expect(apiDocsLink).toHaveAttribute('target', '_blank')
    expect(apiDocsLink).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('should handle NEXT_PUBLIC_API_URL environment variable', () => {
    const originalEnv = process.env.NEXT_PUBLIC_API_URL
    process.env.NEXT_PUBLIC_API_URL = 'https://api.example.com'
    
    mockUsePathname.mockReturnValue('/')
    
    render(<PageHeader />, { wrapper: TestWrapper })
    
    const apiDocsLink = screen.getByText('API Docs').closest('a')
    expect(apiDocsLink).toHaveAttribute('href', 'https://api.example.com/docs')
    
    process.env.NEXT_PUBLIC_API_URL = originalEnv
  })

  it('should reset session state when navigating away from session page', () => {
    const { rerender } = render(<PageHeader />, { wrapper: TestWrapper })
    
    // First render on session page
    mockUsePathname.mockReturnValue('/session/test-id')
    rerender(<PageHeader />)
    
    // Then navigate away
    mockUsePathname.mockReturnValue('/')
    rerender(<PageHeader />)
    
    expect(screen.getByText('AIdeator')).toBeInTheDocument()
  })
})