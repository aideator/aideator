'use client';

import { useState, useCallback, useRef } from 'react';
import { SessionTurn } from '@/context/SessionContext';
import { PreferenceRecord } from './usePreferenceStore';

export interface ModelComparisonRequest {
  sessionId?: string; // Optional - backend will auto-create if not provided
  prompt: string;
  modelIds: string[];
  instanceIds?: string[]; // Frontend instance IDs for state management
  maxTokens?: number;
  temperature?: number;
  systemPrompt?: string;
  agentMode?: string; // Agent execution mode
  repositoryUrl?: string; // GitHub repository URL (only for code modes)
  turnId?: string; // Turn ID for existing turns
}

export interface ModelComparisonResponse {
  runId: string;
  sessionId: string;
  turnId: string;
  modelResponses: {
    modelId: string;
    modelName: string;
    status: 'pending' | 'streaming' | 'completed' | 'error';
    response: string;
    responseTime?: number;
    tokenCount?: number;
    cost?: number;
    error?: string;
  }[];
  metadata: {
    totalTokens: number;
    totalCost: number;
    averageResponseTime: number;
    startTime: string;
    endTime?: string;
  };
}

export interface StreamingUpdate {
  runId: string;
  modelId: string;
  type: 'start' | 'chunk' | 'complete' | 'error';
  content?: string;
  metadata?: {
    tokenCount?: number;
    responseTime?: number;
    cost?: number;
  };
  error?: string;
}

interface APIIntegrationState {
  activeComparisons: Map<string, ModelComparisonResponse>;
  streamingConnections: Map<string, EventSource>;
  isConnected: boolean;
  connectionRetries: number;
  lastError: string | null;
}

// Mock API configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const MAX_RETRY_ATTEMPTS = 3;
const RETRY_DELAY = 1000;

export function useAPIIntegration() {
  const [state, setState] = useState<APIIntegrationState>({
    activeComparisons: new Map(),
    streamingConnections: new Map(),
    isConnected: false,
    connectionRetries: 0,
    lastError: null,
  });

  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const startModelComparison = useCallback(async (
    request: ModelComparisonRequest,
    onUpdate: (update: StreamingUpdate) => void
  ): Promise<{ runId: string; sessionId: string; turnId: string }> => {
    try {
      setState(prev => ({ ...prev, lastError: null }));

      // Transform model IDs to model variants for the API
      // For now, we'll use a simple mapping. In production, this should be enhanced
      // to properly fetch user credentials for each provider
      const modelVariants = request.modelIds.map((modelId, index) => {
        // Extract provider from model ID (e.g., "gpt-4" -> "openai")
        let provider = 'openai'; // default
        if (modelId.includes('claude')) provider = 'anthropic';
        else if (modelId.includes('gemini')) provider = 'gemini';
        else if (modelId.includes('mixtral') || modelId.includes('mistral')) provider = 'mistral';
        
        return {
          model_definition_id: modelId,
          provider_credential_id: null, // Let backend use default credentials if available
          model_parameters: {
            temperature: request.temperature || 0.7,
            max_tokens: request.maxTokens || 4096,
          }
        };
      });

      // Prepare request body based on agent mode
      const requestBody: any = {
        prompt: request.prompt,
        model_variants: modelVariants,
        use_claude_code: false,
        agent_mode: request.agentMode || 'litellm',
      };
      
      // Only include session_id if we have a real session
      // Let the backend auto-create a session if none is provided
      if (request.sessionId && request.sessionId.trim() !== '') {
        requestBody.session_id = request.sessionId;
      }
      
      // Only include turn_id if we have a real turn
      if (request.turnId) {
        requestBody.turn_id = request.turnId;
      }

      // Include github_url - required by backend schema
      if (request.repositoryUrl) {
        requestBody.github_url = request.repositoryUrl;
      } else {
        // Use default repository URL when none is provided
        requestBody.github_url = 'https://github.com/octocat/Hello-World';
      }

      console.log('🔥 API Request details:', {
        url: `${API_BASE_URL}/api/v1/runs`,
        requestBody: requestBody,
        apiKey: localStorage.getItem('api_key') ? '***set***' : 'NOT SET',
      });

      // Start comparison via runs API
      const response = await fetch(`${API_BASE_URL}/api/v1/runs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': localStorage.getItem('api_key') || '', // Use API key authentication
        },
        body: JSON.stringify(requestBody),
      });

      console.log('🔥 Response status:', response.status, response.statusText);
      console.log('🔥 Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.log('🔥 Error response text:', errorText);
        
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch {
          errorData = { detail: errorText };
        }
        
        const errorMessage = Array.isArray(errorData.detail) 
          ? errorData.detail.map((err: any) => err.msg || err).join(', ')
          : errorData.detail || errorData.message || `API request failed: ${response.status} ${response.statusText}`;
        throw new Error(errorMessage);
      }

      const responseText = await response.text();
      console.log('🔥 Success response text:', responseText);
      
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        console.error('🚨 Failed to parse response JSON:', parseError);
        throw new Error(`Invalid JSON response: ${responseText}`);
      }
      
      console.log('🔥 Parsed response data:', data);
      const runId = data.run_id;
      const sessionId = data.session_id;
      const turnId = data.turn_id;
      console.log('🔥 Extracted runId:', runId, 'sessionId:', sessionId, 'turnId:', turnId);

      // Initialize comparison state
      console.log('🔥 BACKEND: Request data:', { 
        modelIds: request.modelIds, 
        instanceIds: request.instanceIds 
      });
      
      const initialResponse: ModelComparisonResponse = {
        runId,
        sessionId: sessionId, // Use the session ID returned from backend
        turnId: turnId, // Use the turn ID returned from backend
        modelResponses: request.modelIds.map((modelId, index) => {
          const finalModelId = request.instanceIds?.[index] || modelId;
          console.log(`🔥 BACKEND: Mapping index ${index}: ${modelId} -> ${finalModelId}`);
          return {
            modelId: finalModelId, // Use instance ID if available, fallback to base model ID
            modelName: modelId, // Will be enriched from model selection
            status: 'pending',
            response: '',
          };
        }),
        metadata: {
          totalTokens: 0,
          totalCost: 0,
          averageResponseTime: 0,
          startTime: new Date().toISOString(),
        },
      };

      setState(prev => ({
        ...prev,
        activeComparisons: new Map(prev.activeComparisons.set(runId, initialResponse)),
        isConnected: true,
        connectionRetries: 0,
      }));

      // Start streaming updates
      startStreaming(runId, onUpdate);

      return { runId, sessionId, turnId };
    } catch (error) {
      console.error('🚨 useAPIIntegration error:', error);
      console.error('🚨 Error type:', typeof error);
      console.error('🚨 Error stringified:', JSON.stringify(error, null, 2));
      
      const errorMessage = error instanceof Error ? error.message : (typeof error === 'string' ? error : `Unknown error: ${JSON.stringify(error)}`);
      setState(prev => ({ ...prev, lastError: errorMessage }));
      throw new Error(errorMessage);
    }
  }, []);

  const startStreaming = useCallback((
    runId: string,
    onUpdate: (update: StreamingUpdate) => void
  ): void => {
    const apiKey = localStorage.getItem('api_key');
    const eventSource = new EventSource(`${API_BASE_URL}/api/v1/runs/${runId}/stream${apiKey ? `?api_key=${apiKey}` : ''}`);

    eventSource.onopen = () => {
      setState(prev => ({
        ...prev,
        streamingConnections: new Map(prev.streamingConnections.set(runId, eventSource)),
        isConnected: true,
        connectionRetries: 0,
      }));
    };

    // Handle different event types
    eventSource.addEventListener('agent_output', (event) => {
      try {
        const data = JSON.parse(event.data);
        const variationId = data.variation_id;
        
        console.log('🔥 FRONTEND: Received agent_output event:', { runId, variationId, content: data.content.substring(0, 50) + '...' });
        
        // Map variation ID to model ID (assuming variation IDs map to model array indices)  
        const comparison = state.activeComparisons.get(runId);
        console.log('🔍 FRONTEND: Comparison data check:', { 
          hasComparison: !!comparison, 
          variationId, 
          responseCount: comparison?.modelResponses?.length 
        });
        
        if (!comparison) {
          console.log('❌ FRONTEND: No comparison data found for runId:', runId);
          return;
        }
        if (variationId >= comparison.modelResponses.length) {
          console.log('❌ FRONTEND: variationId out of bounds:', { variationId, responseCount: comparison.modelResponses.length });
          return;
        }
        
        // Use the instance-specific modelId from the comparison data
        const modelId = comparison.modelResponses[variationId].modelId;
        console.log('🔧 FRONTEND: Mapping variation', variationId, 'to modelId:', modelId);
        console.log('🔧 FRONTEND: Available responses:', comparison.modelResponses.map((r, i) => ({ index: i, id: r.modelId })));
        
        // Parse the content to check if it's a JSON log entry
        let content = data.content;
        try {
          const logEntry = JSON.parse(data.content);
          if (logEntry.message && logEntry.chunk) {
            content = logEntry.chunk;
          }
        } catch {
          // Not JSON, use as-is
        }
        
        const update: StreamingUpdate = {
          runId,
          modelId,
          type: 'chunk',
          content,
        };
        
        console.log('🔄 FRONTEND: Creating update:', { runId, modelId, variationId, content: content.substring(0, 50) + '...' });
        
        // Update local state
        setState(prev => {
          const comparison = prev.activeComparisons.get(runId);
          if (!comparison) return prev;

          const updatedComparison = {
            ...comparison,
            modelResponses: comparison.modelResponses.map((response, idx) => {
              if (idx === variationId) {
                return { 
                  ...response, 
                  response: response.response + content,
                  status: 'streaming' as const,
                };
              }
              return response;
            }),
          };

          return {
            ...prev,
            activeComparisons: new Map(prev.activeComparisons.set(runId, updatedComparison)),
          };
        });

        // Call external update handler
        console.log('📤 FRONTEND: Calling onUpdate callback:', { runId, modelId, type: update.type });
        onUpdate(update);
      } catch (error) {
        console.error('Failed to parse agent_output event:', error);
      }
    });

    eventSource.addEventListener('agent_complete', (event) => {
      try {
        const data = JSON.parse(event.data);
        const variationId = data.variation_id;
        
        const comparison = state.activeComparisons.get(runId);
        if (!comparison || variationId >= comparison.modelResponses.length) return;
        
        const modelId = comparison.modelResponses[variationId].modelId;
        
        const update: StreamingUpdate = {
          runId,
          modelId,
          type: 'complete',
        };
        
        // Update local state
        setState(prev => {
          const comparison = prev.activeComparisons.get(runId);
          if (!comparison) return prev;

          const updatedComparison = {
            ...comparison,
            modelResponses: comparison.modelResponses.map((response, idx) => {
              if (idx === variationId) {
                return { 
                  ...response, 
                  status: 'completed' as const,
                };
              }
              return response;
            }),
          };

          return {
            ...prev,
            activeComparisons: new Map(prev.activeComparisons.set(runId, updatedComparison)),
          };
        });

        // Call external update handler
        onUpdate(update);
      } catch (error) {
        console.error('Failed to parse agent_complete event:', error);
      }
    });

    eventSource.addEventListener('agent_error', (event) => {
      try {
        const data = JSON.parse(event.data);
        const variationId = data.variation_id;
        
        const comparison = state.activeComparisons.get(runId);
        if (!comparison || variationId >= comparison.modelResponses.length) return;
        
        const modelId = comparison.modelResponses[variationId].modelId;
        
        const update: StreamingUpdate = {
          runId,
          modelId,
          type: 'error',
          error: data.error,
        };
        
        // Update local state
        setState(prev => {
          const comparison = prev.activeComparisons.get(runId);
          if (!comparison) return prev;

          const updatedComparison = {
            ...comparison,
            modelResponses: comparison.modelResponses.map((response, idx) => {
              if (idx === variationId) {
                return { 
                  ...response, 
                  status: 'error' as const,
                  error: data.error,
                };
              }
              return response;
            }),
          };

          return {
            ...prev,
            activeComparisons: new Map(prev.activeComparisons.set(runId, updatedComparison)),
          };
        });

        // Call external update handler
        onUpdate(update);
      } catch (error) {
        console.error('Failed to parse agent_error event:', error);
      }
    });

    eventSource.addEventListener('run_complete', (event) => {
      try {
        const data = JSON.parse(event.data);
        
        setState(prev => {
          const comparison = prev.activeComparisons.get(runId);
          if (!comparison) return prev;

          const updatedComparison = {
            ...comparison,
            metadata: {
              ...comparison.metadata,
              endTime: data.timestamp,
            },
          };

          return {
            ...prev,
            activeComparisons: new Map(prev.activeComparisons.set(runId, updatedComparison)),
          };
        });
      } catch (error) {
        console.error('Failed to parse run_complete event:', error);
      }
    });

    // Heartbeat events
    eventSource.addEventListener('heartbeat', (event) => {
      // Just log for now
      console.debug('Heartbeat received:', event.data);
    });

    eventSource.onerror = (error) => {
      console.error('Streaming error:', error);
      
      setState(prev => {
        const newRetries = prev.connectionRetries + 1;
        
        if (newRetries <= MAX_RETRY_ATTEMPTS) {
          // Retry connection
          if (retryTimeoutRef.current) {
            clearTimeout(retryTimeoutRef.current);
          }
          
          retryTimeoutRef.current = setTimeout(() => {
            eventSource.close();
            startStreaming(runId, onUpdate);
          }, RETRY_DELAY * newRetries);
        } else {
          // Max retries reached
          eventSource.close();
          const connections = new Map(prev.streamingConnections);
          connections.delete(runId);
          
          return {
            ...prev,
            streamingConnections: connections,
            isConnected: false,
            lastError: 'Connection failed after maximum retries',
          };
        }

        return {
          ...prev,
          connectionRetries: newRetries,
          isConnected: false,
        };
      });
    };
  }, []);

  const stopComparison = useCallback((runId: string): void => {
    const eventSource = state.streamingConnections.get(runId);
    if (eventSource) {
      eventSource.close();
      setState(prev => {
        const newConnections = new Map(prev.streamingConnections);
        newConnections.delete(runId);
        
        return {
          ...prev,
          streamingConnections: newConnections,
          isConnected: newConnections.size > 0,
        };
      });
    }
  }, [state.streamingConnections]);

  const recordPreference = useCallback(async (
    runId: string,
    selectedModelId: string,
    feedback?: any
  ): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/preferences`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify({
          runId,
          selectedModelId,
          feedback,
          timestamp: new Date().toISOString(),
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to record preference: ${response.status}`);
      }

      setState(prev => ({ ...prev, lastError: null }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setState(prev => ({ ...prev, lastError: errorMessage }));
      throw error;
    }
  }, []);

  const getComparisonResult = useCallback((runId: string): ModelComparisonResponse | undefined => {
    return state.activeComparisons.get(runId);
  }, [state.activeComparisons]);

  const getAllActiveComparisons = useCallback((): ModelComparisonResponse[] => {
    return Array.from(state.activeComparisons.values());
  }, [state.activeComparisons]);

  const isStreamingActive = useCallback((runId: string): boolean => {
    return state.streamingConnections.has(runId);
  }, [state.streamingConnections]);

  const getConnectionStatus = useCallback(() => {
    return {
      isConnected: state.isConnected,
      activeConnections: state.streamingConnections.size,
      retryCount: state.connectionRetries,
      lastError: state.lastError,
    };
  }, [state.isConnected, state.streamingConnections.size, state.connectionRetries, state.lastError]);

  const clearError = useCallback((): void => {
    setState(prev => ({ ...prev, lastError: null }));
  }, []);

  const cleanup = useCallback((): void => {
    // Close all streaming connections
    state.streamingConnections.forEach((eventSource) => {
      eventSource.close();
    });

    // Clear retry timeout
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
    }

    setState({
      activeComparisons: new Map(),
      streamingConnections: new Map(),
      isConnected: false,
      connectionRetries: 0,
      lastError: null,
    });
  }, [state.streamingConnections]);

  return {
    // State
    activeComparisons: state.activeComparisons,
    isConnected: state.isConnected,
    lastError: state.lastError,

    // Actions
    startModelComparison,
    stopComparison,
    recordPreference,
    clearError,
    cleanup,

    // Selectors
    getComparisonResult,
    getAllActiveComparisons,
    isStreamingActive,
    getConnectionStatus,
  };
}

export default useAPIIntegration;