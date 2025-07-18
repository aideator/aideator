"use client"

import { useState, useEffect } from 'react'

export interface TaskDiff {
  id: number
  content: string
  timestamp: string
  variation_id: number
  output_type: string
}

export interface UseTaskDiffsReturn {
  diffs: TaskDiff[]
  loading: boolean
  error: string | null
  refetch: () => void
}

/**
 * Hook for fetching git diff data for a specific task
 */
export function useTaskDiffs(taskId: string, variationId?: number): UseTaskDiffsReturn {
  const [diffs, setDiffs] = useState<TaskDiff[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchDiffs = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Build query parameters
      const params = new URLSearchParams({
        output_type: 'diffs'
      })
      
      if (variationId !== undefined) {
        params.append('variation_id', variationId.toString())
      }
      
      // Call the task outputs API endpoint filtered for diffs
      const url = `http://localhost:8000/api/v1/tasks/${taskId}/outputs?${params}`
      console.log('Fetching task diffs from:', url)
      
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Failed to fetch diffs: ${response.status} ${response.statusText} - ${errorText}`)
      }

      const data: TaskDiff[] = await response.json()
      setDiffs(data)
    } catch (err) {
      console.error('Error fetching task diffs:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch diffs')
      setDiffs([])
    } finally {
      setLoading(false)
    }
  }

  const refetch = () => {
    fetchDiffs()
  }

  useEffect(() => {
    if (taskId) {
      fetchDiffs()
      
      // Poll for updates every 2 seconds while task might be running
      const interval = setInterval(fetchDiffs, 2000)
      
      return () => clearInterval(interval)
    }
  }, [taskId, variationId])

  return {
    diffs,
    loading,
    error,
    refetch,
  }
}