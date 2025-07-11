import * as api from './api'

// Re-export all types from the original API
export * from './api'

// Define API base URL
const API_BASE_URL = 
  typeof window !== "undefined" && window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : "http://localhost:8000" // Update for production

// Helper function to get auth headers
function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  
  // Get token from localStorage
  const token = localStorage.getItem('auth_token')
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  // Get API key from localStorage (for endpoints that require it)
  const apiKey = localStorage.getItem('api_key')
  if (apiKey) {
    headers['X-API-Key'] = apiKey
  }
  
  return headers
}

// Helper function to make authenticated requests
async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const authHeaders = getAuthHeaders()
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...authHeaders,
      ...options.headers,
    },
  })
  
  // If we get a 401, the token might be expired
  if (response.status === 401) {
    // Clear auth data
    localStorage.removeItem('auth_token')
    localStorage.removeItem('api_key')
    
    // In development, try to auto-login again
    if (process.env.NODE_ENV === 'development') {
      // Token expired - attempting dev auto-login
      // Note: We can't use the AuthContext here, so we'll just clear and let the app re-authenticate
      window.location.reload()
    }
  }
  
  return response
}

// Authenticated versions of API functions
export async function createRun(data: api.CreateRunRequest): Promise<api.CreateRunResponse> {
  
  try {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/runs`, {
      method: "POST",
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      // Error details are included in the thrown error
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  } catch (error) {
    // Error handling - re-throw with context
    if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
      throw new Error(
        "Cannot connect to backend. Make sure the server is running on localhost:8000 and CORS is configured.",
      )
    }
    throw error
  }
}

export async function createPrompt(data: api.CreatePromptRequest): Promise<api.CreatePromptResponse> {
  
  try {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/prompts`, {
      method: "POST",
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      // Error details are included in the thrown error
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
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

export async function createSession(data: api.CreateSessionRequest = {}): Promise<api.CreateSessionResponse> {
  
  try {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/sessions`, {
      method: "POST",
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      // Error details are included in the thrown error
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

export async function recordPreference(data: api.PreferenceRequest): Promise<void> {
  
  try {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/preferences`, {
      method: "POST",
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      // Error details are included in the thrown error
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

// For GET requests, we'll wrap all the existing functions
export async function getSessions(): Promise<api.Session[]> {
  
  try {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/sessions`)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      // Error details are included in the thrown error
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()
    // The API returns a SessionListResponse with { sessions, total, limit, offset }
    // We just need the sessions array
    return data.sessions || []
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

export async function getSessionDetails(sessionId: string): Promise<api.SessionDetails> {
  
  try {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/sessions/${sessionId}`)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      // Error details are included in the thrown error
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

export async function getModelCatalog(): Promise<api.ModelCatalogResponse> {
  
  try {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/models/catalog`)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      // Error details are included in the thrown error
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
}): Promise<api.ModelDefinition[]> {
  
  try {
    const queryParams = new URLSearchParams()
    if (params?.provider) queryParams.append('provider', params.provider)
    if (params?.capability) queryParams.append('capability', params.capability)
    if (params?.requires_api_key !== undefined) queryParams.append('requires_api_key', params.requires_api_key.toString())
    
    const url = `${API_BASE_URL}/api/v1/models/models${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    const response = await fetchWithAuth(url)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      // Error details are included in the thrown error
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

export async function getPreferenceStats(): Promise<api.PreferenceStats> {
  
  try {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/preferences/stats`)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      // Error details are included in the thrown error
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

// Functions that don't need authentication (but we'll still use the wrapper for consistency)
export async function getPromptDetails(promptId: string): Promise<api.PromptDetails> {
  
  try {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/prompts/${promptId}`)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      // Error details are included in the thrown error
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

export async function updateSession(sessionId: string, data: { title: string }): Promise<void> {
  
  try {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/sessions/${sessionId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      // Error details are included in the thrown error
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
    const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/sessions/${sessionId}`, {
      method: "DELETE",
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      // Error details are included in the thrown error
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

// Legacy functions for backward compatibility
export async function selectWinner(runId: string, variationId: number): Promise<void> {
  
  try {
    const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/runs/${runId}/select`, {
      method: "POST",
      body: JSON.stringify({ variation_id: variationId }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      // Error details are included in the thrown error
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
    const response = await fetchWithAuth(`${API_BASE_URL}/api/v1/runs/${runId}/status`)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
      // Error details are included in the thrown error
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