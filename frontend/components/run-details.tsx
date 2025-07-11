"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Loader2, CheckCircle, AlertCircle, Clock } from "lucide-react"
import { selectWinner } from "@/lib/api"

interface AgentOutput {
  variation_id: number
  content: string
  pod?: string
}

interface AgentError {
  variation_id: number
  error: string
  job_name?: string
}

interface JobStatus {
  variation_id: number
  status: "completed" | "failed" | "running"
  job_name?: string
}

interface RunStatus {
  run_id: string
  status: "starting" | "running" | "completed" | "failed" | "cancelled"
  message?: string
}

export function RunDetails({ runId }: { runId: string }) {
  const [outputs, setOutputs] = useState<Record<number, string[]>>({})
  const [errors, setErrors] = useState<Record<number, string[]>>({})
  const [jobStatuses, setJobStatuses] = useState<Record<number, JobStatus>>({})
  const [runStatus, setRunStatus] = useState<RunStatus | null>(null)
  const [activeTab, setActiveTab] = useState("0")
  const [isSelectingWinner, setIsSelectingWinner] = useState(false)
  const [selectedWinner, setSelectedWinner] = useState<number | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    const streamUrl = `${apiBase}/api/v1/runs/${runId}/stream`;
    console.log(`Starting SSE stream to:`, streamUrl);
    
    const eventSource = new EventSource(streamUrl)
    setIsConnected(true)

    eventSource.onopen = () => {
      setIsConnected(true)
    }

    eventSource.onerror = () => {
      setIsConnected(false)
      eventSource.close()
    }

    eventSource.addEventListener("status", (event) => {
      const data = JSON.parse(event.data) as RunStatus
      setRunStatus(data)
    })

    eventSource.addEventListener("agent_output", (event) => {
      const data = JSON.parse(event.data) as AgentOutput
      setOutputs((prev) => {
        const variationOutputs = prev[data.variation_id] || []
        return {
          ...prev,
          [data.variation_id]: [...variationOutputs, data.content],
        }
      })
    })

    eventSource.addEventListener("agent_error", (event) => {
      const data = JSON.parse(event.data) as AgentError
      setErrors((prev) => {
        const variationErrors = prev[data.variation_id] || []
        return {
          ...prev,
          [data.variation_id]: [...variationErrors, data.error],
        }
      })
    })

    eventSource.addEventListener("job_completed", (event) => {
      const data = JSON.parse(event.data) as JobStatus
      setJobStatuses((prev) => ({
        ...prev,
        [data.variation_id]: data,
      }))
    })

    eventSource.addEventListener("run_complete", () => {
      eventSource.close()
      setIsConnected(false)
    })

    return () => {
      eventSource.close()
      setIsConnected(false)
    }
  }, [runId])

  const handleSelectWinner = async (variationId: number) => {
    setIsSelectingWinner(true)
    try {
      await selectWinner(runId, variationId)
      setSelectedWinner(variationId)
    } catch (error) {
      console.error("Error selecting winner:", error)
    } finally {
      setIsSelectingWinner(false)
    }
  }

  const variationIds = Object.keys(outputs).map(Number)
  const isRunCompleted = runStatus?.status === "completed"

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Run: {runId}</h2>
          <div className="flex items-center mt-1 space-x-2">
            <StatusBadge status={runStatus?.status || "starting"} />
            {isConnected && (
              <div className="flex items-center gap-4">
                <span className="text-sm text-muted-foreground flex items-center">
                  <span className="relative mr-2 flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                  </span>
                  Connected to stream
                </span>
                <Badge variant="outline" className="text-xs">
                  Redis Streaming
                </Badge>
              </div>
            )}
          </div>
        </div>
      </div>

      {variationIds.length > 0 ? (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-4">
            {variationIds.map((id) => (
              <TabsTrigger key={id} value={id.toString()} className="relative">
                Variation {id + 1}
                {jobStatuses[id]?.status === "completed" && <CheckCircle className="ml-2 h-3 w-3 text-green-500" />}
                {jobStatuses[id]?.status === "failed" && <AlertCircle className="ml-2 h-3 w-3 text-red-500" />}
              </TabsTrigger>
            ))}
          </TabsList>

          {variationIds.map((id) => (
            <TabsContent key={id} value={id.toString()}>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle>Agent Output - Variation {id + 1}</CardTitle>
                  {isRunCompleted && (
                    <Button
                      onClick={() => handleSelectWinner(id)}
                      disabled={isSelectingWinner || selectedWinner === id}
                      variant={selectedWinner === id ? "default" : "outline"}
                    >
                      {isSelectingWinner && selectedWinner === null ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : selectedWinner === id ? (
                        <CheckCircle className="mr-2 h-4 w-4" />
                      ) : null}
                      {selectedWinner === id ? "Selected as Winner" : "Select as Winner"}
                    </Button>
                  )}
                </CardHeader>
                <CardContent>
                  {errors[id]?.length > 0 && (
                    <Alert variant="destructive" className="mb-4">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        {errors[id].map((error, i) => (
                          <div key={i}>{error}</div>
                        ))}
                      </AlertDescription>
                    </Alert>
                  )}
                  <pre className="bg-muted p-4 rounded-md overflow-auto max-h-[600px] text-sm whitespace-pre-wrap">
                    {outputs[id]?.join("\n") || "Waiting for output..."}
                  </pre>
                </CardContent>
              </Card>
            </TabsContent>
          ))}
        </Tabs>
      ) : (
        <Card className="p-6 flex justify-center items-center">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
            <p>Waiting for agent outputs...</p>
          </div>
        </Card>
      )}
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  let color = ""
  let icon = null

  switch (status) {
    case "starting":
      color = "bg-blue-100 text-blue-800"
      icon = <Clock className="h-3 w-3 mr-1" />
      break
    case "running":
      color = "bg-yellow-100 text-yellow-800"
      icon = <Loader2 className="h-3 w-3 mr-1 animate-spin" />
      break
    case "completed":
      color = "bg-green-100 text-green-800"
      icon = <CheckCircle className="h-3 w-3 mr-1" />
      break
    case "failed":
      color = "bg-red-100 text-red-800"
      icon = <AlertCircle className="h-3 w-3 mr-1" />
      break
    case "cancelled":
      color = "bg-gray-100 text-gray-800"
      icon = <AlertCircle className="h-3 w-3 mr-1" />
      break
    default:
      color = "bg-gray-100 text-gray-800"
  }

  return (
    <Badge variant="outline" className={`${color} flex items-center`}>
      {icon}
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  )
}
