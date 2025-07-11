'use client';

import React, { useRef, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  [key: string]: any;
}

interface LogViewerProps {
  logs: LogEntry[];
  maxHeight?: string;
  onClear?: () => void;
}

export function LogViewer({ logs, maxHeight = '200px', onClear }: LogViewerProps) {
  const [autoScroll, setAutoScroll] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isExpanded, setIsExpanded] = useState(true); // Start expanded for debugging
  
  // Debug logging
  useEffect(() => {
    console.log('[LOG-VIEWER-DEBUG] LogViewer received logs:', {
      logCount: logs.length,
      logs: logs,
      timestamp: new Date().toISOString()
    });
  }, [logs]);

  // Auto-scroll to bottom when new logs arrive (if enabled)
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  // Format time from ISO string to HH:MM:SS
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toTimeString().split(' ')[0]; // Gets HH:MM:SS
  };

  // Get level color (using Tailwind classes for terminal feel)
  const getLevelClass = (level: string) => {
    switch (level.toUpperCase()) {
      case 'ERROR':
        return 'text-red-400';
      case 'WARN':
      case 'WARNING':
        return 'text-yellow-400';
      case 'INFO':
        return 'text-gray-300';
      case 'DEBUG':
        return 'text-gray-500';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <div className="border-t border-gray-700 bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-gray-800 border-b border-gray-700">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 text-sm text-gray-300 hover:text-white transition-colors"
        >
          <span className="font-mono">{isExpanded ? '▾' : '▶'}</span>
          <span>Logs</span>
          {logs.length > 0 && (
            <span className="text-xs text-gray-500">({logs.length})</span>
          )}
        </button>
        
        {isExpanded && (
          <div className="flex items-center gap-2">
            {onClear && (
              <Button
                onClick={onClear}
                variant="ghost"
                size="sm"
                className="h-6 px-2 text-xs text-gray-400 hover:text-white"
              >
                Clear
              </Button>
            )}
            <Button
              onClick={() => setAutoScroll(!autoScroll)}
              variant="ghost"
              size="sm"
              className={`h-6 px-2 text-xs ${
                autoScroll ? 'text-green-400' : 'text-gray-400'
              } hover:text-white`}
            >
              {autoScroll ? '↓' : '⏸'}
            </Button>
          </div>
        )}
      </div>

      {/* Logs */}
      {isExpanded && (
        <div
          ref={scrollRef}
          className="overflow-y-auto font-mono text-xs"
          style={{ maxHeight }}
        >
          {logs.length === 0 ? (
            <div className="px-3 py-2 text-gray-500">No logs yet...</div>
          ) : (
            <div className="py-1">
              {logs.map((log, index) => (
                <div
                  key={index}
                  className="px-3 py-0.5 hover:bg-gray-800/50 transition-colors"
                >
                  <span className="text-gray-500">{formatTime(log.timestamp)}</span>
                  <span className={`ml-2 ${getLevelClass(log.level)}`}>
                    {log.level.toUpperCase().padEnd(5)}
                  </span>
                  <span className="ml-2 text-gray-300 break-all">
                    {log.message}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}