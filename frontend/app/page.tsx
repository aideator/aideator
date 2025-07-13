"use client"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { AutoResizeTextarea } from "@/components/auto-resize-textarea"
import { Mic, Loader2, Send } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { apiClient } from "@/lib/api"
import { Session, GitHubRepository, GitHubBranch, CodeRequest } from "@/lib/types"
import { useAuth } from "@/lib/auth-context"
import { ModeSwitcher, Mode } from "@/components/mode-switcher"
import { ModelPicker, ModelVariant } from "@/components/model-picker"
import { CodeModePicker } from "@/components/code-mode-picker"

export default function Home() {
  // Mode state
  const [mode, setMode] = useState<Mode>("chat")
  
  // Common state
  const [taskText, setTaskText] = useState("")
  const [sessions, setSessions] = useState<Session[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isCreatingRun, setIsCreatingRun] = useState(false)
  
  // Chat mode state
  const [selectedModels, setSelectedModels] = useState<ModelVariant[]>([])
  
  // Code mode state
  const [selectedCodeModel, setSelectedCodeModel] = useState("claude-code")
  const [selectedRepo, setSelectedRepo] = useState("")
  const [selectedBranch, setSelectedBranch] = useState("main")
  const [selectedAgentCount, setSelectedAgentCount] = useState("3")
  const [customRepoUrl, setCustomRepoUrl] = useState("")
  const [repositories, setRepositories] = useState<GitHubRepository[]>([])
  const [branches, setBranches] = useState<GitHubBranch[]>([])
  const [isLoadingRepos, setIsLoadingRepos] = useState(false)
  const [isLoadingBranches, setIsLoadingBranches] = useState(false)
  
  // Legacy model state for compatibility
  const [availableModels, setAvailableModels] = useState<string[]>([])
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
    // Default to astral-sh/uv repo instead of API calls
    setIsLoadingRepos(true)
    const defaultRepos: GitHubRepository[] = [
      { 
        id: 1, 
        name: 'uv',
        full_name: 'astral-sh/uv', 
        private: false,
        html_url: 'https://github.com/astral-sh/uv',
        description: 'An extremely fast Python package and project manager, written in Rust.', 
        default_branch: 'main'
      }
    ]
    setRepositories(defaultRepos)
    setSelectedRepo('astral-sh/uv')
    setIsLoadingRepos(false)
  }

  const loadBranches = useCallback(async () => {
    if (!selectedRepo) return
    
    // Default to main branch for astral-sh/uv
    setIsLoadingBranches(true)
    const defaultBranches: GitHubBranch[] = [
      { 
        name: 'main', 
        commit: {
          sha: 'abc123def456',
          url: 'https://api.github.com/repos/astral-sh/uv/commits/abc123def456'
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

  const handleChatSubmit = async () => {
    console.log('🚀 handleChatSubmit called')
    console.log('📝 Task text:', taskText)
    console.log('🔐 Auth state:', { user: !!user, authLoading })
    console.log('🎯 Selected models:', selectedModels)
    
    if (!taskText.trim()) {
      console.warn('❌ No task text provided')
      return
    }
    
    if (!user) {
      console.error('❌ User not authenticated')
      alert('Please sign in to use this feature')
      return
    }
    
    if (selectedModels.length === 0) {
      console.error('❌ No models selected')
      alert('Please select at least one model')
      return
    }
    
    try {
      setIsCreatingRun(true)
      
      // Create session first
      console.log('📋 Creating session...')
      const newSession = await apiClient.createSession({
        title: taskText.slice(0, 50) + (taskText.length > 50 ? '...' : ''),
        description: `Chat session: ${taskText}`,
        models_used: selectedModels.map(v => v.model_definition_id)
      })
      console.log('✅ Session created:', newSession.id)
      
      // Create turn
      console.log('🔄 Creating turn...')
      const newTurn = await apiClient.createTurn(newSession.id, {
        prompt: taskText,
        context: 'Chat conversation',
        models_requested: selectedModels.map(v => v.model_definition_id)
      })
      console.log('✅ Turn created:', newTurn.id)
      
      // Execute chat with model variants
      const chatRequest: CodeRequest = {
        prompt: taskText,
        context: 'Chat conversation',
        model_variants: selectedModels,
        max_models: selectedModels.length
      }
      
      console.log('💬 Executing chat request:', chatRequest)
      const response = await apiClient.executeCode(newSession.id, newTurn.id, chatRequest)
      console.log('✅ Chat execution started, run ID:', response.run_id)
      
      // Navigate to the streaming page
      console.log('🔗 Navigating to run page...')
      router.push(`/session/${newSession.id}/turn/${newTurn.id}/run/${response.run_id}`)
    } catch (err: any) {
      console.error('❌ Failed to create chat session:', err)
      console.error('Error details:', err.detail || err.message || err)
      
      // More specific error messages
      if (err.detail?.includes('401') || err.detail?.includes('Unauthorized')) {
        alert('Authentication error. Please sign in again.')
        router.push('/signin')
      } else if (err.detail?.includes('404')) {
        alert('API endpoint not found. Please check your configuration.')
      } else {
        alert(`Failed to create chat session: ${err.detail || err.message || 'Unknown error'}`)
      }
    } finally {
      setIsCreatingRun(false)
    }
  }

  const handleCodeSubmit = async () => {
    console.log('🚀 handleCodeSubmit called')
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
        models_used: Array(parseInt(selectedAgentCount)).fill(selectedCodeModel)
      })
      console.log('✅ Session created:', newSession.id)
      
      // Create turn
      console.log('🔄 Creating turn...')
      const newTurn = await apiClient.createTurn(newSession.id, {
        prompt: taskText,
        context: customRepoUrl || `https://github.com/${selectedRepo}`,
        models_requested: Array(parseInt(selectedAgentCount)).fill(selectedCodeModel)
      })
      console.log('✅ Turn created:', newTurn.id)
      
      // Execute code with streamlined API
      // Use selected code model
      const codeModels = Array(parseInt(selectedAgentCount)).fill(selectedCodeModel)
      
      const repoUrl = customRepoUrl || `https://github.com/${selectedRepo}`
      const codeRequest: CodeRequest = {
        prompt: taskText,
        context: repoUrl,
        model_variants: codeModels.map((model, index) => ({
          id: `code_variant_${index}`,
          model_definition_id: model,
          model_parameters: { temperature: 0.7, max_tokens: 1000 }
        })),
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
        if (mode === "chat") {
          handleChatSubmit()
        } else {
          handleCodeSubmit()
        }
      }
    }
  }
  
  const handleSubmit = () => {
    if (mode === "chat") {
      handleChatSubmit()
    } else {
      handleCodeSubmit()
    }
  }
  
  const getPlaceholder = () => {
    return mode === "chat" 
      ? "What are we chatting about today?\n\nTry: \"Write a short story about a robot who discovers they can dream\""
      : "Describe a coding task"
  }
  
  const getTitle = () => {
    return mode === "chat"
      ? "What are we chatting about today?"
      : "What are we coding next?"
  }
  
  const canSubmit = () => {
    const hasText = !!taskText.trim()
    const notCreating = !isCreatingRun
    const hasModels = selectedModels.length > 0
    const hasRepo = !!(selectedRepo || customRepoUrl)
    const hasCodeModel = !!selectedCodeModel
    
    console.log('canSubmit check:', { 
      mode, 
      hasText, 
      notCreating, 
      hasModels, 
      selectedModelsCount: selectedModels.length,
      hasRepo, 
      hasCodeModel 
    })
    
    if (!hasText || !notCreating) return false
    
    if (mode === "chat") {
      return hasModels
    } else {
      return hasRepo && hasCodeModel
    }
  }

  return (
    <div className="bg-gray-950 text-gray-50 min-h-screen">
      <div className="container mx-auto max-w-3xl py-16">
        <div className="flex flex-col items-center mb-8">
          <ModeSwitcher mode={mode} onModeChange={setMode} className="mb-6" />
          <h1 className="text-4xl font-medium text-center">{getTitle()}</h1>
        </div>

        <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-6 space-y-6">
          <AutoResizeTextarea
            placeholder={getPlaceholder()}
            minRows={4}
            maxRows={20}
            value={taskText}
            onChange={(e) => setTaskText(e.target.value)}
            onKeyDown={handleKeyDown}
            className="bg-transparent border-0 resize-none focus:ring-0 text-lg"
          />
          
          {/* Mode-specific controls */}
          {mode === "chat" ? (
            <ModelPicker
              selectedVariants={selectedModels}
              onVariantsChange={setSelectedModels}
              maxVariants={5}
            />
          ) : (
            <CodeModePicker
              selectedModel={selectedCodeModel}
              onModelChange={setSelectedCodeModel}
              selectedRepo={selectedRepo}
              onRepoChange={setSelectedRepo}
              selectedBranch={selectedBranch}
              onBranchChange={setSelectedBranch}
              selectedAgentCount={selectedAgentCount}
              onAgentCountChange={setSelectedAgentCount}
              customRepoUrl={customRepoUrl}
              onCustomRepoUrlChange={setCustomRepoUrl}
              repositories={repositories}
              branches={branches}
              isLoadingRepos={isLoadingRepos}
              isLoadingBranches={isLoadingBranches}
            />
          )}
          
          {/* Submit button */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="icon" className="text-gray-400 hover:text-gray-200">
                <Mic className="w-5 h-5" />
              </Button>
            </div>
            <Button
              size="lg"
              onClick={handleSubmit}
              disabled={!canSubmit()}
              className="gap-2 bg-white text-black hover:bg-gray-200 disabled:opacity-50"
            >
              {isCreatingRun ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  {mode === "chat" ? "Start Chat" : "Start Coding"}
                </>
              )}
            </Button>
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
                        <span>{session.total_turns}</span>
                      </div>
                      <div className="font-mono text-sm text-gray-400">
                        ${(session.total_cost || 0).toFixed(2)}
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