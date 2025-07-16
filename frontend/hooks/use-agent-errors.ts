"use client"

import { useState, useEffect, useCallback, useRef } from 'react'

export interface AgentError {
  id: number
  task_id: string
  variation_id: number
  content: string
  timestamp: string
  output_type: 'error' | 'stderr'
}

export interface UseAgentErrorsReturn {
  errors: AgentError[]
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  getErrorsByVariation: (variationId: number) => AgentError[]
  hasErrorsForVariation: (variationId: number) => boolean
}

/**
 * Hook for fetching and continuously polling agent errors from the REST API
 * Fetches output_type=error and output_type=stderr
 */
export function useAgentErrors(taskId: string): UseAgentErrorsReturn {
  const [errors, setErrors] = useState<AgentError[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const cacheRef = useRef<Map<string, AgentError[]>>(new Map())
  const lastFetchedRef = useRef<string>('')

  const fetchErrors = useCallback(async () => {
    if (!taskId) return

    try {
      setError(null)

      // Check cache first (cache for 5 seconds to avoid excessive API calls)
      const cacheKey = `errors-${taskId}`
      const cached = cacheRef.current.get(cacheKey)
      const now = Date.now().toString()
      
      if (cached && (Date.now() - parseInt(lastFetchedRef.current)) < 5000) {
        setErrors(cached)
        setIsLoading(false)
        return
      }

      // Fetch both error and stderr outputs
      const [errorResponse, stderrResponse] = await Promise.all([
        fetch(`http://localhost:8000/api/v1/tasks/${taskId}/outputs?output_type=error`),
        fetch(`http://localhost:8000/api/v1/tasks/${taskId}/outputs?output_type=stderr`)
      ])

      const errorData = errorResponse.ok ? await errorResponse.json() : { outputs: [] }
      const stderrData = stderrResponse.ok ? await stderrResponse.json() : { outputs: [] }

      // Combine both error types
      const allErrors = [
        ...(errorData.outputs || []).map((output: any) => ({
          id: output.id,
          task_id: output.task_id,
          variation_id: output.variation_id,
          content: output.content,
          timestamp: output.timestamp,
          output_type: 'error' as const
        })),
        ...(stderrData.outputs || []).map((output: any) => ({
          id: output.id,
          task_id: output.task_id,
          variation_id: output.variation_id,
          content: output.content,
          timestamp: output.timestamp,
          output_type: 'stderr' as const
        }))
      ]

      // Sort by timestamp in reverse chronological order (newest first)
      allErrors.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())

      setErrors(allErrors)
      
      // Update cache
      cacheRef.current.set(cacheKey, allErrors)
      lastFetchedRef.current = now

    } catch (err) {
      console.error('Failed to fetch agent errors:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch errors')
    } finally {
      setIsLoading(false)
    }
  }, [taskId])

  const getErrorsByVariation = useCallback((variationId: number): AgentError[] => {
    return errors.filter(error => error.variation_id === variationId)
  }, [errors])

  const hasErrorsForVariation = useCallback((variationId: number): boolean => {
    return errors.some(error => error.variation_id === variationId)
  }, [errors])

  // Start continuous polling
  useEffect(() => {
    if (!taskId) return

    // Initial fetch
    fetchErrors()

    // Set up polling every 5 seconds (less frequent than logs)
    pollingIntervalRef.current = setInterval(() => {
      fetchErrors()
    }, 5000)

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
        pollingIntervalRef.current = null
      }
    }
  }, [taskId, fetchErrors])

  // Clear cache when component unmounts
  useEffect(() => {
    return () => {
      cacheRef.current.clear()
    }
  }, [])

  return {
    errors,
    isLoading,
    error,
    refetch: fetchErrors,
    getErrorsByVariation,
    hasErrorsForVariation,
  }
}