"use client"

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { RefreshCw, Trash2, Terminal, AlertCircle } from 'lucide-react'
import { useAgentLogs, type AgentLog } from '@/hooks/use-agent-logs'
import { cn } from '@/lib/utils'

// Agent color system for visual differentiation
const agentColors = {
  0: 'border-cyan-500/20 bg-cyan-50 dark:bg-cyan-950/20',
  1: 'border-violet-500/20 bg-violet-50 dark:bg-violet-950/20',
  2: 'border-amber-500/20 bg-amber-50 dark:bg-amber-950/20',
  3: 'border-rose-500/20 bg-rose-50 dark:bg-rose-950/20',
  4: 'border-emerald-500/20 bg-emerald-50 dark:bg-emerald-950/20',
  5: 'border-indigo-500/20 bg-indigo-50 dark:bg-indigo-950/20',
} as const

const outputTypeColors = {
  stdout: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
  stderr: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  status: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  summary: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  logging: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  diffs: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
  addinfo: 'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-300',
  job_data: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300',
  error: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  // New output types
  assistant_response: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300',
  system_status: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  debug_info: 'bg-gray-100 text-gray-600 dark:bg-gray-800/50 dark:text-gray-400',
} as const

function LoadingStatusIndicator({ isLoading, error }: { isLoading: boolean; error: string | null }) {
  if (error) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <AlertCircle className="h-4 w-4 text-red-500" />
        <span className="text-red-500">Error: {error}</span>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />
        <span className="text-blue-500">Loading...</span>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2 text-sm">
      <RefreshCw className="h-4 w-4 text-green-500" />
      <span className="text-green-500">Polling active</span>
    </div>
  )
}

function OutputLine({ output }: { output: AgentLog }) {
  const typeColor = outputTypeColors[output.output_type] || outputTypeColors.stdout
  const timestamp = new Date(output.timestamp).toLocaleTimeString()

  return (
    <div className="flex items-start gap-3 py-2 px-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800">
      <div className="flex items-center gap-2 min-w-0 flex-1">
        <Badge variant="outline" className={cn('text-xs font-mono', typeColor)}>
          {output.output_type}
        </Badge>
        <span className="text-xs text-gray-500 font-mono">{timestamp}</span>
        <pre className="text-sm font-mono whitespace-pre-wrap break-words min-w-0 flex-1">
          {output.content}
        </pre>
      </div>
    </div>
  )
}

function VariationPanel({ variationId, outputs }: { variationId: number; outputs: AgentLog[] }) {
  const agentColorClass = agentColors[variationId as keyof typeof agentColors] || agentColors[0]
  
  const outputCounts = outputs.reduce((acc, output) => {
    acc[output.output_type] = (acc[output.output_type] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  // Filter outputs by type for different tabs
  const assistantOutputs = outputs.filter(o => o.output_type === 'assistant_response')
  const systemOutputs = outputs.filter(o => o.output_type === 'system_status')
  const debugOutputs = outputs.filter(o => o.output_type === 'debug_info')
  const errorOutputs = outputs.filter(o => o.output_type === 'error')
  const diffOutputs = outputs.filter(o => o.output_type === 'diffs')
  const legacyOutputs = outputs.filter(o => !['assistant_response', 'system_status', 'debug_info', 'error', 'diffs'].includes(o.output_type))

  return (
    <Card className={cn('h-full', agentColorClass)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">
            Agent {variationId}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-xs">
              {outputs.length} outputs
            </Badge>
            {Object.entries(outputCounts).map(([type, count]) => (
              <Badge 
                key={type} 
                variant="outline" 
                className={cn('text-xs', outputTypeColors[type as keyof typeof outputTypeColors])}
              >
                {type}: {count}
              </Badge>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <Tabs defaultValue="conversation" className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="conversation" className="text-xs">
              Conversation
              {assistantOutputs.length > 0 && (
                <Badge variant="secondary" className="ml-1 text-xs">
                  {assistantOutputs.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="system" className="text-xs">
              System
              {systemOutputs.length > 0 && (
                <Badge variant="secondary" className="ml-1 text-xs">
                  {systemOutputs.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="debug" className="text-xs">
              Debug
              {debugOutputs.length > 0 && (
                <Badge variant="secondary" className="ml-1 text-xs">
                  {debugOutputs.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="errors" className="text-xs">
              Errors
              {errorOutputs.length > 0 && (
                <Badge variant="secondary" className="ml-1 text-xs">
                  {errorOutputs.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="diffs" className="text-xs">
              Diffs
              {diffOutputs.length > 0 && (
                <Badge variant="secondary" className="ml-1 text-xs">
                  {diffOutputs.length}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="conversation">
            <ScrollArea className="h-[500px]">
              {assistantOutputs.length === 0 ? (
                <div className="flex items-center justify-center h-32 text-gray-500">
                  <Terminal className="h-8 w-8 mr-2" />
                  <span>No conversation outputs yet...</span>
                </div>
              ) : (
                <div className="space-y-0">
                  {assistantOutputs.map((output, index) => (
                    <OutputLine key={`${output.id}-${index}`} output={output} />
                  ))}
                </div>
              )}
            </ScrollArea>
          </TabsContent>
          
          <TabsContent value="system">
            <ScrollArea className="h-[500px]">
              {systemOutputs.length === 0 ? (
                <div className="flex items-center justify-center h-32 text-gray-500">
                  <Terminal className="h-8 w-8 mr-2" />
                  <span>No system outputs yet...</span>
                </div>
              ) : (
                <div className="space-y-0">
                  {systemOutputs.map((output, index) => (
                    <OutputLine key={`${output.id}-${index}`} output={output} />
                  ))}
                </div>
              )}
            </ScrollArea>
          </TabsContent>
          
          <TabsContent value="debug">
            <ScrollArea className="h-[500px]">
              {debugOutputs.length === 0 ? (
                <div className="flex items-center justify-center h-32 text-gray-500">
                  <Terminal className="h-8 w-8 mr-2" />
                  <span>No debug outputs yet...</span>
                </div>
              ) : (
                <div className="space-y-0">
                  {debugOutputs.map((output, index) => (
                    <OutputLine key={`${output.id}-${index}`} output={output} />
                  ))}
                </div>
              )}
            </ScrollArea>
          </TabsContent>
          
          <TabsContent value="errors">
            <ScrollArea className="h-[500px]">
              {errorOutputs.length === 0 ? (
                <div className="flex items-center justify-center h-32 text-gray-500">
                  <Terminal className="h-8 w-8 mr-2" />
                  <span>No error outputs yet...</span>
                </div>
              ) : (
                <div className="space-y-0">
                  {errorOutputs.map((output, index) => (
                    <OutputLine key={`${output.id}-${index}`} output={output} />
                  ))}
                </div>
              )}
            </ScrollArea>
          </TabsContent>
          
          <TabsContent value="diffs">
            <ScrollArea className="h-[500px]">
              {diffOutputs.length === 0 ? (
                <div className="flex items-center justify-center h-32 text-gray-500">
                  <Terminal className="h-8 w-8 mr-2" />
                  <span>No diff outputs yet...</span>
                </div>
              ) : (
                <div className="space-y-0">
                  {diffOutputs.map((output, index) => (
                    <OutputLine key={`${output.id}-${index}`} output={output} />
                  ))}
                </div>
              )}
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}

interface AgentOutputViewerProps {
  runId: string
  maxVariations?: number
}

export function AgentOutputViewer({ runId, maxVariations = 6 }: AgentOutputViewerProps) {
  const { logs, isLoading, error, refetch, getLogsByVariation } = useAgentLogs(runId)
  
  // Get unique variation IDs
  const variationIds = Array.from(new Set(logs.map(o => o.variation_id))).sort((a, b) => a - b)
  const displayVariations = variationIds.slice(0, maxVariations)

  return (
    <div className="space-y-4">
      {/* Header with status and controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold">Agent Outputs</h2>
          <LoadingStatusIndicator isLoading={isLoading} error={error} />
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={refetch}
            disabled={isLoading}
          >
            <RefreshCw className={cn('h-4 w-4 mr-2', isLoading && 'animate-spin')} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Agent variations display */}
      {displayVariations.length === 0 ? (
        <Card>
          <CardContent className="flex items-center justify-center h-32">
            <div className="text-center text-gray-500">
              <Terminal className="h-8 w-8 mx-auto mb-2" />
              <p>Waiting for agent outputs...</p>
              <p className="text-sm">Task ID: {runId}</p>
            </div>
          </CardContent>
        </Card>
      ) : displayVariations.length === 1 ? (
        // Single variation - full width
        <VariationPanel 
          variationId={displayVariations[0]} 
          outputs={getLogsByVariation(displayVariations[0])} 
        />
      ) : (
        // Multiple variations - use tabs for space efficiency
        <Tabs defaultValue={displayVariations[0].toString()} className="w-full">
          <TabsList className="grid w-full grid-cols-6 max-w-2xl">
            {displayVariations.map(variationId => (
              <TabsTrigger 
                key={variationId} 
                value={variationId.toString()}
                className="text-sm"
              >
                Agent {variationId}
                <Badge variant="secondary" className="ml-2 text-xs">
                  {getLogsByVariation(variationId).length}
                </Badge>
              </TabsTrigger>
            ))}
          </TabsList>
          
          {displayVariations.map(variationId => (
            <TabsContent key={variationId} value={variationId.toString()}>
              <VariationPanel 
                variationId={variationId} 
                outputs={getLogsByVariation(variationId)} 
              />
            </TabsContent>
          ))}
        </Tabs>
      )}

      {/* Summary stats */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Total Outputs:</span>
              <span className="ml-2 font-medium">{logs.length}</span>
            </div>
            <div>
              <span className="text-gray-500">Active Variations:</span>
              <span className="ml-2 font-medium">{variationIds.length}</span>
            </div>
            <div>
              <span className="text-gray-500">Status:</span>
              <span className="ml-2 font-medium capitalize">
                {error ? 'Error' : isLoading ? 'Loading' : 'Active'}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Task ID:</span>
              <span className="ml-2 font-mono text-xs">{runId}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}