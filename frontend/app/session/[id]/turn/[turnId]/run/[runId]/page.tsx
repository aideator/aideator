"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ArrowLeft, Play, Square, Clock, DollarSign, Users, Terminal, FileText, Zap, Bug } from "lucide-react"
import Link from "next/link"
import { apiClient, WebSocketClient } from "@/lib/api"
import { Session, Turn, Run, AgentOutput } from "@/lib/types"
import { useAuthenticatedWebSocket } from "@/lib/api"
import { DebugWindow } from "@/components/debug-window"

export default function RunPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string
  const turnId = params.turnId as string
  const runId = params.runId as string
  
  // Get authenticated WebSocket client
  const { createWebSocketClient } = useAuthenticatedWebSocket('ws://localhost:8000')

  // State management
  const [session, setSession] = useState<Session | null>(null)
  const [turn, setTurn] = useState<Turn | null>(null)
  const [run, setRun] = useState<Run | null>(null)
  const [outputs, setOutputs] = useState<AgentOutput[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [wsClient, setWsClient] = useState<WebSocketClient | null>(null)
  const [showSystemDebug, setShowSystemDebug] = useState(false)
  const messageIdCounter = useRef(0)
  const seenMessageIds = useRef(new Set<string>())
  
  // Ref for auto-scrolling
  const outputsEndRef = useRef<HTMLDivElement>(null)

  // Load data on mount
  useEffect(() => {
    if (sessionId && turnId && runId) {
      loadRunData()
    }
  }, [sessionId, turnId, runId])

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsClient) {
        wsClient.close()
      }
    }
  }, [])

  // Auto-start streaming when run data is loaded
  useEffect(() => {
    if (run && (run.status === 'running' || run.status === 'pending') && !wsClient) {
      startWebSocketConnection()
    }
  }, [run, wsClient, startWebSocketConnection])
  
  // Auto-scroll to bottom when new outputs arrive
  useEffect(() => {
    if (outputsEndRef.current) {
      outputsEndRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [outputs])

  const loadRunData = async () => {
    try {
      setIsLoading(true)
      const [sessionResponse, turnResponse, runResponse] = await Promise.all([
        apiClient.getSession(sessionId),
        apiClient.getTurn(sessionId, turnId),
        apiClient.getRun(runId),
      ])
      setSession(sessionResponse)
      setTurn(turnResponse)
      setRun(runResponse)
      setError(null)
    } catch (err) {
      console.error('Failed to load run data:', err)
      setError('Failed to load run data')
    } finally {
      setIsLoading(false)
    }
  }

  const startWebSocketConnection = useCallback(() => {
    try {
      // Close existing connection if any
      if (wsClient) {
        wsClient.close()
        setWsClient(null)
        setIsStreaming(false)
      }
      
      // Clear seen message IDs for fresh start
      seenMessageIds.current.clear()
      
      const wsUrl = `ws://localhost:8000/api/v1/ws/runs/${runId}`
      const client = createWebSocketClient(wsUrl)
      client.connect({
        onMessage: (message) => {
          // Handle incoming WebSocket messages
          // Only accept LLM output messages, not stdout/stderr which contain logging
          if (message.type === "llm") {
            // Generate or use existing message ID
            const messageId = message.message_id || `msg-${Date.now()}-${Math.random()}`
            
            // Skip if we've already processed this message
            if (seenMessageIds.current.has(messageId)) {
              console.log('Skipping duplicate message:', messageId)
              return
            }
            seenMessageIds.current.add(messageId)
            
            const newOutput: AgentOutput = {
              id: `${messageId}-${message.data.variation_id}-${messageIdCounter.current++}`,
              run_id: runId,
              variation_id: parseInt(message.data.variation_id) || 1,
              content: message.data.content || "",
              timestamp: message.data.timestamp,
              output_type: message.type,
            }
            setOutputs(prev => [...prev, newOutput])
          }
        },
        onError: (error) => {
          console.error('WebSocket error:', error)
          setIsStreaming(false)
        },
        onClose: () => {
          setIsStreaming(false)
        }
      })
      setWsClient(client)
      setIsStreaming(true)
    } catch (err) {
      console.error('Failed to start WebSocket connection:', err)
    }
  }, [wsClient, createWebSocketClient, runId, messageIdCounter, seenMessageIds])


  const stopWebSocketConnection = () => {
    if (wsClient) {
      wsClient.close()
      setWsClient(null)
      setIsStreaming(false)
    }
  }

  const handleCancelRun = async () => {
    try {
      if (wsClient) {
        wsClient.sendControl("cancel")
      }
      // Refresh run status
      await loadRunData()
    } catch (err) {
      console.error('Failed to cancel run:', err)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "default"
      case "failed":
        return "destructive"
      case "running":
        return "secondary"
      default:
        return "outline"
    }
  }

  const getProgress = () => {
    if (!run) return 0
    switch (run.status) {
      case "completed":
        return 100
      case "failed":
        return 0
      case "running":
        return 50 // Approximate progress
      default:
        return 0
    }
  }


  const getOutputIcon = (type: string) => {
    switch (type) {
      case "llm":
        return <Zap className="w-4 h-4 text-blue-400" />
      case "stdout":
        return <Terminal className="w-4 h-4 text-green-400" />
      case "stderr":
        return <Terminal className="w-4 h-4 text-red-400" />
      default:
        return <FileText className="w-4 h-4 text-gray-400" />
    }
  }

  const getOutputBgColor = (type: string) => {
    switch (type) {
      case "llm":
        return "bg-blue-900/20 border-blue-800"
      case "stdout":
        return "bg-green-900/20 border-green-800"
      case "stderr":
        return "bg-red-900/20 border-red-800"
      default:
        return "bg-gray-900/20 border-gray-800"
    }
  }

  if (isLoading) {
    return (
      <div className="bg-gray-950 text-gray-50 min-h-screen">
        <div className="container mx-auto max-w-6xl py-8">
          <div className="flex items-center justify-center py-20">
            <div className="animate-pulse">Loading run...</div>
          </div>
        </div>
      </div>
    )
  }

  if (error || !session || !turn || !run) {
    return (
      <div className="bg-gray-950 text-gray-50 min-h-screen">
        <div className="container mx-auto max-w-6xl py-8">
          <div className="text-center py-20">
            <p className="text-red-400 mb-4">{error || 'Run not found'}</p>
            <Button onClick={() => router.push(`/session/${sessionId}/turn/${turnId}`)} variant="outline">
              Back to Turn
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="bg-gray-950 text-gray-50 min-h-screen">
        <div className="container mx-auto max-w-6xl py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push(`/session/${sessionId}/turn/${turnId}`)}
            className="text-gray-400 hover:text-gray-200"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1 text-sm">
              <Link href={`/session/${sessionId}`} className="text-gray-400 hover:text-gray-200">
                {session.title}
              </Link>
              <span className="text-gray-600">/</span>
              <Link href={`/session/${sessionId}/turn/${turnId}`} className="text-gray-400 hover:text-gray-200">
                Turn {turn.turn_number}
              </Link>
              <span className="text-gray-600">/</span>
              <span className="text-gray-300">Run</span>
            </div>
            <h1 className="text-2xl font-semibold">Run Details</h1>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={getStatusColor(run.status) as any}>
              {run.status}
            </Badge>
            {run.winning_variation_id && (
              <Badge variant="default" className="bg-green-600">
                Winner: Variation {run.winning_variation_id}
              </Badge>
            )}
          </div>
        </div>


        <Tabs defaultValue="variation-1" className="w-full">
          <div className="flex items-center justify-between mb-4">
            <TabsList className="bg-gray-900/50 border border-gray-800">
              {Array.from({ length: run.variations }, (_, i) => i + 1).map((variation) => (
                <TabsTrigger key={variation} value={`variation-${variation}`}>
                  Model {variation}
                </TabsTrigger>
              ))}
              <TabsTrigger value="results">Results</TabsTrigger>
              <TabsTrigger value="config">Configuration</TabsTrigger>
            </TabsList>
            
            <div className="flex items-center gap-2">
              {process.env.NODE_ENV === 'development' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowSystemDebug(!showSystemDebug)}
                  className="gap-2"
                >
                  <Terminal className="w-4 h-4" />
                  System Debug
                </Button>
              )}
            </div>
          </div>

          {Array.from({ length: run.variations }, (_, i) => i + 1).map((variation) => (
            <TabsContent key={variation} value={`variation-${variation}`} className="space-y-4">
              <div className="bg-gray-900/30 border border-gray-800 rounded-lg">
                <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                  <h3 className="font-medium">Model {variation} Output</h3>
                  <div className="flex items-center gap-2">
                    {isStreaming && (
                      <div className="flex items-center gap-2 text-sm text-green-400">
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                        Live
                      </div>
                    )}
                    <Badge variant="outline" className="text-xs">
                      {outputs.filter(o => o.variation_id === variation).length} messages
                    </Badge>
                  </div>
                </div>
                
                <div className="max-h-[600px] overflow-y-auto p-4 bg-gray-950 rounded font-mono text-sm">
                  {outputs.filter(o => o.variation_id === variation).length === 0 ? (
                    <div className="text-center py-8 text-gray-400">
                      {run.status === "pending" ? "Waiting for run to start..." : "No output yet"}
                    </div>
                  ) : (
                    <div className="space-y-0.5">
                      {outputs
                        .filter(o => o.variation_id === variation)
                        .map((output) => {
                          // Only showing LLM output now
                          return (
                            <div key={output.id} className="text-green-400">
                              {output.content}
                            </div>
                          );
                        })}
                    </div>
                  )}
                  <div ref={outputsEndRef} />
                </div>
              </div>
            </TabsContent>
          ))}

          <TabsContent value="results" className="space-y-4">
            <div className="bg-gray-900/30 border border-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-medium mb-4">Run Results</h3>
              {Object.keys(run.results || {}).length === 0 ? (
                <p className="text-gray-400">No results available yet.</p>
              ) : (
                <pre className="text-sm bg-gray-950 p-4 rounded border border-gray-800 overflow-x-auto">
                  {JSON.stringify(run.results, null, 2)}
                </pre>
              )}
            </div>
          </TabsContent>

          <TabsContent value="config" className="space-y-4">
            <div className="bg-gray-900/30 border border-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-medium mb-4">Agent Configuration</h3>
              <pre className="text-sm bg-gray-950 p-4 rounded border border-gray-800 overflow-x-auto">
                {JSON.stringify(run.agent_config, null, 2)}
              </pre>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
    
    {run && (
      <DebugWindow 
        runId={runId} 
        isOpen={showSystemDebug} 
        onClose={() => setShowSystemDebug(false)} 
      />
    )}
    </>
  )
}