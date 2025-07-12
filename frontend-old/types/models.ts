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

