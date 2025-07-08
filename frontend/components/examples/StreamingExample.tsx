'use client';

import React from 'react';
import { useAgentStream } from '@/hooks/useAgentStream';
import { StreamCard } from '@/components/agents/StreamCard';
import { Button } from '@/components/ui/button';
import { Play, Pause, RotateCw, Square } from 'lucide-react';

/**
 * Example component demonstrating smooth streaming with pause/resume functionality
 */
export function StreamingExample() {
  const { 
    streams, 
    isStreaming, 
    connectionState,
    startStream, 
    stopStream, 
    clearStreams,
    pauseStream,
    resumeStream,
    selectAgent 
  } = useAgentStream();
  
  const [isPaused, setIsPaused] = React.useState(false);
  const [selectedRunId] = React.useState('example-run-123');
  
  const handleTogglePause = () => {
    if (isPaused) {
      resumeStream();
      setIsPaused(false);
    } else {
      pauseStream();
      setIsPaused(true);
    }
  };
  
  const handleStart = () => {
    startStream(selectedRunId);
    setIsPaused(false);
  };
  
  const handleStop = () => {
    stopStream();
    setIsPaused(false);
  };
  
  const handleReset = () => {
    clearStreams();
    setIsPaused(false);
  };
  
  const handleSelectAgent = async (variationId: number) => {
    try {
      await selectAgent(variationId);
      console.log(`Selected agent ${variationId}`);
    } catch (error) {
      console.error('Failed to select agent:', error);
    }
  };
  
  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex items-center gap-4 p-4 bg-white rounded-lg shadow">
        <h2 className="text-lg font-semibold flex-1">Smooth Streaming Demo</h2>
        
        <div className="flex items-center gap-2">
          {!isStreaming ? (
            <Button
              onClick={handleStart}
              className="flex items-center gap-2"
              variant="default"
            >
              <Play className="w-4 h-4" />
              Start Streaming
            </Button>
          ) : (
            <>
              <Button
                onClick={handleTogglePause}
                className="flex items-center gap-2"
                variant="outline"
              >
                {isPaused ? (
                  <>
                    <Play className="w-4 h-4" />
                    Resume
                  </>
                ) : (
                  <>
                    <Pause className="w-4 h-4" />
                    Pause
                  </>
                )}
              </Button>
              
              <Button
                onClick={handleStop}
                className="flex items-center gap-2"
                variant="destructive"
              >
                <Square className="w-4 h-4" />
                Stop
              </Button>
            </>
          )}
          
          <Button
            onClick={handleReset}
            className="flex items-center gap-2"
            variant="ghost"
            disabled={isStreaming}
          >
            <RotateCw className="w-4 h-4" />
            Reset
          </Button>
        </div>
        
        {/* Connection State */}
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            connectionState === 'connected' ? 'bg-green-500' :
            connectionState === 'connecting' ? 'bg-yellow-500 animate-pulse' :
            connectionState === 'error' ? 'bg-red-500' :
            'bg-gray-300'
          }`} />
          <span className="text-sm text-gray-600 capitalize">
            {connectionState}
          </span>
        </div>
      </div>
      
      {/* Stream Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from(streams.entries()).map(([variationId, content]) => (
          <StreamCard
            key={variationId}
            variationId={variationId}
            content={content}
            isStreaming={isStreaming}
            onSelect={() => handleSelectAgent(variationId)}
          />
        ))}
        
        {/* Placeholder cards when no streams */}
        {streams.size === 0 && Array.from({ length: 3 }).map((_, index) => (
          <StreamCard
            key={`placeholder-${index}`}
            variationId={index}
            content={[]}
            isStreaming={false}
            onSelect={() => {}}
          />
        ))}
      </div>
      
      {/* Instructions */}
      <div className="p-4 bg-blue-50 rounded-lg">
        <h3 className="font-semibold text-blue-900 mb-2">Smooth Streaming Features:</h3>
        <ul className="space-y-1 text-sm text-blue-800">
          <li>• Text streams at a consistent 50 tokens/second rate</li>
          <li>• Respects word boundaries - never splits words</li>
          <li>• Handles markdown blocks properly (code, tables, lists)</li>
          <li>• Auto-scroll follows new content (pauses when you scroll up)</li>
          <li>• Pause/resume streaming without losing data</li>
          <li>• Smooth animations for text appearance</li>
        </ul>
      </div>
    </div>
  );
}

export default StreamingExample;