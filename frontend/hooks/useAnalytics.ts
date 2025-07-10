'use client';

import { useState, useCallback, useEffect } from 'react';
import { 
  ModelPerformanceData 
} from '@/components/analytics/ModelComparisonChart';
import { 
  SessionMetrics 
} from '@/components/analytics/SessionAnalytics';
import { 
  RealTimeMetrics, 
  HistoricalMetrics 
} from '@/components/analytics/ResponseMetricsPanel';
import { 
  UserPreferenceData 
} from '@/components/analytics/UserPreferenceDashboard';

export interface AnalyticsState {
  modelPerformance: ModelPerformanceData[];
  sessionMetrics: SessionMetrics;
  realTimeMetrics: RealTimeMetrics[];
  historicalMetrics: HistoricalMetrics[];
  userPreferences: UserPreferenceData;
  isLoading: boolean;
  error: string | null;
  lastUpdated: string | null;
}

export interface AnalyticsFilters {
  timeRange: 'day' | 'week' | 'month' | 'quarter' | 'year' | 'all';
  models: string[];
  categories: string[];
  userId?: string;
}

// Mock API functions (replace with actual API calls)
const mockAPI = {
  getModelPerformance: async (filters: AnalyticsFilters): Promise<ModelPerformanceData[]> => {
    await new Promise(resolve => setTimeout(resolve, 800));
    
    return [
      {
        modelId: 'gpt-4',
        modelName: 'GPT-4',
        winRate: 45.2,
        averageResponseTime: 3.2,
        averageCost: 0.0234,
        totalComparisons: 156,
        totalWins: 71,
        color: 'agent-1',
      },
      {
        modelId: 'claude-3-opus',
        modelName: 'Claude-3 Opus',
        winRate: 38.7,
        averageResponseTime: 2.8,
        averageCost: 0.0198,
        totalComparisons: 142,
        totalWins: 55,
        color: 'agent-2',
      },
      {
        modelId: 'gemini-pro',
        modelName: 'Gemini Pro',
        winRate: 16.1,
        averageResponseTime: 2.1,
        averageCost: 0.0087,
        totalComparisons: 124,
        totalWins: 20,
        color: 'agent-3',
      },
    ];
  },

  getSessionMetrics: async (filters: AnalyticsFilters): Promise<SessionMetrics> => {
    await new Promise(resolve => setTimeout(resolve, 600));
    
    return {
      totalSessions: 89,
      averageSessionDuration: 425, // seconds
      averageTurnsPerSession: 3.2,
      totalTurns: 285,
      activeSessionsLast24h: 12,
      topModelsUsed: [
        { modelId: 'gpt-4', modelName: 'GPT-4', usageCount: 156, percentage: 45.2 },
        { modelId: 'claude-3-opus', modelName: 'Claude-3 Opus', usageCount: 142, percentage: 38.7 },
        { modelId: 'gemini-pro', modelName: 'Gemini Pro', usageCount: 124, percentage: 16.1 },
      ],
      sessionDurationDistribution: [
        { range: '< 1 min', count: 12, percentage: 13.5 },
        { range: '1-5 min', count: 34, percentage: 38.2 },
        { range: '5-15 min', count: 28, percentage: 31.5 },
        { range: '> 15 min', count: 15, percentage: 16.8 },
      ],
      turnsPerSessionDistribution: [
        { range: '1 turn', count: 23, percentage: 25.8 },
        { range: '2-3 turns', count: 32, percentage: 36.0 },
        { range: '4-6 turns', count: 21, percentage: 23.6 },
        { range: '7+ turns', count: 13, percentage: 14.6 },
      ],
    };
  },

  getHistoricalMetrics: async (filters: AnalyticsFilters): Promise<HistoricalMetrics[]> => {
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return [
      {
        modelId: 'gpt-4',
        modelName: 'GPT-4',
        averageResponseTime: 3.2,
        averageTokenCount: 487,
        averageCost: 0.0234,
        successRate: 94.2,
        totalRequests: 156,
        totalErrors: 9,
        trend: 'stable',
        trendPercentage: 2.1,
        color: 'agent-1',
      },
      {
        modelId: 'claude-3-opus',
        modelName: 'Claude-3 Opus',
        averageResponseTime: 2.8,
        averageTokenCount: 412,
        averageCost: 0.0198,
        successRate: 96.5,
        totalRequests: 142,
        totalErrors: 5,
        trend: 'up',
        trendPercentage: 5.3,
        color: 'agent-2',
      },
      {
        modelId: 'gemini-pro',
        modelName: 'Gemini Pro',
        averageResponseTime: 2.1,
        averageTokenCount: 356,
        averageCost: 0.0087,
        successRate: 91.9,
        totalRequests: 124,
        totalErrors: 10,
        trend: 'down',
        trendPercentage: 3.7,
        color: 'agent-3',
      },
    ];
  },

  getUserPreferences: async (filters: AnalyticsFilters): Promise<UserPreferenceData> => {
    await new Promise(resolve => setTimeout(resolve, 700));
    
    return {
      totalPreferences: 84,
      favoriteModel: {
        modelId: 'gpt-4',
        modelName: 'GPT-4',
        winRate: 45.2,
        totalWins: 38,
        color: 'agent-1',
      },
      modelPreferences: [
        {
          modelId: 'gpt-4',
          modelName: 'GPT-4',
          winRate: 45.2,
          totalComparisons: 84,
          totalWins: 38,
          averageRating: 4.2,
          color: 'agent-1',
        },
        {
          modelId: 'claude-3-opus',
          modelName: 'Claude-3 Opus',
          winRate: 38.7,
          totalComparisons: 72,
          totalWins: 28,
          averageRating: 3.8,
          color: 'agent-2',
        },
        {
          modelId: 'gemini-pro',
          modelName: 'Gemini Pro',
          winRate: 16.1,
          totalComparisons: 56,
          totalWins: 9,
          averageRating: 3.2,
          color: 'agent-3',
        },
      ],
      preferencesByPromptType: [
        {
          category: 'code analysis',
          favoriteModel: 'GPT-4',
          totalComparisons: 32,
          distribution: [
            { modelId: 'gpt-4', modelName: 'GPT-4', percentage: 50.0 },
            { modelId: 'claude-3-opus', modelName: 'Claude-3 Opus', percentage: 31.3 },
            { modelId: 'gemini-pro', modelName: 'Gemini Pro', percentage: 18.7 },
          ],
        },
        {
          category: 'creative writing',
          favoriteModel: 'Claude-3 Opus',
          totalComparisons: 24,
          distribution: [
            { modelId: 'claude-3-opus', modelName: 'Claude-3 Opus', percentage: 54.2 },
            { modelId: 'gpt-4', modelName: 'GPT-4', percentage: 33.3 },
            { modelId: 'gemini-pro', modelName: 'Gemini Pro', percentage: 12.5 },
          ],
        },
        {
          category: 'technical questions',
          favoriteModel: 'GPT-4',
          totalComparisons: 28,
          distribution: [
            { modelId: 'gpt-4', modelName: 'GPT-4', percentage: 46.4 },
            { modelId: 'claude-3-opus', modelName: 'Claude-3 Opus', percentage: 35.7 },
            { modelId: 'gemini-pro', modelName: 'Gemini Pro', percentage: 17.9 },
          ],
        },
      ],
      preferenceEvolution: [],
      recentPreferences: [
        {
          id: '1',
          modelId: 'gpt-4',
          modelName: 'GPT-4',
          prompt: 'Analyze this TypeScript code and suggest improvements',
          timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
          rating: 4,
          feedback: 'Great analysis with actionable suggestions',
        },
        {
          id: '2',
          modelId: 'claude-3-opus',
          modelName: 'Claude-3 Opus',
          prompt: 'Write a creative story about AI development',
          timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
          rating: 5,
          feedback: 'Excellent creativity and narrative flow',
        },
        {
          id: '3',
          modelId: 'gpt-4',
          modelName: 'GPT-4',
          prompt: 'Explain quantum computing concepts',
          timestamp: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
          rating: 4,
        },
      ],
    };
  },
};

export function useAnalytics() {
  const [state, setState] = useState<AnalyticsState>({
    modelPerformance: [],
    sessionMetrics: {
      totalSessions: 0,
      averageSessionDuration: 0,
      averageTurnsPerSession: 0,
      totalTurns: 0,
      activeSessionsLast24h: 0,
      topModelsUsed: [],
      sessionDurationDistribution: [],
      turnsPerSessionDistribution: [],
    },
    realTimeMetrics: [],
    historicalMetrics: [],
    userPreferences: {
      totalPreferences: 0,
      favoriteModel: {
        modelId: '',
        modelName: '',
        winRate: 0,
        totalWins: 0,
        color: 'agent-1',
      },
      modelPreferences: [],
      preferencesByPromptType: [],
      preferenceEvolution: [],
      recentPreferences: [],
    },
    isLoading: false,
    error: null,
    lastUpdated: null,
  });

  const [filters, setFilters] = useState<AnalyticsFilters>({
    timeRange: 'month',
    models: [],
    categories: [],
  });

  const loadAnalytics = useCallback(async (newFilters?: Partial<AnalyticsFilters>) => {
    const currentFilters = { ...filters, ...newFilters };
    
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const [modelPerformance, sessionMetrics, historicalMetrics, userPreferences] = await Promise.all([
        mockAPI.getModelPerformance(currentFilters),
        mockAPI.getSessionMetrics(currentFilters),
        mockAPI.getHistoricalMetrics(currentFilters),
        mockAPI.getUserPreferences(currentFilters),
      ]);

      setState(prev => ({
        ...prev,
        modelPerformance,
        sessionMetrics,
        historicalMetrics,
        userPreferences,
        isLoading: false,
        lastUpdated: new Date().toISOString(),
      }));

      if (newFilters) {
        setFilters(currentFilters);
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to load analytics',
        isLoading: false,
      }));
    }
  }, [filters]);

  const updateRealTimeMetrics = useCallback((metrics: RealTimeMetrics[]) => {
    setState(prev => ({
      ...prev,
      realTimeMetrics: metrics,
    }));
  }, []);

  const addRealTimeMetric = useCallback((metric: RealTimeMetrics) => {
    setState(prev => ({
      ...prev,
      realTimeMetrics: [...prev.realTimeMetrics.filter(m => m.modelId !== metric.modelId), metric],
    }));
  }, []);

  const updateTimeRange = useCallback((timeRange: AnalyticsFilters['timeRange']) => {
    loadAnalytics({ timeRange });
  }, [loadAnalytics]);

  const updateModelFilter = useCallback((models: string[]) => {
    loadAnalytics({ models });
  }, [loadAnalytics]);

  const updateCategoryFilter = useCallback((categories: string[]) => {
    loadAnalytics({ categories });
  }, [loadAnalytics]);

  const refreshAnalytics = useCallback(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  const getTotalCost = useCallback(() => {
    return state.realTimeMetrics.reduce((sum, metric) => sum + (metric.cost || 0), 0);
  }, [state.realTimeMetrics]);

  const getTotalTokens = useCallback(() => {
    return state.realTimeMetrics.reduce((sum, metric) => sum + (metric.tokenCount || 0), 0);
  }, [state.realTimeMetrics]);

  const getTotalRequests = useCallback(() => {
    return state.historicalMetrics.reduce((sum, metric) => sum + metric.totalRequests, 0);
  }, [state.historicalMetrics]);

  const isStreaming = useCallback(() => {
    return state.realTimeMetrics.some(metric => metric.status === 'streaming');
  }, [state.realTimeMetrics]);

  // Load initial data
  useEffect(() => {
    loadAnalytics();
  }, []);

  return {
    // State
    ...state,
    filters,
    
    // Actions
    loadAnalytics,
    updateRealTimeMetrics,
    addRealTimeMetric,
    updateTimeRange,
    updateModelFilter,
    updateCategoryFilter,
    refreshAnalytics,
    clearError,
    
    // Computed values
    totalCost: getTotalCost(),
    totalTokens: getTotalTokens(),
    totalRequests: getTotalRequests(),
    isStreaming: isStreaming(),
  };
}

export default useAnalytics;