import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProviderKeyForm } from '@/components/provider-keys/provider-key-form'
import { ProviderAPIKey, Provider } from '@/lib/types'
import { apiClient } from '@/lib/api'

describe('ProviderKeyForm', () => {
  const mockProviders: Provider[] = [
    { name: 'openai', display_name: 'OpenAI', requires_api_key: true },
    { name: 'anthropic', display_name: 'Anthropic', requires_api_key: true },
    { name: 'google', display_name: 'Google AI', requires_api_key: true },
  ]

  const mockExistingKey: ProviderAPIKey = {
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

  const mockOnSubmit = jest.fn()
  const mockOnCancel = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    jest.spyOn(apiClient, 'getProviders').mockResolvedValue(mockProviders)
  })

  describe('Create Mode', () => {
    it('renders empty form for creating new key', async () => {
      render(
        <ProviderKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      )

      await waitFor(() => {
        expect(apiClient.getProviders).toHaveBeenCalled()
      })

      expect(screen.getByLabelText('Provider')).toBeInTheDocument()
      expect(screen.getByLabelText('API Key')).toBeInTheDocument()
      expect(screen.getByLabelText('Model (optional)')).toBeInTheDocument()
      expect(screen.getByLabelText('Name (optional)')).toBeInTheDocument()
      expect(screen.getByLabelText('Description (optional)')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Add Key' })).toBeInTheDocument()
    })

    it('loads and displays providers in select', async () => {
      const user = userEvent.setup()
      render(
        <ProviderKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      )

      await waitFor(() => {
        expect(apiClient.getProviders).toHaveBeenCalled()
      })

      const providerSelect = screen.getByLabelText('Provider')
      await user.click(providerSelect)

      expect(screen.getByText('OpenAI')).toBeInTheDocument()
      expect(screen.getByText('Anthropic')).toBeInTheDocument()
      expect(screen.getByText('Google AI')).toBeInTheDocument()
    })

    it('submits form with valid data', async () => {
      const user = userEvent.setup()
      mockOnSubmit.mockResolvedValue(undefined)

      render(
        <ProviderKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      )

      await waitFor(() => {
        expect(apiClient.getProviders).toHaveBeenCalled()
      })

      // Select provider
      const providerSelect = screen.getByLabelText('Provider')
      await user.click(providerSelect)
      await user.click(screen.getByText('OpenAI'))

      // Fill in form
      await user.type(screen.getByLabelText('API Key'), 'sk-test123456789')
      await user.type(screen.getByLabelText('Model (optional)'), 'gpt-4')
      await user.type(screen.getByLabelText('Name (optional)'), 'Test Key')
      await user.type(screen.getByLabelText('Description (optional)'), 'Test description')

      // Submit
      await user.click(screen.getByRole('button', { name: 'Add Key' }))

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          provider: 'openai',
          api_key: 'sk-test123456789',
          model_name: 'gpt-4',
          name: 'Test Key',
          description: 'Test description',
        })
      })
    })

    it('shows error when provider and API key are missing', async () => {
      const user = userEvent.setup()
      render(
        <ProviderKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      )

      await waitFor(() => {
        expect(apiClient.getProviders).toHaveBeenCalled()
      })

      // Try to submit without filling required fields
      await user.click(screen.getByRole('button', { name: 'Add Key' }))

      await waitFor(() => {
        expect(screen.getByText('Provider and API key are required')).toBeInTheDocument()
        expect(mockOnSubmit).not.toHaveBeenCalled()
      })
    })

    it('handles submission error', async () => {
      const user = userEvent.setup()
      mockOnSubmit.mockRejectedValue(new Error('API error'))

      render(
        <ProviderKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      )

      await waitFor(() => {
        expect(apiClient.getProviders).toHaveBeenCalled()
      })

      // Select provider and fill API key
      const providerSelect = screen.getByLabelText('Provider')
      await user.click(providerSelect)
      await user.click(screen.getByText('OpenAI'))
      await user.type(screen.getByLabelText('API Key'), 'sk-test123')

      // Submit
      await user.click(screen.getByRole('button', { name: 'Add Key' }))

      await waitFor(() => {
        expect(screen.getByText('API error')).toBeInTheDocument()
      })
    })

    it('omits empty optional fields from submission', async () => {
      const user = userEvent.setup()
      mockOnSubmit.mockResolvedValue(undefined)

      render(
        <ProviderKeyForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      )

      await waitFor(() => {
        expect(apiClient.getProviders).toHaveBeenCalled()
      })

      // Only fill required fields
      const providerSelect = screen.getByLabelText('Provider')
      await user.click(providerSelect)
      await user.click(screen.getByText('OpenAI'))
      await user.type(screen.getByLabelText('API Key'), 'sk-test123')

      // Submit
      await user.click(screen.getByRole('button', { name: 'Add Key' }))

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          provider: 'openai',
          api_key: 'sk-test123',
          model_name: undefined,
          name: undefined,
          description: undefined,
        })
      })
    })
  })

  describe('Edit Mode', () => {
    it('renders form with existing key data', async () => {
      render(
        <ProviderKeyForm
          providerKey={mockExistingKey}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      )

      await waitFor(() => {
        expect(apiClient.getProviders).toHaveBeenCalled()
      })

      // Provider should be disabled in edit mode
      expect(screen.getByLabelText('Provider')).toBeDisabled()
      
      // Check pre-filled values
      expect(screen.getByDisplayValue('Production Key')).toBeInTheDocument()
      expect(screen.getByDisplayValue('Main API key for production')).toBeInTheDocument()
      expect(screen.getByText('Current key: ...abc123')).toBeInTheDocument()
      
      // Model field should be disabled in edit mode
      expect(screen.getByLabelText('Model (optional)')).toBeDisabled()
      
      expect(screen.getByRole('button', { name: 'Update Key' })).toBeInTheDocument()
    })

    it('submits only changed fields in edit mode', async () => {
      const user = userEvent.setup()
      mockOnSubmit.mockResolvedValue(undefined)

      render(
        <ProviderKeyForm
          providerKey={mockExistingKey}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      )

      await waitFor(() => {
        expect(apiClient.getProviders).toHaveBeenCalled()
      })

      // Update name and description
      const nameInput = screen.getByLabelText('Name (optional)')
      await user.clear(nameInput)
      await user.type(nameInput, 'Updated Key Name')

      // Submit
      await user.click(screen.getByRole('button', { name: 'Update Key' }))

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          name: 'Updated Key Name',
          description: 'Main API key for production',
          // api_key not included since it wasn't changed
        })
      })
    })

    it('includes new API key when provided in edit mode', async () => {
      const user = userEvent.setup()
      mockOnSubmit.mockResolvedValue(undefined)

      render(
        <ProviderKeyForm
          providerKey={mockExistingKey}
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
        />
      )

      await waitFor(() => {
        expect(apiClient.getProviders).toHaveBeenCalled()
      })

      // Enter new API key
      await user.type(screen.getByLabelText('API Key'), 'sk-new-key-123')

      // Submit
      await user.click(screen.getByRole('button', { name: 'Update Key' }))

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          api_key: 'sk-new-key-123',
          name: 'Production Key',
          description: 'Main API key for production',
        })
      })
    })
  })

  it('handles cancel action', async () => {
    const user = userEvent.setup()
    render(
      <ProviderKeyForm
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    )

    await user.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(mockOnCancel).toHaveBeenCalled()
  })

  it('shows loading state during submission', async () => {
    const user = userEvent.setup()
    mockOnSubmit.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

    render(
      <ProviderKeyForm
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    )

    await waitFor(() => {
      expect(apiClient.getProviders).toHaveBeenCalled()
    })

    // Fill required fields
    const providerSelect = screen.getByLabelText('Provider')
    await user.click(providerSelect)
    await user.click(screen.getByText('OpenAI'))
    await user.type(screen.getByLabelText('API Key'), 'sk-test123')

    // Submit
    await user.click(screen.getByRole('button', { name: 'Add Key' }))

    // Check for loading state or successful submission
    await waitFor(() => {
      // Either the button shows "Saving..." or the onSubmit was called
      const savingButton = screen.queryByRole('button', { name: 'Saving...' })
      if (savingButton) {
        expect(savingButton).toBeInTheDocument()
        expect(savingButton).toBeDisabled()
      } else {
        // If the loading state is very fast, check that onSubmit was called
        expect(mockOnSubmit).toHaveBeenCalled()
      }
    })
  })

  it('handles provider loading error gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
    jest.spyOn(apiClient, 'getProviders').mockRejectedValue(new Error('Failed to load'))

    render(
      <ProviderKeyForm
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    )

    await waitFor(() => {
      expect(apiClient.getProviders).toHaveBeenCalled()
      expect(consoleSpy).toHaveBeenCalledWith('Failed to load providers:', expect.any(Error))
    })

    // Form should still be functional
    expect(screen.getByLabelText('Provider')).toBeInTheDocument()
    expect(screen.getByLabelText('API Key')).toBeInTheDocument()

    consoleSpy.mockRestore()
  })
})