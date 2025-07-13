"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ArrowLeft, Clock, DollarSign, Play, Users } from "lucide-react"
import Link from "next/link"
import { apiClient } from "@/lib/api"
import { Session, Turn, Run } from "@/lib/types"

export default function TurnPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string
  const turnId = params.turnId as string

  const [session, setSession] = useState<Session | null>(null)
  const [turn, setTurn] = useState<Turn | null>(null)
  const [runs, setRuns] = useState<Run[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (sessionId && turnId) {
      loadTurnData()
    }
  }, [sessionId, turnId])

  const loadTurnData = async () => {
    try {
      setIsLoading(true)
      const [sessionResponse, turnResponse, runsResponse] = await Promise.all([
        apiClient.getSession(sessionId),
        apiClient.getTurn(sessionId, turnId),
        apiClient.getTurnRuns(sessionId, turnId),
      ])
      setSession(sessionResponse)
      setTurn(turnResponse)
      setRuns(runsResponse)
      setError(null)
    } catch (err) {
      console.error('Failed to load turn data:', err)
      setError('Failed to load turn data')
    } finally {
      setIsLoading(false)
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

  if (isLoading) {
    return (
      <div className="bg-gray-950 text-gray-50 min-h-screen">
        <div className="container mx-auto max-w-6xl py-8">
          <div className="flex items-center justify-center py-20">
            <div className="animate-pulse">Loading turn...</div>
          </div>
        </div>
      </div>
    )
  }

  if (error || !session || !turn) {
    return (
      <div className="bg-gray-950 text-gray-50 min-h-screen">
        <div className="container mx-auto max-w-6xl py-8">
          <div className="text-center py-20">
            <p className="text-red-400 mb-4">{error || 'Turn not found'}</p>
            <Button onClick={() => router.push(`/session/${sessionId}`)} variant="outline">
              Back to Session
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
            onClick={() => router.push(`/session/${sessionId}`)}
            className="text-gray-400 hover:text-gray-200"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Link href={`/session/${sessionId}`} className="text-gray-400 hover:text-gray-200">
                {session.title}
              </Link>
              <span className="text-gray-600">/</span>
              <Badge variant="outline" className="text-xs">
                Turn {turn.turn_number}
              </Badge>
            </div>
            <h1 className="text-2xl font-semibold">{turn.prompt}</h1>
          </div>
          <Badge variant={getStatusColor(turn.status) as any}>
            {turn.status}
          </Badge>
        </div>

        {/* Turn Metadata */}
        <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-gray-400" />
              <div className="text-sm">
                <div className="text-gray-400">Started</div>
                <div>{new Date(turn.started_at).toLocaleString()}</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-gray-400" />
              <div className="text-sm">
                <div className="text-gray-400">Models</div>
                <div>{turn.models_requested.length}</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-gray-400" />
              <div className="text-sm">
                <div className="text-gray-400">Cost</div>
                <div>${turn.total_cost.toFixed(3)}</div>
              </div>
            </div>
            <div className="text-sm">
              <div className="text-gray-400">Duration</div>
              <div>
                {turn.duration_seconds
                  ? `${Math.round(turn.duration_seconds)}s`
                  : turn.completed_at
                  ? `${Math.round((new Date(turn.completed_at).getTime() - new Date(turn.started_at).getTime()) / 1000)}s`
                  : "In progress..."}
              </div>
            </div>
          </div>

          {turn.context && (
            <div className="mt-4 pt-4 border-t border-gray-800">
              <div className="text-sm text-gray-400 mb-2">Context</div>
              <p className="text-sm text-gray-300">{turn.context}</p>
            </div>
          )}
        </div>

        <Tabs defaultValue="runs" className="w-full">
          <TabsList className="bg-gray-900/50 border border-gray-800 mb-6">
            <TabsTrigger value="runs">Runs ({runs.length})</TabsTrigger>
            <TabsTrigger value="responses">Responses</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>

          <TabsContent value="runs" className="space-y-4">
            {runs.length === 0 ? (
              <div className="text-center py-12 bg-gray-900/30 border border-gray-800 rounded-lg">
                <p className="text-gray-400 mb-4">No runs found for this turn.</p>
                <p className="text-sm text-gray-500">
                  Runs should be automatically created when the turn is processed.
                </p>
              </div>
            ) : (
              runs.map((run, index) => (
                <div
                  key={run.id}
                  className="bg-gray-900/30 border border-gray-800 rounded-lg p-4 hover:bg-gray-900/50 transition-colors"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="outline" className="text-xs">
                          Run {index + 1}
                        </Badge>
                        <Badge variant={getStatusColor(run.status) as any} className="text-xs">
                          {run.status}
                        </Badge>
                        {run.winning_variation_id && (
                          <Badge variant="default" className="text-xs bg-green-600">
                            Winner
                          </Badge>
                        )}
                      </div>
                      <div className="text-sm text-gray-400 mb-2">
                        {run.variations} variation{run.variations !== 1 ? 's' : ''}
                        {run.github_url && (
                          <>
                            {" • "}
                            <a
                              href={run.github_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-400 hover:text-blue-300"
                            >
                              {run.github_url.replace('https://github.com/', '')}
                            </a>
                          </>
                        )}
                      </div>
                      <div className="text-sm text-gray-400">
                        Created: {new Date(run.created_at).toLocaleString()}
                        {run.started_at && (
                          <>
                            {" • Started: "}
                            {new Date(run.started_at).toLocaleString()}
                          </>
                        )}
                        {run.completed_at && (
                          <>
                            {" • Completed: "}
                            {new Date(run.completed_at).toLocaleString()}
                          </>
                        )}
                      </div>
                    </div>
                    <div className="text-right text-sm">
                      {run.total_tokens_used && (
                        <div className="text-gray-400">
                          {run.total_tokens_used.toLocaleString()} tokens
                        </div>
                      )}
                      {run.total_cost_usd !== undefined && (
                        <div className="text-gray-400">
                          ${run.total_cost_usd.toFixed(3)}
                        </div>
                      )}
                    </div>
                  </div>

                  {run.error_message && (
                    <div className="mb-3 p-3 bg-red-900/20 border border-red-800 rounded text-sm text-red-300">
                      <strong>Error:</strong> {run.error_message}
                    </div>
                  )}

                  <Separator className="my-3 bg-gray-800" />

                  <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-400">
                      ID: <span className="font-mono text-xs">{run.id}</span>
                    </div>
                    <Link href={`/session/${sessionId}/turn/${turnId}/run/${run.id}`}>
                      <Button variant="outline" size="sm" className="gap-2">
                        <Play className="w-4 h-4" />
                        View Details
                      </Button>
                    </Link>
                  </div>
                </div>
              ))
            )}
          </TabsContent>

          <TabsContent value="responses" className="space-y-4">
            <div className="bg-gray-900/30 border border-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-medium mb-4">Model Responses</h3>
              {Object.keys(turn.responses).length === 0 ? (
                <p className="text-gray-400">No responses available yet.</p>
              ) : (
                <div className="space-y-4">
                  {Object.entries(turn.responses).map(([model, response]) => (
                    <div key={model} className="border border-gray-800 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <Badge variant="outline">{model}</Badge>
                      </div>
                      <div className="text-sm text-gray-300 whitespace-pre-wrap">
                        {typeof response === 'string' ? response : JSON.stringify(response, null, 2)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-4">
            <div className="bg-gray-900/30 border border-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-medium mb-4">Turn Analytics</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-gray-800/50 rounded-lg">
                  <div className="text-2xl font-bold">{runs.length}</div>
                  <div className="text-sm text-gray-400">Total Runs</div>
                </div>
                <div className="text-center p-4 bg-gray-800/50 rounded-lg">
                  <div className="text-2xl font-bold">
                    {runs.filter((r) => r.status === "completed").length}
                  </div>
                  <div className="text-sm text-gray-400">Completed</div>
                </div>
                <div className="text-center p-4 bg-gray-800/50 rounded-lg">
                  <div className="text-2xl font-bold">
                    {runs.reduce((sum, r) => sum + (r.variations || 0), 0)}
                  </div>
                  <div className="text-sm text-gray-400">Total Variations</div>
                </div>
                <div className="text-center p-4 bg-gray-800/50 rounded-lg">
                  <div className="text-2xl font-bold">
                    ${runs.reduce((sum, r) => sum + (r.total_cost_usd || 0), 0).toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-400">Total Cost</div>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}