"use client"

import { useState, useEffect, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Clock, Layers, DollarSign, ArrowLeft, Plus } from "lucide-react"
import Link from "next/link"
import { apiClient } from "@/lib/api"
import { Session, Turn } from "@/lib/types"

export default function SessionPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string

  const [session, setSession] = useState<Session | null>(null)
  const [turns, setTurns] = useState<Turn[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadSessionData = useCallback(async () => {
    try {
      setIsLoading(true)
      const [sessionResponse, turnsResponse] = await Promise.all([
        apiClient.getSession(sessionId),
        apiClient.getSessionTurns(sessionId),
      ])
      setSession(sessionResponse)
      setTurns(turnsResponse)
      setError(null)
    } catch (err) {
      console.error('Failed to load session data:', err)
      setError('Failed to load session data')
    } finally {
      setIsLoading(false)
    }
  }, [sessionId])

  useEffect(() => {
    if (sessionId) {
      loadSessionData()
    }
  }, [sessionId, loadSessionData])

  const handleNewTurn = () => {
    // Navigate back to home with session context for creating new turn
    router.push(`/?session=${sessionId}`)
  }

  if (isLoading) {
    return (
      <div className="bg-gray-950 text-gray-50 min-h-screen">
        <div className="container mx-auto max-w-4xl py-8">
          <div className="flex items-center justify-center py-20">
            <div className="animate-pulse">Loading session...</div>
          </div>
        </div>
      </div>
    )
  }

  if (error || !session) {
    return (
      <div className="bg-gray-950 text-gray-50 min-h-screen">
        <div className="container mx-auto max-w-4xl py-8">
          <div className="text-center py-20">
            <p className="text-red-400 mb-4">{error || 'Session not found'}</p>
            <Button onClick={() => router.push('/')} variant="outline">
              Back to Home
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gray-950 text-gray-50 min-h-screen">
      <div className="container mx-auto max-w-4xl py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push('/')}
            className="text-gray-400 hover:text-gray-200"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex-1">
            <h1 className="text-2xl font-semibold">{session.title}</h1>
            {session.description && (
              <p className="text-gray-400 mt-1">{session.description}</p>
            )}
          </div>
          <Badge variant={session.is_active ? "default" : "secondary"}>
            {session.is_active ? "Active" : "Completed"}
          </Badge>
        </div>

        {/* Session Metadata */}
        <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-gray-400" />
              <div className="text-sm">
                <div className="text-gray-400">Created</div>
                <div>{new Date(session.created_at).toLocaleDateString()}</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-gray-400" />
              <div className="text-sm">
                <div className="text-gray-400">Turns</div>
                <div>{session.total_turns}</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-gray-400" />
              <div className="text-sm">
                <div className="text-gray-400">Total Cost</div>
                <div>${(session.total_cost || 0).toFixed(2)}</div>
              </div>
            </div>
            <div className="text-sm">
              <div className="text-gray-400">Models Used</div>
              <div className="flex flex-wrap gap-1 mt-1">
                {session.models_used.map((model, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {model}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </div>

        <Tabs defaultValue="turns" className="w-full">
          <div className="flex items-center justify-between mb-4">
            <TabsList className="bg-gray-900/50 border border-gray-800">
              <TabsTrigger value="turns">Turns</TabsTrigger>
              <TabsTrigger value="analytics">Analytics</TabsTrigger>
            </TabsList>
            <Button 
              onClick={handleNewTurn} 
              size="sm" 
              className="gap-2" 
              disabled
              title="Multiple turns not yet supported"
            >
              <Plus className="w-4 h-4" />
              New Turn
            </Button>
          </div>

          <TabsContent value="turns" className="space-y-4">
            {turns.length === 0 ? (
              <div className="text-center py-12 bg-gray-900/30 border border-gray-800 rounded-lg">
                <p className="text-gray-400 mb-4">No turns in this session yet.</p>
                <Button 
                  onClick={handleNewTurn} 
                  variant="outline"
                  disabled
                  title="Multiple turns not yet supported"
                >
                  Create First Turn
                </Button>
              </div>
            ) : (
              turns.map((turn) => (
                <div
                  key={turn.id}
                  className="bg-gray-900/30 border border-gray-800 rounded-lg p-4 hover:bg-gray-900/50 transition-colors"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="outline" className="text-xs">
                          Turn {turn.turn_number}
                        </Badge>
                        <Badge
                          variant={
                            turn.status === "completed"
                              ? "default"
                              : turn.status === "failed"
                              ? "destructive"
                              : "secondary"
                          }
                          className="text-xs"
                        >
                          {turn.status}
                        </Badge>
                      </div>
                      <p className="text-gray-200 mb-2">{turn.prompt}</p>
                      <div className="text-sm text-gray-400">
                        {new Date(turn.started_at).toLocaleString()}
                        {turn.completed_at && (
                          <>
                            {" → "}
                            {new Date(turn.completed_at).toLocaleString()}
                          </>
                        )}
                      </div>
                    </div>
                    <div className="text-right text-sm">
                      <div className="text-gray-400">Models: {turn.models_requested.length}</div>
                      <div className="text-gray-400">Cost: ${(turn.total_cost || 0).toFixed(2)}</div>
                      {turn.duration_seconds && (
                        <div className="text-gray-400">
                          Duration: {Math.round(turn.duration_seconds)}s
                        </div>
                      )}
                    </div>
                  </div>

                  <Separator className="my-3 bg-gray-800" />

                  <div className="flex items-center justify-between">
                    <div className="flex flex-wrap gap-1">
                      {turn.models_requested.map((model, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {model}
                        </Badge>
                      ))}
                    </div>
                    <Link href={`/session/${sessionId}/turn/${turn.id}`}>
                      <Button variant="outline" size="sm">
                        View Details
                      </Button>
                    </Link>
                  </div>
                </div>
              ))
            )}
          </TabsContent>

          <TabsContent value="analytics" className="space-y-4">
            <div className="bg-gray-900/30 border border-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-medium mb-4">Session Analytics</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="text-center p-4 bg-gray-800/50 rounded-lg">
                  <div className="text-2xl font-bold">{turns.length}</div>
                  <div className="text-sm text-gray-400">Total Turns</div>
                </div>
                <div className="text-center p-4 bg-gray-800/50 rounded-lg">
                  <div className="text-2xl font-bold">
                    {turns.filter((t) => t.status === "completed").length}
                  </div>
                  <div className="text-sm text-gray-400">Completed</div>
                </div>
                <div className="text-center p-4 bg-gray-800/50 rounded-lg">
                  <div className="text-2xl font-bold">
                    ${(session.total_cost || 0).toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-400">Total Spent</div>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}