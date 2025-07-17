"use client"

import { useState, use, useEffect, useRef } from "react"
import { FileCode, Terminal, AlertTriangle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Input } from "@/components/ui/input"
import { useTaskDetail } from "@/hooks/use-task-detail"
import { useAgentLogs } from "@/hooks/use-agent-logs"
import { useAgentErrors } from "@/hooks/use-agent-errors"
import { useTaskDiffs } from "@/hooks/use-task-diffs"
import { notFound } from "next/navigation"
import DiffViewer from "@/components/diff-viewer"
import { formatLogTimestamp } from "@/utils/timezone"


export default function TaskPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const [activeVersion, setActiveVersion] = useState(1)
  const { task, loading, error } = useTaskDetail(id)
  const { logs, isLoading: logsLoading, error: logsError, getLogsByVariation, hasLogsForVariation } = useAgentLogs(id)
  const { errors, isLoading: errorsLoading, error: errorsError, getErrorsByVariation, hasErrorsForVariation } = useAgentErrors(id)
  const { diffs, loading: diffsLoading, error: diffsError } = useTaskDiffs(id, activeVersion - 1)
  const logsContainerRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (logsContainerRef.current) {
      logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight
    }
  }, [logs, activeVersion])

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

  // Handle case where task exists but has no agent outputs yet
  if (!task.taskDetails || !task.taskDetails.versions || task.taskDetails.versions.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center bg-gray-950 text-gray-200">
        <div className="text-center">
          <div className="animate-pulse rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto mb-4"></div>
          <p className="text-lg mb-2">Task is processing...</p>
          <p className="text-gray-400 text-sm">Waiting for agent outputs to become available</p>
        </div>
      </div>
    )
  }

  const versionData = task.taskDetails.versions.find((v) => v.id === activeVersion)

  if (!versionData) {
    // Fallback to first version if active version not found
    const firstVersion = task.taskDetails.versions[0]
    if (!firstVersion) return notFound()
    setActiveVersion(firstVersion.id)
    return null // Re-render will handle it
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
      <div ref={logsContainerRef} className="space-y-2 max-h-full overflow-y-auto">
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

  return (
    <div className="flex flex-1 overflow-hidden bg-gray-950 text-gray-200">
      {/* Left Sidebar */}
      <aside className="w-80 bg-gray-900/70 border-r border-gray-800 p-4 flex flex-col overflow-y-auto">
          <div className="flex items-center gap-2 mb-4">
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

          <div className="space-y-6 text-sm">
            <div className="space-y-2">
              <h3 className="font-semibold text-gray-400">Summary</h3>
              <p className="text-gray-300">{versionData.summary}</p>
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold text-gray-400">Testing</h3>
              <div className="flex items-center gap-2 text-xs bg-gray-800 p-2 rounded-md">
                <span className="font-mono bg-gray-700 px-1.5 py-0.5 rounded">pytest</span>
                <span className="text-gray-400">-v</span>
                <span className="text-red-400 bg-red-900/50 px-1.5 py-0.5 rounded">0</span>
              </div>
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold text-gray-400">Network access</h3>
              <p className="text-gray-300">Some requests were blocked due to network access restrictions.</p>
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold text-gray-400">FILE ({versionData.files.length})</h3>
              <div className="space-y-1">
                {versionData.files.map((file) => (
                  <div key={file.name} className="flex justify-between items-center p-2 rounded-md hover:bg-gray-800">
                    <span>{file.name}</span>
                    <div className="font-mono text-xs">
                      <span className="text-green-400">+{file.additions}</span>{" "}
                      <span className="text-red-400">-{file.deletions}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="mt-auto pt-4">
            <Input placeholder="Request changes or ask a question" className="bg-gray-800 border-gray-700" />
          </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col bg-gray-950">
          <Tabs defaultValue="logs" className="flex-1 flex flex-col">
            <TabsList className="px-4 border-b border-gray-800 bg-transparent justify-start rounded-none">
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
            </TabsList>
            <TabsContent value="diff" className="flex-1 overflow-y-auto p-4">
              {renderDiffsContent()}
            </TabsContent>
            <TabsContent value="logs" className="flex-1 overflow-y-auto p-4 font-mono text-sm">
              {renderLogsContent()}
            </TabsContent>
            <TabsContent value="errors" className="flex-1 overflow-y-auto p-4">
              {renderErrorsContent()}
            </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
