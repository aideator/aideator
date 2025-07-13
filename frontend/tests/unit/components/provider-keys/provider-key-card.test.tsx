import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ProviderKeyCard } from '@/components/provider-keys/provider-key-card'
import { ProviderAPIKey } from '@/lib/types'
import { apiClient } from '@/lib/api'

describe('ProviderKeyCard', () => {
  const mockKey: ProviderAPIKey = {
    id: 'provkey_123',
    user_id: 'user_123',
    provider: 'openai',
    model_name: 'gpt-4',
    key_hint: '...abc123',
    name: 'Production Key',
    description: 'Main API key for production',
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
  }

  const mockOnEdit = jest.fn()
  const mockOnDelete = jest.fn()
  const mockOnRefresh = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    // Reset window.confirm mock
    global.confirm = jest.fn(() => true)
  })

  it('renders provider key information correctly', () => {
    render(
      <ProviderKeyCard
        providerKey={mockKey}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.getByText('Production Key')).toBeInTheDocument()
    expect(screen.getByText('Main API key for production')).toBeInTheDocument()
    expect(screen.getByText('openai')).toBeInTheDocument()
    expect(screen.getByText('gpt-4')).toBeInTheDocument()
    expect(screen.getByText('...abc123')).toBeInTheDocument()
    expect(screen.getByText('150 requests')).toBeInTheDocument()
  })

  it('shows correct status badges', () => {
    render(
      <ProviderKeyCard
        providerKey={mockKey}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.getByText('Active')).toBeInTheDocument()
    expect(screen.getByText('Valid')).toBeInTheDocument()
  })

  it('shows inactive status when key is inactive', () => {
    const inactiveKey = { ...mockKey, is_active: false }
    render(
      <ProviderKeyCard
        providerKey={inactiveKey}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.getByText('Inactive')).toBeInTheDocument()
  })

  it('shows invalid status when key is invalid', () => {
    const invalidKey = { ...mockKey, is_valid: false }
    render(
      <ProviderKeyCard
        providerKey={invalidKey}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.getByText('Invalid')).toBeInTheDocument()
  })

  it('handles validate action', async () => {
    jest.spyOn(apiClient, 'validateProviderKey').mockResolvedValue({ valid: true })

    render(
      <ProviderKeyCard
        providerKey={mockKey}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    )

    const validateButton = screen.getByRole('button', { name: /validate/i })
    fireEvent.click(validateButton)

    expect(screen.getByText('Validating...')).toBeInTheDocument()

    await waitFor(() => {
      expect(apiClient.validateProviderKey).toHaveBeenCalledWith('provkey_123')
      expect(mockOnRefresh).toHaveBeenCalled()
    })
  })

  it('handles validate error gracefully', async () => {
    jest.spyOn(apiClient, 'validateProviderKey').mockRejectedValue(new Error('Validation failed'))
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation()

    render(
      <ProviderKeyCard
        providerKey={mockKey}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    )

    const validateButton = screen.getByRole('button', { name: /validate/i })
    fireEvent.click(validateButton)

    await waitFor(() => {
      expect(apiClient.validateProviderKey).toHaveBeenCalledWith('provkey_123')
      expect(consoleSpy).toHaveBeenCalledWith('Failed to validate key:', expect.any(Error))
    })

    consoleSpy.mockRestore()
  })

  it('handles edit action', () => {
    render(
      <ProviderKeyCard
        providerKey={mockKey}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    )

    const editButton = screen.getByRole('button', { name: /edit/i })
    fireEvent.click(editButton)

    expect(mockOnEdit).toHaveBeenCalledWith(mockKey)
  })

  it('handles delete action with confirmation', async () => {
    jest.spyOn(apiClient, 'deleteProviderKey').mockResolvedValue(undefined)

    render(
      <ProviderKeyCard
        providerKey={mockKey}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    )

    const deleteButton = screen.getByRole('button', { name: /delete/i })
    fireEvent.click(deleteButton)

    expect(global.confirm).toHaveBeenCalledWith('Are you sure you want to delete this API key?')
    expect(screen.getByText('Deleting...')).toBeInTheDocument()

    await waitFor(() => {
      expect(apiClient.deleteProviderKey).toHaveBeenCalledWith('provkey_123')
      expect(mockOnDelete).toHaveBeenCalledWith(mockKey)
    })
  })

  it('cancels delete when user declines confirmation', async () => {
    global.confirm = jest.fn(() => false)

    render(
      <ProviderKeyCard
        providerKey={mockKey}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    )

    const deleteButton = screen.getByRole('button', { name: /delete/i })
    fireEvent.click(deleteButton)

    expect(global.confirm).toHaveBeenCalled()
    expect(apiClient.deleteProviderKey).not.toHaveBeenCalled()
    expect(mockOnDelete).not.toHaveBeenCalled()
  })

  it('handles delete error gracefully', async () => {
    jest.spyOn(apiClient, 'deleteProviderKey').mockRejectedValue(new Error('Delete failed'))
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation()

    render(
      <ProviderKeyCard
        providerKey={mockKey}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    )

    const deleteButton = screen.getByRole('button', { name: /delete/i })
    fireEvent.click(deleteButton)

    await waitFor(() => {
      expect(apiClient.deleteProviderKey).toHaveBeenCalledWith('provkey_123')
      expect(consoleSpy).toHaveBeenCalledWith('Failed to delete key:', expect.any(Error))
      expect(mockOnDelete).not.toHaveBeenCalled()
    })

    consoleSpy.mockRestore()
  })

  it('formats dates correctly', () => {
    render(
      <ProviderKeyCard
        providerKey={mockKey}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    )

    // Check that dates are displayed (format may vary by locale)
    const lastUsedLabel = screen.getByText('Last used:')
    const lastUsedValue = lastUsedLabel.nextSibling
    expect(lastUsedValue).toBeTruthy()
    expect(lastUsedValue?.textContent).toMatch(/\d/)

    const createdLabel = screen.getByText('Created:')
    const createdValue = createdLabel.nextSibling
    expect(createdValue).toBeTruthy()
    expect(createdValue?.textContent).toMatch(/\d/)
  })

  it('shows "Never" for missing dates', () => {
    const keyWithoutDates = { ...mockKey, last_used_at: undefined }
    render(
      <ProviderKeyCard
        providerKey={keyWithoutDates}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.getByText('Never')).toBeInTheDocument()
  })

  it('does not show usage when total_requests is 0', () => {
    const keyWithoutUsage = { ...mockKey, total_requests: 0 }
    render(
      <ProviderKeyCard
        providerKey={keyWithoutUsage}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.queryByText(/requests/)).not.toBeInTheDocument()
  })

  it('uses provider name as title when name is not provided', () => {
    const keyWithoutName = { ...mockKey, name: undefined }
    render(
      <ProviderKeyCard
        providerKey={keyWithoutName}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.getByText('openai API Key')).toBeInTheDocument()
  })

  it('uses default description when description is not provided', () => {
    const keyWithoutDescription = { ...mockKey, description: undefined }
    render(
      <ProviderKeyCard
        providerKey={keyWithoutDescription}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRefresh={mockOnRefresh}
      />
    )

    expect(screen.getByText('API key for openai')).toBeInTheDocument()
  })
})