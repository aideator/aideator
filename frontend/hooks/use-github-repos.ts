'use client'

import { useState, useEffect } from 'react'

export interface GitHubRepo {
  id: number
  name: string
  full_name: string
  html_url: string
  description: string | null
  private: boolean
  default_branch: string
  updated_at: string
}

export interface GitHubBranch {
  name: string
  commit: {
    sha: string
  }
}

export function useGitHubRepos(token: string | null) {
  const [repos, setRepos] = useState<GitHubRepo[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) {
      setRepos([])
      return
    }

    const fetchRepos = async () => {
      setLoading(true)
      setError(null)
      
      try {
        const response = await fetch('https://api.github.com/user/repos?sort=updated&per_page=50', {
          headers: {
            'Authorization': `token ${token}`,
            'Accept': 'application/vnd.github.v3+json'
          }
        })

        if (response.ok) {
          const repoData = await response.json()
          setRepos(repoData)
        } else {
          setError('Failed to fetch repositories')
        }
      } catch (err) {
        setError('Network error fetching repositories')
        console.error('GitHub repos fetch error:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchRepos()
  }, [token])

  return { repos, loading, error }
}

export function useGitHubBranches(token: string | null, repoUrl: string | null) {
  const [branches, setBranches] = useState<GitHubBranch[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token || !repoUrl) {
      setBranches([])
      return
    }

    // Extract repo full name from URL
    let repoFullName: string | null = null
    
    if (repoUrl.includes('github.com/')) {
      const urlMatch = repoUrl.match(/github\.com\/([^/]+\/[^/]+)/)
      if (urlMatch) {
        repoFullName = urlMatch[1]
      }
    } else {
      // If it's not a full URL, assume it's already a full name
      repoFullName = repoUrl
    }

    if (!repoFullName) {
      setBranches([])
      return
    }

    const fetchBranches = async () => {
      setLoading(true)
      setError(null)
      
      try {
        const response = await fetch(`https://api.github.com/repos/${repoFullName}/branches`, {
          headers: {
            'Authorization': `token ${token}`,
            'Accept': 'application/vnd.github.v3+json'
          }
        })

        if (response.ok) {
          const branchData = await response.json()
          setBranches(branchData)
        } else {
          setError('Failed to fetch branches')
        }
      } catch (err) {
        setError('Network error fetching branches')
        console.error('GitHub branches fetch error:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchBranches()
  }, [token, repoUrl])

  return { branches, loading, error }
}