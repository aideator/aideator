'use client';

import { useState, useCallback, useEffect } from 'react';
import { ModelInfo } from '@/types/models';
import { getModels, ModelDefinition } from '@/lib/api-client';
import { ModelInstance } from '@/components/models/ModelInstanceSelector';

export interface ModelInstancesState {
  selectedInstances: ModelInstance[];
  availableModels: ModelInfo[];
  maxInstances: number;
  isLoading: boolean;
  error: string | null;
}

// Default available models - expanded for testing
const DEFAULT_MODELS: ModelInfo[] = [
  {
    id: 'gpt-4',
    name: 'GPT-4',
    provider: 'OpenAI',
    description: 'Most capable GPT model for complex tasks',
    pricing: { input: 0.03, output: 0.06, currency: 'USD' },
    maxTokens: 8192,
    averageResponseTime: 3.2,
    capabilities: ['Reasoning', 'Code', 'Creative Writing', 'Analysis'],
    isRecommended: true,
  },
  {
    id: 'gpt-3.5-turbo',
    name: 'GPT-3.5 Turbo',
    provider: 'OpenAI',
    description: 'Fast and efficient for most tasks',
    pricing: { input: 0.0005, output: 0.0015, currency: 'USD' },
    maxTokens: 4096,
    averageResponseTime: 1.2,
    capabilities: ['General', 'Code', 'Creative Writing'],
    isRecommended: false,
  },
  {
    id: 'claude-3-opus',
    name: 'Claude-3 Opus',
    provider: 'Anthropic',
    description: 'Most powerful Claude model for complex reasoning',
    pricing: { input: 0.015, output: 0.075, currency: 'USD' },
    maxTokens: 4096,
    averageResponseTime: 2.8,
    capabilities: ['Reasoning', 'Analysis', 'Creative Writing', 'Code'],
    isRecommended: true,
  },
  {
    id: 'claude-3-sonnet',
    name: 'Claude-3 Sonnet',
    provider: 'Anthropic',
    description: 'Balanced Claude model for general use',
    pricing: { input: 0.003, output: 0.015, currency: 'USD' },
    maxTokens: 4096,
    averageResponseTime: 2.1,
    capabilities: ['General', 'Analysis', 'Creative Writing'],
    isRecommended: true,
  },
  {
    id: 'claude-3-haiku',
    name: 'Claude-3 Haiku',
    provider: 'Anthropic',
    description: 'Fastest Claude model for simple tasks',
    pricing: { input: 0.00025, output: 0.00125, currency: 'USD' },
    maxTokens: 4096,
    averageResponseTime: 0.8,
    capabilities: ['General', 'Fast Response'],
    isNew: true,
  },
  {
    id: 'gemini-pro',
    name: 'Gemini Pro',
    provider: 'Google',
    description: 'Google\'s most capable model for complex tasks',
    pricing: { input: 0.0005, output: 0.0015, currency: 'USD' },
    maxTokens: 32768,
    averageResponseTime: 2.5,
    capabilities: ['Reasoning', 'Code', 'Multimodal', 'Analysis'],
    isRecommended: true,
  },
];

// Storage key for persistence
const STORAGE_KEY = 'aideator_model_instances';

// Convert API ModelDefinition to ModelInfo
function convertToModelInfo(model: ModelDefinition): ModelInfo {
  return {
    id: model.id,
    name: model.display_name,
    provider: model.provider,
    description: model.description || '',
    pricing: model.input_price_per_1m_tokens && model.output_price_per_1m_tokens
      ? {
          input: model.input_price_per_1m_tokens / 1000, // Convert to per 1k tokens
          output: model.output_price_per_1m_tokens / 1000,
          currency: 'USD',
        }
      : undefined,
    maxTokens: model.max_output_tokens || model.context_window,
    capabilities: model.capabilities,
    // These fields would need to be added to the API response or calculated
    averageResponseTime: 2.5, // Default value
    isRecommended: model.capabilities.includes('CHAT_COMPLETION'),
    isNew: false,
  };
}

export function useModelInstances() {
  const [state, setState] = useState<ModelInstancesState>({
    selectedInstances: [],
    availableModels: DEFAULT_MODELS, // Start with defaults, will be replaced by API data
    maxInstances: 10,
    isLoading: true,
    error: null,
  });

  // Fetch models from API on mount
  useEffect(() => {
    async function fetchModels() {
      try {
        setState(prev => ({ ...prev, isLoading: true, error: null }));
        
        // Try to fetch models from API
        let modelInfos: ModelInfo[] = [];
        try {
          console.log('Fetching models from API...');
          const models = await getModels();
          console.log('API returned models:', models);
          modelInfos = models.map(convertToModelInfo);
          console.log('Converted to ModelInfo:', modelInfos);
        } catch (error) {
          // If API fails (e.g., not authenticated), use default models
          console.warn('Failed to fetch models from API, using defaults:', error);
          modelInfos = DEFAULT_MODELS;
        }
        
        // Load saved instances from localStorage
        let savedInstances: ModelInstance[] = [];
        if (typeof window !== 'undefined') {
          try {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved) {
              savedInstances = JSON.parse(saved);
              // Validate saved instances against available models
              savedInstances = savedInstances.filter(instance =>
                modelInfos.some(model => model.id === instance.modelId)
              );
              // Update model info for saved instances
              savedInstances = savedInstances.map(instance => ({
                ...instance,
                modelInfo: modelInfos.find(m => m.id === instance.modelId)!
              }));
            }
          } catch (error) {
            console.error('Failed to load model instances from localStorage:', error);
          }
        }
        
        setState(prev => ({
          ...prev,
          availableModels: modelInfos,
          selectedInstances: savedInstances,
          isLoading: false,
          error: null,
        }));
      } catch (error) {
        console.error('Failed to initialize models:', error);
        // Even if everything fails, use defaults
        setState(prev => ({
          ...prev,
          availableModels: DEFAULT_MODELS,
          selectedInstances: [],
          isLoading: false,
          error: null, // Don't show error for auth issues
        }));
      }
    }
    
    fetchModels();
  }, []);

  // Save to localStorage whenever instances change
  useEffect(() => {
    if (typeof window !== 'undefined' && state.selectedInstances.length > 0) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state.selectedInstances));
      } catch (error) {
        console.error('Failed to save model instances to localStorage:', error);
      }
    }
  }, [state.selectedInstances]);

  const addInstance = useCallback((modelId: string): void => {
    setState(prev => {
      if (prev.selectedInstances.length >= prev.maxInstances) {
        return {
          ...prev,
          error: `Cannot add more than ${prev.maxInstances} model instances`,
        };
      }

      const modelInfo = prev.availableModels.find(m => m.id === modelId);
      if (!modelInfo) {
        return {
          ...prev,
          error: `Unknown model: ${modelId}`,
        };
      }

      // Count existing instances of this model
      const existingCount = prev.selectedInstances.filter(i => i.modelId === modelId).length;
      const instanceNumber = existingCount + 1;
      const instanceId = `${modelId}-${Date.now()}-${instanceNumber}`;

      const newInstance: ModelInstance = {
        instanceId,
        modelId,
        modelInfo,
        instanceNumber,
      };

      return {
        ...prev,
        selectedInstances: [...prev.selectedInstances, newInstance],
        error: null,
      };
    });
  }, []);

  const removeInstance = useCallback((instanceId: string): void => {
    setState(prev => {
      const newInstances = prev.selectedInstances.filter(i => i.instanceId !== instanceId);
      
      // Renumber instances for each model
      const modelGroups = new Map<string, ModelInstance[]>();
      newInstances.forEach(instance => {
        if (!modelGroups.has(instance.modelId)) {
          modelGroups.set(instance.modelId, []);
        }
        modelGroups.get(instance.modelId)!.push(instance);
      });

      // Renumber instances within each model group
      const renumberedInstances: ModelInstance[] = [];
      modelGroups.forEach(instances => {
        instances.sort((a, b) => a.instanceId.localeCompare(b.instanceId));
        instances.forEach((instance, idx) => {
          renumberedInstances.push({
            ...instance,
            instanceNumber: idx + 1,
          });
        });
      });

      return {
        ...prev,
        selectedInstances: renumberedInstances,
        error: null,
      };
    });
  }, []);

  const clearInstances = useCallback((): void => {
    setState(prev => ({
      ...prev,
      selectedInstances: [],
      error: null,
    }));
    
    // Clear localStorage
    if (typeof window !== 'undefined') {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  const getModelById = useCallback((modelId: string): ModelInfo | undefined => {
    return state.availableModels.find(model => model.id === modelId);
  }, [state.availableModels]);

  const getInstanceStats = useCallback(() => {
    const modelCounts = new Map<string, number>();
    state.selectedInstances.forEach(instance => {
      modelCounts.set(instance.modelId, (modelCounts.get(instance.modelId) || 0) + 1);
    });

    return {
      totalInstances: state.selectedInstances.length,
      uniqueModels: modelCounts.size,
      modelCounts: Object.fromEntries(modelCounts),
      averageResponseTime: state.selectedInstances.reduce((sum, instance) => 
        sum + (instance.modelInfo.averageResponseTime || 0), 0) / state.selectedInstances.length || 0,
      totalEstimatedCost: state.selectedInstances.reduce((sum, instance) => 
        sum + ((instance.modelInfo.pricing?.input || 0) + (instance.modelInfo.pricing?.output || 0)), 0),
    };
  }, [state.selectedInstances]);

  const clearError = useCallback((): void => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  return {
    // State
    selectedInstances: state.selectedInstances,
    availableModels: state.availableModels,
    maxInstances: state.maxInstances,
    isLoading: state.isLoading,
    error: state.error,

    // Actions
    addInstance,
    removeInstance,
    clearInstances,
    clearError,

    // Selectors
    getModelById,
    getInstanceStats,
  };
}

export default useModelInstances;