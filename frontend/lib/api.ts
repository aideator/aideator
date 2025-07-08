const API_BASE_URL =
  typeof window !== "undefined" && window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : "http://localhost:8000" // You'll need to update this for production

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

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }))
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
