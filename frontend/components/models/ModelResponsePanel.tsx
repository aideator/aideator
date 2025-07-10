'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { CheckCircle2, Clock, AlertCircle, Loader2, Star, Heart, ThumbsUp } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn, getAgentColorClasses } from '@/lib/utils';

interface ModelResponsePanelProps {
  modelId: string;
  modelName: string;
  provider: string;
  status: 'pending' | 'streaming' | 'completed' | 'error';
  content: string;
  responseTime?: number;
  tokenCount?: number;
  wordCount?: number;
  selected?: boolean;
  agentColor: string;
  error?: string;
  onSelect: () => void;
  onPreferenceFeedback?: () => void;
  isSelecting?: boolean;
  selectionType?: 'selected' | 'selecting' | 'none';
  className?: string;
}

export function ModelResponsePanel({
  modelId,
  modelName,
  provider,
  status,
  content,
  responseTime,
  tokenCount,
  wordCount,
  selected,
  agentColor,
  error,
  onSelect,
  onPreferenceFeedback,
  isSelecting = false,
  selectionType = 'none',
  className,
}: ModelResponsePanelProps) {
  const [isAnimating, setIsAnimating] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);

  const handleSelect = () => {
    setIsAnimating(true);
    setShowConfirmation(true);
    onSelect();
    
    // Reset animation state
    setTimeout(() => {
      setIsAnimating(false);
      setShowConfirmation(false);
    }, 2000);
  };
  const getStatusBadge = () => {
    switch (status) {
      case 'pending':
        return (
          <Badge variant="outline" className="text-neutral-shadow border-neutral-shadow">
            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
            Pending
          </Badge>
        );
      case 'streaming':
        return (
          <Badge variant="outline" className="text-ai-accent border-ai-accent">
            <Clock className="w-3 h-3 mr-1 animate-pulse" />
            Streaming
          </Badge>
        );
      case 'completed':
        return (
          <Badge variant="outline" className="text-semantic-success border-semantic-success">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            Completed
          </Badge>
        );
      case 'error':
        return (
          <Badge variant="outline" className="text-semantic-error border-semantic-error">
            <AlertCircle className="w-3 h-3 mr-1" />
            Error
          </Badge>
        );
      default:
        return null;
    }
  };

  const getContentDisplay = () => {
    if (status === 'error') {
      return (
        <div className="text-semantic-error text-body">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-5 h-5" />
            <span className="font-semibold">Error occurred</span>
          </div>
          <p className="text-body-sm">{error || 'An unknown error occurred'}</p>
        </div>
      );
    }

    if (status === 'pending') {
      return (
        <div className="text-neutral-shadow text-body">
          <div className="flex items-center gap-2">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Waiting to start...</span>
          </div>
        </div>
      );
    }

    if (!content && status === 'streaming') {
      return (
        <div className="text-neutral-shadow text-body">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 animate-pulse" />
            <span>Initializing...</span>
          </div>
        </div>
      );
    }

    return (
      <div className="text-body text-neutral-charcoal whitespace-pre-wrap">
        {content}
        {status === 'streaming' && (
          <span className="inline-block w-2 h-5 bg-ai-accent animate-pulse ml-1" />
        )}
      </div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={className}
    >
      <Card className={cn(
        "bg-neutral-paper border-l-4 shadow-md hover:shadow-lg transition-all duration-300 relative overflow-hidden",
        getAgentColorClasses(agentColor).borderL,
        selected && cn("ring-2 ring-opacity-50", getAgentColorClasses(agentColor).ring),
        isSelecting && "scale-105"
      )}>
        
        {/* Selection Confirmation Overlay */}
        <AnimatePresence>
          {showConfirmation && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ duration: 0.5 }}
              className={cn(
                "absolute inset-0 flex items-center justify-center z-10 rounded-lg",
                getAgentColorClasses(agentColor).bgOpacity90
              )}
            >
              <div className="text-center text-white">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.1, type: "spring", stiffness: 200 }}
                >
                  <CheckCircle2 className="w-16 h-16 mx-auto mb-2" />
                </motion.div>
                <motion.h3
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.3 }}
                  className="text-h3 font-semibold"
                >
                  Response Selected!
                </motion.h3>
                <motion.p
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.4 }}
                  className="text-body-sm"
                >
                  {modelName} preference recorded
                </motion.p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <CardHeader className="pb-md">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-sm">
              <motion.div 
                className={cn(
                  "w-3 h-3 rounded-full",
                  getAgentColorClasses(agentColor).bg,
                  status === 'streaming' && 'animate-pulse'
                )}
                animate={isAnimating ? { scale: [1, 1.5, 1] } : {}}
                transition={{ duration: 0.6 }}
              />
              <div>
                <CardTitle className="text-h3 font-medium text-neutral-charcoal">
                  {modelName}
                </CardTitle>
                <p className="text-body-sm text-neutral-shadow">{provider}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {getStatusBadge()}
              {selected && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 200 }}
                >
                  <Badge className={cn(getAgentColorClasses(agentColor).bg, "text-white")}>
                    <Star className="w-3 h-3 mr-1 fill-current" />
                    Preferred
                  </Badge>
                </motion.div>
              )}
            </div>
          </div>
        </CardHeader>
      
      <CardContent className="space-y-md">
        {/* Response Content */}
        <div className="bg-neutral-white rounded-md p-md max-h-96 overflow-y-auto border border-neutral-fog">
          {getContentDisplay()}
        </div>
        
        {/* Response Metrics */}
        {status === 'completed' && (
          <div className="flex items-center justify-between text-body-sm text-neutral-shadow">
            <div className="flex items-center gap-4">
              {responseTime && (
                <span>{responseTime.toFixed(1)}s</span>
              )}
              {tokenCount && (
                <span>{tokenCount} tokens</span>
              )}
              {wordCount && (
                <span>{wordCount} words</span>
              )}
            </div>
            {selected && (
              <Badge className={cn(getAgentColorClasses(agentColor).bg, "text-white")}>
                Selected
              </Badge>
            )}
          </div>
        )}
        
        {/* Action Buttons */}
        {status === 'completed' && (
          <div className="flex gap-2">
            <motion.div className="flex-1">
              <Button
                onClick={handleSelect}
                disabled={isAnimating}
                className={cn(
                  "w-full transition-all duration-300",
                  selected
                    ? cn(getAgentColorClasses(agentColor).bg, "text-white shadow-lg", getAgentColorClasses(agentColor).hoverBg90)
                    : cn("border-2 bg-transparent hover:scale-105", getAgentColorClasses(agentColor).border, getAgentColorClasses(agentColor).text, getAgentColorClasses(agentColor).hoverBg10)
                )}
              >
                <motion.div
                  className="flex items-center justify-center gap-2"
                  animate={isAnimating ? { scale: [1, 1.1, 1] } : {}}
                  transition={{ duration: 0.3 }}
                >
                  {selected ? (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      Selected
                    </>
                  ) : (
                    <>
                      <Heart className="w-4 h-4" />
                      I prefer this
                    </>
                  )}
                </motion.div>
              </Button>
            </motion.div>
            
            {onPreferenceFeedback && (
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Button
                  onClick={onPreferenceFeedback}
                  variant="outline"
                  size="sm"
                  className="text-neutral-shadow hover:text-neutral-charcoal border-neutral-fog hover:border-neutral-shadow"
                >
                  <ThumbsUp className="w-4 h-4 mr-1" />
                  Feedback
                </Button>
              </motion.div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
    </motion.div>
  );
}

export default ModelResponsePanel;