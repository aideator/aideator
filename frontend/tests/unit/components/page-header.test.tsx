import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { usePathname } from 'next/navigation'
import { PageHeader } from '@/components/page-header'
import { apiClient } from '@/lib/api'

// Setup mocks
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(() => '/'),
}))
jest.mock('@/lib/api')

const mockUsePathname = jest.mocked(usePathname)
const mockApiClient = apiClient as jest.Mocked<typeof apiClient>

describe('PageHeader', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should render default header for home page', () => {
    mockUsePathname.mockReturnValue('/')
    
    render(<PageHeader />)
    
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
    
    render(<PageHeader />)
    
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
    
    render(<PageHeader />)
    
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
    
    render(<PageHeader />)
    
    expect(mockApiClient.getSession).toHaveBeenCalledWith('abc-123-def')
  })

  it('should not match invalid session paths', () => {
    mockUsePathname.mockReturnValue('/session/test-id/turn/123')
    
    render(<PageHeader />)
    
    expect(mockApiClient.getSession).not.toHaveBeenCalled()
    expect(screen.getByText('AIdeator')).toBeInTheDocument()
  })

  it('should include API docs link with correct URL', () => {
    mockUsePathname.mockReturnValue('/')
    
    render(<PageHeader />)
    
    const apiDocsLink = screen.getByText('API Docs').closest('a')
    expect(apiDocsLink).toHaveAttribute('href', 'http://localhost:8000/docs')
    expect(apiDocsLink).toHaveAttribute('target', '_blank')
    expect(apiDocsLink).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('should handle NEXT_PUBLIC_API_URL environment variable', () => {
    const originalEnv = process.env.NEXT_PUBLIC_API_URL
    process.env.NEXT_PUBLIC_API_URL = 'https://api.example.com'
    
    mockUsePathname.mockReturnValue('/')
    
    render(<PageHeader />)
    
    const apiDocsLink = screen.getByText('API Docs').closest('a')
    expect(apiDocsLink).toHaveAttribute('href', 'https://api.example.com/docs')
    
    process.env.NEXT_PUBLIC_API_URL = originalEnv
  })

  it('should reset session state when navigating away from session page', () => {
    const { rerender } = render(<PageHeader />)
    
    // First render on session page
    mockUsePathname.mockReturnValue('/session/test-id')
    rerender(<PageHeader />)
    
    // Then navigate away
    mockUsePathname.mockReturnValue('/')
    rerender(<PageHeader />)
    
    expect(screen.getByText('AIdeator')).toBeInTheDocument()
  })
})