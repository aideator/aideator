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
} from './types'

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

  // Model definitions API
  async getModelDefinitions(): Promise<string[]> {
    try {
      interface ModelDefinition {
        id: string
        model_name: string
        display_name: string
      }
      
      const response = await this.request<ModelDefinition[]>('/api/v1/models/models')
      return response.map(model => model.model_name) || ['gpt-4-turbo', 'gpt-3.5-turbo', 'claude-3-sonnet', 'claude-3-haiku']
    } catch (error) {
      console.error('Error fetching model definitions:', error)
      // Fallback to common models
      return ['gpt-4-turbo', 'gpt-3.5-turbo', 'claude-3-sonnet', 'claude-3-haiku']
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    // Auto-authenticate if needed
    if (!this.authToken && !endpoint.includes('/auth/')) {
      try {
        const credentials = await this.getDevCredentials()
        this.setAuthToken(credentials.access_token)
        this.setApiKey(credentials.api_key)
      } catch (error) {
        console.warn('Failed to get dev credentials:', error)
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

    const config: RequestInit = {
      ...options,
      headers,
    }

    const response = await fetch(url, config)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      const error: APIError = {
        detail: typeof errorData.detail === 'string' 
          ? errorData.detail 
          : errorData.detail?.message || response.statusText,
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
        this.onError?.(error)
      }

      this.ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason)
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

// Export singleton instance
export const apiClient = new APIClient()
export default apiClient