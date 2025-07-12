'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { StreamBuffer } from '@/lib/StreamBuffer';

export interface AgentOutput {
  id: number;
  run_id: string;
  variation_id: number;
  content: string;
  timestamp: string;
  output_type: string;
}

export interface AgentPollingState {
  streams: Map<number, string[]>;
  logs: Map<number, any[]>;
  isPolling: boolean;
  error: string | null;
  connectionState: 'disconnected' | 'connecting' | 'connected' | 'error';
}

export interface AgentPollingHook extends AgentPollingState {
  startStream: (runId: string) => void;
  stopStream: () => void;
  clearStreams: () => void;
  clearLogs: (variationId?: number) => void;
  selectAgent: (variationId: number) => Promise<void>;
  pauseStream: (variationId?: number) => void;
  resumeStream: (variationId?: number) => void;
  debugState: () => void;
}

export function useAgentPolling(): AgentPollingHook {
  const [streams, setStreams] = useState<Map<number, string[]>>(new Map());
  const [logs, setLogs] = useState<Map<number, any[]>>(new Map());
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionState, setConnectionState] = useState<AgentPollingState['connectionState']>('disconnected');
  
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const currentRunIdRef = useRef<string | null>(null);
  const streamBuffersRef = useRef<Map<number, StreamBuffer>>(new Map());
  const lastTimestampRef = useRef<string | null>(null);
  const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

  const stopStream = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    // Destroy all stream buffers
    streamBuffersRef.current.forEach(buffer => buffer.destroy());
    streamBuffersRef.current.clear();
    setIsPolling(false);
    setConnectionState('disconnected');
    currentRunIdRef.current = null;
    lastTimestampRef.current = null;
  }, []);

  const processOutput = useCallback((output: AgentOutput) => {
    const variationId = output.variation_id;
    
    // Get or create stream buffer for this variation
    if (!streamBuffersRef.current.has(variationId)) {
      const buffer = new StreamBuffer({
        onChunk: (chunk: string) => {
          setStreams(prev => {
            const updated = new Map(prev);
            const current = updated.get(variationId) || [];
            updated.set(variationId, [...current, chunk]);
            return updated;
          });
        },
        chunkSize: 50,
        delay: 20,
      });
      streamBuffersRef.current.set(variationId, buffer);
    }
    
    // Handle different output types
    switch (output.output_type) {
      case 'stdout':
        const buffer = streamBuffersRef.current.get(variationId);
        if (buffer) {
          buffer.write(output.content);
        }
        break;
        
      case 'logging':
        const logData = JSON.parse(output.content);
        setLogs(prev => {
          const updated = new Map(prev);
          const current = updated.get(variationId) || [];
          updated.set(variationId, [...current, {
            timestamp: output.timestamp,
            ...logData
          }]);
          return updated;
        });
        break;
        
      case 'status':
        const statusData = JSON.parse(output.content);
        if (statusData.status === 'variation_completed') {
          // Mark agent as complete
          console.log(`Agent ${variationId} completed`);
        } else if (statusData.status === 'variation_failed') {
          // Mark agent as failed
          console.error(`Agent ${variationId} failed:`, statusData.metadata);
        }
        break;
    }
    
    // Update last timestamp
    lastTimestampRef.current = output.timestamp;
  }, []);

  const pollForOutputs = useCallback(async () => {
    if (!currentRunIdRef.current) return;
    
    try {
      const params = new URLSearchParams();
      if (lastTimestampRef.current) {
        params.append('since', lastTimestampRef.current);
      }
      
      const response = await fetch(
        `${apiBase}/api/v1/runs/${currentRunIdRef.current}/outputs?${params}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const outputs: AgentOutput[] = await response.json();
      
      // Process each output
      outputs.forEach(processOutput);
      
      // Update connection state
      if (connectionState !== 'connected') {
        setConnectionState('connected');
      }
      setError(null);
      
    } catch (err) {
      console.error('Polling error:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      setConnectionState('error');
    }
  }, [apiBase, connectionState, processOutput]);

  const startStream = useCallback((runId: string) => {
    // Stop any existing streaming
    stopStream();
    
    // Clear previous state
    setStreams(new Map());
    setLogs(new Map());
    setError(null);
    
    // Set up new polling
    currentRunIdRef.current = runId;
    setIsPolling(true);
    setConnectionState('connecting');
    
    // Start polling immediately
    pollForOutputs();
    
    // Set up interval for polling every 500ms
    pollingIntervalRef.current = setInterval(pollForOutputs, 500);
  }, [stopStream, pollForOutputs]);

  const clearStreams = useCallback(() => {
    setStreams(new Map());
    streamBuffersRef.current.forEach(buffer => buffer.clear());
  }, []);

  const clearLogs = useCallback((variationId?: number) => {
    if (variationId !== undefined) {
      setLogs(prev => {
        const updated = new Map(prev);
        updated.delete(variationId);
        return updated;
      });
    } else {
      setLogs(new Map());
    }
  }, []);

  const selectAgent = useCallback(async (variationId: number) => {
    if (!currentRunIdRef.current) return;
    
    try {
      const response = await fetch(
        `${apiBase}/api/v1/runs/${currentRunIdRef.current}/select`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ winning_variation_id: variationId }),
        }
      );
      
      if (!response.ok) {
        throw new Error(`Failed to select agent: ${response.statusText}`);
      }
    } catch (err) {
      console.error('Failed to select agent:', err);
      throw err;
    }
  }, [apiBase]);

  const pauseStream = useCallback((variationId?: number) => {
    if (variationId !== undefined) {
      const buffer = streamBuffersRef.current.get(variationId);
      if (buffer) {
        buffer.pause();
      }
    } else {
      streamBuffersRef.current.forEach(buffer => buffer.pause());
    }
  }, []);

  const resumeStream = useCallback((variationId?: number) => {
    if (variationId !== undefined) {
      const buffer = streamBuffersRef.current.get(variationId);
      if (buffer) {
        buffer.resume();
      }
    } else {
      streamBuffersRef.current.forEach(buffer => buffer.resume());
    }
  }, []);

  const debugState = useCallback(() => {
    console.log('useAgentPolling Debug State:', {
      isPolling,
      connectionState,
      error,
      currentRunId: currentRunIdRef.current,
      lastTimestamp: lastTimestampRef.current,
      streamCount: streams.size,
      logCount: logs.size,
      streamContents: Array.from(streams.entries()).map(([id, content]) => ({
        variation: id,
        lines: content.length,
        preview: content.slice(-3)
      }))
    });
  }, [isPolling, connectionState, error, streams, logs]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      stopStream();
    };
  }, [stopStream]);

  return {
    streams,
    logs,
    isPolling,
    error,
    connectionState,
    startStream,
    stopStream,
    clearStreams,
    clearLogs,
    selectAgent,
    pauseStream,
    resumeStream,
    debugState,
  };
}

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