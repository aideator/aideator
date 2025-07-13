import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProviderKeyManager } from '@/components/provider-keys/provider-key-manager'
import { ProviderAPIKey } from '@/lib/types'
import { apiClient } from '@/lib/api'

// Mock the child components
jest.mock('@/components/provider-keys/provider-key-card', () => ({
  ProviderKeyCard: ({ providerKey, onEdit, onDelete, onRefresh }: any) => (
    <div data-testid={`key-card-${providerKey.id}`}>
      <div>{providerKey.name || `${providerKey.provider} API Key`}</div>
      <button onClick={() => onEdit(providerKey)}>Edit</button>
      <button onClick={() => onDelete(providerKey)}>Delete</button>
      <button onClick={onRefresh}>Refresh</button>
    </div>
  ),
}))

jest.mock('@/components/provider-keys/provider-key-form', () => ({
  ProviderKeyForm: ({ providerKey, onSubmit, onCancel }: any) => (
    <div data-testid="provider-key-form">
      <div>{providerKey ? 'Edit Form' : 'Create Form'}</div>
      <button 
        onClick={() => onSubmit(providerKey ? { name: 'Updated' } : { provider: 'openai', api_key: 'sk-123' })}
      >
        Submit
      </button>
      <button onClick={onCancel}>Cancel</button>
    </div>
  ),
}))

describe('ProviderKeyManager', () => {
  const mockKeys: ProviderAPIKey[] = [
    {
      id: 'provkey_1',
      user_id: 'user_123',
      provider: 'openai',
      model_name: undefined,
      key_hint: '...abc123',
      name: 'Production Key',
      description: 'Main production key',
      is_active: true,
      is_valid: true,
      last_validated_at: '2024-01-15T10:00:00Z',
      last_used_at: '2024-01-15T12:00:00Z',
      last_error: undefined,
      total_requests: 150,
      total_tokens: 50000,
      total_cost_usd: 2.5,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
      expires_at: undefined,
    },
    {
      id: 'provkey_2',
      user_id: 'user_123',
      provider: 'anthropic',
      model_name: 'claude-3-opus',
      key_hint: '...xyz789',
      name: 'Claude Key',
      description: 'For Claude models',
      is_active: true,
      is_valid: true,
      last_validated_at: '2024-01-14T10:00:00Z',
      last_used_at: '2024-01-14T12:00:00Z',
      last_error: undefined,
      total_requests: 75,
      total_tokens: 25000,
      total_cost_usd: 1.2,
      created_at: '2024-01-02T00:00:00Z',
      updated_at: '2024-01-14T10:00:00Z',
      expires_at: undefined,
    },
  ]

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('loads and displays API keys on mount', async () => {
    jest.spyOn(apiClient, 'getProviderKeys').mockResolvedValue(mockKeys)

    const { container } = render(<ProviderKeyManager />)

    // Should show loading state initially (loading spinner)
    expect(container.querySelector('.animate-spin')).toBeInTheDocument()

    await waitFor(() => {
      expect(apiClient.getProviderKeys).toHaveBeenCalled()
      expect(screen.getByText('API Keys')).toBeInTheDocument()
      expect(screen.getByText('Manage your provider API keys for AI models')).toBeInTheDocument()
    })

    // Should display all keys
    expect(screen.getByTestId('key-card-provkey_1')).toBeInTheDocument()
    expect(screen.getByTestId('key-card-provkey_2')).toBeInTheDocument()
    expect(screen.getByText('Production Key')).toBeInTheDocument()
    expect(screen.getByText('Claude Key')).toBeInTheDocument()
  })

  it('shows empty state when no keys exist', async () => {
    jest.spyOn(apiClient, 'getProviderKeys').mockResolvedValue([])

    render(<ProviderKeyManager />)

    await waitFor(() => {
      expect(screen.getByText('No API keys configured')).toBeInTheDocument()
      expect(screen.getByText('Add your provider API keys to start using AI models')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /add your first api key/i })).toBeInTheDocument()
    })
  })

  it('handles loading error gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
    jest.spyOn(apiClient, 'getProviderKeys').mockRejectedValue(new Error('Network error'))

    render(<ProviderKeyManager />)

    await waitFor(() => {
      expect(screen.getByText('Failed to load API keys')).toBeInTheDocument()
      expect(consoleSpy).toHaveBeenCalledWith('Failed to load keys:', expect.any(Error))
    })

    consoleSpy.mockRestore()
  })

  it('opens create form when Add API Key button is clicked', async () => {
    jest.spyOn(apiClient, 'getProviderKeys').mockResolvedValue(mockKeys)

    render(<ProviderKeyManager />)

    await waitFor(() => {
      expect(screen.getByText('API Keys')).toBeInTheDocument()
    })

    const addButtons = screen.getAllByRole('button', { name: /add api key/i })
    fireEvent.click(addButtons[0])

    expect(screen.getByTestId('provider-key-form')).toBeInTheDocument()
    expect(screen.getByText('Create Form')).toBeInTheDocument()
    expect(screen.getAllByText('Add API Key').length).toBeGreaterThan(0)
  })

  it('opens create form from empty state', async () => {
    jest.spyOn(apiClient, 'getProviderKeys').mockResolvedValue([])

    render(<ProviderKeyManager />)

    await waitFor(() => {
      expect(screen.getByText('No API keys configured')).toBeInTheDocument()
    })

    const addButton = screen.getByRole('button', { name: /add your first api key/i })
    fireEvent.click(addButton)

    expect(screen.getByTestId('provider-key-form')).toBeInTheDocument()
    expect(screen.getByText('Create Form')).toBeInTheDocument()
  })

  it('handles creating a new key', async () => {
    jest.spyOn(apiClient, 'getProviderKeys')
      .mockResolvedValueOnce(mockKeys)
      .mockResolvedValueOnce([...mockKeys, { id: 'provkey_3', provider: 'openai' } as any])
    jest.spyOn(apiClient, 'createProviderKey').mockResolvedValue({ id: 'provkey_3' } as any)

    render(<ProviderKeyManager />)

    await waitFor(() => {
      expect(screen.getByText('API Keys')).toBeInTheDocument()
    })

    // Open form - click the main Add API Key button
    const addButtons = screen.getAllByRole('button', { name: /add api key/i })
    fireEvent.click(addButtons[0])

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: 'Submit' }))

    await waitFor(() => {
      expect(apiClient.createProviderKey).toHaveBeenCalledWith({
        provider: 'openai',
        api_key: 'sk-123',
      })
      expect(apiClient.getProviderKeys).toHaveBeenCalledTimes(2) // Initial load + refresh
    })

    // Form should close
    expect(screen.queryByTestId('provider-key-form')).not.toBeInTheDocument()
  })

  it('opens edit form when edit button is clicked', async () => {
    jest.spyOn(apiClient, 'getProviderKeys').mockResolvedValue(mockKeys)

    render(<ProviderKeyManager />)

    await waitFor(() => {
      expect(screen.getByText('API Keys')).toBeInTheDocument()
    })

    // Click edit on first key
    const editButtons = screen.getAllByRole('button', { name: 'Edit' })
    fireEvent.click(editButtons[0])

    expect(screen.getByTestId('provider-key-form')).toBeInTheDocument()
    expect(screen.getByText('Edit Form')).toBeInTheDocument()
    expect(screen.getByText('Edit API Key')).toBeInTheDocument()
  })

  it('handles updating an existing key', async () => {
    jest.spyOn(apiClient, 'getProviderKeys')
      .mockResolvedValueOnce(mockKeys)
      .mockResolvedValueOnce(mockKeys.map(k => k.id === 'provkey_1' ? { ...k, name: 'Updated' } : k))
    jest.spyOn(apiClient, 'updateProviderKey').mockResolvedValue({ id: 'provkey_1' } as any)

    render(<ProviderKeyManager />)

    await waitFor(() => {
      expect(screen.getByText('API Keys')).toBeInTheDocument()
    })

    // Click edit on first key
    const editButtons = screen.getAllByRole('button', { name: 'Edit' })
    fireEvent.click(editButtons[0])

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: 'Submit' }))

    await waitFor(() => {
      expect(apiClient.updateProviderKey).toHaveBeenCalledWith('provkey_1', { name: 'Updated' })
      expect(apiClient.getProviderKeys).toHaveBeenCalledTimes(2)
    })

    // Form should close
    expect(screen.queryByTestId('provider-key-form')).not.toBeInTheDocument()
  })

  it('handles deleting a key', async () => {
    jest.spyOn(apiClient, 'getProviderKeys').mockResolvedValue(mockKeys)

    render(<ProviderKeyManager />)

    await waitFor(() => {
      expect(screen.getByText('API Keys')).toBeInTheDocument()
    })

    // Initially should have 2 keys
    expect(screen.getByTestId('key-card-provkey_1')).toBeInTheDocument()
    expect(screen.getByTestId('key-card-provkey_2')).toBeInTheDocument()

    // Click delete on first key
    const deleteButtons = screen.getAllByRole('button', { name: 'Delete' })
    fireEvent.click(deleteButtons[0])

    // Key should be removed from list immediately
    expect(screen.queryByTestId('key-card-provkey_1')).not.toBeInTheDocument()
    expect(screen.getByTestId('key-card-provkey_2')).toBeInTheDocument()
  })

  it('refreshes keys when refresh is triggered', async () => {
    jest.spyOn(apiClient, 'getProviderKeys')
      .mockResolvedValueOnce(mockKeys)
      .mockResolvedValueOnce([...mockKeys, { id: 'provkey_3', provider: 'google' } as any])

    render(<ProviderKeyManager />)

    await waitFor(() => {
      expect(screen.getByText('API Keys')).toBeInTheDocument()
    })

    // Click refresh on first key
    const refreshButtons = screen.getAllByRole('button', { name: 'Refresh' })
    fireEvent.click(refreshButtons[0])

    await waitFor(() => {
      expect(apiClient.getProviderKeys).toHaveBeenCalledTimes(2)
    })
  })

  it('closes form when cancel is clicked', async () => {
    jest.spyOn(apiClient, 'getProviderKeys').mockResolvedValue(mockKeys)

    render(<ProviderKeyManager />)

    await waitFor(() => {
      expect(screen.getByText('API Keys')).toBeInTheDocument()
    })

    // Open form - click the main Add API Key button
    const addButtons = screen.getAllByRole('button', { name: /add api key/i })
    fireEvent.click(addButtons[0])
    expect(screen.getByTestId('provider-key-form')).toBeInTheDocument()

    // Cancel form
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    // Form should close
    expect(screen.queryByTestId('provider-key-form')).not.toBeInTheDocument()
  })

  it.skip('handles form submission errors', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
    jest.spyOn(apiClient, 'getProviderKeys').mockResolvedValue(mockKeys)
    jest.spyOn(apiClient, 'createProviderKey').mockRejectedValue(new Error('API Error'))

    render(<ProviderKeyManager />)

    await waitFor(() => {
      expect(screen.getByText('API Keys')).toBeInTheDocument()
    })

    // Open form - click the main Add API Key button
    const addButtons = screen.getAllByRole('button', { name: /add api key/i })
    fireEvent.click(addButtons[0])

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: 'Submit' }))

    await waitFor(() => {
      expect(apiClient.createProviderKey).toHaveBeenCalled()
    })

    // Form should remain open on error
    expect(screen.getByTestId('provider-key-form')).toBeInTheDocument()
    
    consoleSpy.mockRestore()
  })

  it('displays keys in a responsive grid', async () => {
    jest.spyOn(apiClient, 'getProviderKeys').mockResolvedValue(mockKeys)

    render(<ProviderKeyManager />)

    await waitFor(() => {
      expect(screen.getByText('API Keys')).toBeInTheDocument()
    })

    // Check that grid container has correct classes
    const keyCards = screen.getAllByTestId(/key-card-/)
    const gridContainer = keyCards[0].parentElement

    expect(gridContainer).toHaveClass('grid')
  })
})