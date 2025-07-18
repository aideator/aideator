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
  
  const fetchTask = async (isInitialLoad = false) => {
    try {
      if (isInitialLoad) {
        setLoading(true)
      }
      setError(null)
      
      // Call the task detail API endpoint
      const url = `http://localhost:8000/api/v1/tasks/${taskId}`
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
      if (isInitialLoad) {
        setLoading(false)
      }
    }
  }

  const refetch = () => {
    fetchTask(true)
  }

  useEffect(() => {
    if (taskId) {
      fetchTask(true)
      
      // Only poll if task is still running
      if (!task || task.status === "Open") {
        const interval = setInterval(() => fetchTask(false), 3000)
        return () => clearInterval(interval)
      }
    }
  }, [taskId, task?.status])

  return {
    task,
    loading,
    error,
    refetch,
  }
}