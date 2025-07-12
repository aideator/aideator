"use client"

import { useState, useEffect } from 'react'

export interface Task {
  id: string
  title: string
  details: string
  status: 'Completed' | 'Open' | 'Failed'
  versions?: number
  additions?: number
  deletions?: number
}

export interface TasksResponse {
  tasks: Task[]
  total: number
  has_more: boolean
}

export interface UseTasksReturn {
  tasks: Task[]
  loading: boolean
  error: string | null
  refetch: () => void
  hasMore: boolean
  total: number
}

/**
 * Hook for fetching tasks from the API
 * Replaces the mock sessions data with real database data
 */
export function useTasks(limit: number = 20): UseTasksReturn {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hasMore, setHasMore] = useState(false)
  const [total, setTotal] = useState(0)

  const fetchTasks = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // TODO: Replace with actual API endpoint when authentication is set up
      // For now, we'll use a placeholder that would work once the backend is running
      const response = await fetch(`/api/v1/runs/tasks?limit=${limit}`, {
        headers: {
          'Content-Type': 'application/json',
          // TODO: Add authentication headers when available
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch tasks: ${response.statusText}`)
      }

      const data: TasksResponse = await response.json()
      
      setTasks(data.tasks)
      setTotal(data.total)
      setHasMore(data.has_more)
    } catch (err) {
      console.error('Error fetching tasks:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch tasks')
      
      // Fallback to mock data for development
      setTasks([
        {
          id: "1",
          title: "Make hello world label ominous",
          details: "8:15 PM · aideator/helloworld",
          status: "Completed",
          versions: 3,
          additions: 1,
          deletions: 1,
        },
        {
          id: "2", 
          title: "Make hello world message cheerier",
          details: "7:29 PM · aideator/helloworld",
          status: "Completed",
          versions: 3,
          additions: 8,
          deletions: 8,
        },
        {
          id: "3",
          title: "Update hello world message",
          details: "Jul 9 · aideator/helloworld",
          status: "Open",
        },
        {
          id: "4",
          title: "Update hello world message", 
          details: "Jul 8 · aideator/helloworld",
          status: "Failed",
        },
      ])
      setTotal(4)
      setHasMore(false)
    } finally {
      setLoading(false)
    }
  }

  const refetch = () => {
    fetchTasks()
  }

  useEffect(() => {
    fetchTasks()
  }, [limit])

  return {
    tasks,
    loading,
    error,
    refetch,
    hasMore,
    total,
  }
}