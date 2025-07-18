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
import { notFound } from "next/navigation"
import DiffViewer from "@/components/diff-viewer"
import { 
  getBodyClasses, 
  getStatusColorClasses,
  commonTypographyCombinations,
  componentTokens,
  getPaddingSpacing,
  getGapSpacing,
  getMarginSpacing
} from "@/lib/design-tokens"

// Convert task data to XML format for DiffViewer
function convertTaskDataToXml(versionData: any): string {
  if (!versionData?.files || versionData.files.length === 0) {
    return `<diff_analysis>
  <file>
    <name>No files to display</name>
    <diff>No changes detected in this task</diff>
    <changes>No modifications were made during task execution</changes>
  </file>
</diff_analysis>`
  }

  const fileElements = versionData.files.map((file: any) => {
    // Convert diff array back to standard diff format
    const diffText = file.diff.map((line: any) => {
      if (line.type === 'add') {
        return `+${line.content}`
      } else if (line.type === 'del') {
        return `-${line.content}`
      } else {
        return line.content
      }
    }).join('\n')

    // Generate changes summary
    const changesSummary = `File modified with ${file.additions} additions and ${file.deletions} deletions`

    return `  <file>
    <name>${file.name}</name>
    <diff>${diffText.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</diff>
    <changes>${changesSummary}</changes>
  </file>`
  }).join('\n')

  return `<diff_analysis>
${fileElements}
</diff_analysis>`
}

export default function TaskPageTokens({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const [activeVersion, setActiveVersion] = useState(1)
  const { task, loading, error } = useTaskDetail(id)
  const { logs, isLoading: logsLoading, error: logsError, getLogsByVariation, hasLogsForVariation } = useAgentLogs(id)
  const { errors, isLoading: errorsLoading, error: errorsError, getErrorsByVariation, hasErrorsForVariation } = useAgentErrors(id)
  const logsContainerRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (logsContainerRef.current) {
      logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight
    }
  }, [logs, activeVersion])

  if (loading) {
    return (
      <div className={`flex flex-1 items-center justify-center ${componentTokens.ui.layout.page}`}>
        <div className="text-center">
          <div className={`animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto ${getMarginSpacing('md')}`}></div>
          <p className={getBodyClasses('primary')}>Loading task details...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`flex flex-1 items-center justify-center ${componentTokens.ui.layout.page}`}>
        <div className="text-center">
          <AlertTriangle className={`w-8 h-8 ${getStatusColorClasses('failed')} mx-auto ${getMarginSpacing('md')}`} />
          <p className={`${getStatusColorClasses('failed')} ${getMarginSpacing('xs')}`}>Failed to load task</p>
          <p className={`${getBodyClasses('secondary')} text-sm`}>{error}</p>
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
      <div className={`flex flex-1 items-center justify-center ${componentTokens.ui.layout.page}`}>
        <div className="text-center">
          <div className={`animate-pulse rounded-full h-8 w-8 border-b-2 ${getStatusColorClasses('processing')} mx-auto ${getMarginSpacing('md')}`}></div>
          <p className={`text-lg ${getMarginSpacing('xs')}`}>Task is processing...</p>
          <p className={`${getBodyClasses('secondary')} text-sm`}>Waiting for agent outputs to become available</p>
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
        <div className={`text-center ${getPaddingSpacing('lg')}`}>
          <AlertTriangle className={`w-8 h-8 ${getStatusColorClasses('failed')} mx-auto ${getMarginSpacing('md')}`} />
          <p className={`${getStatusColorClasses('failed')} ${getMarginSpacing('xs')}`}>Failed to load logs</p>
          <p className={`${getBodyClasses('secondary')} text-sm`}>{logsError}</p>
        </div>
      )
    }

    // Get logs for the current variation (version ID matches variation_id)
    const variationLogs = getLogsByVariation(activeVersion)
    
    if (logsLoading && variationLogs.length === 0) {
      return (
        <div className={`text-center ${getPaddingSpacing('lg')}`}>
          <div className={`animate-pulse rounded-full h-6 w-6 border-b-2 ${getStatusColorClasses('processing')} mx-auto ${getMarginSpacing('md')}`}></div>
          <p className={getBodyClasses('secondary')}>Waiting for logs...</p>
        </div>
      )
    }

    if (variationLogs.length === 0) {
      return (
        <div className={`text-center ${getPaddingSpacing('lg')}`}>
          <Terminal className={`w-8 h-8 ${getBodyClasses('muted')} mx-auto ${getMarginSpacing('md')}`} />
          <p className={getBodyClasses('secondary')}>Waiting for logs...</p>
          <p className={`${getBodyClasses('muted')} text-sm ${getMarginSpacing('xs')}`}>Agent container may still be starting up</p>
        </div>
      )
    }

    return (
      <div ref={logsContainerRef} className={`${getGapSpacing('sm')} space-y-2 max-h-full overflow-y-auto`}>
        {variationLogs.map((log) => (
          <div key={log.id} className={`flex ${getGapSpacing('sm')} text-sm`}>
            <span className={`${getBodyClasses('muted')} text-xs w-24 flex-shrink-0`}>
              {new Date(log.timestamp).toLocaleTimeString()}
            </span>
            <pre className={`${getBodyClasses('primary')} whitespace-pre-wrap flex-1`}>{log.content}</pre>
          </div>
        ))}
        {logsLoading && (
          <div className={`flex items-center ${getGapSpacing('sm')} ${getBodyClasses('muted')} text-sm ${getPaddingSpacing('sm')}`}>
            <div className={`animate-pulse w-2 h-2 ${getStatusColorClasses('processing')} rounded-full`}></div>
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
        <div className={`text-center ${getPaddingSpacing('lg')}`}>
          <AlertTriangle className={`w-8 h-8 ${getStatusColorClasses('failed')} mx-auto ${getMarginSpacing('md')}`} />
          <p className={`${getStatusColorClasses('failed')} ${getMarginSpacing('xs')}`}>Failed to load errors</p>
          <p className={`${getBodyClasses('secondary')} text-sm`}>{errorsError}</p>
        </div>
      )
    }

    // Get errors for the current variation (subtract 1 because variation_id is 0-indexed in API)
    const variationErrors = getErrorsByVariation(activeVersion - 1)
    
    if (errorsLoading && variationErrors.length === 0) {
      return (
        <div className={`text-center ${getPaddingSpacing('lg')}`}>
          <div className={`animate-pulse rounded-full h-6 w-6 border-b-2 ${getStatusColorClasses('failed')} mx-auto ${getMarginSpacing('md')}`}></div>
          <p className={getBodyClasses('secondary')}>Checking for errors...</p>
        </div>
      )
    }

    if (variationErrors.length === 0) {
      return (
        <div className={`text-center ${getPaddingSpacing('lg')} ${getBodyClasses('muted')}`}>
          <AlertTriangle className={`w-8 h-8 ${getBodyClasses('muted')} mx-auto ${getMarginSpacing('md')}`} />
          <p className={`text-lg ${getMarginSpacing('xs')}`}>No errors found</p>
          <p className="text-sm">This variation completed without any reported errors</p>
        </div>
      )
    }

    return (
      <div className={`${getGapSpacing('md')} space-y-4`}>
        {variationErrors.map((errorItem) => (
          <div key={errorItem.id} className={`rounded-lg ${getPaddingSpacing('md')} border ${
            errorItem.output_type === 'error' 
              ? 'bg-red-950/50 border-red-800' 
              : 'bg-orange-950/50 border-orange-800'
          }`}>
            <div className={`flex items-start ${getGapSpacing('sm')}`}>
              <AlertTriangle className={`w-5 h-5 mt-0.5 flex-shrink-0 ${
                errorItem.output_type === 'error' ? 'text-red-400' : 'text-orange-400'
              }`} />
              <div className="flex-1">
                <div className={`flex items-center ${getGapSpacing('sm')} ${getMarginSpacing('xs')}`}>
                  <h4 className={`font-medium ${
                    errorItem.output_type === 'error' ? 'text-red-300' : 'text-orange-300'
                  }`}>
                    {errorItem.output_type === 'error' ? 'Error' : 'Stderr Output'}
                  </h4>
                  <span className={`text-xs ${getBodyClasses('muted')}`}>
                    {new Date(errorItem.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <pre className={`text-sm ${getPaddingSpacing('sm')} rounded border overflow-x-auto whitespace-pre-wrap ${
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
          <div className={`flex items-center ${getGapSpacing('sm')} ${getBodyClasses('muted')} text-sm ${getPaddingSpacing('sm')}`}>
            <div className={`animate-pulse w-2 h-2 ${getStatusColorClasses('failed')} rounded-full`}></div>
            <span>Checking for more errors...</span>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className={`flex flex-1 overflow-hidden ${componentTokens.ui.layout.page}`}>
      {/* Left Sidebar */}
      <aside className={`w-80 ${componentTokens.ui.card.secondary} border-r ${componentTokens.ui.layout.border} ${getPaddingSpacing('md')} flex flex-col overflow-y-auto`}>
          <div className={`flex items-center ${getGapSpacing('sm')} ${getMarginSpacing('md')}`}>
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

          <div className={`${getGapSpacing('lg')} space-y-6 text-sm`}>
            <div className={`${getGapSpacing('sm')} space-y-2`}>
              <h3 className={`font-semibold ${getBodyClasses('secondary')}`}>Summary</h3>
              <p className={getBodyClasses('primary')}>{versionData.summary}</p>
            </div>
            <div className={`${getGapSpacing('sm')} space-y-2`}>
              <h3 className={`font-semibold ${getBodyClasses('secondary')}`}>Testing</h3>
              <div className={`flex items-center ${getGapSpacing('sm')} text-xs ${componentTokens.ui.card.secondary} ${getPaddingSpacing('sm')} rounded-md`}>
                <span className={`${commonTypographyCombinations.codeInline} bg-gray-700 ${getPaddingSpacing('xs')} rounded`}>pytest</span>
                <span className={getBodyClasses('secondary')}>-v</span>
                <span className={`${getStatusColorClasses('failed')} bg-red-900/50 ${getPaddingSpacing('xs')} rounded`}>0</span>
              </div>
            </div>
            <div className={`${getGapSpacing('sm')} space-y-2`}>
              <h3 className={`font-semibold ${getBodyClasses('secondary')}`}>Network access</h3>
              <p className={getBodyClasses('primary')}>Some requests were blocked due to network access restrictions.</p>
            </div>
            <div className={`${getGapSpacing('sm')} space-y-2`}>
              <h3 className={`font-semibold ${getBodyClasses('secondary')}`}>FILE ({versionData.files.length})</h3>
              <div className={`${getGapSpacing('xs')} space-y-1`}>
                {versionData.files.map((file) => (
                  <div key={file.name} className={`flex justify-between items-center ${getPaddingSpacing('sm')} rounded-md hover:bg-gray-800`}>
                    <span className={getBodyClasses('primary')}>{file.name}</span>
                    <div className={`${commonTypographyCombinations.codeInline} text-xs`}>
                      <span className={getStatusColorClasses('success')}>+{file.additions}</span>{" "}
                      <span className={getStatusColorClasses('failed')}>-{file.deletions}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className={`mt-auto ${getPaddingSpacing('md')}`}>
            <Input placeholder="Request changes or ask a question" className={`${componentTokens.ui.card.secondary} ${componentTokens.ui.layout.border}`} />
          </div>
      </aside>

      {/* Main Content */}
      <main className={`flex-1 flex flex-col ${componentTokens.ui.layout.page}`}>
          <Tabs defaultValue="logs" className="flex-1 flex flex-col">
            <TabsList className={`${getPaddingSpacing('md')} border-b ${componentTokens.ui.layout.border} bg-transparent justify-start rounded-none`}>
              <TabsTrigger
                value="diff"
                className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 border-white rounded-none"
              >
                <FileCode className={`w-4 h-4 ${getMarginSpacing('xs')}`} />
                Diff
              </TabsTrigger>
              <TabsTrigger
                value="logs"
                className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 border-white rounded-none"
              >
                <Terminal className={`w-4 h-4 ${getMarginSpacing('xs')}`} />
                Logs
              </TabsTrigger>
              <TabsTrigger
                value="errors"
                className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 border-white rounded-none"
              >
                <AlertTriangle className={`w-4 h-4 ${getMarginSpacing('xs')}`} />
                Errors
              </TabsTrigger>
            </TabsList>
            <TabsContent value="diff" className={`flex-1 overflow-y-auto ${getPaddingSpacing('md')}`}>
              <DiffViewer xmlData={convertTaskDataToXml(versionData)} />
            </TabsContent>
            <TabsContent value="logs" className={`flex-1 overflow-y-auto ${getPaddingSpacing('md')} ${commonTypographyCombinations.codeInline} text-sm`}>
              {renderLogsContent()}
            </TabsContent>
            <TabsContent value="errors" className={`flex-1 overflow-y-auto ${getPaddingSpacing('md')}`}>
              {renderErrorsContent()}
            </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}