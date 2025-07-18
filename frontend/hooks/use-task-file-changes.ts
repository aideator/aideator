"use client"

import { useState, useEffect } from 'react'

export interface FileChange {
  name: string
  additions: number
  deletions: number
}

export interface UseTaskFileChangesReturn {
  files: FileChange[]
  loading: boolean
  error: string | null
}

/**
 * Hook for fetching task file changes from diffs for a specific variation
 */
export function useTaskFileChanges(taskId: string, variationId: number, taskStatus?: string): UseTaskFileChangesReturn {
  const [files, setFiles] = useState<FileChange[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchFileChanges = async (isInitialLoad = false) => {
    try {
      if (isInitialLoad) {
        setLoading(true)
      }
      setError(null)
      
      // Build query parameters for diffs output type and specific variation
      const params = new URLSearchParams({
        output_type: 'diffs',
        variation_id: variationId.toString()
      })
      
      // Call the task outputs API endpoint filtered for diffs
      const url = `http://localhost:8000/api/v1/tasks/${taskId}/outputs?${params}`
      
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Failed to fetch diffs: ${response.status} ${response.statusText} - ${errorText}`)
      }

      const data: Array<{content: string}> = await response.json()
      
      // Parse the latest diff (most recent timestamp)
      if (data.length > 0) {
        const latestDiff = data[data.length - 1]
        
        try {
          // Try to parse as JSON first
          const diffData = JSON.parse(latestDiff.content)
          
          if (diffData.file_changes && Array.isArray(diffData.file_changes)) {
            const fileChanges: FileChange[] = diffData.file_changes.map((file: any) => ({
              name: file.name,
              additions: file.additions || 0,
              deletions: file.deletions || 0
            }))
            setFiles(fileChanges)
          } else {
            setFiles([])
          }
        } catch (jsonError) {
          // If JSON parsing fails, try to parse as XML
          try {
            const content = latestDiff.content
            if (content.includes('<diff_analysis>')) {
              // Parse XML format - extract file names from <name> tags
              const fileMatches = content.match(/<file>(.*?)<\/file>/gs)
              if (fileMatches) {
                const fileChanges: FileChange[] = fileMatches.map((fileBlock) => {
                  const nameMatch = fileBlock.match(/<name>(.*?)<\/name>/s)
                  const diffMatch = fileBlock.match(/<diff>(.*?)<\/diff>/s)
                  
                  let additions = 0
                  let deletions = 0
                  
                  // Count additions and deletions from diff content
                  if (diffMatch) {
                    const diffContent = diffMatch[1]
                    const lines = diffContent.split('\n')
                    for (const line of lines) {
                      const trimmedLine = line.trim()
                      if (trimmedLine.startsWith('+') && !trimmedLine.startsWith('+++')) {
                        additions++
                      } else if (trimmedLine.startsWith('-') && !trimmedLine.startsWith('---')) {
                        deletions++
                      }
                    }
                  }
                  
                  return {
                    name: nameMatch ? nameMatch[1].trim() : 'Unknown',
                    additions,
                    deletions
                  }
                })
                setFiles(fileChanges)
              } else {
                // Fallback: extract file names from diff content
                const diffFileMatches = content.match(/diff --git a\/([^\s]+)/g)
                if (diffFileMatches) {
                  const fileChanges: FileChange[] = diffFileMatches.map((match) => {
                    const fileName = match.replace('diff --git a/', '')
                    return {
                      name: fileName,
                      additions: 0,
                      deletions: 0
                    }
                  })
                  setFiles(fileChanges)
                } else {
                  setFiles([])
                }
              }
            } else {
              // Unknown format, set empty
              console.warn('Unknown diff format:', content.substring(0, 100))
              setFiles([])
            }
          } catch (xmlError) {
            console.error('Failed to parse diff as JSON or XML:', jsonError, xmlError)
            setFiles([])
          }
        }
      } else {
        setFiles([])
      }
    } catch (err) {
      console.error('Error fetching task file changes:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch file changes')
      setFiles([])
    } finally {
      if (isInitialLoad) {
        setLoading(false)
      }
    }
  }

  useEffect(() => {
    if (taskId && variationId !== undefined) {
      fetchFileChanges(true)
      
      // Only poll if task is still running
      if (taskStatus === "Open" || !taskStatus) {
        const interval = setInterval(() => fetchFileChanges(false), 3000)
        return () => clearInterval(interval)
      }
    }
  }, [taskId, variationId, taskStatus])

  return {
    files,
    loading,
    error,
  }
}