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
  /** Owning organisation or user */
  owner?: {
    login: string
  }
}

export interface GitHubBranch {
  name: string
  commit: {
    sha: string
  }
}

export function useGitHubRepos(token: string | null, orgLogins: string[] = []) {
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
        // Fetch all pages (GitHub API paginates at 100 max per_page)
        let page = 1
        const allRepos: GitHubRepo[] = []
        // Fetch user repos first
        while (true) {
          const resp = await fetch(`https://api.github.com/user/repos?sort=updated&per_page=100&page=${page}`, {
            headers: {
              Authorization: `token ${token}`,
              Accept: 'application/vnd.github.v3+json',
            },
          })

          if (!resp.ok) {
            setError('Failed to fetch repositories')
            break
          }

          const data: GitHubRepo[] = await resp.json()
          allRepos.push(...data)

          if (data.length < 100 || allRepos.length >= 300) {
            // Break if last page (<100) or safety cap reached
            break
          }

          page += 1
        }

        // Fetch repos for each additional organisation provided
        for (const org of orgLogins) {
          let orgPage = 1
          while (true) {
            const respOrg = await fetch(`https://api.github.com/orgs/${org}/repos?sort=updated&per_page=100&page=${orgPage}`, {
              headers: {
                Authorization: `token ${token}`,
                Accept: 'application/vnd.github.v3+json',
              },
            })

            if (!respOrg.ok) {
              // If the request fails (e.g., 404 or permission denied), stop trying this org
              console.warn(`Failed to fetch repos for org ${org}:`, respOrg.status)
              break
            }

            const orgData: GitHubRepo[] = await respOrg.json()
            allRepos.push(...orgData)

            if (orgData.length < 100 || orgData.length === 0) {
              break
            }
            // Safety cap similar to user repos
            if (allRepos.length >= 1000) {
              break
            }

            orgPage += 1
          }
        }

        // Deduplicate by repo id (should be unique across GitHub)
        const deduped = Array.from(new Map(allRepos.map(r => [r.id, r])).values())

        setRepos(deduped)
      } catch (err) {
        setError('Network error fetching repositories')
        console.error('GitHub repos fetch error:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchRepos()
  }, [token, orgLogins])

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