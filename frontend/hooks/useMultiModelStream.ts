import { useState, useCallback, useRef, useEffect } from 'react';
import { createPrompt, recordPreference, type CreatePromptRequest, type ModelResponse, type PromptDetails } from '@/lib/api-client';

export interface MultiModelStreamState {
  promptId: string | null;
  sessionId: string | null;
  models: string[];
  modelResponses: Map<string, ModelResponse>;
  isStreaming: boolean;
  error: string | null;
  connectionState: 'disconnected' | 'connecting' | 'connected' | 'error';
  selectedModelId: string | null;
}

export interface MultiModelStreamHook extends MultiModelStreamState {
  startComparison: (request: CreatePromptRequest) => Promise<void>;
  stopComparison: () => void;
  clearResults: () => void;
  selectModel: (modelId: string, feedback?: string) => Promise<void>;
  pauseModel: (modelId: string) => void;
  resumeModel: (modelId: string) => void;
  pauseAll: () => void;
  resumeAll: () => void;
}

interface StreamBuffer {
  modelId: string;
  buffer: string[];
  isPaused: boolean;
  lastUpdate: number;
}

export function useMultiModelStream(): MultiModelStreamHook {
  const [promptId, setPromptId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [models, setModels] = useState<string[]>([]);
  const [modelResponses, setModelResponses] = useState<Map<string, ModelResponse>>(new Map());
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionState, setConnectionState] = useState<MultiModelStreamState['connectionState']>('disconnected');
  const [selectedModelId, setSelectedModelId] = useState<string | null>(null);
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const streamBuffersRef = useRef<Map<string, StreamBuffer>>(new Map());
  const flushTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Initialize stream buffers for models
  const initializeBuffers = useCallback((modelIds: string[]) => {
    const buffers = new Map<string, StreamBuffer>();
    modelIds.forEach(modelId => {
      buffers.set(modelId, {
        modelId,
        buffer: [],
        isPaused: false,
        lastUpdate: Date.now()
      });
    });
    streamBuffersRef.current = buffers;
  }, []);
  
  // Buffer management for smooth streaming
  const addToBuffer = useCallback((modelId: string, content: string) => {
    const buffer = streamBuffersRef.current.get(modelId);
    if (buffer && !buffer.isPaused) {
      buffer.buffer.push(content);
      buffer.lastUpdate = Date.now();
      
      // Flush buffer if it's getting large
      if (buffer.buffer.length > 10) {
        flushBuffer(modelId);
      }
    }
  }, []);
  
  const flushBuffer = useCallback((modelId: string) => {
    const buffer = streamBuffersRef.current.get(modelId);
    if (buffer && buffer.buffer.length > 0) {
      const content = buffer.buffer.join('');
      buffer.buffer = [];
      
      setModelResponses(prev => {
        const newResponses = new Map(prev);
        const existing = newResponses.get(modelId);
        if (existing) {
          newResponses.set(modelId, {
            ...existing,
            content: (existing.content || '') + content
          });
        }
        return newResponses;
      });
    }
  }, []);
  
  const flushAllBuffers = useCallback(() => {
    streamBuffersRef.current.forEach((_, modelId) => {
      flushBuffer(modelId);
    });
  }, [flushBuffer]);
  
  // Auto-flush buffers periodically
  useEffect(() => {
    if (isStreaming) {
      flushTimeoutRef.current = setInterval(() => {
        flushAllBuffers();
      }, 100); // Flush every 100ms
      
      return () => {
        if (flushTimeoutRef.current) {
          clearInterval(flushTimeoutRef.current);
        }
      };
    }
  }, [isStreaming, flushAllBuffers]);
  
  const stopComparison = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    
    // Final flush of all buffers
    flushAllBuffers();
    
    setIsStreaming(false);
    setConnectionState('disconnected');
    
    // Clean up timeout
    if (flushTimeoutRef.current) {
      clearInterval(flushTimeoutRef.current);
      flushTimeoutRef.current = null;
    }
  }, [flushAllBuffers]);
  
  const startComparison = useCallback(async (request: CreatePromptRequest) => {
    try {
      setError(null);
      setConnectionState('connecting');
      
      // Stop any existing comparison
      stopComparison();
      
      // Create prompt via API
      const response = await createPrompt(request);
      
      setPromptId(response.prompt_id);
      setSessionId(response.session_id);
      setModels(response.models);
      
      // Initialize model responses
      const initialResponses = new Map<string, ModelResponse>();
      response.models.forEach(model => {
        initialResponses.set(model, {
          model_id: model,
          model_name: model,
          status: 'pending',
          content: ''
        });
      });
      setModelResponses(initialResponses);
      
      // Initialize stream buffers
      initializeBuffers(response.models);
      
      // Start SSE stream
      const streamUrl = `http://localhost:8000/api/v1/prompts/${response.prompt_id}/stream`;
      console.log('Starting multi-model SSE stream to:', streamUrl);
      
      const eventSource = new EventSource(streamUrl, {
        withCredentials: false
      });
      
      eventSource.onopen = () => {
        console.log('Multi-model SSE connection opened');
        setConnectionState('connected');
        setIsStreaming(true);
      };
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Multi-model SSE event:', data);
          
          switch (data.type) {
            case 'model_output':
              addToBuffer(data.model_id, data.content);
              setModelResponses(prev => {
                const newResponses = new Map(prev);
                const existing = newResponses.get(data.model_id);
                if (existing) {
                  newResponses.set(data.model_id, {
                    ...existing,
                    status: 'streaming'
                  });
                }
                return newResponses;
              });
              break;
              
            case 'model_complete':
              // Final flush for this model
              flushBuffer(data.model_id);
              
              setModelResponses(prev => {
                const newResponses = new Map(prev);
                const existing = newResponses.get(data.model_id);
                if (existing) {
                  newResponses.set(data.model_id, {
                    ...existing,
                    status: 'completed',
                    response_time_ms: data.response_time_ms,
                    token_count: data.token_count,
                    cost_usd: data.cost_usd
                  });
                }
                return newResponses;
              });
              break;
              
            case 'model_error':
              setModelResponses(prev => {
                const newResponses = new Map(prev);
                const existing = newResponses.get(data.model_id);
                if (existing) {
                  newResponses.set(data.model_id, {
                    ...existing,
                    status: 'error',
                    error_message: data.error_message
                  });
                }
                return newResponses;
              });
              break;
              
            case 'comparison_complete':
              setIsStreaming(false);
              setConnectionState('disconnected');
              break;
              
            case 'heartbeat':
              // Keep connection alive
              break;
              
            default:
              console.log('Unknown event type:', data.type);
          }
        } catch (e) {
          console.error('Failed to parse SSE message:', e);
        }
      };
      
      eventSource.onerror = (event) => {
        console.error('Multi-model SSE error:', event);
        setError('Connection error occurred');
        setConnectionState('error');
        setIsStreaming(false);
      };
      
      eventSourceRef.current = eventSource;
      
    } catch (error) {
      console.error('Failed to start comparison:', error);
      setError(error instanceof Error ? error.message : 'Failed to start comparison');
      setConnectionState('error');
      setIsStreaming(false);
    }
  }, [addToBuffer, flushBuffer, initializeBuffers, stopComparison]);
  
  const clearResults = useCallback(() => {
    setPromptId(null);
    setSessionId(null);
    setModels([]);
    setModelResponses(new Map());
    setSelectedModelId(null);
    setError(null);
    streamBuffersRef.current.clear();
  }, []);
  
  const selectModel = useCallback(async (modelId: string, feedback?: string) => {
    if (!promptId) {
      console.error('No prompt ID available for selection');
      return;
    }
    
    try {
      await recordPreference({
        prompt_id: promptId,
        chosen_model_id: modelId,
        feedback_text: feedback
      });
      
      setSelectedModelId(modelId);
      
      // Update model responses to show selection
      setModelResponses(prev => {
        const newResponses = new Map(prev);
        newResponses.forEach((response, id) => {
          if (id === modelId) {
            newResponses.set(id, { ...response, selected: true });
          } else if (response.selected) {
            newResponses.set(id, { ...response, selected: false });
          }
        });
        return newResponses;
      });
      
    } catch (error) {
      console.error('Failed to record preference:', error);
      setError('Failed to record preference');
    }
  }, [promptId]);
  
  const pauseModel = useCallback((modelId: string) => {
    const buffer = streamBuffersRef.current.get(modelId);
    if (buffer) {
      buffer.isPaused = true;
      console.log(`Paused streaming for model: ${modelId}`);
    }
  }, []);
  
  const resumeModel = useCallback((modelId: string) => {
    const buffer = streamBuffersRef.current.get(modelId);
    if (buffer) {
      buffer.isPaused = false;
      console.log(`Resumed streaming for model: ${modelId}`);
    }
  }, []);
  
  const pauseAll = useCallback(() => {
    streamBuffersRef.current.forEach((buffer, modelId) => {
      buffer.isPaused = true;
    });
    console.log('Paused all model streaming');
  }, []);
  
  const resumeAll = useCallback(() => {
    streamBuffersRef.current.forEach((buffer, modelId) => {
      buffer.isPaused = false;
    });
    console.log('Resumed all model streaming');
  }, []);
  
  return {
    promptId,
    sessionId,
    models,
    modelResponses,
    isStreaming,
    error,
    connectionState,
    selectedModelId,
    startComparison,
    stopComparison,
    clearResults,
    selectModel,
    pauseModel,
    resumeModel,
    pauseAll,
    resumeAll,
  };
}