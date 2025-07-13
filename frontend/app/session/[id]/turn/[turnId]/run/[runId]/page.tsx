"use client"

import { useState, useEffect, useRef } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ArrowLeft, Play, Square, Clock, DollarSign, Users, Terminal, FileText, Zap, Bug } from "lucide-react"
import Link from "next/link"
import { apiClient, WebSocketClient } from "@/lib/api"
import { Session, Turn, Run, AgentOutput } from "@/lib/types"

export default function RunPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string
  const turnId = params.turnId as string
  const runId = params.runId as string

  const [session, setSession] = useState<Session | null>(null)
  const [turn, setTurn] = useState<Turn | null>(null)
  const [run, setRun] = useState<Run | null>(null)
  const [outputs, setOutputs] = useState<AgentOutput[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [wsClient, setWsClient] = useState<WebSocketClient | null>(null)
  const [debugWsClient, setDebugWsClient] = useState<WebSocketClient | null>(null)
  const [debugOutputs, setDebugOutputs] = useState<AgentOutput[]>([])
  const [showDebugView, setShowDebugView] = useState(false)

  const outputsEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (sessionId && turnId && runId) {
      loadRunData()
    }
  }, [sessionId, turnId, runId])

  useEffect(() => {
    // Auto-scroll to bottom when new outputs arrive
    if (outputsEndRef.current) {
      outputsEndRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [outputs])

  const loadRunData = async () => {
    try {
      setIsLoading(true)
      const [sessionResponse, turnResponse, runResponse, outputsResponse] = await Promise.all([
        apiClient.getSession(sessionId),
        apiClient.getTurn(sessionId, turnId),
        apiClient.getRun(runId),
        apiClient.getRunOutputs(runId, {}),
      ])
      setSession(sessionResponse)
      setTurn(turnResponse)
      setRun(runResponse)
      setOutputs(outputsResponse)
      setError(null)

      // If run is still active, start WebSocket connections
      if (runResponse.status === "running") {
        startWebSocketConnection()
        startDebugWebSocketConnection()
      }
    } catch (err) {
      console.error('Failed to load run data:', err)
      setError('Failed to load run data')
    } finally {
      setIsLoading(false)
    }
  }

  const startWebSocketConnection = () => {
    try {
      const apiKey = apiClient.getApiKey()
      const wsUrl = `ws://localhost:8000/ws/runs/${runId}${apiKey ? `?api_key=${apiKey}` : ''}`
      const client = new WebSocketClient(wsUrl)
      client.connect({
        onMessage: (message) => {
          // Handle incoming WebSocket messages for parsed/clean output
          if (message.type === "llm" || message.type === "stdout" || message.type === "stderr") {
            const newOutput: AgentOutput = {
              id: Date.now() + Math.random(), // Temporary ID
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
  }

  const startDebugWebSocketConnection = () => {
    try {
      const apiKey = apiClient.getApiKey()
      const debugWsUrl = `ws://localhost:8000/ws/runs/${runId}/debug${apiKey ? `?api_key=${apiKey}` : ''}`
      const debugClient = new WebSocketClient(debugWsUrl)
      debugClient.connect({
        onMessage: (message) => {
          // Handle debug messages (raw logs)
          if (message.type === "stdout") {
            const newOutput: AgentOutput = {
              id: Date.now() + Math.random(), // Temporary ID
              run_id: runId,
              variation_id: parseInt(message.data.variation_id) || 1,
              content: message.data.content || "",
              timestamp: message.data.timestamp,
              output_type: "stdout",
            }
            setDebugOutputs(prev => [...prev, newOutput])
          }
        },
        onError: (error) => {
          console.error('Debug WebSocket error:', error)
        },
        onClose: () => {
          console.log('Debug WebSocket closed')
        }
      })
      setDebugWsClient(debugClient)
    } catch (err) {
      console.error('Failed to start debug WebSocket connection:', err)
    }
  }

  const stopWebSocketConnection = () => {
    if (wsClient) {
      wsClient.close()
      setWsClient(null)
      setIsStreaming(false)
    }
    if (debugWsClient) {
      debugWsClient.close()
      setDebugWsClient(null)
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

        {/* Run Status and Controls */}
        <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className="text-sm">
                <div className="text-gray-400">Status</div>
                <div className="text-lg font-medium">{run.status}</div>
              </div>
              <div className="w-64">
                <Progress value={getProgress()} className="h-2" />
              </div>
            </div>
            <div className="flex items-center gap-2">
              {run.status === "running" && (
                <>
                  {isStreaming ? (
                    <Button onClick={stopWebSocketConnection} variant="outline" size="sm">
                      <Square className="w-4 h-4 mr-2" />
                      Stop Streaming
                    </Button>
                  ) : (
                    <Button onClick={startWebSocketConnection} variant="outline" size="sm">
                      <Play className="w-4 h-4 mr-2" />
                      Start Streaming
                    </Button>
                  )}
                  <Button onClick={handleCancelRun} variant="destructive" size="sm">
                    Cancel Run
                  </Button>
                </>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-gray-400" />
              <div className="text-sm">
                <div className="text-gray-400">Created</div>
                <div>{new Date(run.created_at).toLocaleString()}</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-gray-400" />
              <div className="text-sm">
                <div className="text-gray-400">Variations</div>
                <div>{run.variations}</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-gray-400" />
              <div className="text-sm">
                <div className="text-gray-400">Cost</div>
                <div>${run.total_cost_usd?.toFixed(3) || '0.000'}</div>
              </div>
            </div>
            <div className="text-sm">
              <div className="text-gray-400">Tokens</div>
              <div>{run.total_tokens_used?.toLocaleString() || '0'}</div>
            </div>
          </div>

          {run.github_url && (
            <div className="mt-4 pt-4 border-t border-gray-800">
              <div className="text-sm text-gray-400 mb-1">Repository</div>
              <a
                href={run.github_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 text-sm"
              >
                {run.github_url}
              </a>
            </div>
          )}

          {run.error_message && (
            <div className="mt-4 pt-4 border-t border-gray-800">
              <div className="p-3 bg-red-900/20 border border-red-800 rounded text-sm text-red-300">
                <strong>Error:</strong> {run.error_message}
              </div>
            </div>
          )}
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
              <Button
                variant={showDebugView ? "default" : "outline"}
                size="sm"
                onClick={() => setShowDebugView(!showDebugView)}
                className="gap-2"
              >
                <Bug className="w-4 h-4" />
                Debug {showDebugView ? 'On' : 'Off'}
              </Button>
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
                      {(showDebugView ? debugOutputs : outputs).filter(o => o.variation_id === variation).length} messages
                    </Badge>
                  </div>
                </div>
                
                <div className="max-h-96 overflow-y-auto p-4 space-y-2">
                  {(showDebugView ? debugOutputs : outputs).filter(o => o.variation_id === variation).length === 0 ? (
                    <div className="text-center py-8 text-gray-400">
                      {run.status === "pending" ? "Waiting for run to start..." : "No output yet"}
                    </div>
                  ) : (
                    (showDebugView ? debugOutputs : outputs)
                      .filter(o => o.variation_id === variation)
                      .map((output) => (
                        <div
                          key={output.id}
                          className={`p-3 rounded border ${getOutputBgColor(output.output_type)}`}
                        >
                          <div className="flex items-center gap-2 mb-2">
                            {getOutputIcon(output.output_type)}
                            <Badge variant="outline" className="text-xs">
                              {output.output_type}
                            </Badge>
                            <span className="text-xs text-gray-400">
                              {new Date(output.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                          <pre className="text-sm whitespace-pre-wrap font-mono">
                            {output.content}
                          </pre>
                        </div>
                      ))
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
  )
}