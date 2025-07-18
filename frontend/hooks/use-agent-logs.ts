"use client"

import { useState, useEffect, useCallback, useRef } from 'react'

export interface AgentLog {
  id: number
  task_id: string
  variation_id: number
  content: string
  timestamp: string
  output_type: 'logging' | 'error' | 'stdout' | 'stderr' | 'status' | 'summary' | 'diffs' | 'addinfo' | 'job_data' | 'assistant_response' | 'debug' | 'system_status' | 'debug_info'
}

export interface UseAgentLogsReturn {
  logs: AgentLog[]
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  getLogsByVariation: (variationId: number) => AgentLog[]
  hasLogsForVariation: (variationId: number) => boolean
}

/**
 * Hook for fetching and continuously polling agent logs from the REST API
 * Replaces static log content with real-time data from agent_outputs table
 */
export function useAgentLogs(taskId: string): UseAgentLogsReturn {
  const [logs, setLogs] = useState<AgentLog[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const cacheRef = useRef<Map<string, AgentLog[]>>(new Map())
  const lastFetchedRef = useRef<string>('')

  const fetchLogs = useCallback(async () => {
    if (!taskId) return
    

    try {
      setError(null)

      // Check cache first (cache for 5 seconds to avoid excessive API calls)
      const cacheKey = `logs-${taskId}`
      const cached = cacheRef.current.get(cacheKey)
      const now = Date.now().toString()
      
      if (cached && (Date.now() - parseInt(lastFetchedRef.current)) < 5000) {
        setLogs(cached)
        setIsLoading(false)
        return
      }

      // Fetch from API - get all outputs including assistant responses (frontend on port 3000, API on port 8000)
      // Request a large limit to make sure we receive all log entries (server capped at 5000).
      const response = await fetch(`http://localhost:8000/api/v1/tasks/${taskId}/outputs?limit=5000`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        if (response.status === 404) {
          // Task exists but no logs yet - this is normal
          setLogs([])
          setIsLoading(false)
          return
        }
        throw new Error(`Failed to fetch logs: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()
      
      // Transform API response to AgentLog format - API returns array directly
      const fetchedLogs: AgentLog[] = (Array.isArray(data) ? data : data.outputs || [])
        .filter((output: any) => output.output_type !== 'diffs' && output.output_type !== 'summary') // Filter out diff XML and summaries from logs
        .map((output: any) => ({
          id: output.id,
          task_id: output.task_id,
          variation_id: output.variation_id,
          content: output.content,
          timestamp: output.timestamp,
          output_type: output.output_type
        }))

      // Sort by timestamp in chronological order (oldest first, newest at bottom like chat/terminal)
      fetchedLogs.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())

      setLogs(fetchedLogs)
      
      // Update cache
      cacheRef.current.set(cacheKey, fetchedLogs)
      lastFetchedRef.current = now

    } catch (err) {
      console.error('Failed to fetch agent logs:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch logs')
    } finally {
      setIsLoading(false)
    }
  }, [taskId])

  const getLogsByVariation = useCallback((variationId: number): AgentLog[] => {
    return logs.filter(log => log.variation_id === variationId)
  }, [logs])

  const hasLogsForVariation = useCallback((variationId: number): boolean => {
    return logs.some(log => log.variation_id === variationId)
  }, [logs])

  // Start continuous polling
  useEffect(() => {
    if (!taskId) return

    // Initial fetch
    fetchLogs()

    // Set up polling every 3 seconds
    pollingIntervalRef.current = setInterval(() => {
      fetchLogs()
    }, 3000)

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
        pollingIntervalRef.current = null
      }
    }
  }, [taskId, fetchLogs])

  // Clear cache when component unmounts
  useEffect(() => {
    return () => {
      cacheRef.current.clear()
    }
  }, [])

  return {
    logs,
    isLoading,
    error,
    refetch: fetchLogs,
    getLogsByVariation,
    hasLogsForVariation,
  }
}