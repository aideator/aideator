"use client"

import { useState } from 'react'

export interface UseArchiveReturn {
  archiving: string | null  // Task ID being archived
  deleting: string | null   // Task ID being deleted
  archiveTask: (taskId: string) => Promise<void>
  unarchiveTask: (taskId: string) => Promise<void>
  deleteTask: (taskId: string) => Promise<void>
}

/**
 * Hook for archive/delete operations
 */
export function useArchive(): UseArchiveReturn {
  const [archiving, setArchiving] = useState<string | null>(null)
  const [deleting, setDeleting] = useState<string | null>(null)

  const archiveTask = async (taskId: string) => {
    try {
      setArchiving(taskId)
      
      const token = localStorage.getItem('github_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }
      
      if (token) {
        headers.Authorization = `Bearer ${token}`
      }
      
      const response = await fetch(`http://localhost:8000/api/v1/tasks/${taskId}/archive`, {
        method: 'PATCH',
        headers,
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Failed to archive task: ${response.status} ${response.statusText} - ${errorText}`)
      }
    } catch (err) {
      console.error('Error archiving task:', err)
      throw err
    } finally {
      setArchiving(null)
    }
  }

  const unarchiveTask = async (taskId: string) => {
    try {
      setArchiving(taskId)
      
      const token = localStorage.getItem('github_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }
      
      if (token) {
        headers.Authorization = `Bearer ${token}`
      }
      
      const response = await fetch(`http://localhost:8000/api/v1/tasks/${taskId}/unarchive`, {
        method: 'PATCH',
        headers,
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Failed to unarchive task: ${response.status} ${response.statusText} - ${errorText}`)
      }
    } catch (err) {
      console.error('Error unarchiving task:', err)
      throw err
    } finally {
      setArchiving(null)
    }
  }

  const deleteTask = async (taskId: string) => {
    // Prevent double deletion attempts
    if (deleting === taskId) {
      console.log(`Delete already in progress for task ${taskId}`)
      return
    }

    const maxRetries = 2
    let attempt = 0

    while (attempt < maxRetries) {
      try {
        setDeleting(taskId)
        attempt++
        
        const token = localStorage.getItem('github_token')
        const headers: HeadersInit = {
          'Content-Type': 'application/json',
        }
        
        if (token) {
          headers.Authorization = `Bearer ${token}`
        }
        
        console.log(`Attempting to delete task ${taskId} (attempt ${attempt}/${maxRetries})...`)
        
        // Add retry delay for subsequent attempts
        if (attempt > 1) {
          await new Promise(resolve => setTimeout(resolve, 1000))
        }
        
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 15000) // 15 second timeout
        
        const response = await fetch(`http://localhost:8000/api/v1/tasks/${taskId}`, {
          method: 'DELETE',
          headers,
          signal: controller.signal,
        })

        clearTimeout(timeoutId)
        console.log(`Delete response status: ${response.status}`)

        if (!response.ok) {
          const errorText = await response.text()
          console.error(`Delete failed with ${response.status}: ${errorText}`)
          
          // Don't retry for client errors (4xx)
          if (response.status >= 400 && response.status < 500) {
            throw new Error(`Failed to delete task: ${response.status} ${response.statusText} - ${errorText}`)
          }
          
          // Retry for server errors (5xx) if we have attempts left
          if (attempt < maxRetries) {
            console.log(`Server error ${response.status}, retrying...`)
            continue
          }
          
          throw new Error(`Failed to delete task: ${response.status} ${response.statusText} - ${errorText}`)
        }
        
        console.log(`Task ${taskId} deleted successfully`)
        return // Success, exit retry loop
        
      } catch (err) {
        console.error(`Error deleting task (attempt ${attempt}):`, err)
        
        // Handle specific error types
        if (err instanceof TypeError && err.message === 'Failed to fetch') {
          if (attempt < maxRetries) {
            console.log('Network error, retrying...')
            continue
          }
          throw new Error('Network error: Unable to connect to server after retries. Please check if the backend is running.')
        } else if (err.name === 'AbortError') {
          if (attempt < maxRetries) {
            console.log('Request timed out, retrying...')
            continue
          }
          throw new Error('Delete operation timed out after retries. Please try again.')
        } else {
          // Don't retry for other types of errors
          throw err
        }
      } finally {
        // Only clear deleting state on final attempt or success
        if (attempt === maxRetries || attempt === 0) {
          setDeleting(null)
        }
      }
    }
  }

  return {
    archiving,
    deleting,
    archiveTask,
    unarchiveTask,
    deleteTask,
  }
}