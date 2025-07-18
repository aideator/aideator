"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { AutoResizeTextarea } from "@/components/auto-resize-textarea"
import { RepositorySelect } from "@/components/repository-select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { GitBranch, Layers, Mic, RefreshCw, AlertCircle, ArrowUp } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import Link from "next/link"
import { useTasks } from "@/hooks/use-tasks"
import { useAuth } from "@/components/auth/auth-provider"
import { useGitHubRepos, useGitHubBranches } from "@/hooks/use-github-repos"
import { useLocalStorage } from "@/hooks/use-local-storage"
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
  componentTokens,
  getAgentColorClasses,
  getOutputTypeColorClasses
} from "@/lib/design-tokens"
import { cn } from "@/lib/utils"
import { AgentOutputViewerTokens } from "@/components/agent-output-viewer-tokens"
import { TokenSystemComparison } from "@/components/token-system-comparison"

export default function TokensDemo() {
  const [taskText, setTaskText] = useState("")
  const { tasks, loading, error, refetch } = useTasks()
  const { user, token } = useAuth()
  
  // Persistent settings (shared with main page)
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
        alert(`Error creating task: ${error.detail || 'Unknown error'}`)
      }
    } catch (err) {
      alert(`Network error: ${err}`)
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
        {/* Header with token demo indicator */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <h1 className={`${commonTypographyCombinations.pageTitle} ${getMarginSpacing('lg')}`}>
              Token System Demo
            </h1>
            <span className={`${getBodyClasses('secondary')} ${getStatusColorClasses('success')} bg-green-100 dark:bg-green-900 px-3 py-1 rounded-full text-sm`}>
              Using Design Tokens
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/" className={`${componentTokens.ui.button.secondary} px-4 py-2 rounded-lg text-sm hover:bg-gray-100 dark:hover:bg-gray-800`}>
              View Original
            </Link>
          </div>
        </div>

        <h2 className={`${commonTypographyCombinations.sectionHeader} ${getMarginSpacing('md')}`}>
          What are we coding next?
        </h2>

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
              <RepositorySelect
                value={selectedRepo}
                onChange={setSelectedRepo}
                disabled={reposLoading}
                triggerClassName={`${componentTokens.ui.card.secondary} ${getGapSpacing('sm')}`}
              />
              
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

        {/* Token System Showcase */}
        <div className={`${componentTokens.ui.card.secondary} ${getMarginSpacing('lg')}`}>
          <h3 className={`${commonTypographyCombinations.sectionHeader} ${getMarginSpacing('sm')}`}>
            Token System Showcase
          </h3>
          
          {/* Agent Colors Demo */}
          <div className={`${getMarginSpacing('md')} ${getGapSpacing('md')}`}>
            <h4 className={`${commonTypographyCombinations.cardTitle} ${getMarginSpacing('xs')}`}>
              Agent Colors (from Design Tokens)
            </h4>
            <div className={`grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 ${getGapSpacing('sm')}`}>
              {[1, 2, 3, 4, 5, 6].map(agentId => (
                <div key={agentId} className={`${getAgentColorClasses(agentId)} ${getPaddingSpacing('sm')} rounded-lg text-center`}>
                  <div className="text-sm font-medium">Agent {agentId}</div>
                  <div className="text-xs font-mono mt-1 opacity-75">
                    {getAgentColorClasses(agentId).split(' ').slice(0, 2).join(' ')}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Output Type Colors Demo */}
          <div className={`${getMarginSpacing('md')} ${getGapSpacing('md')}`}>
            <h4 className={`${commonTypographyCombinations.cardTitle} ${getMarginSpacing('xs')}`}>
              Output Type Colors (from Design Tokens)
            </h4>
            <div className={`grid grid-cols-2 md:grid-cols-3 ${getGapSpacing('sm')}`}>
              {['assistant_response', 'system_status', 'debug_info', 'error', 'diffs', 'legacy'].map(outputType => (
                <div key={outputType} className={`${getOutputTypeColorClasses(outputType)} ${getPaddingSpacing('sm')} rounded-lg text-center border`}>
                  <div className="text-sm font-medium">{outputType}</div>
                  <div className="text-xs font-mono mt-1 opacity-75">
                    {getOutputTypeColorClasses(outputType)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Typography Tokens Demo */}
          <div className={`${getMarginSpacing('md')} ${getGapSpacing('md')}`}>
            <h4 className={`${commonTypographyCombinations.cardTitle} ${getMarginSpacing('xs')}`}>
              Typography Tokens
            </h4>
            <div className={`${getGapSpacing('sm')} space-y-3`}>
              <div className={commonTypographyCombinations.pageTitle}>Page Title (pageTitle)</div>
              <div className={commonTypographyCombinations.sectionHeader}>Section Title (sectionTitle)</div>
              <div className={commonTypographyCombinations.cardTitle}>Subsection Title (subsectionTitle)</div>
              <div className={getBodyClasses('primary')}>Primary Body Text (primary)</div>
              <div className={getBodyClasses('secondary')}>Secondary Body Text (secondary)</div>
              <div className={getBodyClasses('muted')}>Muted Body Text (muted)</div>
              <div className={getBodyClasses('detail')}>Detail Body Text (detail)</div>
              <div className={commonTypographyCombinations.codeInline}>Code Inline (codeInline)</div>
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
            <TabsTrigger
              value="agent-demo"
              className="rounded-none data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 border-white"
            >
              Agent Demo
            </TabsTrigger>
            <TabsTrigger
              value="comparison"
              className="rounded-none data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 border-white"
            >
              Validation
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
                <Link href={`/task/${task.id}`} key={task.id}>
                  <div className={`flex items-center justify-between ${getPaddingSpacing('sm')} rounded-lg hover:bg-gray-900 transition-colors cursor-pointer`}>
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
                  </div>
                </Link>
              ))
            )}
          </TabsContent>
          <TabsContent value="archive" className="mt-6">
            <p className={`text-center ${getBodyClasses('muted')}`}>Archived tasks will appear here.</p>
          </TabsContent>
          <TabsContent value="agent-demo" className="mt-6">
            <div className={`${componentTokens.ui.card.secondary} ${getPaddingSpacing('lg')}`}>
              <h3 className={`${commonTypographyCombinations.sectionHeader} ${getMarginSpacing('sm')}`}>
                Agent Output Viewer (Token System)
              </h3>
              <p className={`${getBodyClasses('secondary')} ${getMarginSpacing('md')}`}>
                This is the AgentOutputViewer component using the design token system. 
                It demonstrates how agent colors and output type colors are applied consistently.
              </p>
              <AgentOutputViewerTokens taskId="demo-task-id" />
            </div>
          </TabsContent>
          <TabsContent value="comparison" className="mt-6">
            <div className={`${componentTokens.ui.card.secondary} ${getPaddingSpacing('lg')}`}>
              <h3 className={`${commonTypographyCombinations.sectionHeader} ${getMarginSpacing('sm')}`}>
                Token System Validation
              </h3>
              <p className={`${getBodyClasses('secondary')} ${getMarginSpacing('md')}`}>
                This validates that the design token system produces identical colors to the original hardcoded values.
                It ensures complete compatibility before migrating the main components.
              </p>
              <TokenSystemComparison />
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}