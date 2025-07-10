// Shared model types used across components and hooks

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  description?: string;
  pricing?: {
    input: number;
    output: number;
    currency: string;
  };
  maxTokens?: number;
  averageResponseTime?: number;
  capabilities?: string[];
  isRecommended?: boolean;
  isNew?: boolean;
}

export interface ModelCapability {
  text_completion: string;
  chat_completion: string;
  vision: string;
  embedding: string;
  audio_input: string;
  audio_output: string;
  image_generation: string;
  web_search: string;
  function_calling: string;
  streaming: string;
  json_schema: string;
  pdf_input: string;
}

export interface ModelDefinition {
  id: string;
  provider: string;
  model_name: string;
  litellm_model_name: string;
  display_name: string;
  description?: string;
  context_window?: number;
  max_output_tokens?: number;
  input_price_per_1m_tokens?: number;
  output_price_per_1m_tokens?: number;
  capabilities: string[];
  requires_api_key: boolean;
  requires_region: boolean;
  requires_project_id: boolean;
  is_active: boolean;
}

export interface ProviderSummary {
  provider: string;
  display_name: string;
  description: string;
  requires_api_key: boolean;
  model_count: number;
  user_has_credentials: boolean;
}

export interface ModelVariant {
  id: string;
  model_definition_id: string;
  provider_credential_id?: string;
  model_parameters: {
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
  };
}