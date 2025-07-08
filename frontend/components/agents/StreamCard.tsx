'use client';

import React from 'react';
import { useAgentColor } from '@/hooks/useAgentStream';
import { Clock, Zap, CheckCircle, Loader2 } from 'lucide-react';

interface StreamCardProps {
  variationId: number;
  content: string[];
  isStreaming: boolean;
  onSelect: () => void;
  className?: string;
}

export function StreamCard({ 
  variationId, 
  content, 
  isStreaming, 
  onSelect,
  className = '' 
}: StreamCardProps) {
  const agentColor = useAgentColor(variationId);
  
  // Format the content for display
  const displayContent = content.join('');
  const hasContent = displayContent.length > 0;
  
  // Agent color mappings
  const agentColorMap = {
    'agent-1': {
      bg: 'bg-red-500',
      light: 'bg-red-50',
      text: 'text-red-600',
      border: 'border-red-200',
      hover: 'hover:bg-red-600'
    },
    'agent-2': {
      bg: 'bg-amber-500',
      light: 'bg-amber-50',
      text: 'text-amber-600',
      border: 'border-amber-200',
      hover: 'hover:bg-amber-600'
    },
    'agent-3': {
      bg: 'bg-emerald-500',
      light: 'bg-emerald-50',
      text: 'text-emerald-600',
      border: 'border-emerald-200',
      hover: 'hover:bg-emerald-600'
    },
    'agent-4': {
      bg: 'bg-blue-500',
      light: 'bg-blue-50',
      text: 'text-blue-600',
      border: 'border-blue-200',
      hover: 'hover:bg-blue-600'
    },
    'agent-5': {
      bg: 'bg-purple-500',
      light: 'bg-purple-50',
      text: 'text-purple-600',
      border: 'border-purple-200',
      hover: 'hover:bg-purple-600'
    },
  };
  
  const colors = agentColorMap[agentColor as keyof typeof agentColorMap] || agentColorMap['agent-1'];
  
  return (
    <div className={`bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300 overflow-hidden flex flex-col h-full ${className}`}>
      {/* Header */}
      <div className={`p-4 ${colors.bg} text-white`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center">
              {isStreaming ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : hasContent ? (
                <CheckCircle className="w-4 h-4" />
              ) : (
                <Clock className="w-4 h-4" />
              )}
            </div>
            <div>
              <h3 className="font-semibold">Agent {variationId + 1}</h3>
              <div className="flex items-center gap-2 mt-1">
                {isStreaming ? (
                  <span className="text-xs bg-white/20 px-2 py-0.5 rounded-full flex items-center gap-1">
                    <Zap className="w-3 h-3" />
                    Thinking...
                  </span>
                ) : hasContent ? (
                  <span className="text-xs bg-white/20 px-2 py-0.5 rounded-full">
                    Complete
                  </span>
                ) : (
                  <span className="text-xs bg-white/10 px-2 py-0.5 rounded-full">
                    Waiting
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className={`flex-1 p-4 ${colors.light} ${colors.border} border overflow-y-auto`}>
        {hasContent ? (
          <div>
            <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
              {displayContent}
            </pre>
            {isStreaming && (
              <span className={`inline-block w-2 h-4 ${colors.bg} animate-pulse ml-1`} />
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full min-h-[200px]">
            {isStreaming ? (
              <div className="text-center">
                <Loader2 className={`w-8 h-8 ${colors.text} animate-spin mx-auto mb-3`} />
                <p className={`text-sm ${colors.text}`}>Processing...</p>
              </div>
            ) : (
              <div className="text-center">
                <Clock className={`w-8 h-8 ${colors.text} mx-auto mb-3 opacity-50`} />
                <p className="text-sm text-gray-500">Waiting for agent to start...</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm text-gray-600">
            {content.length > 0 ? `${content.length} messages` : 'No messages yet'}
          </span>
          {hasContent && (
            <span className="text-sm text-gray-600">
              {displayContent.length.toLocaleString()} chars
            </span>
          )}
        </div>
        
        <button
          onClick={onSelect}
          disabled={!hasContent && !isStreaming}
          className={`w-full px-4 py-2 ${colors.bg} ${colors.hover} text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          Select This Agent
        </button>
      </div>
    </div>
  );
}

export default StreamCard;