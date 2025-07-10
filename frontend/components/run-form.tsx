"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Loader2, Info } from "lucide-react"
import { createRun } from "@/lib/api"
import { cn } from "@/lib/utils"

export function RunForm() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [formData, setFormData] = useState({
    github_url: "",
    prompt: "",
    variations: "3",
    agent_config: {
      model: "claude-3-sonnet-20240229",
      temperature: 0.7,
    },
    use_claude_code: false,
  })
  
  // Local state for streaming backend (doesn't go to API)
  const [streamingBackend, setStreamingBackend] = useState(
    process.env.NEXT_PUBLIC_STREAMING_BACKEND || 'redis'
  )
  
  // Load streaming backend preference from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem('streamingBackend')
    if (stored === 'redis' || stored === 'kubectl') {
      setStreamingBackend(stored)
    }
  }, [])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSelectChange = (name: string, value: string) => {
    setFormData((prev) => ({ ...prev, [name]: value }))
  }
  
  const handleSwitchChange = (name: string, checked: boolean) => {
    setFormData((prev) => ({ ...prev, [name]: checked }))
  }
  
  const handleStreamingBackendChange = (backend: 'kubectl' | 'redis') => {
    setStreamingBackend(backend)
    // Update the environment variable for the current session
    if (typeof window !== 'undefined') {
      // This won't actually change the env var, but we can store it in localStorage
      localStorage.setItem('streamingBackend', backend)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const response = await createRun({
        ...formData,
        variations: Number.parseInt(formData.variations),
      })

      router.push(`/runs/${response.run_id}`)
    } catch (error) {
      console.error("Error creating run:", error)
      // Show error to user - you might want to add a toast or alert here
      alert(`Error: ${error instanceof Error ? error.message : "Unknown error occurred"}`)
      setIsLoading(false)
    }
  }

  return (
    <Card className="p-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-4">
          <div>
            <Label htmlFor="github_url">GitHub Repository URL</Label>
            <Input
              id="github_url"
              name="github_url"
              placeholder="https://github.com/username/repository"
              value={formData.github_url}
              onChange={handleChange}
              required
            />
          </div>

          <div>
            <Label htmlFor="prompt">Prompt</Label>
            <Textarea
              id="prompt"
              name="prompt"
              placeholder="Add comprehensive error handling to all API endpoints"
              value={formData.prompt}
              onChange={handleChange}
              rows={4}
              required
            />
          </div>

          <div>
            <Label htmlFor="variations">Number of Variations</Label>
            <Select value={formData.variations} onValueChange={(value) => handleSelectChange("variations", value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select number of variations" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">1</SelectItem>
                <SelectItem value="2">2</SelectItem>
                <SelectItem value="3">3</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          {/* Advanced Settings */}
          <div className="space-y-4 border-t pt-4">
            <h3 className="text-sm font-medium">Advanced Settings</h3>
            
            {/* Claude CLI Toggle */}
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="use_claude_code" className="text-sm font-medium">
                  Use Claude Code CLI
                </Label>
                <p className="text-xs text-muted-foreground">
                  Use Claude Code CLI instead of LiteLLM (experimental)
                </p>
              </div>
              <Switch
                id="use_claude_code"
                checked={formData.use_claude_code}
                onCheckedChange={(checked) => handleSwitchChange("use_claude_code", checked)}
              />
            </div>
            
            {/* Streaming Backend Toggle */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Label className="text-sm font-medium">
                  Streaming Backend
                </Label>
                <Info className="h-3 w-3 text-muted-foreground" />
              </div>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant={streamingBackend === 'kubectl' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleStreamingBackendChange('kubectl')}
                  className="flex-1"
                >
                  Kubectl Logs
                </Button>
                <Button
                  type="button"
                  variant={streamingBackend === 'redis' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleStreamingBackendChange('redis')}
                  className="flex-1"
                >
                  Redis Pub/Sub
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                {streamingBackend === 'redis' 
                  ? "Uses Redis pub/sub for improved reliability and performance"
                  : "Uses kubectl logs streaming (default, stable)"}
              </p>
            </div>
          </div>
        </div>

        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Creating Run...
            </>
          ) : (
            "Create Run"
          )}
        </Button>
      </form>
    </Card>
  )
}
