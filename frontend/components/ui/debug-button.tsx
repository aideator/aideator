'use client';

import { useState } from 'react';
import { Bug, X } from 'lucide-react';
import { Button } from './button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './dialog';

interface DebugButtonProps {
  runId: string;
  variationId: number;
  className?: string;
}

export function DebugButton({ runId, variationId, className }: DebugButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [eventSource, setEventSource] = useState<EventSource | null>(null);

  const startStreaming = () => {
    if (eventSource) {
      eventSource.close();
    }

    setLogs([]);
    setIsStreaming(true);

    const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/runs/${runId}/debug-logs?variation_id=${variationId}`;
    const newEventSource = new EventSource(url);

    newEventSource.onmessage = (event) => {
      const logLine = event.data;
      setLogs(prev => [...prev, logLine]);
    };

    newEventSource.onerror = (error) => {
      console.error('Debug logs stream error:', error);
      setIsStreaming(false);
      setLogs(prev => [...prev, '[ERROR] Stream connection failed']);
    };

    newEventSource.onopen = () => {
      setLogs(prev => [...prev, '[INFO] Debug stream connected']);
    };

    setEventSource(newEventSource);
  };

  const stopStreaming = () => {
    if (eventSource) {
      eventSource.close();
      setEventSource(null);
    }
    setIsStreaming(false);
  };

  const handleClose = () => {
    stopStreaming();
    setIsOpen(false);
  };

  // Only show in development or when debug mode is enabled
  const showDebugButton = process.env.NODE_ENV === 'development' || 
                         process.env.NEXT_PUBLIC_DEBUG_MODE === 'true';

  if (!showDebugButton) {
    return null;
  }

  return (
    <>
      <Button
        size="sm"
        variant="outline"
        onClick={() => setIsOpen(true)}
        className={`gap-2 ${className}`}
      >
        <Bug className="w-4 h-4" />
        Debug
      </Button>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Bug className="w-5 h-5" />
                Debug Logs - Agent {variationId + 1}
              </span>
              <div className="flex items-center gap-2">
                {isStreaming ? (
                  <Button 
                    size="sm" 
                    variant="destructive" 
                    onClick={stopStreaming}
                  >
                    Stop
                  </Button>
                ) : (
                  <Button 
                    size="sm" 
                    onClick={startStreaming}
                  >
                    Start Streaming
                  </Button>
                )}
                <Button 
                  size="sm" 
                  variant="outline" 
                  onClick={() => setLogs([])}
                >
                  Clear
                </Button>
              </div>
            </DialogTitle>
          </DialogHeader>

          <div className="flex-1 overflow-hidden">
            <div className="h-full bg-gray-900 text-green-400 p-4 rounded-lg overflow-y-auto font-mono text-sm">
              {logs.length === 0 ? (
                <div className="text-gray-500 text-center py-8">
                  Click "Start Streaming" to view debug logs
                </div>
              ) : (
                <div className="space-y-1">
                  {logs.map((log, index) => (
                    <div key={index} className="whitespace-pre-wrap">
                      {log}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="text-sm text-gray-500 mt-2">
            Run ID: {runId} | Variation: {variationId}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}