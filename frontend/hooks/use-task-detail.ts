"use client"

import { useState, useEffect } from 'react'

export interface TaskDetail {
  id: string
  title: string
  details: string
  status: 'Completed' | 'Open' | 'Failed'
  versions: number
  taskDetails: {
    versions: Array<{
      id: number
      summary: string
      files: Array<{
        name: string
        additions: number
        deletions: number
        diff: Array<{
          type: 'normal' | 'add' | 'del'
          oldLine: number | null
          newLine: number | null
          content: string
        }>
      }>
    }>
  }
}

export interface UseTaskDetailReturn {
  task: TaskDetail | null
  loading: boolean
  error: string | null
  refetch: () => void
}

/**
 * Hook for fetching individual task details from the API
 */
export function useTaskDetail(taskId: string): UseTaskDetailReturn {
  const [task, setTask] = useState<TaskDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchTask = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Call the task detail API endpoint
      const url = `/api/v1/tasks/${taskId}`
      console.log('Fetching task detail from:', url)
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Failed to fetch task: ${response.status} ${response.statusText} - ${errorText}`)
      }

      const data: TaskDetail = await response.json()
      setTask(data)
    } catch (err) {
      console.error('Error fetching task detail:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch task')
      setTask(null)
    } finally {
      setLoading(false)
    }
  }

  const refetch = () => {
    fetchTask()
  }

  useEffect(() => {
    if (taskId) {
      fetchTask()
    }
  }, [taskId])

  return {
    task,
    loading,
    error,
    refetch,
  }
}