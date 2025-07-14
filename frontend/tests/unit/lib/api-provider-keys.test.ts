import { apiClient } from '@/lib/api'
import { ProviderAPIKey, ProviderAPIKeyCreate, ProviderAPIKeyUpdate, Provider } from '@/lib/types'

// Mock fetch
const mockFetch = jest.fn()
global.fetch = mockFetch

describe('API Client - Provider Key Methods', () => {
  const mockProviders: Provider[] = [
    { name: 'openai', display_name: 'OpenAI', requires_api_key: true },
    { name: 'anthropic', display_name: 'Anthropic', requires_api_key: true },
  ]

  const mockProviderKey: ProviderAPIKey = {
    id: 'provkey_123',
    user_id: 'user_123',
    provider: 'openai',
    model_name: undefined,
    key_hint: '...abc123',
    name: 'Production Key',
    description: 'Main API key',
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

  beforeEach(() => {
    mockFetch.mockClear()
    jest.clearAllMocks()
    
    // Set a dummy auth token to prevent auto-auth calls
    apiClient.setAuthToken('test-token')
  })

  describe('getProviders', () => {
    it('fetches list of providers', async () => {
      // Mock only the actual API call
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ providers: mockProviders }),
      })

      const result = await apiClient.getProviders()

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/provider-keys/providers/list'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token',
          }),
        })
      )
      expect(result).toEqual(mockProviders)
    })

    it('handles provider fetch error', async () => {
      const errorData = { detail: 'Server error' }
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error',
        json: async () => errorData,
        text: async () => JSON.stringify(errorData),
      })

      await expect(apiClient.getProviders()).rejects.toEqual({
        detail: 'Server error',
      })
    })
  })

  describe('getProviderKeys', () => {
    it('fetches user provider keys', async () => {
      const mockKeys = [mockProviderKey]
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockKeys,
      })

      const result = await apiClient.getProviderKeys()

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/provider-keys/'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token',
          }),
        })
      )
      expect(result).toEqual(mockKeys)
    })
  })

  describe('createProviderKey', () => {
    it('creates a new provider key', async () => {
      const newKey: ProviderAPIKeyCreate = {
        provider: 'openai',
        api_key: 'sk-test123456789',
        name: 'Test Key',
        description: 'Test description',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProviderKey,
      })

      const result = await apiClient.createProviderKey(newKey)

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/provider-keys/'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(newKey),
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token',
          }),
        })
      )
      expect(result).toEqual(mockProviderKey)
    })

    it('handles create error with validation details', async () => {
      const newKey: ProviderAPIKeyCreate = {
        provider: 'openai',
        api_key: 'invalid-key',
      }

      const errorData = { 
        detail: { 
          message: 'Invalid API key format',
          suggestion: 'OpenAI keys should start with sk-'
        } 
      }
      
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Bad Request',
        json: async () => errorData.detail,
        text: async () => JSON.stringify(errorData),
      })

      await expect(apiClient.createProviderKey(newKey)).rejects.toEqual({
        detail: 'Invalid API key format',
      })
    })
  })

  describe('updateProviderKey', () => {
    it('updates an existing provider key', async () => {
      const updates: ProviderAPIKeyUpdate = {
        name: 'Updated Name',
        description: 'Updated description',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...mockProviderKey, ...updates }),
      })

      const result = await apiClient.updateProviderKey('provkey_123', updates)

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/provider-keys/provkey_123'),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updates),
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token',
          }),
        })
      )
      expect(result.name).toBe('Updated Name')
      expect(result.description).toBe('Updated description')
    })
  })

  describe('deleteProviderKey', () => {
    it('deletes a provider key', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      })

      await apiClient.deleteProviderKey('provkey_123')

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/provider-keys/provkey_123'),
        expect.objectContaining({
          method: 'DELETE',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token',
          }),
        })
      )
    })

    it('handles delete error', async () => {
      const errorData = { detail: 'Cannot delete active key' }
      
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Forbidden',
        json: async () => errorData,
        text: async () => JSON.stringify(errorData),
      })

      await expect(apiClient.deleteProviderKey('provkey_123')).rejects.toEqual({
        detail: 'Cannot delete active key',
      })
    })
  })

  describe('validateProviderKey', () => {
    it('validates a provider key successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ valid: true }),
      })

      const result = await apiClient.validateProviderKey('provkey_123')

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/provider-keys/provkey_123/validate'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token',
          }),
        })
      )
      expect(result).toEqual({ valid: true })
    })

    it('handles validation failure', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ valid: false, error: 'Invalid API key' }),
      })

      const result = await apiClient.validateProviderKey('provkey_123')

      expect(result).toEqual({ valid: false, error: 'Invalid API key' })
    })

    it('handles validation request error', async () => {
      const errorData = { detail: 'Provider service unavailable' }
      
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Service Unavailable',
        json: async () => errorData,
        text: async () => JSON.stringify(errorData),
      })

      await expect(apiClient.validateProviderKey('provkey_123')).rejects.toEqual({
        detail: 'Provider service unavailable',
      })
    })
  })

  describe('Authentication handling', () => {
    it('automatically authenticates when making provider key requests', async () => {
      // Reset auth state
      apiClient.setAuthToken('')
      apiClient.setApiKey('')

      // Mock auth call then the actual API call
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ access_token: 'new-token', api_key: 'new-api-key' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [mockProviderKey],
        })

      await apiClient.getProviderKeys()

      // Should have called auth endpoint first
      const authCall = mockFetch.mock.calls.find(call => 
        call[0].includes('/auth/dev/test-login')
      )
      expect(authCall).toBeDefined()

      // Then called provider keys with auth header
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/provider-keys/'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer new-token',
            'X-API-Key': 'new-api-key',
          }),
        })
      )
    })
  })
})