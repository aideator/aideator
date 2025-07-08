'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

export interface StreamMessage {
  variation_id: number;
  content: string;
  timestamp: string;
}

export interface AgentStreamState {
  streams: Map<number, string[]>;
  isStreaming: boolean;
  error: string | null;
  connectionState: 'disconnected' | 'connecting' | 'connected' | 'error';
}

export interface AgentStreamHook extends AgentStreamState {
  startStream: (runId: string) => void;
  stopStream: () => void;
  clearStreams: () => void;
  selectAgent: (variationId: number) => Promise<void>;
}

export function useAgentStream(): AgentStreamHook {
  const [streams, setStreams] = useState<Map<number, string[]>>(new Map());
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionState, setConnectionState] = useState<AgentStreamState['connectionState']>('disconnected');
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const currentRunIdRef = useRef<string | null>(null);

  const stopStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsStreaming(false);
    setConnectionState('disconnected');
    currentRunIdRef.current = null;
  }, []);

  const clearStreams = useCallback(() => {
    setStreams(new Map());
    setError(null);
  }, []);

  const startStream = useCallback((runId: string) => {
    // Stop any existing stream
    stopStream();
    
    // Clear previous streams and errors
    clearStreams();
    setConnectionState('connecting');
    setIsStreaming(true);
    currentRunIdRef.current = runId;

    try {
      const eventSource = new EventSource(
        `http://localhost:8000/api/v1/runs/${runId}/stream`,
        {
          withCredentials: false
        }
      );

      eventSource.onopen = () => {
        console.log('SSE connection opened for run:', runId);
        setConnectionState('connected');
        setError(null);
      };

      eventSource.onmessage = (event) => {
        try {
          const data: StreamMessage = JSON.parse(event.data);
          
          setStreams(prevStreams => {
            const newStreams = new Map(prevStreams);
            const existing = newStreams.get(data.variation_id) || [];
            newStreams.set(data.variation_id, [...existing, data.content]);
            return newStreams;
          });
        } catch (parseError) {
          console.error('Failed to parse SSE message:', parseError, 'Raw data:', event.data);
          // Don't set error for individual message parsing failures
        }
      };

      eventSource.onerror = (event) => {
        console.error('SSE connection error:', event);
        setError('Streaming connection failed');
        setConnectionState('error');
        setIsStreaming(false);
        
        // Auto-reconnect after a delay if the run is still active
        if (currentRunIdRef.current === runId) {
          setTimeout(() => {
            if (currentRunIdRef.current === runId) {
              console.log('Attempting to reconnect SSE for run:', runId);
              startStream(runId);
            }
          }, 3000);
        }
      };

      // Handle specific event types if the backend sends them
      eventSource.addEventListener('agent-complete', (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log(`Agent ${data.variation_id} completed`);
          // Could add completion state tracking here
        } catch (parseError) {
          console.error('Failed to parse agent-complete event:', parseError);
        }
      });

      eventSource.addEventListener('run-complete', (event) => {
        console.log('Run completed, stopping stream');
        stopStream();
      });

      eventSourceRef.current = eventSource;

    } catch (initError) {
      console.error('Failed to initialize SSE connection:', initError);
      setError('Failed to start streaming connection');
      setConnectionState('error');
      setIsStreaming(false);
    }
  }, [stopStream, clearStreams]);

  const selectAgent = useCallback(async (variationId: number): Promise<void> => {
    if (!currentRunIdRef.current) {
      throw new Error('No active run to select from');
    }

    try {
      const response = await fetch(`http://localhost:8000/api/v1/runs/${currentRunIdRef.current}/select`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ variation_id: variationId }),
      });

      if (!response.ok) {
        throw new Error(`Failed to select agent: ${response.statusText}`);
      }

      const result = await response.json();
      console.log('Agent selected successfully:', result);
      
      // Optionally stop streaming after selection
      // stopStream();
      
    } catch (selectError) {
      console.error('Failed to select agent:', selectError);
      throw selectError;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopStream();
    };
  }, [stopStream]);

  return {
    streams,
    isStreaming,
    error,
    connectionState,
    startStream,
    stopStream,
    clearStreams,
    selectAgent,
  };
}

// Utility hook for formatting stream content
export function useFormattedStream(content: string[]): string {
  return content.join('');
}

// Utility hook for getting agent color by variation ID
export function useAgentColor(variationId: number): string {
  const colors = [
    'agent-1', // Red
    'agent-2', // Amber
    'agent-3', // Emerald
    'agent-4', // Blue
    'agent-5', // Purple
  ];
  
  return colors[variationId % colors.length] || 'agent-1';
}