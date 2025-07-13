"use client"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { AutoResizeTextarea } from "@/components/auto-resize-textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { GitBranch, Layers, Mic, Github, Loader2 } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { apiClient } from "@/lib/api"
import { Session, GitHubRepository, GitHubBranch, CodeRequest } from "@/lib/types"
import { useAuth } from "@/lib/auth-context"

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
  const { user, loading: authLoading } = useAuth()

  // Wait for auth to load before making API calls
  useEffect(() => {
    if (!authLoading && user) {
      loadSessions()
      loadPopularRepositories()
      loadModelDefinitions()
    }
  }, [authLoading, user])

  const loadSessions = async () => {
    // Don't make API calls if user is not authenticated
    if (!user) {
      setSessions([])
      setIsLoading(false)
      return
    }

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
    // In ask mode, users can select from any available model
    // TODO: Implement model picker UI for ask mode
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
    console.log('🚀 handleCode called')
    console.log('📝 Task text:', taskText)
    console.log('🔐 Auth state:', { user: !!user, authLoading })
    console.log('📦 Available models:', availableModels)
    
    if (!taskText.trim()) {
      console.warn('❌ No task text provided')
      return
    }
    
    if (!user) {
      console.error('❌ User not authenticated')
      alert('Please sign in to use this feature')
      return
    }
    
    if (availableModels.length === 0) {
      console.error('❌ No models available')
      alert('No AI models available. Please try again later.')
      return
    }
    
    try {
      setIsCreatingRun(true)
      
      // Create session first
      console.log('📋 Creating session...')
      const newSession = await apiClient.createSession({
        title: taskText.slice(0, 50) + (taskText.length > 50 ? '...' : ''),
        description: `Code session: ${taskText}`,
        models_used: availableModels.slice(0, parseInt(selectedAgentCount))
      })
      console.log('✅ Session created:', newSession.id)
      
      // Create turn
      console.log('🔄 Creating turn...')
      const newTurn = await apiClient.createTurn(newSession.id, {
        prompt: taskText,
        context: `https://github.com/${selectedRepo}`,
        models_requested: availableModels.slice(0, parseInt(selectedAgentCount))
      })
      console.log('✅ Turn created:', newTurn.id)
      
      // Execute code with streamlined API
      // TODO: Implement proper model picker for code mode
      // For now, hardcode GPT-4o for code mode
      const codeModels = ["gpt-4o", "gpt-4o", "gpt-4o"].slice(0, parseInt(selectedAgentCount))
      
      const codeRequest: CodeRequest = {
        prompt: taskText,
        context: `https://github.com/${selectedRepo}`,
        models: codeModels,
        max_models: parseInt(selectedAgentCount)
      }
      
      console.log('🤖 Executing code request:', codeRequest)
      const response = await apiClient.executeCode(newSession.id, newTurn.id, codeRequest)
      console.log('✅ Code execution started, run ID:', response.run_id)
      
      // Navigate to the streaming page
      console.log('🔗 Navigating to run page...')
      router.push(`/session/${newSession.id}/turn/${newTurn.id}/run/${response.run_id}`)
    } catch (err: any) {
      console.error('❌ Failed to create code session:', err)
      console.error('Error details:', err.detail || err.message || err)
      
      // More specific error messages
      if (err.detail?.includes('401') || err.detail?.includes('Unauthorized')) {
        alert('Authentication error. Please sign in again.')
        router.push('/signin')
      } else if (err.detail?.includes('404')) {
        alert('API endpoint not found. Please check your configuration.')
      } else {
        alert(`Failed to create code session: ${err.detail || err.message || 'Unknown error'}`)
      }
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
        <div className="flex items-center justify-center mb-8">
          <h1 className="text-4xl font-medium text-center">What are we coding next?</h1>
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

        <div className="mt-10">
          <h2 className="text-lg font-semibold mb-6">Sessions</h2>
          <div className="space-y-1">
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
          </div>
        </div>
      </div>
    </div>
  )
}
