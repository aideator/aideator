"use client"

import { useState, useEffect } from "react"
import { Github, AlertCircle } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"
import { apiClient } from "@/lib/api"
import { useAuth } from "@/lib/auth-context"

interface CodeModePickerProps {
  selectedModel: string
  onModelChange: (model: string) => void
  selectedRepo: string
  onRepoChange: (repo: string) => void
  selectedBranch: string
  onBranchChange: (branch: string) => void
  selectedAgentCount: string
  onAgentCountChange: (count: string) => void
  customRepoUrl: string
  onCustomRepoUrlChange: (url: string) => void
  repositories: Array<{ id: number; full_name: string; description?: string }>
  branches: Array<{ name: string; protected?: boolean }>
  isLoadingRepos?: boolean
  isLoadingBranches?: boolean
  className?: string
}

const CODE_MODELS = [
  {
    id: "claude-code",
    name: "Claude Code",
    description: "Anthropic's Claude with code analysis capabilities",
    icon: "🤖",
    provider: "anthropic"
  },
  {
    id: "gpt-4-codex",
    name: "GPT-4 Codex",
    description: "OpenAI's code-specialized model",
    icon: "🔥",
    provider: "openai"
  },
  {
    id: "gemini-code",
    name: "Gemini Code",
    description: "Google's Gemini with code understanding",
    icon: "💎",
    provider: "gemini"
  }
]

interface ProviderInfo {
  provider: string
  display_name: string
  requires_api_key: boolean
  user_has_credentials: boolean
}

export function CodeModePicker({
  selectedModel,
  onModelChange,
  selectedRepo,
  onRepoChange,
  selectedBranch,
  onBranchChange,
  selectedAgentCount,
  onAgentCountChange,
  customRepoUrl,
  onCustomRepoUrlChange,
  repositories,
  branches,
  isLoadingRepos = false,
  isLoadingBranches = false,
  className
}: CodeModePickerProps) {
  const [useCustomRepo, setUseCustomRepo] = useState(false)
  const [providers, setProviders] = useState<ProviderInfo[]>([])
  const [loading, setLoading] = useState(true)
  
  const { user, loading: authLoading } = useAuth()

  // Load provider credentials
  useEffect(() => {
    if (!authLoading && user) {
      const loadProviders = async () => {
        try {
          setLoading(true)
          const data = await apiClient.getModelCatalog()
          setProviders(data.providers || [])
        } catch (err) {
          console.error('Failed to load provider credentials:', err)
        } finally {
          setLoading(false)
        }
      }

      loadProviders()
    } else if (!authLoading && !user) {
      setProviders([])
      setLoading(false)
    }
  }, [authLoading, user])

  // Helper functions
  const getProviderInfo = (providerName: string) => {
    return providers.find(p => p.provider === providerName)
  }

  const isModelAvailable = (model: typeof CODE_MODELS[0]) => {
    const providerInfo = getProviderInfo(model.provider)
    return providerInfo?.user_has_credentials || false
  }

  const getSelectedModelInfo = () => {
    return CODE_MODELS.find(model => model.id === selectedModel)
  }


  return (
    <div className={cn("space-y-4", className)}>
      {/* Model Selection */}
      <div className="space-y-2">
        <Label className="text-sm text-gray-400">Code Model</Label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          {CODE_MODELS.map((model) => {
            const isAvailable = isModelAvailable(model)
            const isSelected = selectedModel === model.id
            
            return (
              <button
                key={model.id}
                onClick={() => onModelChange(model.id)}
                className={cn(
                  "flex items-center gap-3 p-3 rounded-lg border transition-all text-left relative",
                  isSelected
                    ? isAvailable
                      ? "bg-gray-700 text-white border-gray-600"
                      : "bg-amber-100 text-amber-900 border-amber-400"
                    : isAvailable
                    ? "bg-gray-800/60 border-gray-700 hover:bg-gray-700/60 text-gray-200"
                    : "bg-amber-900/20 border-amber-800/60 text-amber-200 hover:bg-amber-900/30"
                )}
              >
                <span className="text-lg">{model.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm flex items-center gap-2">
                    {model.name}
                    {!isAvailable && (
                      <AlertCircle className="w-3 h-3 text-amber-400" />
                    )}
                  </div>
                  <div className={cn(
                    "text-xs truncate",
                    isSelected
                      ? isAvailable ? "text-gray-300" : "text-amber-700"
                      : isAvailable ? "text-gray-400" : "text-amber-400"
                  )}>
                    {model.description}
                  </div>
                  {!isAvailable && (
                    <div className="text-xs text-amber-400 mt-1">
                      Requires API key
                    </div>
                  )}
                </div>
              </button>
            )
          })}
        </div>
      </div>


      {/* Selected Model Warning */}
      {selectedModel && !isModelAvailable(getSelectedModelInfo()!) && (
        <div className="bg-amber-900/20 border border-amber-800/60 rounded-lg p-2">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
            <div className="text-xs text-amber-300">
              <strong>{getSelectedModelInfo()?.name}</strong> requires an API key to function.{' '}
              <Link href="/settings" className="underline hover:text-amber-200">
                Add credentials
              </Link> or select a different model.
            </div>
          </div>
        </div>
      )}

      {/* Repository Selection */}
      <div className="space-y-2">
        <Label className="text-sm text-gray-400">Repository</Label>
        <div className="flex items-center gap-2">
          <Button
            variant={!useCustomRepo ? "default" : "outline"}
            size="sm"
            onClick={() => setUseCustomRepo(false)}
            className={cn(
              "text-xs",
              !useCustomRepo ? "bg-gray-700 text-white hover:bg-gray-600" : ""
            )}
          >
            Popular Repos
          </Button>
          <Button
            variant={useCustomRepo ? "default" : "outline"}
            size="sm"
            onClick={() => setUseCustomRepo(true)}
            className={cn(
              "text-xs",
              useCustomRepo ? "bg-gray-700 text-white hover:bg-gray-600" : ""
            )}
          >
            Custom URL
          </Button>
          <div className="flex-1">
            {!useCustomRepo ? (
              <Select value={selectedRepo} onValueChange={onRepoChange} disabled={isLoadingRepos}>
                <SelectTrigger className="bg-gray-800/60 border-gray-700 gap-2 w-full">
                  <Github className="w-4 h-4 text-gray-400" />
                  <SelectValue placeholder={isLoadingRepos ? "Loading..." : "Select repository"} />
                </SelectTrigger>
                <SelectContent>
                  {repositories.map((repo) => (
                    <SelectItem key={repo.id} value={repo.full_name}>
                      {repo.full_name}
                      {repo.description && (
                        <span className="text-gray-500 text-xs ml-2">
                          - {repo.description.slice(0, 50)}
                        </span>
                      )}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <Input
                placeholder="https://github.com/owner/repo"
                value={customRepoUrl}
                onChange={(e) => onCustomRepoUrlChange(e.target.value)}
                className="bg-gray-800/60 border-gray-700 w-full"
              />
            )}
          </div>
        </div>
      </div>

    </div>
  )
}