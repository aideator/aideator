'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  User, 
  Bot, 
  Clock, 
  MessageSquare, 
  ThumbsUp, 
  Download,
  Share2,
  Copy,
  Check,
  ChevronUp,
  ChevronDown,
  Filter,
  Search,
  Calendar,
  Star,
  StarOff
} from 'lucide-react';
import { SessionTurn } from '@/context/SessionContext';
import { formatDistanceToNow, format } from 'date-fns';
import { cn, getAgentColorClasses } from '@/lib/utils';

interface SessionTranscriptProps {
  sessionId: string;
  sessionTitle: string;
  turns: SessionTurn[];
  onTurnUpdate?: (turnId: string, updates: Partial<SessionTurn>) => void;
  onExport?: (format: 'json' | 'markdown' | 'txt') => void;
  className?: string;
}

type ViewMode = 'full' | 'compact' | 'selected-only';

export function SessionTranscript({
  sessionId,
  sessionTitle,
  turns,
  onTurnUpdate,
  onExport,
  className,
}: SessionTranscriptProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('full');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedTurns, setExpandedTurns] = useState<Set<string>>(new Set());
  const [copiedTurnId, setCopiedTurnId] = useState<string | null>(null);
  const [showTimestamps, setShowTimestamps] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Filter turns based on search query and view mode
  const filteredTurns = React.useMemo(() => {
    let filtered = turns;

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(turn => 
        turn.prompt.toLowerCase().includes(searchQuery.toLowerCase()) ||
        turn.modelResponses.some(response => 
          response.response.toLowerCase().includes(searchQuery.toLowerCase())
        )
      );
    }

    // Apply view mode filter
    if (viewMode === 'selected-only') {
      filtered = filtered.filter(turn => 
        turn.preferredModelId || turn.modelResponses.some(r => r.selected)
      );
    }

    return filtered;
  }, [turns, searchQuery, viewMode]);

  const toggleTurnExpansion = (turnId: string) => {
    setExpandedTurns(prev => {
      const newSet = new Set(prev);
      if (newSet.has(turnId)) {
        newSet.delete(turnId);
      } else {
        newSet.add(turnId);
      }
      return newSet;
    });
  };

  const copyTurnToClipboard = async (turn: SessionTurn) => {
    const text = `Prompt: ${turn.prompt}\n\nResponses:\n${turn.modelResponses.map(r => 
      `${r.modelName}: ${r.response}`
    ).join('\n\n')}`;
    
    try {
      await navigator.clipboard.writeText(text);
      setCopiedTurnId(turn.id);
      setTimeout(() => setCopiedTurnId(null), 2000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const handleTurnRating = (turnId: string, rating: number) => {
    if (onTurnUpdate) {
      onTurnUpdate(turnId, { userFeedback: rating.toString() });
    }
  };

  const getAgentColor = (index: number) => {
    const colors = ['agent-1', 'agent-2', 'agent-3', 'agent-4', 'agent-5'];
    return colors[index % colors.length];
  };

  const renderTurnContent = (turn: SessionTurn, isExpanded: boolean) => {
    const selectedResponse = turn.modelResponses.find(r => r.selected);
    const responsesToShow = viewMode === 'compact' && selectedResponse 
      ? [selectedResponse] 
      : turn.modelResponses;

    return (
      <div className="space-y-md">
        {/* User Prompt */}
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-full bg-ai-primary flex items-center justify-center flex-shrink-0">
            <User className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="bg-neutral-white rounded-lg p-md border border-neutral-fog">
              <p className="text-body text-neutral-charcoal whitespace-pre-wrap">
                {turn.prompt}
              </p>
            </div>
            {showTimestamps && (
              <div className="flex items-center gap-2 mt-1 text-caption text-neutral-shadow">
                <Clock className="w-3 h-3" />
                <span>{format(new Date(turn.createdAt), 'MMM d, yyyy h:mm a')}</span>
              </div>
            )}
          </div>
        </div>

        {/* Model Responses */}
        <div className="ml-11 space-y-sm">
          {responsesToShow.map((response, index) => (
            <div key={`${turn.id}-${response.modelId}`} className="flex items-start gap-3">
              <div className={cn("w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0", getAgentColorClasses(getAgentColor(index)).bg)}>
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium text-neutral-charcoal">
                    {response.modelName}
                  </span>
                  {response.selected && (
                    <Badge className={cn(getAgentColorClasses(getAgentColor(index)).bg, "text-white text-xs")}>
                      Selected
                    </Badge>
                  )}
                  {response.responseTime && (
                    <Badge variant="outline" className="text-xs">
                      {response.responseTime.toFixed(1)}s
                    </Badge>
                  )}
                </div>
                <div className={cn("bg-neutral-paper rounded-lg p-md border-l-4", getAgentColorClasses(getAgentColor(index)).borderL)}>
                  <p className={`text-body text-neutral-charcoal whitespace-pre-wrap ${
                    !isExpanded && response.response.length > 300 ? 'line-clamp-3' : ''
                  }`}>
                    {response.response}
                  </p>
                  {!isExpanded && response.response.length > 300 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleTurnExpansion(turn.id)}
                      className="mt-2 text-neutral-shadow hover:text-neutral-charcoal"
                    >
                      Show more
                    </Button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className={`bg-neutral-paper rounded-lg border border-neutral-fog ${className}`}>
      <CardHeader className="border-b border-neutral-fog">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-h3 font-semibold text-neutral-charcoal">
              {sessionTitle}
            </CardTitle>
            <p className="text-body-sm text-neutral-shadow">
              {filteredTurns.length} {filteredTurns.length === 1 ? 'turn' : 'turns'}
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            {/* View Mode Toggle */}
            <div className="flex items-center border border-neutral-fog rounded-lg">
              <Button
                variant={viewMode === 'full' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('full')}
                className="rounded-r-none"
              >
                Full
              </Button>
              <Button
                variant={viewMode === 'compact' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('compact')}
                className="rounded-none border-x"
              >
                Compact
              </Button>
              <Button
                variant={viewMode === 'selected-only' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('selected-only')}
                className="rounded-l-none"
              >
                Selected
              </Button>
            </div>

            {/* Options */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowTimestamps(!showTimestamps)}
              className={showTimestamps ? 'text-ai-primary' : 'text-neutral-shadow'}
            >
              <Calendar className="w-4 h-4" />
            </Button>

            {/* Export */}
            {onExport && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onExport('markdown')}
                className="text-neutral-shadow hover:text-neutral-charcoal"
              >
                <Download className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-shadow w-4 h-4" />
          <input
            type="text"
            placeholder="Search turns..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-neutral-white border border-neutral-fog rounded-md text-body placeholder:text-neutral-shadow focus:border-ai-primary focus:ring-2 focus:ring-ai-primary/20 transition-colors"
          />
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <ScrollArea ref={scrollAreaRef} className="h-96 p-lg">
          {filteredTurns.length === 0 ? (
            <div className="text-center py-xl">
              {searchQuery ? (
                <div>
                  <Search className="w-12 h-12 mx-auto mb-2 text-neutral-fog" />
                  <p className="text-body-sm text-neutral-shadow">No turns found for "{searchQuery}"</p>
                </div>
              ) : (
                <div>
                  <MessageSquare className="w-12 h-12 mx-auto mb-2 text-neutral-fog" />
                  <p className="text-body-sm text-neutral-shadow">No conversation history yet</p>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-xl">
              {filteredTurns.map((turn, index) => {
                const isExpanded = expandedTurns.has(turn.id);
                
                return (
                  <div key={turn.id} className="relative">
                    {index > 0 && (
                      <div className="absolute left-4 -top-xl w-px h-xl bg-neutral-fog" />
                    )}
                    
                    <div className="bg-neutral-white rounded-lg border border-neutral-fog">
                      <div className="p-lg">
                        <div className="flex items-center justify-between mb-md">
                          <div className="flex items-center gap-2">
                            <span className="text-body-sm font-medium text-neutral-charcoal">
                              Turn {index + 1}
                            </span>
                            <span className="text-body-sm text-neutral-shadow">
                              {formatDistanceToNow(new Date(turn.createdAt), { addSuffix: true })}
                            </span>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            {/* Turn Rating */}
                            <div className="flex items-center gap-1">
                              {[1, 2, 3, 4, 5].map((rating) => (
                                <button
                                  key={rating}
                                  onClick={() => handleTurnRating(turn.id, rating)}
                                  className="text-neutral-shadow hover:text-amber-600 transition-colors"
                                >
                                  {turn.userFeedback && parseInt(turn.userFeedback) >= rating ? (
                                    <Star className="w-4 h-4 fill-amber-600 text-amber-600" />
                                  ) : (
                                    <StarOff className="w-4 h-4" />
                                  )}
                                </button>
                              ))}
                            </div>

                            {/* Copy Button */}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => copyTurnToClipboard(turn)}
                              className="text-neutral-shadow hover:text-neutral-charcoal"
                            >
                              {copiedTurnId === turn.id ? (
                                <Check className="w-4 h-4 text-semantic-success" />
                              ) : (
                                <Copy className="w-4 h-4" />
                              )}
                            </Button>

                            {/* Expand/Collapse */}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => toggleTurnExpansion(turn.id)}
                              className="text-neutral-shadow hover:text-neutral-charcoal"
                            >
                              {isExpanded ? (
                                <ChevronUp className="w-4 h-4" />
                              ) : (
                                <ChevronDown className="w-4 h-4" />
                              )}
                            </Button>
                          </div>
                        </div>

                        {renderTurnContent(turn, isExpanded)}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </div>
  );
}

