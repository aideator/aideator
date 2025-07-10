'use client';

import { useState, useEffect } from 'react';
import { Plus, Search, Filter, Zap, Shield, Globe, Code, Eye, Music, Image, Tool, Cpu, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { cn } from '@/lib/utils';

// Types
interface ModelCapability {
  text_completion: string;
  chat_completion: string;
  vision: string;
  embedding: string;
  audio_input: string;
  audio_output: string;
  image_generation: string;
  web_search: string;
  function_calling: string;
  streaming: string;
  json_schema: string;
  pdf_input: string;
}

interface ModelDefinition {
  id: string;
  provider: string;
  model_name: string;
  litellm_model_name: string;
  display_name: string;
  description?: string;
  context_window?: number;
  max_output_tokens?: number;
  input_price_per_1m_tokens?: number;
  output_price_per_1m_tokens?: number;
  capabilities: string[];
  requires_api_key: boolean;
  requires_region: boolean;
  requires_project_id: boolean;
  is_active: boolean;
}

interface ProviderSummary {
  provider: string;
  display_name: string;
  description: string;
  requires_api_key: boolean;
  model_count: number;
  user_has_credentials: boolean;
}

interface ModelVariant {
  id: string;
  model_definition_id: string;
  provider_credential_id?: string;
  model_parameters: {
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
  };
}

interface ModelSelectorProps {
  selectedVariants: ModelVariant[];
  onVariantsChange: (variants: ModelVariant[]) => void;
  maxVariants?: number;
}

const capabilityIcons = {
  text_completion: Code,
  chat_completion: Shield,
  vision: Eye,
  embedding: Cpu,
  audio_input: Music,
  audio_output: Music,
  image_generation: Image,
  web_search: Globe,
  function_calling: Tool,
  streaming: Zap,
  json_schema: Code,
  pdf_input: Code,
};

const capabilityLabels = {
  text_completion: 'Text Completion',
  chat_completion: 'Chat',
  vision: 'Vision',
  embedding: 'Embedding',
  audio_input: 'Audio Input',
  audio_output: 'Audio Output',
  image_generation: 'Image Generation',
  web_search: 'Web Search',
  function_calling: 'Function Calling',
  streaming: 'Streaming',
  json_schema: 'JSON Schema',
  pdf_input: 'PDF Input',
};

const providerColors = {
  openai: 'bg-emerald-500',
  anthropic: 'bg-orange-500',
  gemini: 'bg-blue-500',
  vertex_ai: 'bg-blue-600',
  mistral: 'bg-purple-500',
  cohere: 'bg-indigo-500',
  bedrock: 'bg-amber-500',
  azure: 'bg-cyan-500',
  huggingface: 'bg-yellow-500',
  groq: 'bg-red-500',
  perplexity: 'bg-pink-500',
  deepseek: 'bg-gray-500',
  together: 'bg-green-500',
  ollama: 'bg-slate-500',
};

export function ModelSelector({ selectedVariants, onVariantsChange, maxVariants = 5 }: ModelSelectorProps) {
  const [models, setModels] = useState<ModelDefinition[]>([]);
  const [providers, setProviders] = useState<ProviderSummary[]>([]);
  const [capabilities, setCapabilities] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProvider, setSelectedProvider] = useState<string>('all');
  const [selectedCapability, setSelectedCapability] = useState<string>('all');
  const [priceRange, setPriceRange] = useState<[number, number]>([0, 100]);
  const [showFreeOnly, setShowFreeOnly] = useState(false);
  const [showWithCredentials, setShowWithCredentials] = useState(false);
  
  // Parameter editing
  const [editingVariant, setEditingVariant] = useState<string | null>(null);
  const [parameterValues, setParameterValues] = useState<{
    temperature: number;
    max_tokens: number;
    top_p: number;
    frequency_penalty: number;
    presence_penalty: number;
  }>({
    temperature: 0.7,
    max_tokens: 1000,
    top_p: 1.0,
    frequency_penalty: 0,
    presence_penalty: 0,
  });

  // Load model catalog
  useEffect(() => {
    const loadModelCatalog = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/v1/models/catalog');
        if (!response.ok) {
          throw new Error('Failed to load model catalog');
        }
        
        const data = await response.json();
        setModels(data.models);
        setProviders(data.providers);
        setCapabilities(data.capabilities);
        
        // Set price range based on actual data
        const prices = data.models
          .filter((m: ModelDefinition) => m.input_price_per_1m_tokens)
          .map((m: ModelDefinition) => m.input_price_per_1m_tokens);
        
        if (prices.length > 0) {
          setPriceRange([0, Math.max(...prices)]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load models');
      } finally {
        setLoading(false);
      }
    };

    loadModelCatalog();
  }, []);

  // Filter models
  const filteredModels = models.filter(model => {
    // Search filter
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      if (
        !model.display_name.toLowerCase().includes(searchLower) &&
        !model.description?.toLowerCase().includes(searchLower) &&
        !model.model_name.toLowerCase().includes(searchLower)
      ) {
        return false;
      }
    }
    
    // Provider filter
    if (selectedProvider !== 'all' && model.provider !== selectedProvider) {
      return false;
    }
    
    // Capability filter
    if (selectedCapability !== 'all' && !model.capabilities.includes(selectedCapability)) {
      return false;
    }
    
    // Price filter
    if (model.input_price_per_1m_tokens) {
      if (
        model.input_price_per_1m_tokens < priceRange[0] ||
        model.input_price_per_1m_tokens > priceRange[1]
      ) {
        return false;
      }
    }
    
    // Free only filter
    if (showFreeOnly && model.requires_api_key) {
      return false;
    }
    
    // With credentials filter
    if (showWithCredentials) {
      const provider = providers.find(p => p.provider === model.provider);
      if (!provider?.user_has_credentials && model.requires_api_key) {
        return false;
      }
    }
    
    return true;
  });

  // Group models by provider
  const groupedModels = filteredModels.reduce((acc, model) => {
    if (!acc[model.provider]) {
      acc[model.provider] = [];
    }
    acc[model.provider].push(model);
    return acc;
  }, {} as Record<string, ModelDefinition[]>);

  const addModelVariant = (model: ModelDefinition) => {
    if (selectedVariants.length >= maxVariants) {
      return;
    }
    
    const provider = providers.find(p => p.provider === model.provider);
    const needsCredentials = model.requires_api_key && !provider?.user_has_credentials;
    
    if (needsCredentials) {
      // TODO: Show credential setup dialog
      alert(`Please set up credentials for ${provider?.display_name || model.provider} first.`);
      return;
    }
    
    const newVariant: ModelVariant = {
      id: `variant_${Date.now()}_${Math.random()}`,
      model_definition_id: model.id,
      provider_credential_id: provider?.user_has_credentials ? 'auto' : undefined,
      model_parameters: {
        temperature: 0.7,
        max_tokens: 1000,
      },
    };
    
    onVariantsChange([...selectedVariants, newVariant]);
  };

  const removeModelVariant = (variantId: string) => {
    onVariantsChange(selectedVariants.filter(v => v.id !== variantId));
  };

  const updateModelVariant = (variantId: string, updates: Partial<ModelVariant>) => {
    onVariantsChange(
      selectedVariants.map(v => v.id === variantId ? { ...v, ...updates } : v)
    );
  };

  const openParameterEditor = (variant: ModelVariant) => {
    setEditingVariant(variant.id);
    setParameterValues({
      temperature: variant.model_parameters.temperature || 0.7,
      max_tokens: variant.model_parameters.max_tokens || 1000,
      top_p: variant.model_parameters.top_p || 1.0,
      frequency_penalty: variant.model_parameters.frequency_penalty || 0,
      presence_penalty: variant.model_parameters.presence_penalty || 0,
    });
  };

  const saveParameters = () => {
    if (!editingVariant) return;
    
    updateModelVariant(editingVariant, {
      model_parameters: parameterValues,
    });
    
    setEditingVariant(null);
  };

  const getModelById = (id: string) => models.find(m => m.id === id);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-ai-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-semantic-error">{error}</p>
        <Button 
          variant="outline" 
          onClick={() => window.location.reload()}
          className="mt-4"
        >
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Selected Variants */}
      {selectedVariants.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              Selected Model Variants ({selectedVariants.length}/{maxVariants})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {selectedVariants.map(variant => {
                const model = getModelById(variant.model_definition_id);
                if (!model) return null;
                
                const provider = providers.find(p => p.provider === model.provider);
                
                return (
                  <div key={variant.id} className="relative">
                    <Card className="border-l-4 border-ai-primary">
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <div className={cn(
                                "w-3 h-3 rounded-full",
                                providerColors[model.provider as keyof typeof providerColors] || 'bg-gray-500'
                              )}></div>
                              <span className="text-body-sm font-medium text-neutral-shadow">
                                {provider?.display_name || model.provider}
                              </span>
                            </div>
                            <h4 className="font-medium text-neutral-charcoal mb-1">
                              {model.display_name}
                            </h4>
                            <p className="text-caption text-neutral-shadow">
                              T: {variant.model_parameters.temperature || 0.7} | 
                              Max: {variant.model_parameters.max_tokens || 1000}
                            </p>
                          </div>
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openParameterEditor(variant)}
                              className="p-1 h-8 w-8"
                            >
                              <Tool className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removeModelVariant(variant.id)}
                              className="p-1 h-8 w-8 text-semantic-error hover:bg-semantic-error/10"
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Model Browser */}
      <Card>
        <CardHeader>
          <CardTitle>Model Browser</CardTitle>
          
          {/* Search and Filters */}
          <div className="flex flex-col lg:flex-row gap-4 pt-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-neutral-shadow" />
                <Input
                  placeholder="Search models..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <div className="flex flex-wrap gap-2">
              <Select value={selectedProvider} onValueChange={setSelectedProvider}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Providers</SelectItem>
                  {providers.map(provider => (
                    <SelectItem key={provider.provider} value={provider.provider}>
                      {provider.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <Select value={selectedCapability} onValueChange={setSelectedCapability}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Capabilities</SelectItem>
                  {capabilities.map(capability => (
                    <SelectItem key={capability} value={capability}>
                      {capabilityLabels[capability as keyof typeof capabilityLabels] || capability}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <Button
                variant={showFreeOnly ? "default" : "outline"}
                size="sm"
                onClick={() => setShowFreeOnly(!showFreeOnly)}
              >
                Free Only
              </Button>
              
              <Button
                variant={showWithCredentials ? "default" : "outline"}
                size="sm"
                onClick={() => setShowWithCredentials(!showWithCredentials)}
              >
                <Shield className="h-4 w-4 mr-1" />
                With Credentials
              </Button>
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          <Tabs defaultValue="grouped">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="grouped">By Provider</TabsTrigger>
              <TabsTrigger value="list">All Models</TabsTrigger>
            </TabsList>
            
            <TabsContent value="grouped" className="space-y-6">
              {Object.entries(groupedModels).map(([providerId, providerModels]) => {
                const provider = providers.find(p => p.provider === providerId);
                if (!provider) return null;
                
                return (
                  <div key={providerId} className="space-y-4">
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        "w-4 h-4 rounded-full",
                        providerColors[providerId as keyof typeof providerColors] || 'bg-gray-500'
                      )}></div>
                      <h3 className="text-h3 font-semibold">{provider.display_name}</h3>
                      <Badge variant={provider.user_has_credentials ? "default" : "secondary"}>
                        {provider.user_has_credentials ? 'Connected' : 'Setup Required'}
                      </Badge>
                      <span className="text-body-sm text-neutral-shadow">
                        {providerModels.length} models
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {providerModels.map(model => (
                        <ModelCard
                          key={model.id}
                          model={model}
                          provider={provider}
                          onSelect={addModelVariant}
                          isSelected={selectedVariants.some(v => v.model_definition_id === model.id)}
                          canSelect={selectedVariants.length < maxVariants}
                        />
                      ))}
                    </div>
                  </div>
                );
              })}
            </TabsContent>
            
            <TabsContent value="list">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredModels.map(model => {
                  const provider = providers.find(p => p.provider === model.provider);
                  if (!provider) return null;
                  
                  return (
                    <ModelCard
                      key={model.id}
                      model={model}
                      provider={provider}
                      onSelect={addModelVariant}
                      isSelected={selectedVariants.some(v => v.model_definition_id === model.id)}
                      canSelect={selectedVariants.length < maxVariants}
                    />
                  );
                })}
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Parameter Editor Dialog */}
      <Dialog open={!!editingVariant} onOpenChange={(open) => !open && setEditingVariant(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Configure Model Parameters</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6">
            <div className="space-y-2">
              <Label>Temperature: {parameterValues.temperature}</Label>
              <Slider
                value={[parameterValues.temperature]}
                onValueChange={([value]) => setParameterValues(prev => ({ ...prev, temperature: value }))}
                min={0}
                max={2}
                step={0.1}
                className="w-full"
              />
              <p className="text-caption text-neutral-shadow">
                Higher values make output more random
              </p>
            </div>
            
            <div className="space-y-2">
              <Label>Max Tokens: {parameterValues.max_tokens}</Label>
              <Slider
                value={[parameterValues.max_tokens]}
                onValueChange={([value]) => setParameterValues(prev => ({ ...prev, max_tokens: value }))}
                min={100}
                max={4000}
                step={100}
                className="w-full"
              />
            </div>
            
            <div className="space-y-2">
              <Label>Top P: {parameterValues.top_p}</Label>
              <Slider
                value={[parameterValues.top_p]}
                onValueChange={([value]) => setParameterValues(prev => ({ ...prev, top_p: value }))}
                min={0}
                max={1}
                step={0.1}
                className="w-full"
              />
            </div>
            
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setEditingVariant(null)}>
                Cancel
              </Button>
              <Button onClick={saveParameters}>
                Save Parameters
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

interface ModelCardProps {
  model: ModelDefinition;
  provider: ProviderSummary;
  onSelect: (model: ModelDefinition) => void;
  isSelected: boolean;
  canSelect: boolean;
}

function ModelCard({ model, provider, onSelect, isSelected, canSelect }: ModelCardProps) {
  const needsCredentials = model.requires_api_key && !provider.user_has_credentials;
  
  return (
    <Card className={cn(
      "relative transition-all duration-200",
      isSelected && "ring-2 ring-ai-primary",
      needsCredentials && "opacity-60"
    )}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h4 className="font-medium text-neutral-charcoal mb-1">
              {model.display_name}
            </h4>
            {model.description && (
              <p className="text-caption text-neutral-shadow line-clamp-2">
                {model.description}
              </p>
            )}
          </div>
          {needsCredentials && (
            <Badge variant="secondary" className="text-xs">
              Setup Required
            </Badge>
          )}
        </div>
        
        {/* Capabilities */}
        <div className="flex flex-wrap gap-1 mb-3">
          {model.capabilities.slice(0, 4).map(capability => {
            const Icon = capabilityIcons[capability as keyof typeof capabilityIcons];
            if (!Icon) return null;
            
            return (
              <Badge key={capability} variant="outline" className="text-xs p-1">
                <Icon className="h-3 w-3" />
              </Badge>
            );
          })}
          {model.capabilities.length > 4 && (
            <Badge variant="outline" className="text-xs">
              +{model.capabilities.length - 4}
            </Badge>
          )}
        </div>
        
        {/* Pricing */}
        <div className="flex items-center justify-between text-caption text-neutral-shadow mb-3">
          <span>
            {model.input_price_per_1m_tokens 
              ? `$${model.input_price_per_1m_tokens}/1M tokens`
              : 'Free'
            }
          </span>
          {model.context_window && (
            <span>{model.context_window.toLocaleString()} context</span>
          )}
        </div>
        
        <Button
          variant={isSelected ? "secondary" : "default"}
          size="sm"
          onClick={() => onSelect(model)}
          disabled={!canSelect && !isSelected}
          className="w-full"
        >
          {isSelected ? 'Selected' : 'Add Variant'}
        </Button>
      </CardContent>
    </Card>
  );
}

export default ModelSelector;