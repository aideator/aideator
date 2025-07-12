'use client';

import React, { useState, useMemo } from 'react';
import { Search, CheckCircle2, Info, Sparkles, Zap, Star } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { ModelInfo } from '@/types/models';

interface EnhancedModelSelectorProps {
  availableModels: ModelInfo[];
  selectedModels: string[];
  onModelToggle: (modelId: string) => void;
  maxSelection: number;
  isLoading?: boolean;
}

interface ProviderGroup {
  provider: string;
  models: ModelInfo[];
  hasApiKey?: boolean;
}

const PROVIDER_LOGOS: Record<string, string> = {
  'OpenAI': '🟢',
  'Anthropic': '🔶',
  'Google': '🔵',
  'Meta': '⚪',
  'Mistral': '🟠',
  'Cohere': '🟣',
  'Hugging Face': '🤗',
};

const PROVIDER_COLORS: Record<string, string> = {
  'OpenAI': 'border-green-500 bg-green-50',
  'Anthropic': 'border-orange-500 bg-orange-50',
  'Google': 'border-blue-500 bg-blue-50',
  'Meta': 'border-gray-500 bg-gray-50',
  'Mistral': 'border-amber-500 bg-amber-50',
  'Cohere': 'border-purple-500 bg-purple-50',
  'Hugging Face': 'border-yellow-500 bg-yellow-50',
};

export function EnhancedModelSelector({
  availableModels,
  selectedModels,
  onModelToggle,
  maxSelection,
  isLoading = false,
}: EnhancedModelSelectorProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('all');

  // Group models by provider
  const providerGroups = useMemo(() => {
    const groups: Record<string, ProviderGroup> = {};
    
    availableModels.forEach(model => {
      if (!groups[model.provider]) {
        groups[model.provider] = {
          provider: model.provider,
          models: [],
        };
      }
      groups[model.provider].models.push(model);
    });

    return Object.values(groups).sort((a, b) => a.provider.localeCompare(b.provider));
  }, [availableModels]);

  // Filter models based on search query
  const filteredModels = useMemo(() => {
    const query = searchQuery.toLowerCase();
    return availableModels.filter(model =>
      model.name.toLowerCase().includes(query) ||
      model.provider.toLowerCase().includes(query) ||
      model.description?.toLowerCase().includes(query) ||
      model.capabilities?.some(cap => cap.toLowerCase().includes(query))
    );
  }, [availableModels, searchQuery]);

  // Get models for current tab
  const displayModels = useMemo(() => {
    if (activeTab === 'all') return filteredModels;
    if (activeTab === 'selected') return filteredModels.filter(m => selectedModels.includes(m.id));
    if (activeTab === 'recommended') return filteredModels.filter(m => m.isRecommended);
    
    // Provider-specific tab
    return filteredModels.filter(m => m.provider === activeTab);
  }, [filteredModels, activeTab, selectedModels]);

  const canSelectMore = selectedModels.length < maxSelection;

  const ModelCard = ({ model }: { model: ModelInfo }) => {
    const isSelected = selectedModels.includes(model.id);
    
    return (
      <div
        className={`p-3 rounded-md border cursor-pointer transition-all ${
          isSelected
            ? 'border-ai-primary bg-ai-primary/10'
            : 'border-neutral-fog bg-neutral-white hover:border-neutral-shadow'
        } ${!canSelectMore && !isSelected ? 'opacity-50 cursor-not-allowed' : ''}`}
        onClick={() => {
          if (isSelected || canSelectMore) {
            onModelToggle(model.id);
          }
        }}
      >
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <span className="text-sm flex-shrink-0">{PROVIDER_LOGOS[model.provider] || '🤖'}</span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h4 className="font-medium text-sm text-neutral-charcoal truncate">{model.name}</h4>
                {model.isRecommended && (
                  <Star className="w-3 h-3 text-yellow-500 flex-shrink-0" />
                )}
                {model.isNew && (
                  <Sparkles className="w-3 h-3 text-green-500 flex-shrink-0" />
                )}
              </div>
              <div className="flex items-center gap-2 text-xs text-neutral-shadow">
                <span>{model.provider}</span>
                {model.pricing && (
                  <span>• ${(model.pricing.input + model.pricing.output).toFixed(3)}/1K</span>
                )}
                {model.averageResponseTime && (
                  <span>• {model.averageResponseTime}s</span>
                )}
              </div>
            </div>
          </div>
          <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all flex-shrink-0 ${
            isSelected
              ? 'border-ai-primary bg-ai-primary'
              : 'border-neutral-fog bg-white'
          }`}>
            {isSelected && (
              <CheckCircle2 className="w-3 h-3 text-white" />
            )}
          </div>
        </div>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-32 bg-neutral-fog rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-shadow w-4 h-4" />
        <Input
          type="text"
          placeholder="Search models by name, provider, or capability..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Selection Info */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-neutral-shadow">
          {selectedModels.length} models selected
        </span>
        {selectedModels.length > 0 && (
          <button
            onClick={() => selectedModels.forEach(id => onModelToggle(id))}
            className="text-sm text-ai-primary hover:underline"
          >
            Clear selection
          </button>
        )}
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid grid-cols-4 lg:grid-cols-6 mb-4">
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="selected">
            Selected ({selectedModels.length})
          </TabsTrigger>
          <TabsTrigger value="recommended">
            <Star className="w-3 h-3 mr-1" />
            Recommended
          </TabsTrigger>
          {providerGroups.slice(0, 3).map(group => (
            <TabsTrigger key={group.provider} value={group.provider}>
              {PROVIDER_LOGOS[group.provider]} {group.provider}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value={activeTab} className="mt-0">
          <ScrollArea className="h-[300px] pr-4">
            <div className="space-y-2">
              {displayModels.length === 0 ? (
                <div className="text-center py-8 text-neutral-shadow">
                  <Info className="w-12 h-12 mx-auto mb-2 text-neutral-fog" />
                  <p>No models found</p>
                  {searchQuery && (
                    <p className="text-sm mt-2">
                      Try adjusting your search query
                    </p>
                  )}
                </div>
              ) : (
                displayModels.map(model => (
                  <ModelCard key={model.id} model={model} />
                ))
              )}
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>

      {/* Quick Actions */}
      <div className="flex items-center gap-2 pt-2 border-t border-neutral-fog">
        <button
          onClick={() => {
            const recommended = availableModels
              .filter(m => m.isRecommended && !selectedModels.includes(m.id));
            recommended.forEach(m => onModelToggle(m.id));
          }}
          className="text-sm text-ai-primary hover:underline"
        >
          Select all recommended
        </button>
        <span className="text-neutral-fog">•</span>
        <button
          onClick={() => {
            const allModels = availableModels
              .filter(m => !selectedModels.includes(m.id));
            allModels.forEach(m => onModelToggle(m.id));
          }}
          className="text-sm text-ai-primary hover:underline"
        >
          Select all
        </button>
      </div>
    </div>
  );
}