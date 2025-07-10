'use client';

import React from 'react';
import { CollapsibleStreamCard } from './CollapsibleStreamCard';
import { AlertCircle, Wifi, WifiOff, TrendingUp } from 'lucide-react';

interface StreamGridProps {
  streams: Map<number, string[]>;
  isStreaming: boolean;
  connectionState: 'disconnected' | 'connecting' | 'connected' | 'error';
  error: string | null;
  onSelectAgent: (variationId: number) => void;
  runId?: string;
  maxVariations?: number;
}

export function StreamGrid({ 
  streams, 
  isStreaming, 
  connectionState,
  error,
  onSelectAgent,
  runId,
  maxVariations = 5 
}: StreamGridProps) {
  
  // Create array of variation IDs for consistent grid layout
  const variationIds = Array.from({ length: maxVariations }, (_, i) => i);
  
  // Connection status indicator
  const getConnectionStatus = () => {
    switch (connectionState) {
      case 'connecting':
        return { icon: Wifi, colorClass: 'text-amber-700 bg-amber-50', text: 'Connecting...' };
      case 'error':
        return { icon: WifiOff, colorClass: 'text-red-600 bg-red-50', text: 'Connection Error' };
      default:
        return null; // Don't show ready/connected/disconnected status
    }
  };
  
  const connectionStatus = getConnectionStatus();
  const StatusIcon = connectionStatus?.icon;
  
  return (
    <div className="w-full">
      {/* Status bar - only show when connecting, error, or streaming */}
      {(connectionStatus || isStreaming) && (
        <div className="mb-6 flex justify-end items-center gap-3">
          {connectionStatus && (
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${connectionStatus.colorClass}`}>
              <StatusIcon className="w-4 h-4 mr-2" />
              {connectionStatus.text}
            </span>
          )}
          
          {isStreaming && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-600 text-white">
              <TrendingUp className="w-4 h-4 mr-2" />
              {streams.size} / {maxVariations} Active
            </span>
          )}
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2 text-red-800">
            <AlertCircle className="h-5 w-5" />
            <span className="font-medium">{error}</span>
          </div>
        </div>
      )}

      {/* Responsive Grid - optimal layout for 1-3 agents */}
      <div className={`grid gap-4 ${
        maxVariations === 1 ? 'grid-cols-1' : 
        maxVariations === 2 ? 'grid-cols-1 md:grid-cols-2' : 
        'grid-cols-1 md:grid-cols-3'
      }`}>
        {variationIds.map((variationId) => {
          const content = streams.get(variationId) || [];
          const hasContent = content.length > 0;
          const isThisAgentStreaming = isStreaming && (hasContent || streams.has(variationId));
          
          return (
            <div key={variationId} className="h-full">
              <CollapsibleStreamCard
                variationId={variationId}
                content={content}
                isStreaming={isThisAgentStreaming}
                onSelect={() => onSelectAgent(variationId)}
                runId={runId}
                className="h-full"
              />
            </div>
          );
        })}
      </div>


    </div>
  );
}

export default StreamGrid;