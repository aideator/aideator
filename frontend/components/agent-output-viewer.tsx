"use client"

import { useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Wifi, WifiOff, RotateCcw, Trash2, Terminal } from 'lucide-react'
import { useAgentOutputs, type AgentOutput, type ConnectionStatus } from '@/hooks/use-agent-outputs'
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
} as const

function ConnectionStatusIndicator({ status }: { status: ConnectionStatus }) {
  const statusConfig = {
    connecting: { icon: Wifi, color: 'text-yellow-500', label: 'Connecting...' },
    connected: { icon: Wifi, color: 'text-green-500', label: 'Connected' },
    disconnected: { icon: WifiOff, color: 'text-gray-500', label: 'Disconnected' },
    error: { icon: WifiOff, color: 'text-red-500', label: 'Connection Error' },
  }

  const config = statusConfig[status]
  const IconComponent = config.icon

  return (
    <div className="flex items-center gap-2 text-sm">
      <IconComponent className={cn('h-4 w-4', config.color)} />
      <span className={config.color}>{config.label}</span>
    </div>
  )
}

function OutputLine({ output }: { output: AgentOutput }) {
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

function VariationPanel({ variationId, outputs }: { variationId: number; outputs: AgentOutput[] }) {
  const agentColorClass = agentColors[variationId as keyof typeof agentColors] || agentColors[0]
  
  const outputCounts = outputs.reduce((acc, output) => {
    acc[output.output_type] = (acc[output.output_type] || 0) + 1
    return acc
  }, {} as Record<string, number>)

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
        <ScrollArea className="h-[500px]">
          {outputs.length === 0 ? (
            <div className="flex items-center justify-center h-32 text-gray-500">
              <Terminal className="h-8 w-8 mr-2" />
              <span>No outputs yet...</span>
            </div>
          ) : (
            <div className="space-y-0">
              {outputs.map((output, index) => (
                <OutputLine key={`${output.id}-${index}`} output={output} />
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  )
}

interface AgentOutputViewerProps {
  runId: string
  maxVariations?: number
}

export function AgentOutputViewer({ runId, maxVariations = 6 }: AgentOutputViewerProps) {
  const { outputs, connectionStatus, reconnect, clearOutputs, getOutputsByVariation } = useAgentOutputs(runId)
  
  // Get unique variation IDs
  const variationIds = Array.from(new Set(outputs.map(o => o.variation_id))).sort((a, b) => a - b)
  const displayVariations = variationIds.slice(0, maxVariations)

  return (
    <div className="space-y-4">
      {/* Header with connection status and controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold">Agent Outputs</h2>
          <ConnectionStatusIndicator status={connectionStatus} />
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={reconnect}
            disabled={connectionStatus === 'connecting'}
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            Reconnect
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={clearOutputs}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Clear
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
              <p className="text-sm">Run ID: {runId}</p>
            </div>
          </CardContent>
        </Card>
      ) : displayVariations.length === 1 ? (
        // Single variation - full width
        <VariationPanel 
          variationId={displayVariations[0]} 
          outputs={getOutputsByVariation(displayVariations[0])} 
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
                  {getOutputsByVariation(variationId).length}
                </Badge>
              </TabsTrigger>
            ))}
          </TabsList>
          
          {displayVariations.map(variationId => (
            <TabsContent key={variationId} value={variationId.toString()}>
              <VariationPanel 
                variationId={variationId} 
                outputs={getOutputsByVariation(variationId)} 
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
              <span className="ml-2 font-medium">{outputs.length}</span>
            </div>
            <div>
              <span className="text-gray-500">Active Variations:</span>
              <span className="ml-2 font-medium">{variationIds.length}</span>
            </div>
            <div>
              <span className="text-gray-500">Connection:</span>
              <span className="ml-2 font-medium capitalize">{connectionStatus}</span>
            </div>
            <div>
              <span className="text-gray-500">Run ID:</span>
              <span className="ml-2 font-mono text-xs">{runId}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}