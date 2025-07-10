'use client';

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useAgentColor } from '@/hooks/useAgentStream';
import { Clock, Zap, CheckCircle, Loader2 } from 'lucide-react';
import { MemoizedMarkdown } from './MemoizedMarkdown';
import { motion, AnimatePresence } from 'framer-motion';
import { DebugButton } from '@/components/ui/debug-button';
import { getAgentColorClasses } from '@/lib/utils';

interface StreamCardProps {
  variationId: number;
  content: string[];
  isStreaming: boolean;
  onSelect: () => void;
  runId?: string;
  className?: string;
}

export function StreamCard({ 
  variationId, 
  content, 
  isStreaming, 
  onSelect,
  runId,
  className = '' 
}: StreamCardProps) {
  const agentColor = useAgentColor(variationId);
  const contentRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [userScrolled, setUserScrolled] = useState(false);
  
  // Format the content for display
  const displayContent = content.join('');
  const hasContent = displayContent.length > 0;
  
  // Check if user has scrolled up
  const handleScroll = useCallback(() => {
    if (!contentRef.current) return;
    
    const { scrollTop, scrollHeight, clientHeight } = contentRef.current;
    const isAtBottom = Math.abs(scrollHeight - scrollTop - clientHeight) < 50;
    
    if (!isAtBottom && !userScrolled) {
      setUserScrolled(true);
      setAutoScroll(false);
    } else if (isAtBottom && userScrolled) {
      setUserScrolled(false);
      setAutoScroll(true);
    }
  }, [userScrolled]);
  
  // Auto-scroll to bottom when new content arrives (if enabled)
  useEffect(() => {
    if (contentRef.current && isStreaming && autoScroll) {
      contentRef.current.scrollTo({
        top: contentRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [content, isStreaming, autoScroll]);
  
  // Use design system colors
  const colors = getAgentColorClasses(agentColor);
  
  // Create light background variants for card sections
  const lightVariants = {
    'agent-1': 'bg-red-50',
    'agent-2': 'bg-amber-50', 
    'agent-3': 'bg-emerald-50',
    'agent-4': 'bg-blue-50',
    'agent-5': 'bg-purple-50'
  };
  
  const lightBg = lightVariants[agentColor as keyof typeof lightVariants] || lightVariants['agent-1'];
  
  // Create border variants for cards
  const borderVariants = {
    'agent-1': 'border-red-200',
    'agent-2': 'border-amber-200',
    'agent-3': 'border-emerald-200', 
    'agent-4': 'border-blue-200',
    'agent-5': 'border-purple-200'
  };
  
  const borderColor = borderVariants[agentColor as keyof typeof borderVariants] || borderVariants['agent-1'];
  
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
              <h3 className="font-semibold">gpt-4o-mini {variationId + 1}</h3>
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
          
          {/* Debug Button */}
          {runId && (
            <DebugButton 
              runId={runId} 
              variationId={variationId} 
              className="bg-white/20 hover:bg-white/30 text-white border-white/30"
            />
          )}
        </div>
      </div>

      {/* Content Area */}
      <div className={`flex-1 p-4 ${lightBg} ${borderColor} border overflow-hidden relative`}>
        <AnimatePresence mode="wait">
          {hasContent ? (
            <motion.div
              key="content"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="h-full overflow-y-auto smooth-scroll"
              ref={contentRef}
              onScroll={handleScroll}
            >
              <MemoizedMarkdown 
                content={displayContent} 
                isStreaming={isStreaming}
                className="text-sm"
              />
            </motion.div>
          ) : (
            <motion.div 
              key="empty"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.3 }}
              className="flex items-center justify-center h-full min-h-[200px]"
            >
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
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* Auto-scroll indicator */}
        {hasContent && isStreaming && (
          <AnimatePresence>
            {!autoScroll && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="auto-scroll-indicator paused"
              >
                Auto-scroll paused
              </motion.div>
            )}
          </AnimatePresence>
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
          className={`w-full px-4 py-2 ${colors.bg} ${colors.hoverBg90} text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          I prefer this response
        </button>
      </div>
    </div>
  );
}

export default StreamCard;