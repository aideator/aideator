const API_BASE_URL =
  typeof window !== "undefined" && window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : "http://localhost:8000" // You'll need to update this for production

// Legacy run interface for backward compatibility
interface CreateRunRequest {
  github_url: string
  prompt: string
  variations: number
  agent_mode?: string
  agent_config?: {
    model: string
    temperature: number
    max_tokens?: number
    system_prompt?: string
    stop_sequences?: string[]
  }
  use_claude_code?: boolean
}

interface CreateRunResponse {
  run_id: string
  stream_url: string
  status: string
  estimated_duration_seconds: number
}

// New multi-model comparison interfaces
interface CreatePromptRequest {
  prompt: string
  models: string[]
  session_id?: string
  github_url?: string
  agent_config?: {
    temperature: number
    max_tokens?: number
    system_prompt?: string
    stop_sequences?: string[]
  }
}

interface CreatePromptResponse {
  prompt_id: string
  session_id: string
  stream_url: string
  status: string
  models: string[]
  estimated_duration_seconds: number
}

interface ModelResponse {
  model_id: string
  model_name: string
  status: 'pending' | 'streaming' | 'completed' | 'error'
  content?: string
  response_time_ms?: number
  token_count?: number
  cost_usd?: number
  error_message?: string
}

interface PromptDetails {
  prompt_id: string
  session_id: string
  prompt: string
  models: string[]
  responses: ModelResponse[]
  selected_model_id?: string
  status: string
  created_at: string
  completed_at?: string
}

// Session management interfaces
interface CreateSessionRequest {
  title?: string
  description?: string
}

interface CreateSessionResponse {
  id: string
  title: string
  description?: string
  created_at: string
}

interface Session {
  id: string
  title: string
  description?: string
  created_at: string
  updated_at: string
  total_turns: number
  last_activity_at: string
  is_active: boolean
  is_archived: boolean
}

interface SessionDetails extends Session {
  turns: PromptDetails[]
}

// Preference tracking interfaces
interface PreferenceRequest {
  prompt_id: string
  chosen_model_id: string
  feedback_text?: string
}

interface PreferenceStats {
  total_preferences: number
  model_win_rates: Record<string, number>
  favorite_model: string
  preference_trends: {
    date: string
    model_id: string
    win_rate: number
  }[]
}

export async function createRun(data: CreateRunRequest): Promise<CreateRunResponse> {
  console.log("Making request to:", `${API_BASE_URL}/api/v1/runs`)
  console.log("Request data:", data)

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/runs`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    })

    console.log("Response status:", response.status)
    console.log("Response ok:", response.ok)
    console.log("Response headers:", response.headers)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      console.error("API Error Response:", errorData)
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }

    const result = await response.json()
    console.log("Response data:", result)
    return result
  } catch (error) {
    console.error("Fetch error:", error)
    if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
      throw new Error(
        "Cannot connect to backend. Make sure the server is running on localhost:8000 and CORS is configured.",
      )
    }
    throw error
  }
}

export async function selectWinner(runId: string, variationId: number): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/runs/${runId}/select`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ variation_id: variationId }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      console.error("API Error Response:", errorData)
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }
  } catch (error) {
    console.error("Select winner error:", error)
    if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
      throw new Error(
        "Cannot connect to backend. Make sure the server is running on localhost:8000 and CORS is configured.",
      )
    }
    throw error
  }
}

export async function getRunStatus(runId: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/runs/${runId}/status`)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      console.error("API Error Response:", errorData)
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  } catch (error) {
    console.error("Get run status error:", error)
    if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
      throw new Error(
        "Cannot connect to backend. Make sure the server is running on localhost:8000 and CORS is configured.",
      )
    }
    throw error
  }
}

// New multi-model comparison API functions
export async function createPrompt(data: CreatePromptRequest): Promise<CreatePromptResponse> {
  console.log("Making request to:", `${API_BASE_URL}/api/v1/prompts`)
  console.log("Request data:", data)

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/prompts`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    })

    console.log("Response status:", response.status)
    console.log("Response ok:", response.ok)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      console.error("API Error Response:", errorData)
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }

    const result = await response.json()
    console.log("Response data:", result)
    return result
  } catch (error) {
    console.error("Create prompt error:", error)
    if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
      throw new Error(
        "Cannot connect to backend. Make sure the server is running on localhost:8000 and CORS is configured.",
      )
    }
    throw error
  }
}

export async function getPromptDetails(promptId: string): Promise<PromptDetails> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/prompts/${promptId}`)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      console.error("API Error Response:", errorData)
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  } catch (error) {
    console.error("Get prompt details error:", error)
    if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
      throw new Error(
        "Cannot connect to backend. Make sure the server is running on localhost:8000 and CORS is configured.",
      )
    }
    throw error
  }
}

// Session management functions
export async function createSession(data: CreateSessionRequest = {}): Promise<CreateSessionResponse> {
  try {
    const token = localStorage.getItem('auth_token');
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_BASE_URL}/api/v1/sessions`, {
      method: "POST",
      headers,
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      console.error("API Error Response:", errorData)
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  } catch (error) {
    console.error("Create session error:", error)
    if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
      throw new Error(
        "Cannot connect to backend. Make sure the server is running on localhost:8000 and CORS is configured.",
      )
    }
    throw error
  }
}

export async function getSessions(): Promise<Session[]> {
  try {
    const token = localStorage.getItem('auth_token');
    const headers: Record<string, string> = {};
    
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_BASE_URL}/api/v1/sessions`, {
      headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      console.error("API Error Response:", errorData)
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  } catch (error) {
    console.error("Get sessions error:", error)
    if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
      throw new Error(
        "Cannot connect to backend. Make sure the server is running on localhost:8000 and CORS is configured.",
      )
    }
    throw error
  }
}

export async function getSessionDetails(sessionId: string): Promise<SessionDetails> {
  try {
    const token = localStorage.getItem('auth_token');
    const headers: Record<string, string> = {};
    
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}`, {
      headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      console.error("API Error Response:", errorData)
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  } catch (error) {
    console.error("Get session details error:", error)
    if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
      throw new Error(
        "Cannot connect to backend. Make sure the server is running on localhost:8000 and CORS is configured.",
      )
    }
    throw error
  }
}

export async function updateSession(sessionId: string, data: { title: string }): Promise<void> {
  try {
    const token = localStorage.getItem('auth_token');
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}`, {
      method: "PUT",
      headers,
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      console.error("API Error Response:", errorData)
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }
  } catch (error) {
    console.error("Update session error:", error)
    if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
      throw new Error(
        "Cannot connect to backend. Make sure the server is running on localhost:8000 and CORS is configured.",
      )
    }
    throw error
  }
}

export async function deleteSession(sessionId: string): Promise<void> {
  try {
    const token = localStorage.getItem('auth_token');
    const headers: Record<string, string> = {};
    
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}`, {
      method: "DELETE",
      headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      console.error("API Error Response:", errorData)
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }
  } catch (error) {
    console.error("Delete session error:", error)
    if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
      throw new Error(
        "Cannot connect to backend. Make sure the server is running on localhost:8000 and CORS is configured.",
      )
    }
    throw error
  }
}

// Preference tracking functions
export async function recordPreference(data: PreferenceRequest): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/preferences`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      console.error("API Error Response:", errorData)
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }
  } catch (error) {
    console.error("Record preference error:", error)
    if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
      throw new Error(
        "Cannot connect to backend. Make sure the server is running on localhost:8000 and CORS is configured.",
      )
    }
    throw error
  }
}

export async function getPreferenceStats(): Promise<PreferenceStats> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/preferences/stats`)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      console.error("API Error Response:", errorData)
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  } catch (error) {
    console.error("Get preference stats error:", error)
    if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
      throw new Error(
        "Cannot connect to backend. Make sure the server is running on localhost:8000 and CORS is configured.",
      )
    }
    throw error
  }
}

// Model catalog interfaces
export interface ModelDefinition {
  id: string
  provider: string
  model_name: string
  litellm_model_name: string
  display_name: string
  description?: string
  context_window?: number
  max_output_tokens?: number
  input_price_per_1m_tokens?: number
  output_price_per_1m_tokens?: number
  capabilities: string[]
  requires_api_key: boolean
  requires_region?: boolean
  requires_project_id?: boolean
  is_active: boolean
}

export interface ProviderSummary {
  provider: string
  display_name: string
  description: string
  requires_api_key: boolean
  model_count: number
  user_has_credentials: boolean
}

export interface ModelCatalogResponse {
  providers: ProviderSummary[]
  models: ModelDefinition[]
  capabilities: string[]
}

// Model catalog functions
export async function getModelCatalog(): Promise<ModelCatalogResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/models/catalog`)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      console.error("API Error Response:", errorData)
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  } catch (error) {
    console.error("Get model catalog error:", error)
    if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
      throw new Error(
        "Cannot connect to backend. Make sure the server is running on localhost:8000 and CORS is configured.",
      )
    }
    throw error
  }
}

export async function getModels(params?: {
  provider?: string
  capability?: string
  requires_api_key?: boolean
}): Promise<ModelDefinition[]> {
  try {
    const queryParams = new URLSearchParams()
    if (params?.provider) queryParams.append('provider', params.provider)
    if (params?.capability) queryParams.append('capability', params.capability)
    if (params?.requires_api_key !== undefined) queryParams.append('requires_api_key', params.requires_api_key.toString())
    
    const url = `${API_BASE_URL}/api/v1/models/models${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    const response = await fetch(url)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      console.error("API Error Response:", errorData)
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  } catch (error) {
    console.error("Get models error:", error)
    if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
      throw new Error(
        "Cannot connect to backend. Make sure the server is running on localhost:8000 and CORS is configured.",
      )
    }
    throw error
  }
}

// Export all interfaces for use in other files
export type {
  CreateRunRequest,
  CreateRunResponse,
  CreatePromptRequest,
  CreatePromptResponse,
  ModelResponse,
  PromptDetails,
  CreateSessionRequest,
  CreateSessionResponse,
  Session,
  SessionDetails,
  PreferenceRequest,
  PreferenceStats,
}
