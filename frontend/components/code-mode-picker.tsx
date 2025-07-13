"use client"

import { useState } from "react"
import { Github, GitBranch, Layers } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"

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
    icon: "🤖"
  },
  {
    id: "gpt-4-codex",
    name: "GPT-4 Codex",
    description: "OpenAI's code-specialized model",
    icon: "🔥"
  },
  {
    id: "gemini-code",
    name: "Gemini Code",
    description: "Google's Gemini with code understanding",
    icon: "💎"
  }
]

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

  return (
    <div className={cn("space-y-4", className)}>
      {/* Model Selection */}
      <div className="space-y-2">
        <Label className="text-sm text-gray-400">Code Model</Label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          {CODE_MODELS.map((model) => (
            <button
              key={model.id}
              onClick={() => onModelChange(model.id)}
              className={cn(
                "flex items-center gap-3 p-3 rounded-lg border transition-all text-left",
                selectedModel === model.id
                  ? "bg-white text-black border-white"
                  : "bg-gray-800/60 border-gray-700 hover:bg-gray-700/60 text-gray-200"
              )}
            >
              <span className="text-lg">{model.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm">{model.name}</div>
                <div className={cn(
                  "text-xs truncate",
                  selectedModel === model.id ? "text-gray-700" : "text-gray-400"
                )}>
                  {model.description}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Repository Selection */}
      <div className="space-y-2">
        <Label className="text-sm text-gray-400">Repository</Label>
        <div className="flex items-center gap-2 mb-2">
          <Button
            variant={!useCustomRepo ? "default" : "outline"}
            size="sm"
            onClick={() => setUseCustomRepo(false)}
            className="text-xs"
          >
            Popular Repos
          </Button>
          <Button
            variant={useCustomRepo ? "default" : "outline"}
            size="sm"
            onClick={() => setUseCustomRepo(true)}
            className="text-xs"
          >
            Custom URL
          </Button>
        </div>

        {useCustomRepo ? (
          <div className="space-y-2">
            <Input
              placeholder="https://github.com/owner/repo"
              value={customRepoUrl}
              onChange={(e) => onCustomRepoUrlChange(e.target.value)}
              className="bg-gray-800/60 border-gray-700"
            />
          </div>
        ) : (
          <Select value={selectedRepo} onValueChange={onRepoChange} disabled={isLoadingRepos}>
            <SelectTrigger className="bg-gray-800/60 border-gray-700 gap-2">
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
        )}
      </div>

      {/* Branch and Agent Count */}
      <div className="flex gap-4">
        <div className="flex-1">
          <Label className="text-sm text-gray-400">Branch</Label>
          <Select 
            value={selectedBranch} 
            onValueChange={onBranchChange} 
            disabled={isLoadingBranches || (!selectedRepo && !customRepoUrl)}
          >
            <SelectTrigger className="bg-gray-800/60 border-gray-700 gap-2">
              <GitBranch className="w-4 h-4 text-gray-400" />
              <SelectValue placeholder={isLoadingBranches ? "Loading..." : "Select branch"} />
            </SelectTrigger>
            <SelectContent>
              {branches.map((branch) => (
                <SelectItem key={branch.name} value={branch.name}>
                  {branch.name}
                  {branch.protected && (
                    <span className="text-yellow-500 text-xs ml-2">🔒</span>
                  )}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="w-32">
          <Label className="text-sm text-gray-400">Agents</Label>
          <Select value={selectedAgentCount} onValueChange={onAgentCountChange}>
            <SelectTrigger className="bg-gray-800/60 border-gray-700 gap-2">
              <Layers className="w-4 h-4 text-gray-400" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">1x</SelectItem>
              <SelectItem value="2">2x</SelectItem>
              <SelectItem value="3">3x</SelectItem>
              <SelectItem value="4">4x</SelectItem>
              <SelectItem value="5">5x</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  )
}