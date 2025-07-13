import { apiClient, WebSocketClient } from '@/lib/api'
import { SessionCreate, CreateRunRequest } from '@/lib/types'

// Set test environment variables
const TEST_API_URL = process.env.TEST_API_URL || 'http://localhost:8000'
const TEST_WS_URL = process.env.TEST_WS_URL || 'ws://localhost:8000'

// Mock fetch
const mockFetch = jest.fn()
global.fetch = mockFetch

// Mock WebSocket
const mockWebSocket = {
  send: jest.fn(),
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  onmessage: null as ((event: MessageEvent) => void) | null,
  onerror: null as ((event: Event) => void) | null,
  readyState: WebSocket.OPEN,
}

global.WebSocket = jest.fn().mockImplementation(() => mockWebSocket) as any
// Add static constants
Object.assign(global.WebSocket, {
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3,
})

describe('APIClient', () => {
  beforeEach(() => {
    mockFetch.mockClear()
    jest.clearAllMocks()
    
    // Reset auth token to avoid auto-auth calls
    apiClient.setAuthToken('')
  })

  describe('Sessions API', () => {
    it('should fetch sessions with default parameters', async () => {
      const mockResponse = {
        sessions: [
          {
            id: 'session-1',
            user_id: 'user-1',
            title: 'Test Session',
            is_active: true,
            is_archived: false,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
            last_activity_at: '2024-01-01T00:00:00Z',
            models_used: ['gpt-4'],
            total_turns: 1,
            total_cost: 0.05,
          },
        ],
        total: 1,
        limit: 100,
        offset: 0,
      }

      // Mock both auth request and actual request
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ access_token: 'test-token', api_key: 'test-key' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        })

      const result = await apiClient.getSessions()

      expect(mockFetch).toHaveBeenCalledWith(
`${TEST_API_URL}/api/v1/sessions`,
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should create a new session', async () => {
      const sessionData: SessionCreate = {
        title: 'New Session',
        description: 'Test session',
        models_used: ['gpt-4', 'claude-3'],
      }

      const mockResponse = {
        id: 'session-123',
        user_id: 'user-1',
        ...sessionData,
        is_active: true,
        is_archived: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        last_activity_at: '2024-01-01T00:00:00Z',
        total_turns: 0,
        total_cost: 0,
      }

      // Mock both auth request and actual request  
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ access_token: 'test-token', api_key: 'test-key' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        })

      const result = await apiClient.createSession(sessionData)

      expect(mockFetch).toHaveBeenCalledWith(
`${TEST_API_URL}/api/v1/sessions`,
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(sessionData),
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should handle API errors', async () => {
      const errorResponse = {
        detail: 'Session not found',
      }

      // Mock dev credentials failure (auto-auth attempt) and then the actual API call
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 401,
          statusText: 'Unauthorized',
          json: async () => ({ detail: 'Failed to get development credentials' }),
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 404,
          statusText: 'Not Found',
          json: async () => errorResponse,
        })

      await expect(apiClient.getSession('invalid-id')).rejects.toHaveProperty('detail', 'Session not found')
    })
  })

  describe('Runs API', () => {
    it('should create a new run', async () => {
      const runRequest: CreateRunRequest = {
        github_url: 'https://github.com/test/repo',
        prompt: 'Test prompt',
        model_variants: [
          {
            model_definition_id: 'gpt-4',
            model_parameters: { temperature: 0.7 },
          },
        ],
        agent_mode: 'litellm',
      }

      const mockResponse = {
        run_id: 'run-123',
websocket_url: `${TEST_WS_URL}/ws/runs/run-123`,
        polling_url: '/api/v1/runs/run-123/outputs',
        status: 'accepted',
        estimated_duration_seconds: 120,
        session_id: 'session-123',
        turn_id: 'turn-123',
      }

      // Mock both auth request and actual request
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ access_token: 'test-token', api_key: 'test-key' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        })

      const result = await apiClient.createRun(runRequest)

      expect(mockFetch).toHaveBeenCalledWith(
`${TEST_API_URL}/api/v1/runs`,
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(runRequest),
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should get run outputs with filters', async () => {
      const mockOutputs = [
        {
          id: 1,
          run_id: 'run-123',
          variation_id: 0,
          content: 'Test output',
          timestamp: '2024-01-01T00:00:00Z',
          output_type: 'llm' as const,
        },
      ]

      // Mock both auth request and actual request
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ access_token: 'test-token', api_key: 'test-key' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockOutputs,
        })

      const result = await apiClient.getRunOutputs('run-123', {
        variation_id: 0,
        output_type: 'llm',
        limit: 10,
      })

      expect(mockFetch).toHaveBeenCalledWith(
`${TEST_API_URL}/api/v1/runs/run-123/outputs?variation_id=0&output_type=llm&limit=10`,
        expect.any(Object)
      )
      expect(result).toEqual(mockOutputs)
    })
  })

  describe('Authentication', () => {
    it('should include auth token in requests when set', async () => {
      const token = 'test-token'
      apiClient.setAuthToken(token)

      // Set the token first so no auth call is made
      apiClient.setAuthToken(token)
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ sessions: [], total: 0, limit: 100, offset: 0 }),
      })

      await apiClient.getSessions()

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': `Bearer ${token}`,
          }),
        })
      )
    })

    it('should handle dev login endpoint successfully', async () => {
      const mockDevLoginResponse = {
        user: {
          id: 'user_test_abc123',
          email: 'test@aideator.local',
          full_name: 'Test User',
          company: 'AIdeator Development',
        },
        access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
        token_type: 'bearer',
        api_key: 'aid_sk_test_1234567890abcdef...',
        message: 'Development test user login successful',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockDevLoginResponse,
      })

      // Make direct fetch call since this endpoint isn't in the APIClient yet
      const response = await fetch(`${TEST_API_URL}/api/v1/auth/dev/test-login`)
      const result = await response.json()

      expect(mockFetch).toHaveBeenCalledWith(`${TEST_API_URL}/api/v1/auth/dev/test-login`)
      expect(result).toEqual(mockDevLoginResponse)
      expect(result.user).toHaveProperty('id')
      expect(result.user).toHaveProperty('email', 'test@aideator.local')
      expect(result).toHaveProperty('access_token')
      expect(result).toHaveProperty('api_key')
      expect(result).toHaveProperty('message')
    })
  })
})

describe('WebSocketClient', () => {
  let wsClient: WebSocketClient
  let mockCallbacks: {
    onMessage: jest.Mock
    onError: jest.Mock
    onClose: jest.Mock
  }

  beforeEach(() => {
wsClient = new WebSocketClient(`${TEST_WS_URL}/ws/runs/test`)
    mockCallbacks = {
      onMessage: jest.fn(),
      onError: jest.fn(),
      onClose: jest.fn(),
    }
    jest.clearAllMocks()
  })

  it('should establish WebSocket connection', () => {
    wsClient.connect(mockCallbacks)

expect(WebSocket).toHaveBeenCalledWith(`${TEST_WS_URL}/ws/runs/test`)
  })

  it('should handle incoming messages', () => {
    wsClient.connect(mockCallbacks)

    const mockMessage = {
      type: 'llm',
      message_id: 'msg-1',
      data: {
        run_id: 'run-123',
        variation_id: '0',
        content: 'Hello world',
        timestamp: '2024-01-01T00:00:00Z',
      },
    }

    // Simulate onmessage event
    const messageEvent = new MessageEvent('message', {
      data: JSON.stringify(mockMessage),
    })

    // Trigger the onmessage handler
    if (mockWebSocket.onmessage) {
      mockWebSocket.onmessage(messageEvent)
    }

    expect(mockCallbacks.onMessage).toHaveBeenCalledWith(mockMessage)
  })

  it('should send control messages', () => {
    wsClient.connect(mockCallbacks)

    const controlMessage = {
      control: 'ping',
      data: {},
    }

    wsClient.send(controlMessage)

    expect(mockWebSocket.send).toHaveBeenCalledWith(JSON.stringify(controlMessage))
  })

  it('should handle connection errors gracefully', () => {
    wsClient.connect(mockCallbacks)

    const errorEvent = new Event('error')
    if (mockWebSocket.onerror) {
      mockWebSocket.onerror(errorEvent)
    }

    expect(mockCallbacks.onError).toHaveBeenCalledWith(errorEvent)
  })

  it('should close connection properly', () => {
    wsClient.connect(mockCallbacks)
    wsClient.close()

    expect(mockWebSocket.close).toHaveBeenCalled()
  })
})