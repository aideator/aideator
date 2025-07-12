'use client';

import { useState, useCallback, useEffect } from 'react';
import { ModelInfo } from '@/types/models';
import { getModels, ModelDefinition } from '@/lib/api-client';
import { useAuth } from '@/contexts/AuthContext';

export interface ModelSelectionState {
  selectedModels: string[];
  availableModels: ModelInfo[];
  maxSelection: number;
  minSelection: number;
  selectionHistory: string[][];
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
  {
    id: 'llama-2-70b',
    name: 'Llama 2 70B',
    provider: 'Meta',
    description: 'Open-source model with strong performance',
    pricing: { input: 0.0007, output: 0.0009, currency: 'USD' },
    maxTokens: 4096,
    averageResponseTime: 4.1,
    capabilities: ['General', 'Code', 'Reasoning'],
    isNew: true,
  },
  {
    id: 'mistral-large',
    name: 'Mistral Large',
    provider: 'Mistral',
    description: 'European model with strong multilingual capabilities',
    pricing: { input: 0.004, output: 0.012, currency: 'USD' },
    maxTokens: 32768,
    averageResponseTime: 2.3,
    capabilities: ['Multilingual', 'Code', 'Reasoning'],
    isNew: true,
  },
  {
    id: 'cohere-command',
    name: 'Command R+',
    provider: 'Cohere',
    description: 'Enterprise-focused with retrieval augmentation',
    pricing: { input: 0.003, output: 0.015, currency: 'USD' },
    maxTokens: 4096,
    averageResponseTime: 2.0,
    capabilities: ['RAG', 'Enterprise', 'Multilingual'],
    isRecommended: false,
  },
];

// Storage key for persistence
const STORAGE_KEY = 'aideator_model_selection';

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

export function useModelSelection() {
  const auth = useAuth();
  const [state, setState] = useState<ModelSelectionState>({
    selectedModels: [],
    availableModels: DEFAULT_MODELS, // Start with defaults, will be replaced by API data
    maxSelection: 99, // Allow selecting many models
    minSelection: 1,
    selectionHistory: [],
    isLoading: true,
    error: null,
  });

  // Fetch models from API after auth completes
  useEffect(() => {
    // Don't make API calls if auth is still loading or user is not authenticated
    if (auth.isLoading || !auth.isAuthenticated) {
      // Set default models immediately if not authenticated
      if (!auth.isLoading && !auth.isAuthenticated) {
        setState(prev => ({ ...prev, isLoading: false, error: null }));
        // Initialize with default recommended models for unauthenticated users
        const defaultSelectedModels = DEFAULT_MODELS.filter(m => m.isRecommended).slice(0, 3).map(m => m.id);
        setState(prev => ({ 
          ...prev, 
          selectedModels: defaultSelectedModels,
          availableModels: DEFAULT_MODELS
        }));
      }
      return;
    }

    async function fetchModels() {
      try {
        setState(prev => ({ ...prev, isLoading: true, error: null }));
        
        // Try to fetch models from API
        let modelInfos: ModelInfo[] = [];
        try {
          const models = await getModels();
          modelInfos = models.map(convertToModelInfo);
        } catch (error) {
          // If API fails (e.g., not authenticated), use default models
          modelInfos = DEFAULT_MODELS;
        }
        
        // Load saved selection from localStorage
        let savedSelection: string[] = [];
        let savedHistory: string[][] = [];
        if (typeof window !== 'undefined') {
          try {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved) {
              const data = JSON.parse(saved);
              savedSelection = data.selectedModels || [];
              savedHistory = data.selectionHistory || [];
            }
          } catch (error) {
            console.error('Failed to load model selection from localStorage:', error);
          }
        }
        
        // Filter saved selection to only include models that exist
        const validSavedSelection = savedSelection.filter(id =>
          modelInfos.some(model => model.id === id)
        );
        
        // If no valid saved selection, select recommended models
        const selectedModels = validSavedSelection.length > 0
          ? validSavedSelection
          : modelInfos
              .filter(model => model.isRecommended)
              .slice(0, 3)
              .map(model => model.id);
        
        setState(prev => ({
          ...prev,
          availableModels: modelInfos,
          selectedModels,
          selectionHistory: savedHistory,
          isLoading: false,
          error: null,
        }));
      } catch (error) {
        console.error('Failed to initialize models:', error);
        // Even if everything fails, use defaults
        setState(prev => ({
          ...prev,
          availableModels: DEFAULT_MODELS,
          selectedModels: DEFAULT_MODELS.filter(m => m.isRecommended).slice(0, 3).map(m => m.id),
          isLoading: false,
          error: null, // Don't show error for auth issues
        }));
      }
    }
    
    fetchModels();
  }, [auth.isLoading, auth.isAuthenticated]);

  // Save to localStorage whenever selection changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({
          selectedModels: state.selectedModels,
          selectionHistory: state.selectionHistory,
        }));
      } catch (error) {
        console.error('Failed to save model selection to localStorage:', error);
      }
    }
  }, [state.selectedModels, state.selectionHistory]);

  const toggleModel = useCallback((modelId: string): void => {
    setState(prev => {
      const isSelected = prev.selectedModels.includes(modelId);
      let newSelection: string[];

      if (isSelected) {
        // Don't allow deselection if it would go below minimum
        if (prev.selectedModels.length <= prev.minSelection) {
          return prev;
        }
        newSelection = prev.selectedModels.filter(id => id !== modelId);
      } else {
        // Don't allow selection if it would exceed maximum
        if (prev.selectedModels.length >= prev.maxSelection) {
          return prev;
        }
        newSelection = [...prev.selectedModels, modelId];
      }

      // Add to history
      const newHistory = [newSelection, ...prev.selectionHistory.slice(0, 9)];

      return {
        ...prev,
        selectedModels: newSelection,
        selectionHistory: newHistory,
        error: null,
      };
    });
  }, []);

  const setSelectedModels = useCallback((modelIds: string[]): void => {
    setState(prev => {
      // Validate selection
      if (modelIds.length < prev.minSelection) {
        return {
          ...prev,
          error: `Must select at least ${prev.minSelection} model${prev.minSelection > 1 ? 's' : ''}`,
        };
      }

      if (modelIds.length > prev.maxSelection) {
        return {
          ...prev,
          error: `Cannot select more than ${prev.maxSelection} models`,
        };
      }

      // Validate all models exist
      const invalidModels = modelIds.filter(id => 
        !prev.availableModels.some(model => model.id === id)
      );

      if (invalidModels.length > 0) {
        return {
          ...prev,
          error: `Unknown models: ${invalidModels.join(', ')}`,
        };
      }

      // Add to history
      const newHistory = [modelIds, ...prev.selectionHistory.slice(0, 9)];

      return {
        ...prev,
        selectedModels: modelIds,
        selectionHistory: newHistory,
        error: null,
      };
    });
  }, []);

  const selectRecommended = useCallback((): void => {
    const recommended = state.availableModels
      .filter(model => model.isRecommended)
      .slice(0, state.maxSelection)
      .map(model => model.id);
    
    setSelectedModels(recommended);
  }, [state.availableModels, state.maxSelection, setSelectedModels]);

  const selectAll = useCallback((): void => {
    const allModels = state.availableModels
      .slice(0, state.maxSelection)
      .map(model => model.id);
    
    setSelectedModels(allModels);
  }, [state.availableModels, state.maxSelection, setSelectedModels]);

  const clearSelection = useCallback((): void => {
    setSelectedModels([]);
  }, [setSelectedModels]);

  const restoreFromHistory = useCallback((index: number): void => {
    if (index >= 0 && index < state.selectionHistory.length) {
      setSelectedModels(state.selectionHistory[index]);
    }
  }, [state.selectionHistory, setSelectedModels]);

  const updateModelInfo = useCallback((modelId: string, updates: Partial<ModelInfo>): void => {
    setState(prev => ({
      ...prev,
      availableModels: prev.availableModels.map(model =>
        model.id === modelId ? { ...model, ...updates } : model
      ),
    }));
  }, []);

  const getSelectedModelInfo = useCallback((): ModelInfo[] => {
    return state.selectedModels
      .map(id => state.availableModels.find(model => model.id === id))
      .filter((model): model is ModelInfo => model !== undefined);
  }, [state.selectedModels, state.availableModels]);

  const getModelById = useCallback((modelId: string): ModelInfo | undefined => {
    return state.availableModels.find(model => model.id === modelId);
  }, [state.availableModels]);

  const canSelectMore = useCallback((): boolean => {
    return state.selectedModels.length < state.maxSelection;
  }, [state.selectedModels.length, state.maxSelection]);

  const canDeselectMore = useCallback((): boolean => {
    return state.selectedModels.length > state.minSelection;
  }, [state.selectedModels.length, state.minSelection]);

  const getSelectionStats = useCallback(() => {
    const selectedInfo = getSelectedModelInfo();
    
    return {
      totalSelected: state.selectedModels.length,
      averageResponseTime: selectedInfo.reduce((sum, model) => 
        sum + (model.averageResponseTime || 0), 0) / selectedInfo.length,
      totalEstimatedCost: selectedInfo.reduce((sum, model) => 
        sum + (model.pricing?.input || 0) + (model.pricing?.output || 0), 0),
      providers: [...new Set(selectedInfo.map(model => model.provider))],
      capabilities: [...new Set(selectedInfo.flatMap(model => model.capabilities || []))],
    };
  }, [getSelectedModelInfo, state.selectedModels.length]);

  const clearError = useCallback((): void => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  return {
    // State
    selectedModels: state.selectedModels,
    availableModels: state.availableModels,
    maxSelection: state.maxSelection,
    minSelection: state.minSelection,
    selectionHistory: state.selectionHistory,
    isLoading: state.isLoading,
    error: state.error,

    // Actions
    toggleModel,
    setSelectedModels,
    selectRecommended,
    selectAll,
    clearSelection,
    restoreFromHistory,
    updateModelInfo,
    clearError,

    // Selectors
    getSelectedModelInfo,
    getModelById,
    canSelectMore,
    canDeselectMore,
    getSelectionStats,
  };
}

