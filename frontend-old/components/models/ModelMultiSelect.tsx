'use client';

import React, { useState, useRef, useEffect, useMemo } from 'react';
import { 
  Check, 
  ChevronDown, 
  X, 
  Search, 
  Sparkles, 
  Star,
  ChevronRight,
  Loader2
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ModelInfo } from '@/types/models';
import { cn } from '@/lib/utils';

interface ModelMultiSelectProps {
  availableModels: ModelInfo[];
  selectedModels: string[];
  onModelToggle: (modelId: string) => void;
  maxSelection?: number;
  minSelection?: number;
  isLoading?: boolean;
  placeholder?: string;
}

interface GroupedModels {
  [provider: string]: ModelInfo[];
}

const PROVIDER_EMOJIS: Record<string, string> = {
  'OpenAI': '🟢',
  'Anthropic': '🔶',
  'Google': '🔵',
  'Meta': '⚪',
  'Mistral': '🟠',
  'Cohere': '🟣',
  'Hugging Face': '🤗',
};

export function ModelMultiSelect({
  availableModels,
  selectedModels,
  onModelToggle,
  maxSelection,
  minSelection = 1,
  isLoading = false,
  placeholder = "Select models to compare..."
}: ModelMultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node) &&
          buttonRef.current && !buttonRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Group models by provider
  const groupedModels = useMemo(() => {
    const groups: GroupedModels = {};
    
    availableModels.forEach(model => {
      if (!groups[model.provider]) {
        groups[model.provider] = [];
      }
      groups[model.provider].push(model);
    });

    return groups;
  }, [availableModels]);

  // Filter models based on search
  const filteredGroups = useMemo(() => {
    if (!searchQuery) return groupedModels;

    const query = searchQuery.toLowerCase();
    const filtered: GroupedModels = {};

    Object.entries(groupedModels).forEach(([provider, models]) => {
      const filteredModels = models.filter(model =>
        model.name.toLowerCase().includes(query) ||
        model.provider.toLowerCase().includes(query) ||
        model.description?.toLowerCase().includes(query) ||
        model.capabilities?.some(cap => cap.toLowerCase().includes(query))
      );

      if (filteredModels.length > 0) {
        filtered[provider] = filteredModels;
      }
    });

    return filtered;
  }, [groupedModels, searchQuery]);

  // Get selected model info
  const selectedModelInfo = selectedModels
    .map(id => availableModels.find(m => m.id === id))
    .filter((m): m is ModelInfo => m !== undefined);

  // Toggle group expansion
  const toggleGroup = (provider: string) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(provider)) {
      newExpanded.delete(provider);
    } else {
      newExpanded.add(provider);
    }
    setExpandedGroups(newExpanded);
  };

  // Check if can select more
  const canSelectMore = !maxSelection || selectedModels.length < maxSelection;
  const canDeselectMore = selectedModels.length > minSelection;

  return (
    <div className="relative w-full">
      {/* Selected Models as Chips */}
      {selectedModelInfo.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-2">
          {selectedModelInfo.map(model => (
            <Badge
              key={model.id}
              variant="secondary"
              className="pl-2 pr-1 py-1 flex items-center gap-1"
            >
              <span className="text-xs">{PROVIDER_EMOJIS[model.provider]}</span>
              <span>{model.name}</span>
              {canDeselectMore && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onModelToggle(model.id);
                  }}
                  className="ml-1 rounded-full hover:bg-neutral-fog p-0.5"
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </Badge>
          ))}
        </div>
      )}

      {/* Dropdown Trigger */}
      <Button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        variant="outline"
        className="w-full justify-between font-normal"
        disabled={isLoading}
      >
        <span className={cn(
          "text-left",
          selectedModels.length === 0 && "text-neutral-shadow"
        )}>
          {isLoading ? (
            <span className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading models...
            </span>
          ) : selectedModels.length === 0 ? (
            placeholder
          ) : (
            `${selectedModels.length} model${selectedModels.length === 1 ? '' : 's'} selected`
          )}
        </span>
        <ChevronDown className={cn(
          "h-4 w-4 transition-transform",
          isOpen && "rotate-180"
        )} />
      </Button>

      {/* Dropdown Content */}
      {isOpen && !isLoading && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-2 bg-neutral-white border border-neutral-fog rounded-lg shadow-lg"
          style={{ maxHeight: 'min(600px, calc(100vh - 200px))' }}
        >
          {/* Search Bar */}
          <div className="p-3 border-b border-neutral-fog">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-neutral-shadow" />
              <input
                type="text"
                placeholder="Search models..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-3 py-2 text-sm border border-neutral-fog rounded-md focus:outline-none focus:border-ai-primary"
                autoFocus
              />
            </div>
          </div>

          {/* Quick Actions */}
          <div className="px-3 py-2 border-b border-neutral-fog flex items-center gap-2">
            <button
              onClick={() => {
                const recommended = availableModels
                  .filter(m => m.isRecommended && !selectedModels.includes(m.id));
                recommended.forEach(m => onModelToggle(m.id));
              }}
              className="text-xs text-ai-primary hover:underline"
            >
              Select recommended
            </button>
            {selectedModels.length > 0 && (
              <>
                <span className="text-neutral-fog">•</span>
                <button
                  onClick={() => {
                    selectedModels.forEach(id => onModelToggle(id));
                  }}
                  className="text-xs text-ai-primary hover:underline"
                >
                  Clear all
                </button>
              </>
            )}
            {maxSelection && (
              <span className="ml-auto text-xs text-neutral-shadow">
                {selectedModels.length}/{maxSelection} selected
              </span>
            )}
          </div>

          {/* Model List */}
          <div className="overflow-y-auto" style={{ maxHeight: 'calc(min(600px, calc(100vh - 200px)) - 120px)' }}>
            {Object.keys(filteredGroups).length === 0 ? (
              <div className="p-8 text-center text-neutral-shadow">
                <p className="text-sm">No models found</p>
                {searchQuery && (
                  <p className="text-xs mt-1">Try adjusting your search</p>
                )}
              </div>
            ) : (
              Object.entries(filteredGroups).map(([provider, models]) => {
                const isExpanded = expandedGroups.has(provider) || searchQuery.length > 0;
                const selectedCount = models.filter(m => selectedModels.includes(m.id)).length;
                
                return (
                  <div key={provider} className="border-b border-neutral-fog last:border-0">
                    {/* Provider Header */}
                    <button
                      onClick={() => toggleGroup(provider)}
                      className="w-full px-3 py-2 flex items-center justify-between hover:bg-neutral-fog/50 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <ChevronRight className={cn(
                          "h-4 w-4 transition-transform",
                          isExpanded && "rotate-90"
                        )} />
                        <span className="text-sm font-medium">
                          {PROVIDER_EMOJIS[provider]} {provider}
                        </span>
                        <span className="text-xs text-neutral-shadow">
                          ({models.length} models)
                        </span>
                        {selectedCount > 0 && (
                          <Badge variant="secondary" className="text-xs px-1.5 py-0">
                            {selectedCount} selected
                          </Badge>
                        )}
                      </div>
                    </button>

                    {/* Model Items */}
                    {isExpanded && (
                      <div className="pb-2">
                        {models.map(model => {
                          const isSelected = selectedModels.includes(model.id);
                          const isDisabled = !isSelected && !canSelectMore;
                          
                          return (
                            <button
                              key={model.id}
                              onClick={() => {
                                if (!isDisabled || isSelected) {
                                  onModelToggle(model.id);
                                }
                              }}
                              disabled={isDisabled}
                              className={cn(
                                "w-full px-8 py-2 flex items-center gap-3 hover:bg-neutral-fog/50 transition-colors text-left",
                                isSelected && "bg-ai-primary/10",
                                isDisabled && "opacity-50 cursor-not-allowed"
                              )}
                            >
                              <div className={cn(
                                "w-4 h-4 rounded border-2 flex items-center justify-center transition-all",
                                isSelected
                                  ? "border-ai-primary bg-ai-primary"
                                  : "border-neutral-fog"
                              )}>
                                {isSelected && (
                                  <Check className="w-3 h-3 text-white" />
                                )}
                              </div>
                              
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-medium truncate">
                                    {model.name}
                                  </span>
                                  {model.isRecommended && (
                                    <Star className="h-3 w-3 text-yellow-500 flex-shrink-0" />
                                  )}
                                  {model.isNew && (
                                    <Sparkles className="h-3 w-3 text-green-500 flex-shrink-0" />
                                  )}
                                </div>
                                <div className="flex items-center gap-3 text-xs text-neutral-shadow">
                                  {model.pricing && (
                                    <span>
                                      ${(model.pricing.input + model.pricing.output).toFixed(3)}/1K
                                    </span>
                                  )}
                                  {model.averageResponseTime && (
                                    <span>{model.averageResponseTime}s</span>
                                  )}
                                  {model.maxTokens && (
                                    <span>{model.maxTokens.toLocaleString()} tokens</span>
                                  )}
                                </div>
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}