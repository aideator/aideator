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
      
      // Call the tasks API endpoint (separated from runs)
      const url = `http://localhost:8000/api/v1/tasks?limit=${limit}`
      console.log('Fetching tasks from:', url)
      // Get auth token from localStorage
      const token = localStorage.getItem('github_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }
      
      // Add authorization header if token exists
      if (token) {
        headers.Authorization = `Bearer ${token}`
      }
      
      const response = await fetch(url, { headers })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Failed to fetch tasks: ${response.status} ${response.statusText} - ${errorText}`)
      }

      const data: TasksResponse = await response.json()
      
      setTasks(data.tasks)
      setTotal(data.total)
      setHasMore(data.has_more)
    } catch (err) {
      console.error('Error fetching tasks:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch tasks')
      
      // No fallback to mock data - use real API data only
      setTasks([])
      setTotal(0)
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