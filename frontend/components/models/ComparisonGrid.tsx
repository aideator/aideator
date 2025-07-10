'use client';

import React, { useState } from 'react';
import { ModelResponsePanel } from './ModelResponsePanel';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ChevronLeft, ChevronRight, Grid3X3, Maximize2, Minimize2, Eye, EyeOff } from 'lucide-react';
import { cn, getAgentColorClasses } from '@/lib/utils';

export interface ModelResponse {
  id: string;
  name: string;
  provider: string;
  status: 'pending' | 'streaming' | 'completed' | 'error';
  content: string;
  responseTime?: number;
  tokenCount?: number;
  wordCount?: number;
  selected?: boolean;
  error?: string;
}

interface ComparisonGridProps {
  responses: ModelResponse[];
  onSelectResponse: (modelId: string) => void;
  onPreferenceFeedback?: (modelId: string) => void;
  className?: string;
}

export function ComparisonGrid({
  responses,
  onSelectResponse,
  onPreferenceFeedback,
  className,
}: ComparisonGridProps) {
  const [currentPage, setCurrentPage] = useState(0);
  const [isExpanded, setIsExpanded] = useState(false);
  const [hiddenPanels, setHiddenPanels] = useState<Set<string>>(new Set());

  const getAgentColor = (index: number) => {
    const colors = ['agent-1', 'agent-2', 'agent-3', 'agent-4', 'agent-5'];
    return colors[index % colors.length];
  };

  const getGridLayout = () => {
    const visibleResponses = responses.filter(r => !hiddenPanels.has(r.id));
    const count = visibleResponses.length;
    
    if (count === 0) return 'grid-cols-1';
    if (count === 1) return 'grid-cols-1';
    if (count === 2) return 'grid-cols-1 md:grid-cols-2';
    if (count === 3) return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3';
    if (count === 4) return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-4';
    
    // For 5+ models, show 4 at a time with pagination
    return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-4';
  };

  const getVisibleResponses = () => {
    const visibleResponses = responses.filter(r => !hiddenPanels.has(r.id));
    
    if (visibleResponses.length <= 4) {
      return visibleResponses;
    }
    
    // Pagination for 5+ models
    const itemsPerPage = 4;
    const startIndex = currentPage * itemsPerPage;
    return visibleResponses.slice(startIndex, startIndex + itemsPerPage);
  };

  const togglePanelVisibility = (modelId: string) => {
    setHiddenPanels(prev => {
      const newSet = new Set(prev);
      if (newSet.has(modelId)) {
        newSet.delete(modelId);
      } else {
        newSet.add(modelId);
      }
      return newSet;
    });
  };

  const visibleResponses = getVisibleResponses();
  const totalVisibleResponses = responses.filter(r => !hiddenPanels.has(r.id)).length;
  const totalPages = Math.ceil(totalVisibleResponses / 4);
  const showPagination = totalVisibleResponses > 4;

  const getStatusSummary = () => {
    const statusCounts = responses.reduce((acc, response) => {
      acc[response.status] = (acc[response.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return statusCounts;
  };

  const statusSummary = getStatusSummary();

  if (responses.length === 0) {
    return (
      <div className="text-center py-xl">
        <Grid3X3 className="w-16 h-16 text-neutral-shadow mx-auto mb-4" />
        <p className="text-body-lg text-neutral-shadow">No model responses yet</p>
        <p className="text-body-sm text-neutral-shadow">Start a comparison to see results</p>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Grid Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h3 className="text-h3 font-semibold text-neutral-charcoal">
            Model Comparison
          </h3>
          <div className="flex items-center gap-2">
            {Object.entries(statusSummary).map(([status, count]) => (
              <Badge
                key={status}
                variant="outline"
                className={`text-xs ${
                  status === 'completed' ? 'text-semantic-success border-semantic-success' :
                  status === 'streaming' ? 'text-ai-accent border-ai-accent' :
                  status === 'error' ? 'text-semantic-error border-semantic-error' :
                  'text-neutral-shadow border-neutral-shadow'
                }`}
              >
                {count} {status}
              </Badge>
            ))}
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Panel Visibility Controls */}
          {responses.length > 1 && (
            <div className="flex items-center gap-1">
              {responses.map((response, index) => (
                <Button
                  key={response.id}
                  onClick={() => togglePanelVisibility(response.id)}
                  variant="ghost"
                  size="sm"
                  className={cn(
                    "w-8 h-8 p-0",
                    hiddenPanels.has(response.id)
                      ? "text-neutral-shadow hover:text-neutral-charcoal"
                      : cn(getAgentColorClasses(getAgentColor(index)).text, "hover:opacity-80")
                  )}
                  title={`${hiddenPanels.has(response.id) ? 'Show' : 'Hide'} ${response.name}`}
                >
                  {hiddenPanels.has(response.id) ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </Button>
              ))}
            </div>
          )}

          {/* Expand/Collapse Toggle */}
          <Button
            onClick={() => setIsExpanded(!isExpanded)}
            variant="ghost"
            size="sm"
            className="text-neutral-shadow hover:text-neutral-charcoal"
          >
            {isExpanded ? (
              <Minimize2 className="w-4 h-4" />
            ) : (
              <Maximize2 className="w-4 h-4" />
            )}
          </Button>
        </div>
      </div>

      {/* Pagination Controls */}
      {showPagination && (
        <div className="flex items-center justify-center gap-4">
          <Button
            onClick={() => setCurrentPage(prev => Math.max(0, prev - 1))}
            disabled={currentPage === 0}
            variant="outline"
            size="sm"
          >
            <ChevronLeft className="w-4 h-4" />
            Previous
          </Button>
          
          <div className="flex items-center gap-1">
            {Array.from({ length: totalPages }, (_, i) => (
              <Button
                key={i}
                onClick={() => setCurrentPage(i)}
                variant={currentPage === i ? "default" : "ghost"}
                size="sm"
                className="w-8 h-8 p-0"
              >
                {i + 1}
              </Button>
            ))}
          </div>
          
          <Button
            onClick={() => setCurrentPage(prev => Math.min(totalPages - 1, prev + 1))}
            disabled={currentPage === totalPages - 1}
            variant="outline"
            size="sm"
          >
            Next
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      )}

      {/* Model Response Grid */}
      <div className={`grid gap-2 ${getGridLayout()}`}>
        {visibleResponses.map((response, index) => {
          const originalIndex = responses.findIndex(r => r.id === response.id);
          return (
            <ModelResponsePanel
              key={response.id}
              modelId={response.id}
              modelName={response.name}
              provider={response.provider}
              status={response.status}
              content={response.content}
              responseTime={response.responseTime}
              tokenCount={response.tokenCount}
              wordCount={response.wordCount}
              selected={response.selected}
              agentColor={getAgentColor(originalIndex)}
              error={response.error}
              onSelect={() => onSelectResponse(response.id)}
              onPreferenceFeedback={onPreferenceFeedback ? () => onPreferenceFeedback(response.id) : undefined}
              className={isExpanded ? 'h-full' : ''}
            />
          );
        })}
      </div>

      {/* Summary Information */}
      {responses.some(r => r.status === 'completed') && (
        <div className="bg-neutral-paper rounded-lg p-md border border-neutral-fog">
          <h4 className="text-h3 font-medium text-neutral-charcoal mb-2">
            Comparison Summary
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-body-sm">
            <div>
              <span className="text-neutral-shadow">Average Response Time:</span>
              <span className="ml-2 font-medium text-neutral-charcoal">
                {responses
                  .filter(r => r.status === 'completed' && r.responseTime)
                  .reduce((acc, r) => acc + (r.responseTime || 0), 0) / 
                  responses.filter(r => r.status === 'completed' && r.responseTime).length || 0
                }s
              </span>
            </div>
            <div>
              <span className="text-neutral-shadow">Total Tokens:</span>
              <span className="ml-2 font-medium text-neutral-charcoal">
                {responses
                  .filter(r => r.status === 'completed')
                  .reduce((acc, r) => acc + (r.tokenCount || 0), 0)
                }
              </span>
            </div>
            <div>
              <span className="text-neutral-shadow">Selected:</span>
              <span className="ml-2 font-medium text-neutral-charcoal">
                {responses.find(r => r.selected)?.name || 'None'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ComparisonGrid;