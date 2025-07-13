"use client"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { AutoResizeTextarea } from "@/components/auto-resize-textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { GitBranch, Layers, Mic, Github, Loader2, Settings } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { apiClient } from "@/lib/api"
import { Session, CreateRunRequest, GitHubRepository, GitHubBranch } from "@/lib/types"

export default function Home() {
  const [taskText, setTaskText] = useState("")
  const [sessions, setSessions] = useState<Session[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isCreatingRun, setIsCreatingRun] = useState(false)
  const [selectedRepo, setSelectedRepo] = useState("")
  const [selectedBranch, setSelectedBranch] = useState("main")
  const [selectedAgentCount, setSelectedAgentCount] = useState("3")
  const [repositories, setRepositories] = useState<GitHubRepository[]>([])
  const [branches, setBranches] = useState<GitHubBranch[]>([])
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [isLoadingRepos, setIsLoadingRepos] = useState(false)
  const [isLoadingBranches, setIsLoadingBranches] = useState(false)
  const [, setIsLoadingModels] = useState(false)
  
  const router = useRouter()

  useEffect(() => {
    loadSessions()
    loadPopularRepositories()
    loadModelDefinitions()
  }, [])

  const loadSessions = async () => {
    try {
      setIsLoading(true)
      const response = await apiClient.getSessions({ limit: 50 })
      setSessions(response.sessions)
      setError(null)
    } catch (err) {
      console.error('Failed to load sessions:', err)
      setError('Failed to load sessions')
      // For development, fall back to empty array
      setSessions([])
    } finally {
      setIsLoading(false)
    }
  }

  const loadPopularRepositories = async () => {
    // Default to hello-world-octocat repo instead of API calls
    setIsLoadingRepos(true)
    const defaultRepos: GitHubRepository[] = [
      { 
        id: 1, 
        name: 'Hello-World',
        full_name: 'octocat/Hello-World', 
        private: false,
        html_url: 'https://github.com/octocat/Hello-World',
        description: 'My first repository on GitHub!', 
        default_branch: 'main'
      }
    ]
    setRepositories(defaultRepos)
    setSelectedRepo('octocat/Hello-World')
    setIsLoadingRepos(false)
  }

  const loadBranches = useCallback(async () => {
    if (!selectedRepo) return
    
    // Default to main branch for octocat/Hello-World
    setIsLoadingBranches(true)
    const defaultBranches: GitHubBranch[] = [
      { 
        name: 'main', 
        commit: {
          sha: 'abc123def456',
          url: 'https://api.github.com/repos/octocat/Hello-World/commits/abc123def456'
        },
        protected: false 
      }
    ]
    setBranches(defaultBranches)
    setSelectedBranch('main')
    setIsLoadingBranches(false)
  }, [selectedRepo])

  useEffect(() => {
    if (selectedRepo) {
      loadBranches()
    }
  }, [selectedRepo, loadBranches])

  const loadModelDefinitions = async () => {
    try {
      setIsLoadingModels(true)
      const models = await apiClient.getModelDefinitions()
      setAvailableModels(models)
    } catch (err) {
      console.error('Failed to load model definitions:', err)
    } finally {
      setIsLoadingModels(false)
    }
  }

  const handleAsk = async () => {
    // Create session-only interaction for Q&A mode
    try {
      const newSession = await apiClient.createSession({
        title: taskText.slice(0, 50) + (taskText.length > 50 ? '...' : ''),
        description: `Q&A session: ${taskText}`,
        models_used: availableModels.slice(0, parseInt(selectedAgentCount))
      })
      
      router.push(`/session/${newSession.id}`)
    } catch (err) {
      console.error('Failed to create session:', err)
      alert('Failed to create session. Please try again.')
    }
  }

  const handleCode = async () => {
    if (!taskText.trim()) return
    
    try {
      setIsCreatingRun(true)
      
      // Create run request with multiple model variants
      const agentCount = parseInt(selectedAgentCount)
      const modelVariants = Array.from({ length: agentCount }, (_, i) => {
        // Use different models if available, otherwise vary parameters
        const modelId = availableModels[i % availableModels.length] || 'gpt-4-turbo'
        return {
          model_definition_id: modelId,
          model_parameters: { 
            temperature: 0.7 + (i * 0.1), // Vary temperature slightly
            max_tokens: 4096,
          },
        }
      })

      const runRequest: CreateRunRequest = {
        github_url: `https://github.com/${selectedRepo}`,
        prompt: taskText,
        model_variants: modelVariants,
        agent_mode: 'litellm',
        use_claude_code: false,
      }

      const response = await apiClient.createRun(runRequest)
      
      // Navigate to the run page via session/turn structure
      router.push(`/session/${response.session_id}/turn/${response.turn_id}/run/${response.run_id}`)
    } catch (err) {
      console.error('Failed to create run:', err)
      alert('Failed to create run. Please try again.')
    } finally {
      setIsCreatingRun(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.metaKey && e.key === "Enter") {
      e.preventDefault()
      if (taskText.trim()) {
        handleCode()
      }
    }
  }

  return (
    <div className="bg-gray-950 text-gray-50 min-h-screen">
      <div className="container mx-auto max-w-3xl py-16">
        <div className="flex items-center justify-between mb-8">
          <div className="flex-1" />
          <h1 className="text-4xl font-medium text-center">What are we coding next?</h1>
          <div className="flex-1 flex justify-end">
            <Link href="/settings">
              <Button variant="ghost" size="icon" className="text-gray-400 hover:text-gray-200">
                <Settings className="w-5 h-5" />
              </Button>
            </Link>
          </div>
        </div>

        <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-4 space-y-4">
          <AutoResizeTextarea
            placeholder="Describe a task"
            minRows={5}
            maxRows={20}
            value={taskText}
            onChange={(e) => setTaskText(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Select value={selectedRepo} onValueChange={setSelectedRepo} disabled={isLoadingRepos}>
                <SelectTrigger className="bg-gray-800/60 border-gray-700 w-auto gap-2">
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
              <Select value={selectedBranch} onValueChange={setSelectedBranch} disabled={isLoadingBranches || !selectedRepo}>
                <SelectTrigger className="bg-gray-800/60 border-gray-700 w-auto gap-2">
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
              <Select value={selectedAgentCount} onValueChange={setSelectedAgentCount}>
                <SelectTrigger className="bg-gray-800/60 border-gray-700 w-auto gap-2">
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
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="icon">
                <Mic className="w-5 h-5" />
              </Button>
              {taskText.trim() && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleAsk}
                    disabled={!taskText.trim() || isCreatingRun}
                    className="rounded-full px-4 py-1 h-auto bg-gray-800/60 border-gray-700 hover:bg-gray-700/60"
                  >
                    Ask
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleCode}
                    disabled={!taskText.trim() || isCreatingRun}
                    className="rounded-full px-4 py-1 h-auto bg-white text-black hover:bg-gray-200"
                  >
                    {isCreatingRun ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      'Code'
                    )}
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>

        <Tabs defaultValue="sessions" className="mt-10">
          <TabsList className="border-b border-gray-800 rounded-none w-full justify-start bg-transparent p-0">
            <TabsTrigger
              value="sessions"
              className="rounded-none data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 border-white"
            >
              Sessions
            </TabsTrigger>
            <TabsTrigger
              value="archive"
              className="rounded-none data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 border-white"
            >
              Archive
            </TabsTrigger>
          </TabsList>
          <TabsContent value="sessions" className="mt-6 space-y-1">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin" />
                <span className="ml-2">Loading sessions...</span>
              </div>
            ) : error ? (
              <div className="text-center py-8">
                <p className="text-red-400 mb-2">{error}</p>
                <Button onClick={loadSessions} variant="outline" size="sm">
                  Retry
                </Button>
              </div>
            ) : sessions.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500">No sessions yet. Create your first session above!</p>
              </div>
            ) : (
              sessions.map((session) => (
                <Link href={`/session/${session.id}`} key={session.id}>
                  <div className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-900 transition-colors cursor-pointer">
                    <div className="flex flex-col">
                      <span className="font-medium">{session.title}</span>
                      <span className="text-sm text-gray-400">
                        {new Date(session.last_activity_at).toLocaleDateString()} · {session.models_used.length} models
                      </span>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-1 text-sm text-gray-400">
                        <Layers className="w-4 h-4" />
                        <span>{session.total_turns}</span>
                      </div>
                      <div className="font-mono text-sm text-gray-400">
                        ${session.total_cost.toFixed(3)}
                      </div>
                      {session.is_active ? (
                        <span className="text-sm text-green-400 bg-green-900/50 px-2 py-1 rounded-md">Active</span>
                      ) : (
                        <span className="text-sm text-gray-400">Completed</span>
                      )}
                    </div>
                  </div>
                </Link>
              ))
            )}
          </TabsContent>
          <TabsContent value="archive" className="mt-6">
            <p className="text-center text-gray-500">Archived sessions will appear here.</p>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
