'use client';

import { useState, useRef, useEffect } from 'react';
import { Bug, X, Terminal, Trash2 } from 'lucide-react';
import { Button } from './button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './dialog';

interface DebugButtonProps {
  runId: string;
  variationId: number;
  className?: string;
}

interface LogEntry {
  timestamp: string;
  level: 'INFO' | 'DEBUG' | 'ERROR' | 'WARN';
  message: string;
  raw: string;
  isAgentOutput?: boolean;
}

export function DebugButton({ runId, variationId, className }: DebugButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [eventSource, setEventSource] = useState<EventSource | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const parseLogLine = (logLine: string): LogEntry => {
    // Try to parse as JSON first (structured logs)
    try {
      const parsed = JSON.parse(logLine);
      if (parsed.timestamp && parsed.level && parsed.message) {
        return {
          timestamp: parsed.timestamp,
          level: parsed.level,
          message: parsed.message,
          raw: logLine,
          isAgentOutput: false
        };
      }
    } catch {
      // Not JSON, continue with text parsing
    }

    // Check if it's an agent output (markdown content)
    const isAgentOutput = logLine.includes('```') || 
                         logLine.includes('#') || 
                         logLine.match(/^[A-Z][a-z].*\.$/) ||
                         logLine.includes('**') ||
                         logLine.includes('*') ||
                         logLine.length > 200;

    // Parse log level from text
    let level: LogEntry['level'] = 'INFO';
    if (logLine.includes('[ERROR]') || logLine.includes('ERROR:')) level = 'ERROR';
    else if (logLine.includes('[WARN]') || logLine.includes('WARN:')) level = 'WARN';
    else if (logLine.includes('[DEBUG]') || logLine.includes('DEBUG:')) level = 'DEBUG';

    return {
      timestamp: new Date().toISOString(),
      level,
      message: logLine,
      raw: logLine,
      isAgentOutput
    };
  };

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
      const entry = parseLogLine(logLine);
      
      // Filter out agent outputs, only show debug/system logs
      if (!entry.isAgentOutput) {
        setLogs(prev => [...prev, entry]);
      }
    };

    newEventSource.onerror = (error) => {
      console.error('Debug logs stream error:', error);
      setIsStreaming(false);
      setLogs(prev => [...prev, {
        timestamp: new Date().toISOString(),
        level: 'ERROR',
        message: 'Stream connection failed',
        raw: '[ERROR] Stream connection failed',
        isAgentOutput: false
      }]);
    };

    newEventSource.onopen = () => {
      setLogs(prev => [...prev, {
        timestamp: new Date().toISOString(),
        level: 'INFO',
        message: 'Debug stream connected',
        raw: '[INFO] Debug stream connected',
        isAgentOutput: false
      }]);
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

  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
      const isAtBottom = Math.abs(scrollHeight - scrollTop - clientHeight) < 10;
      setAutoScroll(isAtBottom);
    }
  };

  const getLogColor = (level: LogEntry['level']) => {
    switch (level) {
      case 'ERROR': return 'text-red-400';
      case 'WARN': return 'text-yellow-400';
      case 'DEBUG': return 'text-blue-400';
      default: return 'text-green-400';
    }
  };

  const getLogIcon = (level: LogEntry['level']) => {
    switch (level) {
      case 'ERROR': return '❌';
      case 'WARN': return '⚠️';
      case 'DEBUG': return '🔍';
      default: return 'ℹ️';
    }
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
        <DialogContent className="max-w-6xl max-h-[85vh] flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Terminal className="w-5 h-5" />
                Debug Logs - Agent {variationId + 1}
                <span className="text-sm font-normal text-gray-500">
                  (System logs only)
                </span>
              </span>
              <div className="flex items-center gap-2">
                {isStreaming ? (
                  <Button 
                    size="sm" 
                    variant="destructive" 
                    onClick={stopStreaming}
                    className="gap-2"
                  >
                    <X className="w-4 h-4" />
                    Stop
                  </Button>
                ) : (
                  <Button 
                    size="sm" 
                    onClick={startStreaming}
                    className="gap-2"
                  >
                    <Terminal className="w-4 h-4" />
                    Start Streaming
                  </Button>
                )}
                <Button 
                  size="sm" 
                  variant="outline" 
                  onClick={() => setLogs([])}
                  className="gap-2"
                >
                  <Trash2 className="w-4 h-4" />
                  Clear
                </Button>
              </div>
            </DialogTitle>
          </DialogHeader>

          <div className="flex-1 overflow-hidden">
            <div 
              ref={containerRef}
              onScroll={handleScroll}
              className="h-full bg-gray-900 text-green-400 p-4 rounded-lg overflow-y-auto font-mono text-sm"
            >
              {logs.length === 0 ? (
                <div className="text-gray-500 text-center py-8">
                  <Terminal className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Click "Start Streaming" to view debug logs</p>
                  <p className="text-xs mt-2">System logs and debug messages only</p>
                </div>
              ) : (
                <div className="space-y-1">
                  {logs.map((log, index) => (
                    <div key={index} className="flex items-start gap-2 hover:bg-gray-800/50 p-1 rounded">
                      <span className="text-xs">{getLogIcon(log.level)}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
                          <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${getLogColor(log.level)}`}>
                            {log.level}
                          </span>
                        </div>
                        <div className={`whitespace-pre-wrap break-words ${getLogColor(log.level)}`}>
                          {log.message}
                        </div>
                      </div>
                    </div>
                  ))}
                  <div ref={logsEndRef} />
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between text-sm text-gray-500 mt-2">
            <div>
              Run ID: {runId} | Variation: {variationId}
            </div>
            <div className="flex items-center gap-4">
              <span>{logs.length} log entries</span>
              {!autoScroll && (
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => {
                    setAutoScroll(true);
                    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
                  }}
                  className="text-xs"
                >
                  Scroll to bottom
                </Button>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}