'use client';

import { useState, useCallback, useRef } from 'react';
import { PreferenceFeedbackData } from '@/components/models/PreferenceFeedback';

export interface PreferenceRecord {
  id: string;
  sessionId: string;
  turnId: string;
  selectedModelId: string;
  selectedModelName: string;
  prompt: string;
  modelResponses: {
    modelId: string;
    modelName: string;
    response: string;
    responseTime?: number;
    tokenCount?: number;
  }[];
  feedback?: PreferenceFeedbackData;
  timestamp: string;
  isOptimistic?: boolean;
}

export interface PreferenceStats {
  totalPreferences: number;
  modelWinRates: Record<string, number>;
  averageResponseTime: Record<string, number>;
  preferencesByPromptType: Record<string, number>;
  recentPreferences: PreferenceRecord[];
}

interface PreferenceStoreState {
  preferences: PreferenceRecord[];
  stats: PreferenceStats;
  isLoading: boolean;
  error: string | null;
  optimisticUpdates: Map<string, PreferenceRecord>;
}

// Mock API functions (replace with actual API calls)
const mockAPI = {
  recordPreference: async (preference: Omit<PreferenceRecord, 'id' | 'timestamp'>): Promise<PreferenceRecord> => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // Simulate occasional failures for testing
    if (Math.random() < 0.1) {
      throw new Error('Failed to record preference');
    }
    
    return {
      ...preference,
      id: `pref-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
    };
  },

  getPreferenceStats: async (): Promise<PreferenceStats> => {
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      totalPreferences: 0,
      modelWinRates: {},
      averageResponseTime: {},
      preferencesByPromptType: {},
      recentPreferences: [],
    };
  },

  updatePreferenceFeedback: async (
    preferenceId: string, 
    feedback: PreferenceFeedbackData
  ): Promise<void> => {
    await new Promise(resolve => setTimeout(resolve, 300));
  },
};

export function usePreferenceStore() {
  const [state, setState] = useState<PreferenceStoreState>({
    preferences: [],
    stats: {
      totalPreferences: 0,
      modelWinRates: {},
      averageResponseTime: {},
      preferencesByPromptType: {},
      recentPreferences: [],
    },
    isLoading: false,
    error: null,
    optimisticUpdates: new Map(),
  });

  const optimisticTimeoutRef = useRef<Map<string, NodeJS.Timeout>>(new Map());

  const recordPreference = useCallback(async (
    preferenceData: Omit<PreferenceRecord, 'id' | 'timestamp'>
  ): Promise<string> => {
    const optimisticId = `optimistic-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    // Create optimistic preference
    const optimisticPreference: PreferenceRecord = {
      ...preferenceData,
      id: optimisticId,
      timestamp: new Date().toISOString(),
      isOptimistic: true,
    };

    // Add optimistic update
    setState(prev => ({
      ...prev,
      optimisticUpdates: new Map(prev.optimisticUpdates.set(optimisticId, optimisticPreference)),
      preferences: [optimisticPreference, ...prev.preferences],
      stats: {
        ...prev.stats,
        totalPreferences: prev.stats.totalPreferences + 1,
        modelWinRates: {
          ...prev.stats.modelWinRates,
          [preferenceData.selectedModelId]: (prev.stats.modelWinRates[preferenceData.selectedModelId] || 0) + 1,
        },
        recentPreferences: [optimisticPreference, ...prev.stats.recentPreferences.slice(0, 9)],
      },
    }));

    try {
      // Record preference via API
      const actualPreference = await mockAPI.recordPreference(preferenceData);
      
      // Clear optimistic timeout
      const timeout = optimisticTimeoutRef.current.get(optimisticId);
      if (timeout) {
        clearTimeout(timeout);
        optimisticTimeoutRef.current.delete(optimisticId);
      }

      // Replace optimistic with actual
      setState(prev => {
        const newOptimisticUpdates = new Map(prev.optimisticUpdates);
        newOptimisticUpdates.delete(optimisticId);
        
        const updatedPreferences = prev.preferences.map(p => 
          p.id === optimisticId 
            ? { ...actualPreference, isOptimistic: false }
            : p
        );

        return {
          ...prev,
          optimisticUpdates: newOptimisticUpdates,
          preferences: updatedPreferences,
          error: null,
        };
      });

      return actualPreference.id;
    } catch (error) {
      // Set timeout to remove optimistic update after delay
      const timeout = setTimeout(() => {
        setState(prev => {
          const newOptimisticUpdates = new Map(prev.optimisticUpdates);
          newOptimisticUpdates.delete(optimisticId);
          
          return {
            ...prev,
            optimisticUpdates: newOptimisticUpdates,
            preferences: prev.preferences.filter(p => p.id !== optimisticId),
            stats: {
              ...prev.stats,
              totalPreferences: Math.max(0, prev.stats.totalPreferences - 1),
              modelWinRates: {
                ...prev.stats.modelWinRates,
                [preferenceData.selectedModelId]: Math.max(0, 
                  (prev.stats.modelWinRates[preferenceData.selectedModelId] || 0) - 1
                ),
              },
              recentPreferences: prev.stats.recentPreferences.filter(p => p.id !== optimisticId),
            },
            error: `Failed to record preference: ${error instanceof Error ? error.message : 'Unknown error'}`,
          };
        });
        optimisticTimeoutRef.current.delete(optimisticId);
      }, 3000);

      optimisticTimeoutRef.current.set(optimisticId, timeout);
      
      throw error;
    }
  }, []);

  const addFeedback = useCallback(async (
    preferenceId: string, 
    feedback: PreferenceFeedbackData
  ): Promise<void> => {
    // Optimistically update the preference
    setState(prev => ({
      ...prev,
      preferences: prev.preferences.map(p => 
        p.id === preferenceId 
          ? { ...p, feedback }
          : p
      ),
    }));

    try {
      await mockAPI.updatePreferenceFeedback(preferenceId, feedback);
      setState(prev => ({ ...prev, error: null }));
    } catch (error) {
      // Revert optimistic update on error
      setState(prev => ({
        ...prev,
        preferences: prev.preferences.map(p => 
          p.id === preferenceId 
            ? { ...p, feedback: undefined }
            : p
        ),
        error: `Failed to add feedback: ${error instanceof Error ? error.message : 'Unknown error'}`,
      }));
    }
  }, []);

  const loadStats = useCallback(async (): Promise<void> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const stats = await mockAPI.getPreferenceStats();
      setState(prev => ({
        ...prev,
        stats,
        isLoading: false,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: `Failed to load stats: ${error instanceof Error ? error.message : 'Unknown error'}`,
        isLoading: false,
      }));
    }
  }, []);

  const clearError = useCallback((): void => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  const getPreferenceForTurn = useCallback((turnId: string): PreferenceRecord | undefined => {
    return state.preferences.find(p => p.turnId === turnId);
  }, [state.preferences]);

  const getModelWinRate = useCallback((modelId: string): number => {
    const total = state.stats.totalPreferences;
    const wins = state.stats.modelWinRates[modelId] || 0;
    return total > 0 ? (wins / total) * 100 : 0;
  }, [state.stats]);

  const getOptimisticPreferences = useCallback((): PreferenceRecord[] => {
    return Array.from(state.optimisticUpdates.values());
  }, [state.optimisticUpdates]);

  return {
    // State
    preferences: state.preferences,
    stats: state.stats,
    isLoading: state.isLoading,
    error: state.error,
    optimisticPreferences: getOptimisticPreferences(),

    // Actions
    recordPreference,
    addFeedback,
    loadStats,
    clearError,

    // Selectors
    getPreferenceForTurn,
    getModelWinRate,
  };
}

