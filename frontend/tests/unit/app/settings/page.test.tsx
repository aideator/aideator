import { render, screen } from '@testing-library/react'
import SettingsPage from '@/app/settings/page'
import { useRouter } from 'next/navigation'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))

// Mock the ProviderKeyManager component
jest.mock('@/components/provider-keys/provider-key-manager', () => ({
  ProviderKeyManager: () => <div data-testid="provider-key-manager">Provider Key Manager</div>,
}))

describe('SettingsPage', () => {
  const mockPush = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    })
  })

  it('renders the settings page correctly', () => {
    render(<SettingsPage />)

    // Check page title and description
    expect(screen.getByText('Settings')).toBeInTheDocument()
    expect(screen.getByText('Manage your account settings and preferences')).toBeInTheDocument()

    // Check back button
    const backButton = screen.getByRole('button', { name: /back to home/i })
    expect(backButton).toBeInTheDocument()

    // Check that ProviderKeyManager is rendered
    expect(screen.getByTestId('provider-key-manager')).toBeInTheDocument()
  })

  it('has correct page structure and styling', () => {
    render(<SettingsPage />)

    // Check that the page has dark theme classes
    const pageContainer = screen.getByText('Settings').closest('div.bg-gray-950')
    expect(pageContainer).toHaveClass('bg-gray-950')
    expect(pageContainer).toHaveClass('text-gray-50')
    expect(pageContainer).toHaveClass('min-h-screen')

    // Check container max width
    const contentContainer = screen.getByText('Settings').closest('div.container')
    expect(contentContainer).toHaveClass('container')
    expect(contentContainer).toHaveClass('mx-auto')
    expect(contentContainer).toHaveClass('max-w-5xl')
    expect(contentContainer).toHaveClass('py-8')
  })

  it('renders back to home link correctly', () => {
    render(<SettingsPage />)

    const backLink = screen.getByRole('link', { name: /back to home/i })
    expect(backLink).toHaveAttribute('href', '/')
    
    // Check that it contains the arrow icon
    const backButton = screen.getByRole('button', { name: /back to home/i })
    expect(backButton).toHaveClass('mb-4')
  })
})