"use client"

import { useState, useEffect, useMemo } from "react"
import { Search, Check, Clock, Building2, Github } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import { GitHubRepo } from "@/hooks/use-github-repos"

interface RepositorySelectorProps {
  repos: GitHubRepo[]
  selectedRepo: string
  onRepoSelect: (repoUrl: string) => void
  loading?: boolean
  token?: string | null
  demoRepoUrl?: string
}

interface RecentRepo {
  url: string
  name: string
  organization: string
  lastUsed: number
}

export function RepositorySelector({
  repos,
  selectedRepo,
  onRepoSelect,
  loading = false,
  token,
  demoRepoUrl = "https://github.com/aideator/helloworld"
}: RepositorySelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [recentRepos, setRecentRepos] = useState<RecentRepo[]>([])

  // Load recent repos from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('recent_repos')
    if (stored) {
      try {
        setRecentRepos(JSON.parse(stored))
      } catch (e) {
        console.error('Failed to parse recent repos:', e)
      }
    }
  }, [])

  // Group repos by organization
  const reposByOrg = useMemo(() => {
    const groups: Record<string, GitHubRepo[]> = {}
    
    repos.forEach(repo => {
      const [org] = repo.full_name.split('/')
      if (!groups[org]) {
        groups[org] = []
      }
      groups[org].push(repo)
    })
    
    return groups
  }, [repos])

  // Filter repos based on search query
  const filteredRepos = useMemo(() => {
    if (!searchQuery.trim()) return repos
    
    const query = searchQuery.toLowerCase()
    return repos.filter(repo => 
      repo.full_name.toLowerCase().includes(query) ||
      repo.name.toLowerCase().includes(query) ||
      (repo.description && repo.description.toLowerCase().includes(query))
    )
  }, [repos, searchQuery])

  // Filter recent repos based on search query
  const filteredRecentRepos = useMemo(() => {
    if (!searchQuery.trim()) return recentRepos
    
    const query = searchQuery.toLowerCase()
    return recentRepos.filter(repo => 
      repo.name.toLowerCase().includes(query) ||
      repo.organization.toLowerCase().includes(query)
    )
  }, [recentRepos, searchQuery])

  // Filter organizations based on search query
  const filteredOrgs = useMemo(() => {
    if (!searchQuery.trim()) return Object.keys(reposByOrg)
    
    const query = searchQuery.toLowerCase()
    return Object.keys(reposByOrg).filter(org => 
      org.toLowerCase().includes(query) ||
      reposByOrg[org].some(repo => 
        repo.full_name.toLowerCase().includes(query) ||
        repo.name.toLowerCase().includes(query)
      )
    )
  }, [reposByOrg, searchQuery])

  // Highlight matching text
  const highlightText = (text: string, query: string) => {
    if (!query.trim()) return text
    
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
    const parts = text.split(regex)
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <span key={index} className="bg-yellow-200 dark:bg-yellow-800 font-medium">
          {part}
        </span>
      ) : part
    )
  }

  // Handle repo selection
  const handleRepoSelect = (repoUrl: string, repoName: string, organization: string) => {
    onRepoSelect(repoUrl)
    setIsOpen(false)
    setSearchQuery("")
    
    // Update recent repos
    const newRecent: RecentRepo = {
      url: repoUrl,
      name: repoName,
      organization,
      lastUsed: Date.now()
    }
    
    const updated = [
      newRecent,
      ...recentRepos.filter(r => r.url !== repoUrl)
    ].slice(0, 10) // Keep only 10 most recent
    
    setRecentRepos(updated)
    localStorage.setItem('recent_repos', JSON.stringify(updated))
  }

  // Get current repo display info
  const getCurrentRepoInfo = () => {
    if (!selectedRepo) return { name: "Select repository", org: "" }
    
    if (selectedRepo === demoRepoUrl) {
      return { name: "aideator/helloworld", org: "aideator" }
    }
    
    const repo = repos.find(r => r.html_url === selectedRepo)
    if (repo) {
      const [org, name] = repo.full_name.split('/')
      return { name, org }
    }
    
    // Fallback for unknown repos
    const urlMatch = selectedRepo.match(/github\.com\/([^/]+\/[^/]+)/)
    if (urlMatch) {
      const [org, name] = urlMatch[1].split('/')
      return { name, org }
    }
    
    return { name: "Unknown repository", org: "" }
  }

  const currentRepo = getCurrentRepoInfo()

  return (
    <div className="relative">
      <Button
        variant="outline"
        onClick={() => setIsOpen(!isOpen)}
        disabled={loading}
        className="w-auto justify-between min-w-[200px]"
      >
        <div className="flex items-center gap-2">
          <Github className="w-4 h-4" />
          <span className="truncate">
            {loading ? "Loading repos..." : currentRepo.name}
          </span>
        </div>
      </Button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 w-80 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg z-50">
          {/* Search Input */}
          <div className="p-3 border-b border-slate-200 dark:border-slate-700">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Search repositories..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
                autoFocus
              />
            </div>
          </div>

          <ScrollArea className="max-h-96">
            {/* Recent Repositories */}
            {filteredRecentRepos.length > 0 && (
              <div className="p-3">
                <div className="flex items-center gap-2 mb-2 text-sm font-medium text-slate-600 dark:text-slate-400">
                  <Clock className="w-4 h-4" />
                  Recent
                </div>
                <div className="space-y-1">
                  {filteredRecentRepos.map((repo) => (
                    <button
                      key={repo.url}
                      onClick={() => handleRepoSelect(repo.url, repo.name, repo.organization)}
                      className={cn(
                        "w-full text-left p-2 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors",
                        selectedRepo === repo.url && "bg-blue-50 dark:bg-blue-900/20"
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="font-medium truncate">
                            {highlightText(repo.name, searchQuery)}
                          </div>
                          <div className="text-xs text-slate-500 dark:text-slate-400 truncate">
                            {highlightText(repo.organization, searchQuery)}
                          </div>
                        </div>
                        {selectedRepo === repo.url && (
                          <Check className="w-4 h-4 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Demo Repository (for unauthenticated users) */}
            {!token && (
              <div className="p-3 border-t border-slate-200 dark:border-slate-700">
                <button
                  onClick={() => handleRepoSelect(demoRepoUrl, "helloworld", "aideator")}
                  className={cn(
                    "w-full text-left p-2 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors",
                    selectedRepo === demoRepoUrl && "bg-blue-50 dark:bg-blue-900/20"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">
                        {highlightText("helloworld", searchQuery)}
                        <span className="text-xs text-slate-500 dark:text-slate-400 ml-1">(demo)</span>
                      </div>
                      <div className="text-xs text-slate-500 dark:text-slate-400 truncate">
                        {highlightText("aideator", searchQuery)}
                      </div>
                    </div>
                    {selectedRepo === demoRepoUrl && (
                      <Check className="w-4 h-4 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                    )}
                  </div>
                </button>
              </div>
            )}

            {/* Organizations and Repositories */}
            {filteredOrgs.length > 0 && (
              <div className="p-3">
                {filteredOrgs.map((org) => (
                  <div key={org} className="mb-4 last:mb-0">
                    <div className="flex items-center gap-2 mb-2 text-sm font-medium text-slate-600 dark:text-slate-400">
                      <Building2 className="w-4 h-4" />
                      {highlightText(org, searchQuery)}
                    </div>
                    <div className="space-y-1 ml-4">
                      {reposByOrg[org]
                        .filter(repo => 
                          !searchQuery.trim() || 
                          repo.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          repo.name.toLowerCase().includes(searchQuery.toLowerCase())
                        )
                        .map((repo) => (
                          <button
                            key={repo.id}
                            onClick={() => handleRepoSelect(repo.html_url, repo.name, org)}
                            className={cn(
                              "w-full text-left p-2 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors",
                              selectedRepo === repo.html_url && "bg-blue-50 dark:bg-blue-900/20"
                            )}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex-1 min-w-0">
                                <div className="font-medium truncate">
                                  {highlightText(repo.name, searchQuery)}
                                  {repo.private && (
                                    <span className="text-xs text-slate-500 dark:text-slate-400 ml-1">(private)</span>
                                  )}
                                </div>
                                <div className="text-xs text-slate-500 dark:text-slate-400 truncate">
                                  {highlightText(org, searchQuery)}
                                </div>
                              </div>
                              {selectedRepo === repo.html_url && (
                                <Check className="w-4 h-4 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                              )}
                            </div>
                          </button>
                        ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* No results */}
            {searchQuery.trim() && filteredRepos.length === 0 && filteredRecentRepos.length === 0 && (
              <div className="p-4 text-center text-slate-500 dark:text-slate-400">
                No repositories found matching "{searchQuery}"
              </div>
            )}
          </ScrollArea>
        </div>
      )}

      {/* Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  )
}