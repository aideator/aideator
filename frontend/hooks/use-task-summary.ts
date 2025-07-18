"use client"

import { useState, useEffect } from 'react'

export interface TaskSummary {
  id: number
  content: string
  timestamp: string
  variation_id: number
  output_type: string
}

export interface UseTaskSummaryReturn {
  summary: string | null
  loading: boolean
  error: string | null
  refetch: () => void
}

/**
 * Hook for fetching task summary for a specific variation
 */
export function useTaskSummary(taskId: string, variationId: number, taskStatus?: string): UseTaskSummaryReturn {
  const [summary, setSummary] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSummary = async (isInitialLoad = false) => {
    try {
      if (isInitialLoad) {
        setLoading(true)
      }
      setError(null)
      
      // Build query parameters for summary output type and specific variation
      const params = new URLSearchParams({
        output_type: 'summary',
        variation_id: variationId.toString()
      })
      
      // Call the task outputs API endpoint filtered for summaries
      const url = `http://localhost:8000/api/v1/tasks/${taskId}/outputs?${params}`
      console.log('Fetching task summary from:', url)
      
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Failed to fetch summary: ${response.status} ${response.statusText} - ${errorText}`)
      }

      const data: TaskSummary[] = await response.json()
      
      // Get the latest summary (most recent timestamp)
      if (data.length > 0) {
        const latestSummary = data[data.length - 1]
        setSummary(latestSummary.content)
      } else {
        setSummary(null)
      }
    } catch (err) {
      console.error('Error fetching task summary:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch summary')
      setSummary(null)
    } finally {
      if (isInitialLoad) {
        setLoading(false)
      }
    }
  }

  const refetch = () => {
    fetchSummary(true)
  }

  useEffect(() => {
    if (taskId && variationId !== undefined) {
      fetchSummary(true)
      
      // Only poll if task is still running
      if (taskStatus === "Open" || !taskStatus) {
        const interval = setInterval(() => fetchSummary(false), 2000)
        return () => clearInterval(interval)
      }
    }
  }, [taskId, variationId, taskStatus])

  return {
    summary,
    loading,
    error,
    refetch,
  }
}