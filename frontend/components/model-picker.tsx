"use client"

import { useState, useEffect } from "react"
import { X, Search, Settings, Plus, ChevronDown, ChevronRight, AlertCircle } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { cn } from "@/lib/utils"
import { apiClient } from "@/lib/api"
import { useAuth } from "@/lib/auth-context"

export interface ModelDefinition {
  id: string
  provider: string
  model_name: string
  litellm_model_name: string
  display_name: string
  description?: string
  context_window?: number
  max_output_tokens?: number
  input_price_per_1m_tokens?: number
  output_price_per_1m_tokens?: number
  capabilities: string[]
  requires_api_key: boolean
  is_active: boolean
}

export interface ModelVariant {
  id: string
  model_definition_id: string
  model_parameters: {
    temperature?: number
    max_tokens?: number
    top_p?: number
  }
}

interface ModelPickerProps {
  selectedVariants: ModelVariant[]
  onVariantsChange: (variants: ModelVariant[]) => void
  maxVariants?: number
  className?: string
}

const PROVIDER_EMOJIS = {
  openai: '🟢',
  anthropic: '🔶', 
  gemini: '🔵',
  vertex_ai: '🔵',
  mistral: '🟣',
  cohere: '🔷',
  groq: '🔴',
  perplexity: '🩷',
  deepseek: '⚫',
  together: '🟡',
  ollama: '🟠',
}

interface ProviderSummary {
  provider: string
  display_name: string
  description: string
  requires_api_key: boolean
  model_count: number
  user_has_credentials: boolean
}

export function ModelPicker({ selectedVariants, onVariantsChange, maxVariants = 5, className }: ModelPickerProps) {
  const [models, setModels] = useState<ModelDefinition[]>([])
  const [providers, setProviders] = useState<ProviderSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedProvider, setSelectedProvider] = useState<string>('all')
  const [showModelList, setShowModelList] = useState(false)
  const [expandedProviders, setExpandedProviders] = useState<Set<string>>(new Set())
  const [editingVariant, setEditingVariant] = useState<string | null>(null)
  const [parameterValues, setParameterValues] = useState({
    temperature: 0.7,
    max_tokens: 1000,
    top_p: 1.0,
  })

  const { user, loading: authLoading } = useAuth()

  // Load models - wait for auth to complete
  useEffect(() => {
    console.log('ModelPicker: Auth state changed', { authLoading, user: !!user })
    if (!authLoading && user) {
      const loadModels = async () => {
        try {
          console.log('ModelPicker: Loading models...')
          setLoading(true)
          const data = await apiClient.getModelCatalog()
          console.log('ModelPicker: Models loaded', data.models?.length, 'models,', data.providers?.length, 'providers')
          setModels(data.models || [])
          setProviders(data.providers || [])
          setError(null)
        } catch (err) {
          console.error('ModelPicker: Failed to load models', err)
          setError(err instanceof Error ? err.message : 'Failed to load models')
        } finally {
          setLoading(false)
        }
      }

      loadModels()
    } else if (!authLoading && !user) {
      console.log('ModelPicker: User not authenticated')
      setModels([])
      setLoading(false)
      setError('Please sign in to view available models')
    }
  }, [authLoading, user])

  // Filter models
  const filteredModels = models.filter(model => {
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase()
      if (
        !model.display_name.toLowerCase().includes(searchLower) &&
        !model.description?.toLowerCase().includes(searchLower) &&
        !model.model_name.toLowerCase().includes(searchLower)
      ) {
        return false
      }
    }
    
    if (selectedProvider !== 'all' && model.provider !== selectedProvider) {
      return false
    }
    
    return model.is_active
  })

  const providerNames = [...new Set(models.map(m => m.provider))]

  // Group models by provider for hierarchical display
  const groupedModels = filteredModels.reduce((acc, model) => {
    if (!acc[model.provider]) {
      acc[model.provider] = []
    }
    acc[model.provider].push(model)
    return acc
  }, {} as Record<string, ModelDefinition[]>)

  // Helper functions
  const getProviderInfo = (providerName: string) => {
    return providers.find(p => p.provider === providerName)
  }

  const isModelAvailable = (model: ModelDefinition) => {
    if (!model.requires_api_key) return true
    const providerInfo = getProviderInfo(model.provider)
    return providerInfo?.user_has_credentials || false
  }

  const getUnavailableModelsCount = () => {
    return selectedVariants.filter(variant => {
      const model = getModelById(variant.model_definition_id)
      return model && !isModelAvailable(model)
    }).length
  }

  const getMissingProviders = () => {
    const missingProviders = new Set<string>()
    selectedVariants.forEach(variant => {
      const model = getModelById(variant.model_definition_id)
      if (model && !isModelAvailable(model)) {
        missingProviders.add(model.provider)
      }
    })
    return Array.from(missingProviders)
  }

  const toggleProvider = (provider: string) => {
    const newExpanded = new Set(expandedProviders)
    if (newExpanded.has(provider)) {
      newExpanded.delete(provider)
    } else {
      newExpanded.add(provider)
    }
    setExpandedProviders(newExpanded)
  }

  const addModelVariant = (model: ModelDefinition) => {
    if (selectedVariants.length >= maxVariants) {
      return
    }
    
    // Create variant with slightly randomized parameters to differentiate multiple instances
    const existingModelCount = selectedVariants.filter(v => v.model_definition_id === model.litellm_model_name).length
    const baseTemp = 0.7
    const tempVariation = existingModelCount * 0.1 // Vary temperature for multiple instances
    
    const newVariant: ModelVariant = {
      id: `variant_${Date.now()}_${Math.random()}`,
      model_definition_id: model.litellm_model_name,
      model_parameters: {
        temperature: Math.min(2.0, baseTemp + tempVariation),
        max_tokens: 1000,
        top_p: 1.0,
      },
    }
    
    onVariantsChange([...selectedVariants, newVariant])
    // Don't auto-close the list to allow adding multiple variants
  }

  const removeModelVariant = (variantId: string) => {
    onVariantsChange(selectedVariants.filter(v => v.id !== variantId))
  }

  const updateModelVariant = (variantId: string, updates: Partial<ModelVariant>) => {
    onVariantsChange(
      selectedVariants.map(v => v.id === variantId ? { ...v, ...updates } : v)
    )
  }

  const openParameterEditor = (variant: ModelVariant) => {
    setEditingVariant(variant.id)
    setParameterValues({
      temperature: variant.model_parameters.temperature || 0.7,
      max_tokens: variant.model_parameters.max_tokens || 1000,
      top_p: variant.model_parameters.top_p || 1.0,
    })
  }

  const saveParameters = () => {
    if (!editingVariant) return
    
    updateModelVariant(editingVariant, {
      model_parameters: parameterValues,
    })
    
    setEditingVariant(null)
  }

  const getModelById = (id: string) => models.find(m => m.litellm_model_name === id)
  
  const getUniqueModelCount = () => {
    const uniqueModels = new Set(selectedVariants.map(v => v.model_definition_id))
    return uniqueModels.size
  }

  if (loading && authLoading) {
    return (
      <div className={cn("flex items-center justify-center py-8", className)}>
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={cn("text-center py-4", className)}>
        <p className="text-red-400 text-sm">{error}</p>
      </div>
    )
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Selected Models Display */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Label className="text-sm text-gray-400">
              AI Agents ({selectedVariants.length}/{maxVariants})
            </Label>
            {selectedVariants.length > 0 && (
              <span className="text-xs text-gray-500">
                • {getUniqueModelCount()} unique model{getUniqueModelCount() !== 1 ? 's' : ''}
              </span>
            )}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowModelList(!showModelList)}
            disabled={selectedVariants.length >= maxVariants}
            className="gap-2 text-xs"
          >
            <Plus className="w-3 h-3" />
            {selectedVariants.length === 0 ? 'Add Agent' : 'Add Another'}
            <ChevronDown className={cn("w-3 h-3 transition-transform", showModelList && "rotate-180")} />
          </Button>
        </div>

        {/* Selected Model Chips */}
        {selectedVariants.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {selectedVariants.map((variant) => {
              const model = getModelById(variant.model_definition_id)
              if (!model) return null
              
              const providerEmoji = PROVIDER_EMOJIS[model.provider as keyof typeof PROVIDER_EMOJIS] || '⚪'
              const isAvailable = isModelAvailable(model)
              
              // Count instances of this model for numbering
              const modelInstances = selectedVariants.filter(v => v.model_definition_id === variant.model_definition_id)
              const instanceNumber = modelInstances.findIndex(v => v.id === variant.id) + 1
              const showInstanceNumber = modelInstances.length > 1
              
              return (
                <div key={variant.id} className={cn(
                  "flex items-center gap-2 rounded-lg px-3 py-2 group",
                  isAvailable 
                    ? "bg-gray-800/60 border border-gray-700"
                    : "bg-amber-900/20 border border-amber-800/60"
                )}>
                  <span className="text-sm">{providerEmoji}</span>
                  <span className={cn(
                    "text-sm font-medium",
                    isAvailable ? "text-gray-200" : "text-amber-200"
                  )}>
                    {model.display_name}
                    {showInstanceNumber && (
                      <span className="text-xs ml-1 opacity-75">#{instanceNumber}</span>
                    )}
                  </span>
                  {!isAvailable && (
                    <AlertCircle className="w-3 h-3 text-amber-400" />
                  )}
                  <span className="text-xs text-gray-400">
                    T:{Number(variant.model_parameters.temperature || 0.7).toFixed(1)}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => openParameterEditor(variant)}
                    className="p-1 h-5 w-5 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <Settings className="h-3 w-3" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeModelVariant(variant.id)}
                    className="p-1 h-5 w-5 text-red-400 hover:text-red-300 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              )
            })}
          </div>
        )}

        {selectedVariants.length === 0 && (
          <div className="text-center py-4 text-gray-500 text-sm border border-dashed border-gray-700 rounded-lg">
            No AI agents configured. Click &quot;Add Agent&quot; to get started.
          </div>
        )}

        {/* API Key Warning */}
        {getUnavailableModelsCount() > 0 && (
          <div className="bg-amber-900/20 border border-amber-800/60 rounded-lg p-3">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <div className="text-sm font-medium text-amber-200">
                  {getUnavailableModelsCount()} model{getUnavailableModelsCount() > 1 ? 's' : ''} require{getUnavailableModelsCount() === 1 ? 's' : ''} API keys
                </div>
                <div className="text-xs text-amber-300 mt-1">
                  Missing credentials for: {getMissingProviders().map(provider => {
                    const emoji = PROVIDER_EMOJIS[provider as keyof typeof PROVIDER_EMOJIS] || '⚪'
                    return `${emoji} ${provider}`
                  }).join(', ')}
                </div>
                <div className="flex flex-wrap items-center gap-2 mt-3">
                  <Link 
                    href="/settings" 
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-medium rounded-md transition-colors"
                  >
                    <Settings className="w-3 h-3" />
                    Add API Keys
                  </Link>
                  <span className="text-xs text-amber-400">
                    or continue with available models only
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Model Selection List (Collapsible) */}
      {showModelList && (
        <div className="space-y-3 border border-gray-700 rounded-lg p-4 bg-gray-900/30">
          {/* Search and Filter */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search models..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-gray-800/60 border-gray-700 text-sm"
              />
            </div>
            <Select value={selectedProvider} onValueChange={setSelectedProvider}>
              <SelectTrigger className="w-36 bg-gray-800/60 border-gray-700 text-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Providers</SelectItem>
                {providerNames.map(provider => (
                  <SelectItem key={provider} value={provider}>
                    {PROVIDER_EMOJIS[provider as keyof typeof PROVIDER_EMOJIS] || '⚪'} {provider}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Provider Hierarchy */}
          <div className="max-h-60 overflow-y-auto space-y-2">
            {Object.keys(groupedModels).length === 0 ? (
              <div className="text-center py-4 text-gray-500 text-sm">
                No models found
              </div>
            ) : (
              Object.entries(groupedModels).map(([provider, providerModels]) => {
                const isExpanded = expandedProviders.has(provider)
                const providerEmoji = PROVIDER_EMOJIS[provider as keyof typeof PROVIDER_EMOJIS] || '⚪'
                const providerInfo = getProviderInfo(provider)
                const needsApiKey = providerInfo?.requires_api_key && !providerInfo?.user_has_credentials
                
                return (
                  <div key={provider} className={cn(
                    "border rounded-lg",
                    needsApiKey 
                      ? "border-amber-800/60 bg-amber-900/10"
                      : "border-gray-700 bg-gray-800/20"
                  )}>
                    {/* Provider Header */}
                    <button
                      onClick={() => toggleProvider(provider)}
                      className="w-full flex items-center gap-3 p-3 text-left hover:bg-gray-700/30 transition-colors rounded-lg"
                    >
                      <div className="flex items-center gap-2 flex-1">
                        <span className="text-base">{providerEmoji}</span>
                        <span className={cn(
                          "font-medium capitalize",
                          needsApiKey ? "text-amber-200" : "text-gray-200"
                        )}>
                          {provider}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {providerModels.length} models
                        </Badge>
                        {needsApiKey && (
                          <div className="flex items-center gap-1">
                            <AlertCircle className="w-3 h-3 text-amber-400" />
                            <Link 
                              href="/settings" 
                              className="text-xs text-amber-400 hover:text-amber-300 underline"
                              onClick={(e) => e.stopPropagation()}
                            >
                              Add Key
                            </Link>
                          </div>
                        )}
                      </div>
                      <ChevronRight 
                        className={cn("w-4 h-4 text-gray-400 transition-transform", 
                          isExpanded && "rotate-90"
                        )} 
                      />
                    </button>
                    
                    {/* Provider Models */}
                    {isExpanded && (
                      <div className="border-t border-gray-700 space-y-1 p-2">
                        {providerModels.map(model => {
                          const existingVariants = selectedVariants.filter(v => v.model_definition_id === model.id)
                          const isAvailable = isModelAvailable(model)
                          const canAdd = selectedVariants.length < maxVariants && isAvailable
                          
                          return (
                            <button
                              key={model.id}
                              onClick={() => canAdd && addModelVariant(model)}
                              disabled={!canAdd}
                              className={cn(
                                "w-full flex items-center gap-3 p-2 text-left rounded border transition-all",
                                !isAvailable
                                  ? "bg-amber-900/20 border-amber-800/60 text-amber-200 cursor-not-allowed"
                                  : selectedVariants.length >= maxVariants
                                  ? "bg-gray-800/30 border-gray-600 text-gray-500 cursor-not-allowed"
                                  : "bg-gray-800/40 border-gray-600 hover:bg-gray-700/50 text-gray-200"
                              )}
                            >
                              <div className="flex-1 min-w-0">
                                <div className="font-medium text-sm flex items-center gap-2">
                                  {model.display_name}
                                  {!isAvailable && (
                                    <AlertCircle className="w-3 h-3 text-amber-400" />
                                  )}
                                  {existingVariants.length > 0 && (
                                    <span className="text-xs bg-blue-600 text-white px-1.5 py-0.5 rounded">
                                      {existingVariants.length}
                                    </span>
                                  )}
                                </div>
                                {model.description && (
                                  <div className="text-xs text-gray-400 truncate">{model.description}</div>
                                )}
                                {!isAvailable && (
                                  <div className="text-xs text-amber-400">Requires API key</div>
                                )}
                                {existingVariants.length > 0 && canAdd && (
                                  <div className="text-xs text-blue-400">Click to add another variant</div>
                                )}
                              </div>
                              <div className="text-xs text-gray-400">
                                {model.input_price_per_1m_tokens 
                                  ? `$${model.input_price_per_1m_tokens}/1M`
                                  : 'Free'
                                }
                              </div>
                              {existingVariants.length > 0 && (
                                <div className="text-xs text-blue-400">
                                  +
                                </div>
                              )}
                            </button>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )
              })
            )}
          </div>
        </div>
      )}

      {/* Parameter Editor Dialog */}
      <Dialog open={!!editingVariant} onOpenChange={(open) => !open && setEditingVariant(null)}>
        <DialogContent className="sm:max-w-md bg-gray-900 border-gray-800">
          <DialogHeader>
            <DialogTitle className="text-gray-100">Configure Model Parameters</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6">
            <div className="space-y-2">
              <Label className="text-gray-200">Temperature: {parameterValues.temperature}</Label>
              <Slider
                value={[parameterValues.temperature]}
                onValueChange={([value]) => setParameterValues(prev => ({ ...prev, temperature: value }))}
                min={0}
                max={2}
                step={0.1}
                className="w-full"
              />
              <p className="text-xs text-gray-400">
                Higher values make output more random
              </p>
            </div>
            
            <div className="space-y-2">
              <Label className="text-gray-200">Max Tokens: {parameterValues.max_tokens}</Label>
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
              <Label className="text-gray-200">Top P: {parameterValues.top_p}</Label>
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
  )
}