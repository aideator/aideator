import {
  Session,
  SessionCreate,
  SessionUpdate,
  SessionListResponse,
  Turn,
  TurnCreate,
  Run,
  CreateRunRequest,
  CreateRunResponse,
  AgentOutput,
  Preference,
  PreferenceCreate,
  PaginatedResponse,
  APIError,
  GitHubRepository,
  GitHubBranch,
  ProviderAPIKey,
  ProviderAPIKeyCreate,
  ProviderAPIKeyUpdate,
  Provider,
  CodeRequest,
  CodeResponse,
} from './types'
import { useAuth } from './auth-context'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class APIClient {
  private baseURL: string
  private authToken?: string
  private apiKey?: string

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL
  }

  setAuthToken(token: string) {
    this.authToken = token
  }

  setApiKey(key: string) {
    this.apiKey = key
  }

  getApiKey(): string | undefined {
    return this.apiKey
  }

  // GitHub API methods
  async searchGitHubRepositories(query: string): Promise<GitHubRepository[]> {
    try {
      const response = await fetch(`https://api.github.com/search/repositories?q=${encodeURIComponent(query)}&sort=stars&order=desc&per_page=10`, {
        headers: {
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'AIdeator-Frontend',
        },
      })
      
      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('GitHub API rate limit exceeded. Please try again later.')
        }
        throw new Error(`GitHub API error: ${response.status} ${response.statusText}`)
      }
      
      const data = await response.json()
      return data.items || []
    } catch (error) {
      console.error('Error searching GitHub repositories:', error)
      throw error  // Re-throw to let the UI handle the error properly
    }
  }

  async getGitHubRepositoryBranches(owner: string, repo: string): Promise<GitHubBranch[]> {
    try {
      const response = await fetch(`https://api.github.com/repos/${owner}/${repo}/branches`, {
        headers: {
          'Accept': 'application/vnd.github.v3+json',
        },
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch branches')
      }
      
      const data = await response.json()
      return data || []
    } catch (error) {
      console.error('Error fetching GitHub branches:', error)
      return []
    }
  }

  // Development login for getting auth credentials
  async getDevCredentials(): Promise<{ access_token: string; api_key: string }> {
    const response = await fetch(`${this.baseURL}/api/v1/auth/dev/test-login`)
    if (!response.ok) {
      throw new Error('Failed to get development credentials')
    }
    const data = await response.json()
    return { access_token: data.access_token, api_key: data.api_key }
  }

  async getModelCatalog(): Promise<{ models: any[], providers: any[], capabilities: string[] }> {
    try {
      const response = await this.request<{ models: any[], providers: any[], capabilities: string[] }>('/api/v1/models/catalog')
      return response
    } catch (error) {
      console.error('getModelCatalog: Error occurred', error)
      throw error
    }
  }

  async getModelDefinitions(): Promise<string[]> {
    try {
      // Backend returns a direct array of models, not wrapped in an object
      const response = await this.request<Array<{ id: string; model_name: string; display_name: string; litellm_model_name: string }>>('/api/v1/models/models')
      
      // Add defensive checks
      if (!response) {
        console.error('getModelDefinitions: No response received')
        return []
      }
      
      if (!Array.isArray(response)) {
        console.error('getModelDefinitions: response is not an array', typeof response, response)
        return []
      }
      
      return response.map((model) => {
        if (!model || typeof model !== 'object') {
          console.warn('getModelDefinitions: Invalid model object', model)
          return 'unknown'
        }
        // Use litellm_model_name which is the actual model name to pass to the agent
        return model.litellm_model_name || model.model_name || model.id
      }).filter(id => id !== 'unknown')
    } catch (error) {
      console.error('getModelDefinitions: Error occurred', error)
      throw error
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    // Auto-authenticate if no credentials are set
    if (!this.authToken && !this.apiKey) {
      try {
        const credentials = await this.getDevCredentials()
        this.authToken = credentials.access_token
        this.apiKey = credentials.api_key
      } catch (error) {
        console.error('Failed to get dev credentials:', error)
      }
    }

    const url = `${this.baseURL}${endpoint}`
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    }

    if (this.authToken) {
      headers.Authorization = `Bearer ${this.authToken}`
    }

    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey
    }

    console.log(`🌐 Making request to: ${endpoint}`)
    console.log('📤 Request headers:', {
      ...headers,
      Authorization: headers.Authorization ? `Bearer ${headers.Authorization.substring(7, 27)}...` : 'none',
      'X-API-Key': headers['X-API-Key'] ? `${headers['X-API-Key'].substring(0, 10)}...` : 'none'
    })

    const config: RequestInit = {
      ...options,
      headers,
    }

    const response = await fetch(url, config)
    
    console.log(`📥 Response: ${response.status} ${response.statusText}`)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error(`❌ API Error for ${endpoint}:`, errorText)
      let errorDetail = 'Unknown error'
      
      try {
        const errorData = JSON.parse(errorText)
        // Handle both string and object detail
        if (typeof errorData.detail === 'object' && errorData.detail?.message) {
          errorDetail = errorData.detail.message
        } else {
          errorDetail = errorData.detail || errorData.message || 'Unknown error'
        }
      } catch {
        errorDetail = errorText || 'Unknown error'
      }
      
      const error: APIError = {
        detail: errorDetail
      }
      throw error
    }

    return response.json()
  }

  // Session API
  async getSessions(params: {
    skip?: number
    limit?: number
    active_only?: boolean
    archived_only?: boolean
  } = {}): Promise<SessionListResponse> {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, value.toString())
      }
    })
    const query = searchParams.toString()
    return this.request<SessionListResponse>(`/api/v1/sessions${query ? `?${query}` : ''}`)
  }

  async createSession(session: SessionCreate): Promise<Session> {
    return this.request<Session>('/api/v1/sessions', {
      method: 'POST',
      body: JSON.stringify(session),
    })
  }

  async getSession(sessionId: string): Promise<Session> {
    return this.request<Session>(`/api/v1/sessions/${sessionId}`)
  }

  async updateSession(sessionId: string, updates: SessionUpdate): Promise<Session> {
    return this.request<Session>(`/api/v1/sessions/${sessionId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    })
  }

  async deleteSession(sessionId: string): Promise<void> {
    await this.request(`/api/v1/sessions/${sessionId}`, {
      method: 'DELETE',
    })
  }

  // Turn API
  async getSessionTurns(sessionId: string): Promise<Turn[]> {
    return this.request<Turn[]>(`/api/v1/sessions/${sessionId}/turns`)
  }

  async createTurn(sessionId: string, turn: TurnCreate): Promise<Turn> {
    return this.request<Turn>(`/api/v1/sessions/${sessionId}/turns`, {
      method: 'POST',
      body: JSON.stringify(turn),
    })
  }

  async getTurn(sessionId: string, turnId: string): Promise<Turn> {
    return this.request<Turn>(`/api/v1/sessions/${sessionId}/turns/${turnId}`)
  }

  // Code execution API
  async executeCode(sessionId: string, turnId: string, request: CodeRequest): Promise<CodeResponse> {
    return this.request<CodeResponse>(`/api/v1/sessions/${sessionId}/turns/${turnId}/code`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  // Run API
  async getRuns(params: {
    status?: string
    page?: number
    per_page?: number
  } = {}): Promise<PaginatedResponse<Run>> {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, value.toString())
      }
    })
    const query = searchParams.toString()
    return this.request<PaginatedResponse<Run>>(`/api/v1/runs${query ? `?${query}` : ''}`)
  }

  async getTurnRuns(sessionId: string, turnId: string): Promise<Run[]> {
    return this.request<Run[]>(`/api/v1/sessions/${sessionId}/turns/${turnId}/runs`)
  }

  async createRun(request: CreateRunRequest): Promise<CreateRunResponse> {
    return this.request<CreateRunResponse>('/api/v1/runs', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  async getRun(runId: string): Promise<Run> {
    return this.request<Run>(`/api/v1/runs/${runId}`)
  }

  async getRunOutputs(
    runId: string,
    params: {
      since?: string
      variation_id?: number
      output_type?: string
      limit?: number
    } = {}
  ): Promise<AgentOutput[]> {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, value.toString())
      }
    })
    const query = searchParams.toString()
    return this.request<AgentOutput[]>(`/api/v1/runs/${runId}/outputs${query ? `?${query}` : ''}`)
  }

  async getRunDiffs(
    runId: string,
    params: {
      variation_id?: number
    } = {}
  ): Promise<Array<{ oldFile: { name: string; content: string }; newFile: { name: string; content: string } }>> {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, value.toString())
      }
    })
    const query = searchParams.toString()
    return this.request<Array<{ oldFile: { name: string; content: string }; newFile: { name: string; content: string } }>>(`/api/v1/runs/${runId}/diffs${query ? `?${query}` : ''}`)
  }

  async selectWinner(runId: string, winningVariationId: number): Promise<Run> {
    return this.request<Run>(`/api/v1/runs/${runId}/select`, {
      method: 'POST',
      body: JSON.stringify({ winning_variation_id: winningVariationId }),
    })
  }

  async cancelRun(runId: string): Promise<void> {
    await this.request(`/api/v1/runs/${runId}`, {
      method: 'DELETE',
    })
  }

  // Preference API
  async createPreference(
    sessionId: string,
    turnId: string,
    preference: PreferenceCreate
  ): Promise<Preference> {
    return this.request<Preference>(`/api/v1/sessions/${sessionId}/turns/${turnId}/preferences`, {
      method: 'POST',
      body: JSON.stringify(preference),
    })
  }

  async getSessionPreferences(sessionId: string): Promise<Preference[]> {
    return this.request<Preference[]>(`/api/v1/sessions/${sessionId}/preferences`)
  }

  // Provider API Key management
  async getProviders(): Promise<Provider[]> {
    const response = await this.request<{ providers: Provider[] }>('/api/v1/provider-keys/providers/list')
    return response.providers
  }

  async getProviderKeys(): Promise<ProviderAPIKey[]> {
    return this.request<ProviderAPIKey[]>('/api/v1/provider-keys/')
  }

  async createProviderKey(key: ProviderAPIKeyCreate): Promise<ProviderAPIKey> {
    return this.request<ProviderAPIKey>('/api/v1/provider-keys/', {
      method: 'POST',
      body: JSON.stringify(key),
    })
  }

  async updateProviderKey(keyId: string, updates: ProviderAPIKeyUpdate): Promise<ProviderAPIKey> {
    return this.request<ProviderAPIKey>(`/api/v1/provider-keys/${keyId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    })
  }

  async deleteProviderKey(keyId: string): Promise<void> {
    await this.request(`/api/v1/provider-keys/${keyId}`, {
      method: 'DELETE',
    })
  }

  async validateProviderKey(keyId: string): Promise<{ valid: boolean; error?: string }> {
    return this.request<{ valid: boolean; error?: string }>(
      `/api/v1/provider-keys/${keyId}/validate`,
      {
        method: 'POST',
      }
    )
  }

  // GitHub API (for repository/branch fetching)
  async getGitHubRepos(accessToken: string): Promise<GitHubRepository[]> {
    const response = await fetch('https://api.github.com/user/repos', {
      headers: {
        Authorization: `token ${accessToken}`,
        'Accept': 'application/vnd.github.v3+json',
      },
    })

    if (!response.ok) {
      throw new Error('Failed to fetch GitHub repositories')
    }

    return response.json()
  }

  async getGitHubBranches(
    accessToken: string,
    owner: string,
    repo: string
  ): Promise<GitHubBranch[]> {
    const response = await fetch(`https://api.github.com/repos/${owner}/${repo}/branches`, {
      headers: {
        Authorization: `token ${accessToken}`,
        'Accept': 'application/vnd.github.v3+json',
      },
    })

    if (!response.ok) {
      throw new Error('Failed to fetch GitHub branches')
    }

    return response.json()
  }
}

// WebSocket client for real-time streaming
export class WebSocketClient {
  private ws?: WebSocket
  private url: string
  private onMessage?: (message: any) => void
  private onError?: (error: Event) => void
  private onClose?: () => void
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  constructor(url: string) {
    this.url = url
  }

  connect(callbacks: {
    onMessage?: (message: any) => void
    onError?: (error: Event) => void
    onClose?: () => void
  } = {}) {
    this.onMessage = callbacks.onMessage
    this.onError = callbacks.onError
    this.onClose = callbacks.onClose

    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          this.onMessage?.(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        console.error('WebSocket readyState:', this.ws?.readyState)
        console.error('WebSocket URL:', this.url)
        this.onError?.(error)
      }

      this.ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason)
        // Log more details about close event
        if (event.code === 1006) {
          console.error('WebSocket closed abnormally (1006) - possible authentication issue')
        } else if (event.code === 1000) {
          console.log('WebSocket closed normally')
        } else {
          console.warn(`WebSocket closed with code: ${event.code}, reason: ${event.reason || 'No reason provided'}`)
        }
        this.onClose?.()

        // Auto-reconnect logic
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++
          console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
          setTimeout(() => this.connect({ onMessage: this.onMessage, onError: this.onError, onClose: this.onClose }), this.reconnectDelay)
          this.reconnectDelay *= 2 // Exponential backoff
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      this.onError?.(error as Event)
    }
  }

  send(message: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not open. Cannot send message:', message)
    }
  }

  disconnect() {
    this.reconnectAttempts = this.maxReconnectAttempts // Prevent auto-reconnect
    this.ws?.close()
  }

  close() {
    this.disconnect()
  }

  sendControl(control: 'cancel' | 'ping', data?: Record<string, any>) {
    this.send({ control, data })
  }

  get readyState() {
    return this.ws?.readyState ?? WebSocket.CLOSED
  }
}

// Create and export the singleton API client
export const apiClient = new APIClient()

// Hook to automatically configure API client with auth context
export function useAuthenticatedApiClient() {
  const { token, apiKey } = useAuth()
  
  // Set auth credentials on the client
  if (token) {
    apiClient.setAuthToken(token)
  }
  
  if (apiKey) {
    apiClient.setApiKey(apiKey)
  }
  
  return apiClient
}

// Hook to create authenticated WebSocket client
export function useAuthenticatedWebSocket(baseUrl: string) {
  const { apiKey } = useAuth()
  
  const createWebSocketClient = (url: string) => {
    // Append API key to URL if available
    const wsUrl = apiKey ? `${url}?api_key=${apiKey}` : url
    console.log('Creating WebSocket client with URL:', wsUrl)
    console.log('API key available:', !!apiKey)
    return new WebSocketClient(wsUrl)
  }
  
  return { createWebSocketClient }
}

// Export the class for testing
export { APIClient }