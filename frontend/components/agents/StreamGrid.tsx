'use client';

import React from 'react';
import { StreamCard } from './StreamCard';
import { AlertCircle, Wifi, WifiOff, Users, Activity, TrendingUp, Sparkles } from 'lucide-react';

interface StreamGridProps {
  streams: Map<number, string[]>;
  isStreaming: boolean;
  connectionState: 'disconnected' | 'connecting' | 'connected' | 'error';
  error: string | null;
  onSelectAgent: (variationId: number) => void;
  maxVariations?: number;
}

export function StreamGrid({ 
  streams, 
  isStreaming, 
  connectionState,
  error,
  onSelectAgent,
  maxVariations = 5 
}: StreamGridProps) {
  
  // Create array of variation IDs for consistent grid layout
  const variationIds = Array.from({ length: maxVariations }, (_, i) => i);
  
  // Connection status indicator
  const getConnectionStatus = () => {
    switch (connectionState) {
      case 'connected':
        return { icon: Wifi, colorClass: 'text-green-600 bg-green-50', text: 'Connected' };
      case 'connecting':
        return { icon: Wifi, colorClass: 'text-yellow-600 bg-yellow-50', text: 'Connecting...' };
      case 'error':
        return { icon: WifiOff, colorClass: 'text-red-600 bg-red-50', text: 'Connection Error' };
      default:
        return { icon: WifiOff, colorClass: 'text-gray-600 bg-gray-50', text: 'Disconnected' };
    }
  };
  
  const connectionStatus = getConnectionStatus();
  const StatusIcon = connectionStatus.icon;
  
  return (
    <div className="w-full">
      {/* Header with connection status */}
      <div className="bg-white rounded-2xl shadow-xl p-6 mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 text-white">
              <Users className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                Agent Variations
              </h2>
              <p className="text-gray-600 flex items-center gap-2">
                <Activity className="h-4 w-4" />
                {maxVariations} agents working in parallel on your task
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${connectionStatus.colorClass}`}>
              <StatusIcon className="w-4 h-4 mr-2" />
              {connectionStatus.text}
            </span>
            
            {isStreaming && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-600 text-white">
                <TrendingUp className="w-4 h-4 mr-2" />
                {streams.size} / {maxVariations} Active
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2 text-red-800">
            <AlertCircle className="h-5 w-5" />
            <span className="font-medium">{error}</span>
          </div>
        </div>
      )}

      {/* Responsive Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
        {variationIds.map((variationId) => {
          const content = streams.get(variationId) || [];
          const hasContent = content.length > 0;
          const isThisAgentStreaming = isStreaming && (hasContent || streams.has(variationId));
          
          return (
            <div key={variationId} className="h-full">
              <StreamCard
                variationId={variationId}
                content={content}
                isStreaming={isThisAgentStreaming}
                onSelect={() => onSelectAgent(variationId)}
                className="h-full"
              />
            </div>
          );
        })}
      </div>

      {/* Empty State */}
      {streams.size === 0 && !isStreaming && (
        <div className="p-16 text-center bg-white rounded-2xl shadow-lg border-2 border-dashed border-gray-300">
          <div className="mb-6">
            <div className="w-20 h-20 bg-gradient-to-br from-purple-100 to-pink-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Sparkles className="w-10 h-10 text-purple-600" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">
              Ready to Start Multi-Agent Generation
            </h3>
            <p className="text-lg text-gray-600 max-w-md mx-auto">
              Configure your task above and click "Start Generation" to see real-time agent results here.
            </p>
          </div>
        </div>
      )}

      {/* Progress Summary */}
      {(isStreaming || streams.size > 0) && (
        <div className="mt-8 p-6 bg-white rounded-2xl shadow-lg">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-green-100 text-green-600">
              <TrendingUp className="h-5 w-5" />
            </div>
            <h4 className="text-lg font-bold text-gray-900">
              Progress Summary
            </h4>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {variationIds.map((variationId) => {
              const content = streams.get(variationId) || [];
              const hasContent = content.length > 0;
              const colors = ['bg-red-500', 'bg-amber-500', 'bg-emerald-500', 'bg-blue-500', 'bg-purple-500'];
              const bgColor = colors[variationId % colors.length];
              
              return (
                <div key={variationId} className="text-center">
                  <div className={`w-12 h-12 ${bgColor} rounded-xl mx-auto mb-2 flex items-center justify-center text-white text-lg font-bold shadow-lg`}>
                    {variationId + 1}
                  </div>
                  <div className="text-sm font-semibold text-gray-700">
                    {hasContent ? `${content.join('').length.toLocaleString()} chars` : 'Waiting'}
                  </div>
                  {hasContent && (
                    <div className="text-xs text-gray-500">
                      {content.length} messages
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default StreamGrid;