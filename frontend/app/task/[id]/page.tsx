"use client"

import { useState, use, useEffect, useRef } from "react"
import { FileCode, Terminal, AlertTriangle, Github } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Input } from "@/components/ui/input"
import { useTaskDetail } from "@/hooks/use-task-detail"
import { useAgentLogs } from "@/hooks/use-agent-logs"
import { useAgentErrors } from "@/hooks/use-agent-errors"
import { useTaskDiffs } from "@/hooks/use-task-diffs"
import { useTaskSummary } from "@/hooks/use-task-summary"
import { useTaskFileChanges } from "@/hooks/use-task-file-changes"
import { notFound } from "next/navigation"
import DiffViewer from "@/components/diff-viewer"
import { TaskSummary } from "@/components/task-summary"
import { PRCreation } from "@/components/pr-creation"
import { formatLogTimestamp } from "@/utils/timezone"


export default function TaskPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const [activeVersion, setActiveVersion] = useState(1)
  // Persist selected version so other components (e.g., PageHeader) can access
  useEffect(() => {
    if (id) {
      try {
        localStorage.setItem(`task_selected_version_${id}`, String(activeVersion))
      } catch (_) {
        /* ignore localStorage errors (e.g., SSR) */
      }
    }
  }, [activeVersion, id])
  const [activeTab, setActiveTab] = useState("logs")
  const { task, loading, error } = useTaskDetail(id)
  const { logs, isLoading: logsLoading, error: logsError, getLogsByVariation, hasLogsForVariation } = useAgentLogs(id)
  const { errors, isLoading: errorsLoading, error: errorsError, getErrorsByVariation, hasErrorsForVariation } = useAgentErrors(id)
  const { diffs, loading: diffsLoading, error: diffsError } = useTaskDiffs(id, activeVersion - 1)
  const { summary, loading: summaryLoading, error: summaryError } = useTaskSummary(id, activeVersion - 1, task?.status)
  const { files: changedFiles, loading: filesLoading, error: filesError } = useTaskFileChanges(id, activeVersion - 1, task?.status)
  const logsContainerRef = useRef<HTMLDivElement>(null)
  const [isManualScrolling, setIsManualScrolling] = useState(false)

  // Handle file click - switch to diff tab and scroll to file
  const handleFileClick = (fileName: string) => {
    setActiveTab("diff")
    
    // Use setTimeout to allow tab to switch first, then scroll and expand
    setTimeout(() => {
      const fileElement = document.querySelector(`[data-file-name="${fileName}"]`)
      if (fileElement) {
        // Scroll to the file
        fileElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
        
        // Find and click the file header to expand it if it's collapsed
        const fileHeader = fileElement.querySelector('.cursor-pointer')
        if (fileHeader) {
          // Check if the file is already expanded by looking for the chevron rotation
          const chevron = fileHeader.querySelector('svg')
          if (chevron && !chevron.classList.contains('rotate-90')) {
            (fileHeader as HTMLElement).click()
          }
        }
      }
    }, 100)
  }

  // Auto-scroll to bottom when new logs arrive (only if not manually scrolling)
  useEffect(() => {
    if (logsContainerRef.current && !isManualScrolling) {
      // Find the scrollable parent (TabsContent with explicit height)
      const scrollableParent = logsContainerRef.current.closest('[data-state="active"]')
      if (scrollableParent) {
        console.log('Auto-scrolling logs:', {
          scrollHeight: scrollableParent.scrollHeight,
          scrollTop: scrollableParent.scrollTop,
          clientHeight: scrollableParent.clientHeight,
          isManualScrolling
        })
        scrollableParent.scrollTop = scrollableParent.scrollHeight
      }
    }
  }, [logs, activeVersion, isManualScrolling])

  // Detect manual scrolling and add debugging
  useEffect(() => {
    const handleScroll = (e: Event) => {
      const target = e.target as HTMLElement
      console.log('Scroll event:', {
        target: target.tagName,
        deltaY: (e as any).deltaY,
        scrollTop: target.scrollTop,
        scrollHeight: target.scrollHeight,
        clientHeight: target.clientHeight,
        isNearBottom: target.scrollHeight - target.scrollTop - target.clientHeight < 50
      })
      
      setIsManualScrolling(true)
      // Clear manual scrolling flag after 2 seconds
      setTimeout(() => setIsManualScrolling(false), 2000)
    }

    // Add scroll listeners to all scrollable containers
    const scrollContainers = document.querySelectorAll('.custom-scrollbar')
    scrollContainers.forEach(container => {
      container.addEventListener('scroll', handleScroll)
    })

    return () => {
      scrollContainers.forEach(container => {
        container.removeEventListener('scroll', handleScroll)
      })
    }
  }, [])

  // Add wheel event debugging to understand scroll direction issues
  useEffect(() => {
    const handleWheel = (e: WheelEvent) => {
      console.log('Wheel event:', {
        deltaY: e.deltaY,
        deltaX: e.deltaX,
        deltaMode: e.deltaMode,
        target: (e.target as HTMLElement).tagName,
        ctrlKey: e.ctrlKey,
        shiftKey: e.shiftKey
      })
    }

    document.addEventListener('wheel', handleWheel)
    return () => document.removeEventListener('wheel', handleWheel)
  }, [])

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center bg-gray-950 text-gray-200">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
          <p>Loading task details...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-1 items-center justify-center bg-gray-950 text-gray-200">
        <div className="text-center">
          <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-4" />
          <p className="text-red-300 mb-2">Failed to load task</p>
          <p className="text-gray-400 text-sm">{error}</p>
        </div>
      </div>
    )
  }

  if (!task) {
    return notFound()
  }

  // Always show the full interface immediately when clicking on any task
  // This creates the "jump to logs" behavior as if we refreshed and checked task_outputs
  // The logs tab will handle loading states and show real data from task_outputs table

  // Always create version data to show the interface
  // This allows logs tab to display actual task_outputs data regardless of task status
  let versionData = null
  if (task.taskDetails?.versions) {
    versionData = task.taskDetails.versions.find((v) => v.id === activeVersion)
    
    if (!versionData) {
      // Fallback to first version if active version not found
      const firstVersion = task.taskDetails.versions[0]
      if (firstVersion) {
        setActiveVersion(firstVersion.id)
        return null // Re-render will handle it
      }
    }
  }

  // If we don't have version data from taskDetails, create a minimal structure
  // This allows the logs tab to always show the actual task_outputs data
  if (!versionData) {
    versionData = {
      id: 1,
      summary: task.status === "Open" ? "Task is processing..." : "View logs for task details",
      files: []
    }
  }

  // Render logs content for the current variation
  const renderLogsContent = () => {
    if (logsError) {
      return (
        <div className="text-center py-8">
          <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-4" />
          <p className="text-red-300 mb-2">Failed to load logs</p>
          <p className="text-gray-400 text-sm">{logsError}</p>
        </div>
      )
    }

    // Get logs for the current variation (convert 1-indexed version to 0-indexed variation_id)
    const variationLogs = getLogsByVariation(activeVersion - 1)
    
    if (logsLoading && variationLogs.length === 0) {
      return (
        <div className="text-center py-8">
          <div className="animate-pulse rounded-full h-6 w-6 border-b-2 border-blue-400 mx-auto mb-4"></div>
          <p className="text-gray-400">Waiting for logs...</p>
        </div>
      )
    }

    if (variationLogs.length === 0) {
      return (
        <div className="text-center py-8">
          <Terminal className="w-8 h-8 text-gray-500 mx-auto mb-4" />
          <p className="text-gray-400">Waiting for logs...</p>
          <p className="text-gray-500 text-sm mt-2">Agent container may still be starting up</p>
        </div>
      )
    }

    return (
      <div ref={logsContainerRef} className="space-y-2">
        {variationLogs.map((log) => (
          <div key={log.id} className="flex gap-3 text-sm">
            <span className="text-gray-500 text-xs w-24 flex-shrink-0">
              {formatLogTimestamp(log.timestamp)}
            </span>
            <pre className="text-gray-300 whitespace-pre-wrap flex-1">{log.content}</pre>
          </div>
        ))}
        {logsLoading && (
          <div className="flex items-center gap-2 text-gray-500 text-sm py-2">
            <div className="animate-pulse w-2 h-2 bg-blue-400 rounded-full"></div>
            <span>Loading more logs...</span>
          </div>
        )}
      </div>
    )
  }

  // Render errors content for the current variation
  const renderErrorsContent = () => {
    if (errorsError) {
      return (
        <div className="text-center py-8">
          <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-4" />
          <p className="text-red-300 mb-2">Failed to load errors</p>
          <p className="text-gray-400 text-sm">{errorsError}</p>
        </div>
      )
    }

    // Get errors for the current variation (subtract 1 because variation_id is 0-indexed in API)
    const variationErrors = getErrorsByVariation(activeVersion - 1)
    
    if (errorsLoading && variationErrors.length === 0) {
      return (
        <div className="text-center py-8">
          <div className="animate-pulse rounded-full h-6 w-6 border-b-2 border-red-400 mx-auto mb-4"></div>
          <p className="text-gray-400">Checking for errors...</p>
        </div>
      )
    }

    if (variationErrors.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          <AlertTriangle className="w-8 h-8 text-gray-600 mx-auto mb-4" />
          <p className="text-lg mb-2">No errors found</p>
          <p className="text-sm">This variation completed without any reported errors</p>
        </div>
      )
    }

    return (
      <div className="space-y-4">
        {variationErrors.map((errorItem) => (
          <div key={errorItem.id} className={`rounded-lg p-4 border ${
            errorItem.output_type === 'error' 
              ? 'bg-red-950/50 border-red-800' 
              : 'bg-orange-950/50 border-orange-800'
          }`}>
            <div className="flex items-start gap-3">
              <AlertTriangle className={`w-5 h-5 mt-0.5 flex-shrink-0 ${
                errorItem.output_type === 'error' ? 'text-red-400' : 'text-orange-400'
              }`} />
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h4 className={`font-medium ${
                    errorItem.output_type === 'error' ? 'text-red-300' : 'text-orange-300'
                  }`}>
                    {errorItem.output_type === 'error' ? 'Error' : 'Stderr Output'}
                  </h4>
                  <span className="text-xs text-gray-500">
                    {formatLogTimestamp(errorItem.timestamp)}
                  </span>
                </div>
                <pre className={`text-sm p-3 rounded border overflow-x-auto whitespace-pre-wrap ${
                  errorItem.output_type === 'error' 
                    ? 'bg-black/50 border-red-700/50 text-red-200' 
                    : 'bg-black/50 border-orange-700/50 text-orange-200'
                }`}>
                  {errorItem.content}
                </pre>
              </div>
            </div>
          </div>
        ))}
        {errorsLoading && (
          <div className="flex items-center gap-2 text-gray-500 text-sm py-2">
            <div className="animate-pulse w-2 h-2 bg-red-400 rounded-full"></div>
            <span>Checking for more errors...</span>
          </div>
        )}
      </div>
    )
  }

  // Render diffs content for the current variation
  const renderDiffsContent = () => {
    if (diffsError) {
      return (
        <div className="text-center py-8">
          <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-4" />
          <p className="text-red-300 mb-2">Failed to load diffs</p>
          <p className="text-gray-400 text-sm">{diffsError}</p>
        </div>
      )
    }

    if (diffsLoading && diffs.length === 0) {
      return (
        <div className="text-center py-8">
          <div className="animate-pulse rounded-full h-6 w-6 border-b-2 border-blue-400 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading diff data...</p>
        </div>
      )
    }

    if (diffs.length === 0) {
      return (
        <div className="text-center py-8">
          <FileCode className="w-8 h-8 text-gray-500 mx-auto mb-4" />
          <p className="text-gray-400">No diffs available yet</p>
          <p className="text-gray-500 text-sm mt-2">Diffs will appear after the agent makes changes</p>
        </div>
      )
    }

    // Get the latest diff data (most recent timestamp)
    const latestDiff = diffs[diffs.length - 1]
    
    // Pass XML content directly to DiffViewer
    return <DiffViewer xmlData={latestDiff.content} />
  }

  // Render PR creation content for the current variation
  const renderPRContent = () => {
    // Get the latest diff data for the current variation
    const latestDiff = diffs[diffs.length - 1]
    const diffContent = latestDiff?.content || ""
    
    return (
      <div className="max-w-4xl mx-auto">
        <PRCreation
          taskId={id}
          variationId={activeVersion - 1}
          summary={summary || undefined}
          diffContent={diffContent}
          changedFiles={changedFiles}
          githubUrl={task.github_url}
        />
      </div>
    )
  }

  return (
    <div className="flex flex-1 h-full overflow-hidden bg-gray-950 text-gray-200">
      {/* Left Sidebar */}
      <aside className="w-80 bg-gray-900/70 border-r border-gray-800 flex flex-col">
        {/* Version selector - fixed height */}
        <div className="flex items-center gap-2 mb-4 p-4 pb-0">
          {task.taskDetails.versions.map((v) => (
            <Button
              key={v.id}
              variant={activeVersion === v.id ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setActiveVersion(v.id)}
              className="data-[state=active]:bg-gray-700"
            >
              Version {v.id}
            </Button>
          ))}
        </div>

        {/* Scrollable content area - explicit height */}
        <div className="flex-1 px-4 overflow-y-auto custom-scrollbar" style={{ height: 'calc(100vh - 140px)' }}>
          <div className="space-y-6 text-sm">
            <div className="space-y-2">
              <TaskSummary 
                summary={summary || undefined}
                isLoading={summaryLoading}
                error={summaryError}
              />
            </div>
            <div className="space-y-2">
              <div className="p-3 bg-gray-800/30 border border-gray-700/50 rounded-lg">
                <h3 className="font-semibold text-gray-400 mb-3">FILES ({changedFiles.length})</h3>
                {filesLoading ? (
                  <div className="flex items-center gap-2 text-xs text-gray-400">
                    <div className="w-3 h-3 border border-gray-400 border-t-transparent rounded-full animate-spin" />
                    Loading files...
                  </div>
                ) : filesError ? (
                  <div className="text-red-400 text-xs">Error loading files</div>
                ) : changedFiles.length === 0 ? (
                  <div className="text-gray-400 text-xs">No files changed</div>
                ) : (
                  <div className="space-y-1">
                    {changedFiles.map((file) => (
                      <div 
                        key={file.name} 
                        className="flex justify-between items-center p-2 rounded-md hover:bg-gray-700/50 cursor-pointer transition-colors"
                        onClick={() => handleFileClick(file.name)}
                      >
                        <span className="text-sm text-cyan-300 hover:text-cyan-200">{file.name}</span>
                        <div className="font-mono text-xs">
                          <span className="text-green-400">+{file.additions}</span>{" "}
                          <span className="text-red-400">-{file.deletions}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Input box - fixed at bottom */}
        <div className="p-4 pt-0">
          <Input placeholder="Request changes or ask a question" className="bg-gray-800 border-gray-700" />
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col bg-gray-950">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
            {/* Fixed tabs header */}
            <TabsList className="px-4 bg-gray-800/50 justify-start rounded-none border-b-0">
              <TabsTrigger
                value="diff"
                className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 border-white rounded-none"
              >
                <FileCode className="w-4 h-4 mr-2" />
                Diff
              </TabsTrigger>
              <TabsTrigger
                value="logs"
                className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 border-white rounded-none"
              >
                <Terminal className="w-4 h-4 mr-2" />
                Logs
              </TabsTrigger>
              <TabsTrigger
                value="errors"
                className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 border-white rounded-none"
              >
                <AlertTriangle className="w-4 h-4 mr-2" />
                Errors
              </TabsTrigger>
              <TabsTrigger
                value="pr"
                className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 border-white rounded-none"
              >
                <Github className="w-4 h-4 mr-2" />
                Create PR
              </TabsTrigger>
            </TabsList>
            
            {/* Scrollable tab content - explicit height */}
            <TabsContent value="diff" className="p-4 overflow-y-auto custom-scrollbar" style={{ height: 'calc(100vh - 120px)' }}>
              {renderDiffsContent()}
            </TabsContent>
            <TabsContent value="logs" className="p-4 font-mono text-sm overflow-y-auto custom-scrollbar relative" style={{ height: 'calc(100vh - 120px)' }}>
              {isManualScrolling && (
                <div className="absolute top-2 right-2 bg-blue-600 text-white px-2 py-1 rounded text-xs z-10">
                  Manual scrolling detected
                </div>
              )}
              {renderLogsContent()}
            </TabsContent>
            <TabsContent value="errors" className="p-4 overflow-y-auto custom-scrollbar" style={{ height: 'calc(100vh - 120px)' }}>
              {renderErrorsContent()}
            </TabsContent>
            <TabsContent value="pr" className="p-4 overflow-y-auto custom-scrollbar" style={{ height: 'calc(100vh - 120px)' }}>
              {renderPRContent()}
            </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
