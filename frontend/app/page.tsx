"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { AutoResizeTextarea } from "@/components/auto-resize-textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { GitBranch, Layers, Mic, Github, RefreshCw, AlertCircle, Archive, X, ArrowUp } from "lucide-react"
import Link from "next/link"
import { useTasks } from "@/hooks/use-tasks"
import { useArchive } from "@/hooks/use-archive"
import { useAuth } from "@/components/auth/auth-provider"
import { useGitHubRepos, useGitHubBranches } from "@/hooks/use-github-repos"
import { useLocalStorage } from "@/hooks/use-local-storage"
import { useConfirmation } from "@/hooks/use-confirmation"
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog"
import { 
  getHeadingClasses, 
  getBodyClasses, 
  getStatusColorClasses,
  getContainerSpacing,
  getGapSpacing,
  getPaddingSpacing,
  getMarginSpacing,
  getComponentSpacing,
  commonTypographyCombinations,
  commonSpacingCombinations,
  componentTokens
} from "@/lib/design-tokens"
import { cn } from "@/lib/utils"

export default function Home() {
  const [taskText, setTaskText] = useState("")
  const [hoveredTask, setHoveredTask] = useState<string | null>(null)
  const { tasks, loading, error, refetch } = useTasks()
  const { tasks: archivedTasks, loading: archivedLoading, error: archivedError, refetch: refetchArchived } = useTasks(20, true)
  const { archiving, deleting, unarchiveTask, deleteTask } = useArchive()
  const { user, token } = useAuth()
  const confirmation = useConfirmation()
  
  // Persistent settings
  const [variations, setVariations, variationsLoaded] = useLocalStorage('task_variations', 1)
  const [selectedRepo, setSelectedRepo, repoLoaded] = useLocalStorage('selected_repo', '')
  const [selectedBranch, setSelectedBranch, branchLoaded] = useLocalStorage('selected_branch', 'main')
  
  // GitHub data
  const { repos, loading: reposLoading } = useGitHubRepos(token)
  const { branches, loading: branchesLoading } = useGitHubBranches(token, selectedRepo)

  // Default demo configuration
  const demoRepoUrl = "https://github.com/aideator/helloworld"
  const promptVariations = ["cheerier", "more ominous", "funnier", "gloomier", "cooler"]
  
  // Set default repo when not authenticated or when repos load
  useEffect(() => {
    if (!token && !selectedRepo && repoLoaded) {
      setSelectedRepo(demoRepoUrl)
    }
  }, [token, selectedRepo, repoLoaded, setSelectedRepo])
  
  // Set first repo as default when user logs in and has repos
  useEffect(() => {
    if (token && repos.length > 0 && !selectedRepo && repoLoaded) {
      setSelectedRepo(repos[0].html_url)
    }
  }, [token, repos, selectedRepo, repoLoaded, setSelectedRepo])
  
  // Update branch when repo changes
  useEffect(() => {
    if (branches.length > 0 && branchLoaded) {
      const defaultBranch = branches.find(b => b.name === 'main') || branches.find(b => b.name === 'master') || branches[0]
      if (defaultBranch && selectedBranch !== defaultBranch.name) {
        setSelectedBranch(defaultBranch.name)
      }
    }
  }, [branches, selectedBranch, branchLoaded, setSelectedBranch])


  const handleCode = async () => {
    // Use provided task text or generate random demo prompt
    let finalPrompt = taskText.trim()
    if (!finalPrompt) {
      const randomVariation = promptVariations[Math.floor(Math.random() * promptVariations.length)]
      finalPrompt = `Change the hello world label to be ${randomVariation}`
    }

    // Determine final repo URL - use selected repo or fallback to demo
    const finalRepoUrl = selectedRepo || demoRepoUrl
    
    // Add branch to repo URL if specified and not default
    let repoUrlWithBranch = finalRepoUrl
    if (selectedBranch && selectedBranch !== 'main' && selectedBranch !== 'master') {
      repoUrlWithBranch = `${finalRepoUrl}/tree/${selectedBranch}`
    }

    try {
      // Get auth token from localStorage
      const authToken = localStorage.getItem('github_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }
      
      // Add authorization header if token exists
      if (authToken) {
        headers.Authorization = `Bearer ${authToken}`
      }
      
      const response = await fetch('http://localhost:8000/api/v1/tasks', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          github_url: repoUrlWithBranch,
          prompt: finalPrompt,
          model_names: ["gpt-4o-mini"],
          agent_mode: "claude-cli",
          variations: variations,
        })
      })

      if (response.ok) {
        const result = await response.json()
        setTaskText("")
        refetch() // Refresh tasks list
        // Navigate to task page
        window.location.href = `/task/${result.task_id}`
      } else {
        const error = await response.json()
        console.error('Task creation failed:', error)
        
        // Provide better error messages
        let errorMessage = 'Unknown error'
        if (error.detail) {
          if (Array.isArray(error.detail)) {
            // Validation errors
            errorMessage = error.detail.map((e: any) => e.msg).join(', ')
          } else if (typeof error.detail === 'string') {
            errorMessage = error.detail
          }
        }
        alert(`Error creating task: ${errorMessage}`)
      }
    } catch (err) {
      console.error('Network error:', err)
      alert(`Network error: ${err}`)
    }
  }

  const handleUnarchive = async (e: React.MouseEvent, taskId: string) => {
    e.preventDefault()
    e.stopPropagation()
    try {
      await unarchiveTask(taskId)
      refetch() // Refresh main tasks list
      refetchArchived() // Refresh archived tasks list
    } catch (err) {
      alert(`Failed to unarchive task: ${err}`)
    }
  }

  const handleDelete = async (e: React.MouseEvent, taskId: string) => {
    e.preventDefault()
    e.stopPropagation()
    
    // Prevent double-clicks
    if (deleting === taskId) {
      console.log(`Delete already in progress for task ${taskId}, ignoring click`)
      return
    }
    
    try {
      await confirmation.confirm(
        {
          title: 'Delete Task',
          description: 'Are you sure you want to permanently delete this task?',
          confirmText: 'Delete',
          cancelText: 'Cancel',
          variant: 'destructive',
        },
        async () => {
          console.log(`Starting delete for task ${taskId}`)
          await deleteTask(taskId)
          console.log(`Delete successful for task ${taskId}, refreshing list`)
          refetchArchived() // Refresh archived tasks list
        }
      )
    } catch (err) {
      console.error(`Delete failed for task ${taskId}:`, err)
      
      // Provide more user-friendly error messages
      let errorMessage = 'Unknown error occurred'
      if (err instanceof Error) {
        errorMessage = err.message
      } else if (typeof err === 'string') {
        errorMessage = err
      }
      
      alert(`Failed to delete task: ${errorMessage}`)
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
    <div className={componentTokens.ui.layout.page}>
      <div className={componentTokens.ui.layout.container}>
        <h1 className={`${commonTypographyCombinations.pageTitle} ${getMarginSpacing('lg')}`}>What are we coding next?</h1>

        <div className={componentTokens.ui.card.primary}>
          <AutoResizeTextarea
            placeholder="Describe a task"
            minRows={5}
            maxRows={20}
            value={taskText}
            onChange={(e) => setTaskText(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <div className="flex items-center justify-between">
            <div className={commonSpacingCombinations.buttonGroup}>
              {/* Repository Selector */}
              <Select 
                value={selectedRepo} 
                onValueChange={setSelectedRepo}
                disabled={reposLoading}
              >
                <SelectTrigger className={`${componentTokens.ui.card.secondary} w-auto ${getGapSpacing('sm')}`}>
                  <Github className={`w-4 h-4 ${getBodyClasses('secondary')}`} />
                  <SelectValue placeholder={reposLoading ? "Loading repos..." : "Select repository"} />
                </SelectTrigger>
                <SelectContent>
                  {/* Show demo repo for unauthenticated users */}
                  {!token && (
                    <SelectItem value={demoRepoUrl}>aideator/helloworld (demo)</SelectItem>
                  )}
                  
                  {/* Show user's repos when authenticated */}
                  {token && repos.map((repo) => (
                    <SelectItem key={repo.id} value={repo.html_url}>
                      {repo.full_name}
                      {repo.private && <span className="text-xs opacity-60 ml-1">(private)</span>}
                    </SelectItem>
                  ))}
                  
                  {/* Show demo option for authenticated users too */}
                  {token && (
                    <SelectItem value={demoRepoUrl}>aideator/helloworld (demo)</SelectItem>
                  )}
                </SelectContent>
              </Select>
              
              {/* Branch Selector */}
              <Select 
                value={selectedBranch} 
                onValueChange={setSelectedBranch}
                disabled={branchesLoading || !selectedRepo}
              >
                <SelectTrigger className={`${componentTokens.ui.card.secondary} w-auto ${getGapSpacing('sm')}`}>
                  <GitBranch className={`w-4 h-4 ${getBodyClasses('secondary')}`} />
                  <SelectValue placeholder={branchesLoading ? "Loading..." : "Branch"} />
                </SelectTrigger>
                <SelectContent>
                  {branches.length > 0 ? (
                    branches.map((branch) => (
                      <SelectItem key={branch.name} value={branch.name}>
                        {branch.name}
                      </SelectItem>
                    ))
                  ) : (
                    <SelectItem value="main">main</SelectItem>
                  )}
                </SelectContent>
              </Select>
              
              {/* Variations Selector */}
              <Select 
                value={String(variations)} 
                onValueChange={(value) => setVariations(Number(value))}
              >
                <SelectTrigger className={`${componentTokens.ui.card.secondary} w-auto ${getGapSpacing('sm')}`}>
                  <Layers className={`w-4 h-4 ${getBodyClasses('secondary')}`} />
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
            <div className={commonSpacingCombinations.buttonGroup}>
              <Button variant="ghost" size="icon">
                <Mic className="w-5 h-5" />
              </Button>
              {taskText.trim() && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleCode}
                  className={cn(
                    "rounded-lg transition-all duration-200",
                    taskText.trim() 
                      ? "bg-blue-600 hover:bg-blue-700 text-white" 
                      : "hover:bg-gray-800 text-gray-400"
                  )}
                >
                  <ArrowUp className="w-5 h-5" />
                </Button>
              )}
            </div>
          </div>
        </div>

        <Tabs defaultValue="tasks" className="mt-10">
          <TabsList className={commonSpacingCombinations.tabsLayout}>
            <TabsTrigger
              value="tasks"
              className="rounded-none data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 border-white"
            >
              Tasks
            </TabsTrigger>
            <TabsTrigger
              value="archive"
              className="rounded-none data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 border-white"
            >
              Archive
            </TabsTrigger>
          </TabsList>
          <TabsContent value="tasks" className={`mt-6 ${commonSpacingCombinations.listLayout}`}>
            {loading ? (
              <div className={`${commonSpacingCombinations.loadingContainer} py-8`}>
                <RefreshCw className={`w-6 h-6 animate-spin ${getBodyClasses('secondary')}`} />
                <span className={`ml-2 ${getBodyClasses('secondary')}`}>Loading tasks...</span>
              </div>
            ) : error ? (
              <div className={`${commonSpacingCombinations.loadingContainer} py-8`}>
                <AlertCircle className={`w-6 h-6 ${getStatusColorClasses('failed')}`} />
                <span className={`ml-2 ${getStatusColorClasses('failed')}`}>{error}</span>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={refetch}
                  className="ml-4"
                >
                  Retry
                </Button>
              </div>
            ) : tasks.length === 0 ? (
              <div className={`text-center py-8 ${getBodyClasses('muted')}`}>
                No tasks yet. Create your first coding task above!
              </div>
            ) : (
              tasks.map((task) => (
                <div 
                  key={task.id}
                  className={`flex items-center justify-between ${getPaddingSpacing('sm')} rounded-lg hover:bg-gray-900 transition-colors cursor-pointer group`}
                  onMouseEnter={() => setHoveredTask(task.id)}
                  onMouseLeave={() => setHoveredTask(null)}
                >
                  <Link href={`/task/${task.id}`} className="flex-1 flex items-center justify-between">
                    <div className="flex flex-col">
                      <span className="font-medium">{task.title}</span>
                      <span className={getBodyClasses('detail')}>{task.details}</span>
                    </div>
                    <div className={`flex items-center ${getGapSpacing('lg')}`}>
                      {task.status === "Completed" && (
                        <>
                          {task.versions && (
                            <div className={`flex items-center ${getGapSpacing('xs')} ${getBodyClasses('detail')}`}>
                              <Layers className="w-4 h-4" />
                              <span>{task.versions}</span>
                            </div>
                          )}
                          {(task.additions !== undefined || task.deletions !== undefined) && (
                            <div className={`${commonTypographyCombinations.codeInline} text-sm`}>
                              <span className={getStatusColorClasses('success')}>+{task.additions || 0}</span>{" "}
                              <span className={getStatusColorClasses('failed')}>-{task.deletions || 0}</span>
                            </div>
                          )}
                        </>
                      )}
                      {task.status === "Open" && (
                        <span className={`text-sm ${getStatusColorClasses('open')} ${getPaddingSpacing('badgeSecondary')} rounded-md`}>Open</span>
                      )}
                      {task.status === "Failed" && <span className={`text-sm ${getStatusColorClasses('failed')}`}>Failed</span>}
                    </div>
                  </Link>
                </div>
              ))
            )}
          </TabsContent>
          <TabsContent value="archive" className={`mt-6 ${commonSpacingCombinations.listLayout}`}>
            {archivedLoading ? (
              <div className={`${commonSpacingCombinations.loadingContainer} py-8`}>
                <RefreshCw className={`w-6 h-6 animate-spin ${getBodyClasses('secondary')}`} />
                <span className={`ml-2 ${getBodyClasses('secondary')}`}>Loading archived tasks...</span>
              </div>
            ) : archivedError ? (
              <div className={`${commonSpacingCombinations.loadingContainer} py-8`}>
                <AlertCircle className={`w-6 h-6 ${getStatusColorClasses('failed')}`} />
                <span className={`ml-2 ${getStatusColorClasses('failed')}`}>{archivedError}</span>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={refetchArchived}
                  className="ml-4"
                >
                  Retry
                </Button>
              </div>
            ) : archivedTasks.length === 0 ? (
              <div className={`text-center py-8 ${getBodyClasses('muted')}`}>
                No archived tasks yet.
              </div>
            ) : (
              archivedTasks.map((task) => (
                <div 
                  key={task.id}
                  className={`flex items-center justify-between ${getPaddingSpacing('sm')} rounded-lg hover:bg-gray-900 transition-colors cursor-pointer group`}
                  onMouseEnter={() => setHoveredTask(task.id)}
                  onMouseLeave={() => setHoveredTask(null)}
                >
                  <Link href={`/task/${task.id}`} className="flex-1 flex items-center justify-between">
                    <div className="flex flex-col">
                      <span className="font-medium">{task.title}</span>
                      <span className={getBodyClasses('detail')}>{task.details}</span>
                    </div>
                    <div className={`flex items-center ${getGapSpacing('lg')}`}>
                      {task.status === "Completed" && (
                        <>
                          {task.versions && (
                            <div className={`flex items-center ${getGapSpacing('xs')} ${getBodyClasses('detail')}`}>
                              <Layers className="w-4 h-4" />
                              <span>{task.versions}</span>
                            </div>
                          )}
                          {(task.additions !== undefined || task.deletions !== undefined) && (
                            <div className={`${commonTypographyCombinations.codeInline} text-sm`}>
                              <span className={getStatusColorClasses('success')}>+{task.additions || 0}</span>{" "}
                              <span className={getStatusColorClasses('failed')}>-{task.deletions || 0}</span>
                            </div>
                          )}
                        </>
                      )}
                      {task.status === "Open" && (
                        <span className={`text-sm ${getStatusColorClasses('open')} ${getPaddingSpacing('badgeSecondary')} rounded-md`}>Open</span>
                      )}
                      {task.status === "Failed" && <span className={`text-sm ${getStatusColorClasses('failed')}`}>Failed</span>}
                    </div>
                  </Link>
                  {/* Delete button - shows on hover for archived tasks */}
                  {hoveredTask === task.id && (
                    <div className={`flex items-center ${getGapSpacing('xs')} ml-2`}>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="opacity-70 hover:opacity-100"
                        onClick={(e) => handleUnarchive(e, task.id)}
                        disabled={archiving === task.id}
                        title="Unarchive task"
                      >
                        {archiving === task.id ? (
                          <RefreshCw className="w-4 h-4 animate-spin" />
                        ) : (
                          <Archive className="w-4 h-4" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="opacity-70 hover:opacity-100 hover:text-red-400"
                        onClick={(e) => handleDelete(e, task.id)}
                        disabled={deleting === task.id}
                        title="Delete task permanently"
                      >
                        {deleting === task.id ? (
                          <RefreshCw className="w-4 h-4 animate-spin" />
                        ) : (
                          <X className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                  )}
                </div>
              ))
            )}
          </TabsContent>
        </Tabs>
      </div>
      
      {/* Confirmation Dialog */}
      <ConfirmationDialog
        isOpen={confirmation.isOpen}
        onClose={confirmation.close}
        onConfirm={confirmation.onConfirm}
        title={confirmation.title}
        description={confirmation.description}
        confirmText={confirmation.confirmText}
        cancelText={confirmation.cancelText}
        variant={confirmation.variant}
        isLoading={confirmation.isLoading}
      />
    </div>
  )
}
