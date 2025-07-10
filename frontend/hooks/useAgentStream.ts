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
  startStream: (runId: string, backend?: 'kubectl' | 'redis') => void;
  stopStream: () => void;
  clearStreams: () => void;
  selectAgent: (variationId: number) => Promise<void>;
  pauseStream: (variationId?: number) => void;
  resumeStream: (variationId?: number) => void;
  debugState: () => void;
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
        console.log('[STREAM-DEBUG] StreamBuffer onToken called:', {
          variationId,
          tokenLength: token.length,
          tokenPreview: token.substring(0, 50) + (token.length > 50 ? '...' : ''),
          timestamp: new Date().toISOString()
        });
        
        setStreams(prevStreams => {
          const newStreams = new Map(prevStreams);
          const existing = newStreams.get(variationId) || [];
          const newContent = [...existing, token];
          newStreams.set(variationId, newContent);
          
          console.log('[STREAM-DEBUG] Stream state updated:', {
            variationId,
            previousLength: existing.length,
            newLength: newContent.length,
            totalContentLength: newContent.join('').length
          });
          
          return newStreams;
        });
      },
      onFlush: () => {
        console.log('[STREAM-DEBUG] StreamBuffer flushed:', {
          variationId,
          timestamp: new Date().toISOString()
        });
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

  const startStream = useCallback((runId: string, backend?: 'kubectl' | 'redis') => {
    // Stop any existing stream
    stopStream();
    
    // Clear previous streams and errors
    clearStreams();
    setConnectionState('connecting');
    setIsStreaming(true);
    currentRunIdRef.current = runId;

    // Check which streaming backend to use - prefer parameter, then localStorage, then env var
    const storedBackend = typeof window !== 'undefined' ? localStorage.getItem('streamingBackend') : null;
    const streamingBackend = backend || storedBackend || process.env.NEXT_PUBLIC_STREAMING_BACKEND || 'redis';
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    
    // Use Redis endpoint if configured, otherwise use kubectl endpoint
    const streamPath = streamingBackend === 'redis' 
      ? `/api/v1/runs/${runId}/stream/redis`
      : `/api/v1/runs/${runId}/stream`;
    
    const streamUrl = `${apiBase}${streamPath}`;
    console.log(`[STREAM-DEBUG] Starting SSE stream:`, {
      backend: streamingBackend,
      runId,
      streamUrl,
      timestamp: new Date().toISOString()
    });

    try {
      const eventSource = new EventSource(streamUrl, {
        withCredentials: false
      });

      eventSource.onopen = () => {
        console.log('[STREAM-DEBUG] SSE connection opened:', {
          runId,
          backend: streamingBackend,
          readyState: eventSource.readyState,
          url: eventSource.url,
          timestamp: new Date().toISOString()
        });
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
        console.log('[STREAM-DEBUG] Received agent_output event:', {
          eventType: event.type,
          eventData: event.data,
          lastEventId: event.lastEventId,
          timestamp: new Date().toISOString()
        });
        
        try {
          const data: StreamMessage = JSON.parse(event.data);
          console.log('[STREAM-DEBUG] Parsed agent_output data:', {
            variation_id: data.variation_id,
            contentLength: data.content?.length || 0,
            contentPreview: data.content?.substring(0, 100) + (data.content?.length > 100 ? '...' : ''),
            timestamp: data.timestamp
          });
          
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
            console.log('[STREAM-DEBUG] Adding content to buffer:', {
              variation_id: data.variation_id,
              displayContentLength: displayContent.length,
              displayContentPreview: displayContent.substring(0, 50) + (displayContent.length > 50 ? '...' : '')
            });
            
            // Get or create stream buffer for this variation
            // Convert variation_id to number (Redis sends strings)
            const variationId = typeof data.variation_id === 'string' ? parseInt(data.variation_id, 10) : data.variation_id;
            let buffer = streamBuffersRef.current.get(variationId);
            if (!buffer) {
              console.log('[STREAM-DEBUG] Creating new stream buffer for variation:', variationId);
              buffer = createStreamBuffer(variationId);
            }
            
            // Add content to the smooth streaming buffer
            console.log('[STREAM-DEBUG] Calling buffer.add():', {
              variationId: variationId,
              contentLength: displayContent.length,
              hasBuffer: !!buffer,
              timestamp: new Date().toISOString()
            });
            buffer.add(displayContent);
          } else {
            console.log('[STREAM-DEBUG] Skipping display of JSON log entry');
          }
        } catch (parseError) {
          console.error('[STREAM-DEBUG] Failed to parse agent_output event:', {
            error: parseError,
            rawData: event.data,
            eventType: event.type
          });
        }
      });

      // Handle agent error events
      eventSource.addEventListener('agent_error', (event) => {
        console.log('[STREAM-DEBUG] Received agent_error event:', {
          eventType: event.type,
          eventData: event.data,
          timestamp: new Date().toISOString()
        });
        
        try {
          const data = JSON.parse(event.data);
          console.error('[STREAM-DEBUG] Agent error:', {
            variation_id: data.variation_id,
            error: data.error,
            timestamp: new Date().toISOString()
          });
          
          // Add error to stream as a special message
          setStreams(prevStreams => {
            const newStreams = new Map(prevStreams);
            const variationId = typeof data.variation_id === 'string' ? parseInt(data.variation_id, 10) : data.variation_id;
            const existing = newStreams.get(variationId) || [];
            newStreams.set(variationId, [...existing, `ERROR: ${data.error}`]);
            return newStreams;
          });
        } catch (parseError) {
          console.error('[STREAM-DEBUG] Failed to parse agent_error event:', {
            error: parseError,
            rawData: event.data
          });
        }
      });

      // Handle agent complete events
      eventSource.addEventListener('agent_complete', (event) => {
        console.log('[STREAM-DEBUG] Received agent_complete event:', {
          eventType: event.type,
          eventData: event.data,
          timestamp: new Date().toISOString()
        });
        
        try {
          const data = JSON.parse(event.data);
          console.log('[STREAM-DEBUG] Agent completed:', {
            variation_id: data.variation_id,
            timestamp: new Date().toISOString()
          });
          // Complete the stream buffer for this variation
          const variationId = typeof data.variation_id === 'string' ? parseInt(data.variation_id, 10) : data.variation_id;
          const buffer = streamBuffersRef.current.get(variationId);
          if (buffer) {
            buffer.complete();
          }
        } catch (parseError) {
          console.error('[STREAM-DEBUG] Failed to parse agent_complete event:', {
            error: parseError,
            rawData: event.data
          });
        }
      });

      // Handle run complete event
      eventSource.addEventListener('run_complete', (event) => {
        console.log('[STREAM-DEBUG] Received run_complete event:', {
          eventType: event.type,
          eventData: event.data,
          timestamp: new Date().toISOString()
        });
        console.log('[STREAM-DEBUG] Run completed, stopping stream');
        stopStream();
      });

      // Handle heartbeat events
      eventSource.addEventListener('heartbeat', (event) => {
        console.log('[STREAM-DEBUG] Heartbeat received:', {
          eventType: event.type,
          eventData: event.data,
          timestamp: new Date().toISOString()
        });
        // Heartbeat keeps connection alive, no action needed
      });

      eventSource.onerror = (event) => {
        console.error('[STREAM-DEBUG] SSE connection error:', {
          error: event,
          readyState: eventSource.readyState,
          url: eventSource.url,
          backend: streamingBackend,
          timestamp: new Date().toISOString(),
          readyStateMapping: {
            0: 'CONNECTING',
            1: 'OPEN',
            2: 'CLOSED'
          }[eventSource.readyState]
        });
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
            console.log('[STREAM-DEBUG] Attempting SSE reconnection:', {
              backend: streamingBackend,
              runId,
              retryCount: retryCount + 1,
              maxRetries,
              delayMs: delay,
              timestamp: new Date().toISOString()
            });
            
            setTimeout(() => {
              if (currentRunIdRef.current === runId) {
                (eventSourceRef as any).retryCount = retryCount + 1;
                startStream(runId);
              }
            }, delay);
          } else {
            console.error('[STREAM-DEBUG] Max reconnection attempts reached:', {
              backend: streamingBackend,
              maxRetries,
              runId,
              timestamp: new Date().toISOString()
            });
            setError(`Unable to maintain connection after ${maxRetries} attempts`);
          }
        }
      };

      // Add a general message handler to catch any unexpected events
      eventSource.onmessage = (event) => {
        console.warn('[STREAM-DEBUG] Received unexpected default message event:', {
          eventType: 'message',
          eventData: event.data,
          lastEventId: event.lastEventId,
          timestamp: new Date().toISOString()
        });
      };

      // Log all events for debugging
      const originalAddEventListener = eventSource.addEventListener;
      eventSource.addEventListener = function(type: string, listener: any, options?: any) {
        console.log('[STREAM-DEBUG] Adding event listener:', {
          eventType: type,
          timestamp: new Date().toISOString()
        });
        return originalAddEventListener.call(this, type, listener, options);
      };

      eventSourceRef.current = eventSource;
      
      console.log('[STREAM-DEBUG] EventSource created and stored:', {
        readyState: eventSource.readyState,
        url: eventSource.url,
        withCredentials: eventSource.withCredentials,
        timestamp: new Date().toISOString()
      });

    } catch (initError) {
      console.error('[STREAM-DEBUG] Failed to initialize SSE connection:', {
        error: initError,
        backend: streamingBackend,
        runId,
        streamUrl,
        timestamp: new Date().toISOString()
      });
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

  // Debug helper - can be called from browser console via React DevTools
  const debugState = useCallback(() => {
    console.log('[STREAM-DEBUG] Current state:', {
      runId: currentRunIdRef.current,
      isStreaming,
      connectionState,
      error,
      eventSourceExists: !!eventSourceRef.current,
      eventSourceReadyState: eventSourceRef.current?.readyState,
      streamCount: streams.size,
      streamBufferCount: streamBuffersRef.current.size,
      streams: Array.from(streams.entries()).map(([id, content]) => ({
        variationId: id,
        contentItems: content.length,
        totalLength: content.join('').length
      })),
      timestamp: new Date().toISOString()
    });
  }, [streams, isStreaming, connectionState, error]);

  // Expose debug function globally for easier access
  if (typeof window !== 'undefined') {
    (window as any).__debugAgentStream = debugState;
  }

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
    debugState, // Include in return for component access
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