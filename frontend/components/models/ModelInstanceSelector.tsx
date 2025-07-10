'use client';

import React, { useState, useRef, useEffect, useMemo } from 'react';
import { 
  Plus, 
  X, 
  Search, 
  Sparkles, 
  Star,
  ChevronRight,
  Loader2,
  Hash
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ModelInfo } from '@/types/models';
import { cn } from '@/lib/utils';

export interface ModelInstance {
  instanceId: string;
  modelId: string;
  modelInfo: ModelInfo;
  instanceNumber: number;
}

interface ModelInstanceSelectorProps {
  availableModels: ModelInfo[];
  selectedInstances: ModelInstance[];
  onAddInstance: (modelId: string) => void;
  onRemoveInstance: (instanceId: string) => void;
  maxInstances?: number;
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

export function ModelInstanceSelector({
  availableModels,
  selectedInstances,
  onAddInstance,
  onRemoveInstance,
  maxInstances = 10,
  isLoading = false,
  placeholder = "Click to add models..."
}: ModelInstanceSelectorProps) {
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

  // Count instances per model
  const instanceCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    selectedInstances.forEach(instance => {
      counts[instance.modelId] = (counts[instance.modelId] || 0) + 1;
    });
    return counts;
  }, [selectedInstances]);

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

  // Check if can add more
  const canAddMore = selectedInstances.length < maxInstances;

  // Group instances by model for display
  const groupedInstances = useMemo(() => {
    const groups: Record<string, ModelInstance[]> = {};
    selectedInstances.forEach(instance => {
      if (!groups[instance.modelId]) {
        groups[instance.modelId] = [];
      }
      groups[instance.modelId].push(instance);
    });
    return groups;
  }, [selectedInstances]);

  return (
    <div className="relative w-full">
      {/* Selected Models as Grouped Chips */}
      {selectedInstances.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-2">
          {Object.entries(groupedInstances).map(([modelId, instances]) => {
            const modelInfo = instances[0].modelInfo;
            return (
              <div key={modelId} className="flex items-center gap-1">
                <Badge
                  variant="secondary"
                  className="pl-2 pr-1 py-1 flex items-center gap-1"
                >
                  <span className="text-xs">{PROVIDER_EMOJIS[modelInfo.provider]}</span>
                  <span>{modelInfo.name}</span>
                  {instances.length > 1 && (
                    <span className="text-xs bg-neutral-fog rounded-full px-1.5 py-0.5 ml-1">
                      ×{instances.length}
                    </span>
                  )}
                </Badge>
                {/* Individual remove buttons for each instance */}
                {instances.map((instance, idx) => (
                  <button
                    key={instance.instanceId}
                    onClick={() => onRemoveInstance(instance.instanceId)}
                    className="p-1 rounded-full hover:bg-neutral-fog transition-colors"
                    title={`Remove ${modelInfo.name} #${instance.instanceNumber}`}
                  >
                    <X className="h-3 w-3" />
                  </button>
                ))}
              </div>
            );
          })}
        </div>
      )}

      {/* Dropdown Trigger */}
      <Button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        variant="outline"
        className="w-full justify-between font-normal"
        disabled={isLoading || !canAddMore}
        data-testid="model-selector"
      >
        <span className={cn(
          "text-left",
          selectedInstances.length === 0 && "text-neutral-shadow"
        )}>
          {isLoading ? (
            <span className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading models...
            </span>
          ) : !canAddMore ? (
            `Maximum ${maxInstances} models selected`
          ) : selectedInstances.length === 0 ? (
            placeholder
          ) : (
            `${selectedInstances.length} model${selectedInstances.length === 1 ? '' : 's'} selected (click to add more)`
          )}
        </span>
        <Plus className={cn(
          "h-4 w-4",
          !canAddMore && "opacity-50"
        )} />
      </Button>

      {/* Dropdown Content */}
      {isOpen && !isLoading && canAddMore && (
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
                placeholder="Search models to add..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-3 py-2 text-sm border border-neutral-fog rounded-md focus:outline-none focus:border-ai-primary"
                autoFocus
              />
            </div>
          </div>

          {/* Quick Actions */}
          <div className="px-3 py-2 border-b border-neutral-fog flex items-center justify-between">
            <span className="text-xs text-neutral-shadow">
              Click on any model to add it
            </span>
            {maxInstances && (
              <span className="text-xs text-neutral-shadow">
                {selectedInstances.length}/{maxInstances} slots used
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
                      </div>
                    </button>

                    {/* Model Items */}
                    {isExpanded && (
                      <div className="pb-2">
                        {models.map(model => {
                          const count = instanceCounts[model.id] || 0;
                          
                          return (
                            <button
                              key={model.id}
                              onClick={() => onAddInstance(model.id)}
                              className="w-full px-8 py-2 flex items-center gap-3 hover:bg-ai-primary/10 transition-colors text-left group"
                            >
                              <Plus className="h-4 w-4 text-ai-primary opacity-0 group-hover:opacity-100 transition-opacity" />
                              
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-medium truncate">
                                    {model.name}
                                  </span>
                                  {count > 0 && (
                                    <Badge variant="secondary" className="text-xs px-1.5 py-0">
                                      <Hash className="h-3 w-3 mr-0.5" />
                                      {count}
                                    </Badge>
                                  )}
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