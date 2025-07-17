"use client"

import { useEffect, useRef } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { RefreshCw, Trash2, Terminal, AlertCircle } from 'lucide-react'
import { useAgentLogs, type AgentLog } from '@/hooks/use-agent-logs'
import { cn } from '@/lib/utils'
import { 
  getAgentColorClasses, 
  getOutputTypeColorClasses,
  getBodyClasses,
  getStatusColorClasses,
  commonTypographyCombinations,
  componentTokens,
  getPaddingSpacing,
  getGapSpacing
} from '@/lib/design-tokens'

// THIS IS THE TOKEN SYSTEM VERSION
// Agent colors and output type colors are provided by the design token system
// This ensures consistent colors across the application and easier maintenance

function LoadingStatusIndicator({ isLoading, error }: { isLoading: boolean; error: string | null }) {
  if (error) {
    return (
      <div className={`flex items-center ${getGapSpacing('sm')} text-sm`}>
        <AlertCircle className={`h-4 w-4 ${getStatusColorClasses('failed')}`} />
        <span className={getStatusColorClasses('failed')}>Error: {error}</span>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className={`flex items-center ${getGapSpacing('sm')} text-sm`}>
        <RefreshCw className={`h-4 w-4 ${getStatusColorClasses('pending')} animate-spin`} />
        <span className={getStatusColorClasses('pending')}>Loading...</span>
      </div>
    )
  }

  return (
    <div className={`flex items-center ${getGapSpacing('sm')} text-sm`}>
      <RefreshCw className={`h-4 w-4 ${getStatusColorClasses('success')}`} />
      <span className={getStatusColorClasses('success')}>Polling active</span>
    </div>
  )
}

function OutputLine({ output }: { output: AgentLog }) {
  const typeColor = getOutputTypeColorClasses(output.output_type)
  const timestamp = new Date(output.timestamp).toLocaleTimeString()

  return (
    <div className={`flex items-start ${getGapSpacing('sm')} ${getPaddingSpacing('sm')} hover:bg-gray-50 dark:hover:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800`}>
      <div className="flex items-center gap-2 min-w-0 flex-1">
        <Badge variant="outline" className={cn('text-xs font-mono', typeColor)}>
          {output.output_type}
        </Badge>
        <span className={`text-xs ${getBodyClasses('detail')} font-mono`}>{timestamp}</span>
        <pre className={`text-sm font-mono whitespace-pre-wrap break-words min-w-0 flex-1 ${getBodyClasses('primary')}`}>
          {output.content}
        </pre>
      </div>
    </div>
  )
}

function VariationPanel({ variationId, outputs }: { variationId: number; outputs: AgentLog[] }) {
  const agentColorClass = getAgentColorClasses(variationId)
  const scrollAreaRefs = useRef<{ [key: string]: HTMLDivElement | null }>({})
  
  // Auto-scroll to bottom when new outputs arrive
  useEffect(() => {
    Object.values(scrollAreaRefs.current).forEach(ref => {
      if (ref) {
        ref.scrollTop = ref.scrollHeight
      }
    })
  }, [outputs])
  
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
      <CardHeader className={getPaddingSpacing('card')}>
        <div className="flex items-center justify-between">
          <CardTitle className={`text-sm font-medium ${getBodyClasses('primary')}`}>
            Agent {variationId} (Token System)
          </CardTitle>
          <div className={`flex items-center ${getGapSpacing('sm')}`}>
            <Badge variant="secondary" className="text-xs">
              {outputs.length} outputs
            </Badge>
            {Object.entries(outputCounts).map(([type, count]) => (
              <Badge 
                key={type} 
                variant="outline" 
                className={cn('text-xs', getOutputTypeColorClasses(type))}
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
            <ScrollArea 
              className="h-[500px]"
              ref={(el) => { scrollAreaRefs.current['conversation'] = el }}
            >
              {assistantOutputs.length === 0 ? (
                <div className={`flex items-center justify-center h-32 ${getBodyClasses('muted')}`}>
                  <Terminal className={`h-8 w-8 mr-2 ${getBodyClasses('muted')}`} />
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
            <ScrollArea 
              className="h-[500px]"
              ref={(el) => { scrollAreaRefs.current['system'] = el }}
            >
              {systemOutputs.length === 0 ? (
                <div className={`flex items-center justify-center h-32 ${getBodyClasses('muted')}`}>
                  <Terminal className={`h-8 w-8 mr-2 ${getBodyClasses('muted')}`} />
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
            <ScrollArea 
              className="h-[500px]"
              ref={(el) => { scrollAreaRefs.current['debug'] = el }}
            >
              {debugOutputs.length === 0 ? (
                <div className={`flex items-center justify-center h-32 ${getBodyClasses('muted')}`}>
                  <Terminal className={`h-8 w-8 mr-2 ${getBodyClasses('muted')}`} />
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
            <ScrollArea 
              className="h-[500px]"
              ref={(el) => { scrollAreaRefs.current['errors'] = el }}
            >
              {errorOutputs.length === 0 ? (
                <div className={`flex items-center justify-center h-32 ${getBodyClasses('muted')}`}>
                  <Terminal className={`h-8 w-8 mr-2 ${getBodyClasses('muted')}`} />
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
            <ScrollArea 
              className="h-[500px]"
              ref={(el) => { scrollAreaRefs.current['diffs'] = el }}
            >
              {diffOutputs.length === 0 ? (
                <div className={`flex items-center justify-center h-32 ${getBodyClasses('muted')}`}>
                  <Terminal className={`h-8 w-8 mr-2 ${getBodyClasses('muted')}`} />
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

interface AgentOutputViewerTokensProps {
  taskId: string
  maxVariations?: number
}

export function AgentOutputViewerTokens({ taskId, maxVariations = 6 }: AgentOutputViewerTokensProps) {
  const { logs, isLoading, error, refetch, getLogsByVariation } = useAgentLogs(taskId)
  
  // Get unique variation IDs
  const variationIds = Array.from(new Set(logs.map(o => o.variation_id))).sort((a, b) => a - b)
  const displayVariations = variationIds.slice(0, maxVariations)

  return (
    <div className="space-y-4">
      {/* Header with status and controls */}
      <div className="flex items-center justify-between">
        <div className={`flex items-center ${getGapSpacing('md')}`}>
          <h2 className={`text-lg font-semibold ${getBodyClasses('primary')}`}>Agent Outputs (Token System)</h2>
          <LoadingStatusIndicator isLoading={isLoading} error={error} />
        </div>
        <div className={`flex items-center ${getGapSpacing('sm')}`}>
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

      {/* Color System Display */}
      <div className={componentTokens.ui.card.secondary}>
        <h3 className={`${commonTypographyCombinations.cardTitle} mb-4`}>
          Active Token System Colors
        </h3>
        <div className={`grid grid-cols-2 ${getGapSpacing('md')}`}>
          <div>
            <h4 className={`text-sm font-medium ${getBodyClasses('secondary')} mb-2`}>Agent Colors</h4>
            <div className={`space-y-1 ${getGapSpacing('xs')}`}>
              {[1, 2, 3, 4, 5, 6].map(agentId => (
                <div key={agentId} className={`${getAgentColorClasses(agentId)} ${getPaddingSpacing('xs')} rounded text-xs`}>
                  Agent {agentId}: {getAgentColorClasses(agentId)}
                </div>
              ))}
            </div>
          </div>
          <div>
            <h4 className={`text-sm font-medium ${getBodyClasses('secondary')} mb-2`}>Output Type Colors</h4>
            <div className={`space-y-1 ${getGapSpacing('xs')}`}>
              {['assistant_response', 'system_status', 'debug_info', 'error', 'diffs'].map(type => (
                <div key={type} className={`${getOutputTypeColorClasses(type)} ${getPaddingSpacing('xs')} rounded text-xs border`}>
                  {type}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Agent variations display */}
      {displayVariations.length === 0 ? (
        <Card>
          <CardContent className={`flex items-center justify-center h-32 ${componentTokens.ui.card.primary}`}>
            <div className={`text-center ${getBodyClasses('muted')}`}>
              <Terminal className={`h-8 w-8 mx-auto mb-2 ${getBodyClasses('muted')}`} />
              <p>Waiting for agent outputs...</p>
              <p className={`text-sm ${commonTypographyCombinations.codeInline}`}>Task ID: {taskId}</p>
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
        <CardContent className={getPaddingSpacing('card')}>
          <div className={`grid grid-cols-2 md:grid-cols-4 ${getGapSpacing('md')} text-sm`}>
            <div>
              <span className={getBodyClasses('secondary')}>Total Outputs:</span>
              <span className={`ml-2 font-medium ${getBodyClasses('primary')}`}>{logs.length}</span>
            </div>
            <div>
              <span className={getBodyClasses('secondary')}>Active Variations:</span>
              <span className={`ml-2 font-medium ${getBodyClasses('primary')}`}>{variationIds.length}</span>
            </div>
            <div>
              <span className={getBodyClasses('secondary')}>Status:</span>
              <span className={`ml-2 font-medium capitalize ${getBodyClasses('primary')}`}>
                {error ? 'Error' : isLoading ? 'Loading' : 'Active'}
              </span>
            </div>
            <div>
              <span className={getBodyClasses('secondary')}>Task ID:</span>
              <span className={`ml-2 ${commonTypographyCombinations.codeInline} text-xs`}>{taskId}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}