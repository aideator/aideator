'use client';

import React, { useRef, useEffect, useState, useMemo } from 'react';
import { useAgentColor } from '@/hooks/useAgentStream';
import { Clock, Zap, CheckCircle, Loader2, ChevronDown, ChevronUp, Maximize2, Minimize2 } from 'lucide-react';
import { MemoizedMarkdown } from './MemoizedMarkdown';
import { motion, AnimatePresence } from 'framer-motion';
import { DebugButton } from '@/components/ui/debug-button';
import { getAgentColorClasses } from '@/lib/utils';

interface CollapsibleStreamCardProps {
  variationId: number;
  content: string[];
  isStreaming: boolean;
  onSelect: () => void;
  runId?: string;
  className?: string;
}

export function CollapsibleStreamCard({ 
  variationId, 
  content, 
  isStreaming, 
  onSelect,
  runId,
  className = '' 
}: CollapsibleStreamCardProps) {
  const agentColor = useAgentColor(variationId);
  const contentRef = useRef<HTMLDivElement>(null);
  const [isExpanded, setIsExpanded] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // Format the content for display
  const displayContent = content.join('');
  const hasContent = displayContent.length > 0;
  
  // Calculate content summary for collapsed view
  const contentSummary = useMemo(() => {
    if (!hasContent) return '';
    const lines = displayContent.split('\n').filter(line => line.trim());
    const firstMeaningfulLine = lines.find(line => 
      !line.startsWith('#') && 
      !line.startsWith('==') && 
      line.length > 20
    ) || lines[0] || '';
    return firstMeaningfulLine.slice(0, 150) + (firstMeaningfulLine.length > 150 ? '...' : '');
  }, [displayContent, hasContent]);
  
  // Auto-scroll to bottom when new content arrives
  useEffect(() => {
    if (contentRef.current && isStreaming && isExpanded) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [content, isStreaming, isExpanded]);
  
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
  
  // Create ring variants for focus states
  const ringVariants = {
    'agent-1': 'ring-red-200',
    'agent-2': 'ring-amber-200',
    'agent-3': 'ring-emerald-200',
    'agent-4': 'ring-blue-200',
    'agent-5': 'ring-purple-200'
  };
  
  const ringColor = ringVariants[agentColor as keyof typeof ringVariants] || ringVariants['agent-1'];
  
  const cardClasses = isFullscreen
    ? 'fixed inset-4 z-50 bg-white rounded-xl shadow-2xl flex flex-col'
    : `bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden flex flex-col ${className}`;
  
  return (
    <>
      {/* Fullscreen backdrop */}
      <AnimatePresence>
        {isFullscreen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => setIsFullscreen(false)}
          />
        )}
      </AnimatePresence>
      
      <motion.div 
        layout
        className={cardClasses}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
      >
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
              <div className="flex-1">
                <h3 className="font-semibold text-sm">gpt-4o-mini {variationId + 1}</h3>
                <div className="flex items-center gap-2 mt-1">
                  {isStreaming ? (
                    <span className="text-[0.65rem] bg-white/20 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <Zap className="w-3 h-3" />
                      Thinking...
                    </span>
                  ) : hasContent ? (
                    <span className="text-[0.65rem] bg-white/20 px-2 py-0.5 rounded-full">
                      Complete
                    </span>
                  ) : (
                    <span className="text-[0.65rem] bg-white/10 px-2 py-0.5 rounded-full">
                      Waiting
                    </span>
                  )}
                  {hasContent && (
                    <span className="text-[0.65rem] opacity-70">
                      {displayContent.length.toLocaleString()} chars
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                {/* Debug Button */}
                {runId && (
                  <DebugButton 
                    runId={runId} 
                    variationId={variationId} 
                    className="bg-white/10 hover:bg-white/20 text-white border-white/20 text-xs px-2 py-1"
                  />
                )}
                
                <button
                  onClick={() => setIsFullscreen(!isFullscreen)}
                  className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
                  title={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
                >
                  {isFullscreen ? (
                    <Minimize2 className="w-4 h-4" />
                  ) : (
                    <Maximize2 className="w-4 h-4" />
                  )}
                </button>
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
                >
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
          </div>
          
          {/* Collapsed preview */}
          <AnimatePresence>
            {!isExpanded && hasContent && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2 }}
                className="mt-3 pt-3 border-t border-white/20"
              >
                <p className="text-xs opacity-90 line-clamp-2">
                  {contentSummary}
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Content Area */}
        <AnimatePresence mode="wait">
          {isExpanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className={`${lightBg} ${borderColor} border overflow-hidden`}
              style={{ maxHeight: isFullscreen ? 'calc(100vh - 200px)' : 'calc(100vh - 300px)' }}
            >
              {hasContent ? (
                <div
                  className="h-full overflow-y-auto p-4"
                  ref={contentRef}
                >
                  <MemoizedMarkdown 
                    content={displayContent} 
                    isStreaming={isStreaming}
                  />
                </div>
              ) : (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.3 }}
                  className="flex items-center justify-center h-full"
                >
                  {isStreaming ? (
                    <div className="text-center">
                      <Loader2 className={`w-8 h-8 ${colors.text} animate-spin mx-auto mb-3`} />
                      <p className={`text-xs ${colors.text}`}>Processing...</p>
                    </div>
                  ) : (
                    <div className="text-center">
                      <Clock className={`w-8 h-8 ${colors.text} mx-auto mb-3 opacity-50`} />
                      <p className="text-xs text-gray-500">Waiting for agent to start...</p>
                    </div>
                  )}
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Footer */}
        {isExpanded && (
          <div className="p-4 border-t border-gray-200">
            <button
              onClick={onSelect}
              disabled={!hasContent && !isStreaming}
              className={`w-full px-4 py-2 ${colors.bg} ${colors.hoverBg90} text-white rounded-lg font-medium text-sm transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 focus:outline-none focus:ring-2 ${ringColor}`}
            >
              I prefer this response
            </button>
          </div>
        )}
      </motion.div>
    </>
  );
}

export default CollapsibleStreamCard;