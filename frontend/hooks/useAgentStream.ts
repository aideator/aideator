'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { StreamBuffer } from '@/lib/StreamBuffer';

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
  pauseStream: (variationId?: number) => void;
  resumeStream: (variationId?: number) => void;
}

export function useAgentStream(): AgentStreamHook {
  const [streams, setStreams] = useState<Map<number, string[]>>(new Map());
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionState, setConnectionState] = useState<AgentStreamState['connectionState']>('disconnected');
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const currentRunIdRef = useRef<string | null>(null);
  const streamBuffersRef = useRef<Map<number, StreamBuffer>>(new Map());

  const stopStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    // Destroy all stream buffers
    streamBuffersRef.current.forEach(buffer => buffer.destroy());
    streamBuffersRef.current.clear();
    
    setIsStreaming(false);
    setConnectionState('disconnected');
    currentRunIdRef.current = null;
  }, []);

  const pauseStream = useCallback((variationId?: number) => {
    if (variationId !== undefined) {
      // Pause specific stream
      const buffer = streamBuffersRef.current.get(variationId);
      if (buffer) {
        buffer.pause();
      }
    } else {
      // Pause all streams
      streamBuffersRef.current.forEach(buffer => buffer.pause());
    }
  }, []);

  const resumeStream = useCallback((variationId?: number) => {
    if (variationId !== undefined) {
      // Resume specific stream
      const buffer = streamBuffersRef.current.get(variationId);
      if (buffer) {
        buffer.resume();
      }
    } else {
      // Resume all streams
      streamBuffersRef.current.forEach(buffer => buffer.resume());
    }
  }, []);

  const createStreamBuffer = useCallback((variationId: number): StreamBuffer => {
    const buffer = new StreamBuffer({
      onToken: (token: string) => {
        setStreams(prevStreams => {
          const newStreams = new Map(prevStreams);
          const existing = newStreams.get(variationId) || [];
          newStreams.set(variationId, [...existing, token]);
          return newStreams;
        });
      },
      onFlush: () => {
        console.log(`Stream buffer for agent ${variationId} flushed`);
      }
    }, {
      tokensPerSecond: 50, // Smooth streaming rate
      minChunkSize: 5,     // Start streaming after 5 chars
      maxBufferSize: 1000, // Force drain at 1000 chars
      respectWordBoundaries: true,
      respectMarkdownBlocks: true
    });
    
    streamBuffersRef.current.set(variationId, buffer);
    return buffer;
  }, []);

  const clearStreams = useCallback(() => {
    setStreams(new Map());
    setError(null);
    // Destroy all stream buffers
    streamBuffersRef.current.forEach(buffer => buffer.destroy());
    streamBuffersRef.current.clear();
  }, []);

  const startStream = useCallback((runId: string) => {
    // Stop any existing stream
    stopStream();
    
    // Clear previous streams and errors
    clearStreams();
    setConnectionState('connecting');
    setIsStreaming(true);
    currentRunIdRef.current = runId;

    // Check which streaming backend to use - prefer localStorage over env var
    const storedBackend = typeof window !== 'undefined' ? localStorage.getItem('streamingBackend') : null;
    const streamingBackend = storedBackend || process.env.NEXT_PUBLIC_STREAMING_BACKEND || 'redis';
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    
    // Use Redis endpoint if configured, otherwise use kubectl endpoint
    const streamPath = streamingBackend === 'redis' 
      ? `/api/v1/runs/${runId}/stream/redis`
      : `/api/v1/runs/${runId}/stream`;
    
    const streamUrl = `${apiBase}${streamPath}`;
    console.log(`Starting SSE stream (${streamingBackend}) to:`, streamUrl);

    try {
      const eventSource = new EventSource(streamUrl, {
        withCredentials: false
      });

      eventSource.onopen = () => {
        console.log('SSE connection opened for run:', runId);
        setConnectionState('connected');
        setError(null);
        // Reset retry count on successful connection
        if (eventSourceRef.current) {
          (eventSourceRef as any).retryCount = 0;
        }
      };

      // The backend sends named events, not default messages
      // Handle agent output events
      eventSource.addEventListener('agent_output', (event) => {
        try {
          const data: StreamMessage = JSON.parse(event.data);
          
          // Filter out JSON log entries - only show actual content
          let shouldDisplay = true;
          let displayContent = data.content;
          
          try {
            const logEntry = JSON.parse(data.content);
            // If it's a JSON log entry with timestamp/level, skip it
            if (logEntry.timestamp && logEntry.level) {
              shouldDisplay = false;
              console.log('Agent log:', logEntry.message || logEntry);
            } else {
              // It's JSON but not a log, display it formatted
              displayContent = JSON.stringify(logEntry, null, 2);
            }
          } catch {
            // It's plain text markdown content, display as-is
            displayContent = data.content;
          }
          
          if (shouldDisplay) {
            // Get or create stream buffer for this variation
            let buffer = streamBuffersRef.current.get(data.variation_id);
            if (!buffer) {
              buffer = createStreamBuffer(data.variation_id);
            }
            
            // Add content to the smooth streaming buffer
            buffer.add(displayContent);
          }
        } catch (parseError) {
          console.error('Failed to parse agent_output event:', parseError, 'Raw data:', event.data);
        }
      });

      // Handle agent error events
      eventSource.addEventListener('agent_error', (event) => {
        try {
          const data = JSON.parse(event.data);
          console.error(`Agent ${data.variation_id} error:`, data.error);
          
          // Add error to stream as a special message
          setStreams(prevStreams => {
            const newStreams = new Map(prevStreams);
            const existing = newStreams.get(data.variation_id) || [];
            newStreams.set(data.variation_id, [...existing, `ERROR: ${data.error}`]);
            return newStreams;
          });
        } catch (parseError) {
          console.error('Failed to parse agent_error event:', parseError);
        }
      });

      // Handle agent complete events
      eventSource.addEventListener('agent_complete', (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log(`Agent ${data.variation_id} completed`);
          // Complete the stream buffer for this variation
          const buffer = streamBuffersRef.current.get(data.variation_id);
          if (buffer) {
            buffer.complete();
          }
        } catch (parseError) {
          console.error('Failed to parse agent_complete event:', parseError);
        }
      });

      // Handle run complete event
      eventSource.addEventListener('run_complete', (event) => {
        console.log('Run completed, stopping stream');
        stopStream();
      });

      // Handle heartbeat events
      eventSource.addEventListener('heartbeat', (event) => {
        console.log('Heartbeat received:', event.data);
        // Heartbeat keeps connection alive, no action needed
      });

      eventSource.onerror = (event) => {
        console.error('SSE connection error:', event);
        setError('Streaming connection failed');
        setConnectionState('error');
        setIsStreaming(false);
        
        // Enhanced reconnection logic for Redis
        const storedBackend = typeof window !== 'undefined' ? localStorage.getItem('streamingBackend') : null;
        const streamingBackend = storedBackend || process.env.NEXT_PUBLIC_STREAMING_BACKEND || 'redis';
        const isRedis = streamingBackend === 'redis';
        
        // Auto-reconnect with exponential backoff
        if (currentRunIdRef.current === runId) {
          const reconnectDelay = isRedis ? 1000 : 3000; // Faster reconnect for Redis
          const maxRetries = isRedis ? 10 : 3; // More retries for Redis
          
          // Track retry count (stored on the ref to persist across renders)
          if (!eventSourceRef.current) return;
          const retryCount = (eventSourceRef as any).retryCount || 0;
          
          if (retryCount < maxRetries) {
            const delay = Math.min(reconnectDelay * Math.pow(2, retryCount), 30000);
            console.log(`Attempting to reconnect SSE (${streamingBackend}) for run: ${runId} in ${delay}ms (retry ${retryCount + 1}/${maxRetries})`);
            
            setTimeout(() => {
              if (currentRunIdRef.current === runId) {
                (eventSourceRef as any).retryCount = retryCount + 1;
                startStream(runId);
              }
            }, delay);
          } else {
            console.error(`Max reconnection attempts (${maxRetries}) reached for ${streamingBackend} streaming`);
            setError(`Unable to maintain connection after ${maxRetries} attempts`);
          }
        }
      };

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

    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

    try {
      const response = await fetch(`${apiBase}/api/v1/runs/${currentRunIdRef.current}/select`, {
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
    pauseStream,
    resumeStream,
  };
}

// Utility hook for formatting stream content
export function useFormattedStream(content: string[]): string {
  // Join content array while preserving original formatting
  // The StreamBuffer already handles proper tokenization including newlines
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