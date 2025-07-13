// Backend model types
export type RunStatus = "pending" | "running" | "completed" | "failed" | "cancelled"
export type TurnStatus = "pending" | "streaming" | "completed" | "failed"
export type OutputType = "llm" | "stdout" | "stderr" | "status" | "system" | "summary" | "diffs" | "logging" | "addinfo"

// Session types
export interface Session {
  id: string
  user_id: string
  title: string
  description?: string
  is_active: boolean
  is_archived: boolean
  created_at: string
  updated_at: string
  last_activity_at: string
  models_used: string[]
  total_turns: number
  total_cost: number
}

export interface SessionCreate {
  title: string
  description?: string
  models_used: string[]
}

export interface SessionUpdate {
  title?: string
  description?: string
  is_active?: boolean
  is_archived?: boolean
}

export interface SessionListResponse {
  sessions: Session[]
  total: number
  limit: number
  offset: number
}

// Turn types
export interface Turn {
  id: string
  session_id: string
  user_id: string
  turn_number: number
  prompt: string
  context?: string
  model: string
  models_requested: string[]
  responses: Record<string, any>
  started_at: string
  completed_at?: string
  duration_seconds?: number
  total_cost: number
  status: TurnStatus
}

export interface TurnCreate {
  prompt: string
  context?: string
  models_requested: string[]
}

// Run types
export interface ModelVariant {
  model_definition_id: string
  provider_credential_id?: string
  model_parameters?: Record<string, any>
}

export interface Run {
  id: string
  github_url: string
  prompt: string
  variations: number
  status: RunStatus
  winning_variation_id?: number
  created_at: string
  started_at?: string
  completed_at?: string
  agent_config: Record<string, any>
  user_id?: string
  api_key_id?: string
  results: Record<string, any>
  error_message?: string
  total_tokens_used?: number
  total_cost_usd?: number
}

export interface CreateRunRequest {
  github_url: string
  prompt: string
  model_variants: ModelVariant[]
  use_claude_code?: boolean
  agent_mode?: string
  session_id?: string
  turn_id?: string
}

export interface CreateRunResponse {
  run_id: string
  websocket_url: string
  polling_url: string
  status: string
  estimated_duration_seconds: number
  session_id: string
  turn_id: string
}

export interface AgentOutput {
  id: number
  run_id: string
  variation_id: number
  content: string
  timestamp: string
  output_type: OutputType
}

// Preference types
export interface Preference {
  id: string
  user_id: string
  session_id: string
  turn_id: string
  preferred_model: string
  preferred_response_id: string
  compared_models: string[]
  response_quality_scores: Record<string, number>
  feedback_text?: string
  confidence_score?: number
  created_at: string
  preference_type: string
}

export interface PreferenceCreate {
  preferred_model: string
  preferred_response_id: string
  compared_models: string[]
  response_quality_scores: Record<string, number>
  feedback_text?: string
  confidence_score?: number
  preference_type: string
}

// WebSocket message types
export interface WSMessage {
  type: "connected" | "llm" | "stdout" | "stderr" | "status" | "control_ack" | "error" | "pong"
  message_id: string
  data: {
    run_id: string
    variation_id: string
    content?: string
    timestamp: string
    metadata?: Record<string, any>
    status?: string
    error?: string
  }
}

export interface WSControlMessage {
  control: "cancel" | "ping"
  data?: Record<string, any>
}

// GitHub integration types
export interface GitHubRepository {
  id: number
  name: string
  full_name: string
  private: boolean
  html_url: string
  description?: string
  default_branch: string
}

export interface GitHubBranch {
  name: string
  commit: {
    sha: string
    url: string
  }
  protected: boolean
}

// UI state types
export interface AgentVariation {
  id: string
  variation_id: number
  model_name: string
  status: "pending" | "running" | "completed" | "failed" | "cancelled"
  outputs: string[]
  progress?: number
  error?: string
}

export interface StreamingState {
  isConnected: boolean
  isConnecting: boolean
  error?: string
  variations: Map<number, AgentVariation>
  lastMessageId?: string
}

// Form types
export interface CreateSessionForm {
  title: string
  description: string
  github_url: string
  prompt: string
  model_variants: ModelVariant[]
  agent_mode: string
}

// API response types
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface APIError {
  detail: string | {
    message: string
    unavailable_models?: Array<{
      model: string
      error: string
    }>
    available_models?: string[]
    suggestion?: string
  }
}

// Provider API Key types
export interface ProviderAPIKey {
  id: string
  user_id: string
  provider: string
  model_name?: string
  key_hint: string
  name?: string
  description?: string
  is_active: boolean
  is_valid?: boolean
  last_validated_at?: string
  last_used_at?: string
  last_error?: string
  total_requests: number
  total_tokens: number
  total_cost_usd: number
  created_at: string
  updated_at: string
  expires_at?: string
}

export interface ProviderAPIKeyCreate {
  provider: string
  api_key: string
  model_name?: string
  name?: string
  description?: string
}

export interface ProviderAPIKeyUpdate {
  api_key?: string
  name?: string
  description?: string
  is_active?: boolean
}

export interface Provider {
  name: string
  display_name: string
  requires_api_key: boolean
  supports_models?: string[]
}

// Code execution types
export interface CodeRequest {
  prompt: string
  context?: string
  models: string[]
  max_models: number
}

export interface CodeResponse {
  turn_id: string
  run_id: string
  websocket_url: string
  debug_websocket_url: string
  status: string
  models_used: string[]
}

// Legacy types for migration (to be phased out)
export type DiffLine = {
  type: "add" | "del" | "normal"
  oldLine?: number
  newLine?: number
  content: string
}

export type FileDetail = {
  name: string
  additions: number
  deletions: number
  diff: DiffLine[]
}

export type VersionDetail = {
  id: number
  summary: string
  files: FileDetail[]
}

export type SessionDetail = {
  versions: VersionDetail[]
}

export type LegacySession = {
  id: string
  title: string
  details: string
  status: "Completed" | "Open" | "Failed"
  versions?: number
  additions?: number
  deletions?: number
  sessionDetails?: SessionDetail
}