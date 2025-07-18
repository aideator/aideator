"use client"

import React, { useMemo, useState, useCallback, useEffect, useRef } from "react"
import { Github, Search, Check } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectGroup, SelectLabel, SelectSeparator, SelectTrigger, SelectValue } from "@/components/ui/select"
import * as SelectPrimitive from "@radix-ui/react-select"
import { useLocalStorage } from "@/hooks/use-local-storage"
import { useAuth } from "@/components/auth/auth-provider"
import { useGitHubRepos } from "@/hooks/use-github-repos"
import { GitHubRepo } from "@/hooks/use-github-repos"
import { cn } from "@/lib/utils"

interface RepositorySelectProps {
  /** The currently selected repo URL */
  value: string | null
  /** Callback fired when user picks a different repo */
  onChange: (newValue: string) => void
  /** Optional: disable the selector */
  disabled?: boolean
  /** Demo repo URL shown when unauthenticated */
  demoRepoUrl?: string
  /** Additional className for the trigger */
  triggerClassName?: string
}

/**
 * A searchable repository selector with recent-repo memory and grouping by organisation.
 *
 * Design details:
 *  - Search input at top filters in-place, case-insensitive
 *  - "Recent" group (max 5) is shown first (if present)
 *  - Rest of repos are grouped by owner login alphabetically
 *  - Matched query fragments are highlighted using <mark>
 *  - Currently selected repo gets the default Radix check-mark indicator
 */
export function RepositorySelect({
  value,
  onChange,
  disabled,
  demoRepoUrl = "https://github.com/aideator/helloworld",
  triggerClassName,
}: RepositorySelectProps) {
  // Auth state
  const { token } = useAuth()

  // Fetch repos (up to 300) – see updated hook
  const { repos, loading, error } = useGitHubRepos(token)

  // Search term state with debouncing
  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  
  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search)
    }, 300)
    
    return () => clearTimeout(timer)
  }, [search])
  
  // Re-focus search input after debouncing
  useEffect(() => {
    if (searchInputRef.current && debouncedSearch) {
      searchInputRef.current.focus()
    }
  }, [debouncedSearch])

  // Recent repos are tracked in localStorage
  const [recentRepos, setRecentRepos] = useLocalStorage<string[]>("recent_repos", [])
  
  // Search input ref for focus management
  const searchInputRef = useRef<HTMLInputElement>(null)

  // Handle any item selection attempt (including same value)
  const handleItemPointerDown = useCallback(() => {
    setSearch("")
  }, [])

  // Update recent repos list whenever user selects
  const handleValueChange = useCallback(
    (newValue: string) => {
      // Clear search when selection is made
      setSearch("")
      
      // Update recent list – move to front, unique, max 5
      setRecentRepos((prev) => {
        const updated = [newValue, ...prev.filter((r) => r !== newValue)].slice(0, 5)
        return updated
      })
      onChange(newValue)
    },
    [onChange, setRecentRepos]
  )

  // Utility: escape regex special chars
  const escapeRegex = (str: string) => str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")

  // Highlight helper – wraps matches in <mark>
  const highlightMatch = useCallback((text: string, query: string) => {
    if (!query) return text
    const regex = new RegExp(`(${escapeRegex(query)})`, "ig")
    const parts = text.split(regex)
    return (
      <span>
        {parts.map((part, idx) =>
          regex.test(part) ? (
            <mark key={idx} className="bg-accent/50 text-cyan-400 rounded-sm">
              {part}
            </mark>
          ) : (
            <span key={idx}>{part}</span>
          )
        )}
      </span>
    )
  }, [])

  // Combine demo repo when authenticated too
  const allRepos: GitHubRepo[] = useMemo(() => {
    const list = [...repos]
    // Inject demo repo as a pseudo-repo so it can participate in search / recents
    const demoRepo: GitHubRepo = {
      id: -1,
      name: "helloworld",
      full_name: "aideator/helloworld (demo)",
      html_url: demoRepoUrl,
      description: "Demo repository",
      private: false,
      default_branch: "main",
      updated_at: "",
      owner: { login: "aideator" },
    }
    list.push(demoRepo)
    return list
  }, [repos, demoRepoUrl])

  // Filter based on debounced search
  const filteredRepos = useMemo(() => {
    if (!debouncedSearch) return allRepos
    const lower = debouncedSearch.toLowerCase()
    return allRepos.filter((r) => r.full_name.toLowerCase().includes(lower))
  }, [allRepos, debouncedSearch])

  // Recent list intersecting filteredRepos order preserved
  const recentFiltered = useMemo(() => {
    return recentRepos
      .filter((url) => filteredRepos.some((r) => r.html_url === url))
      .map((url) => filteredRepos.find((r) => r.html_url === url)!)
  }, [recentRepos, filteredRepos])

  // Remaining repos (excluding recents) grouped by org
  const groupedRepos = useMemo(() => {
    const remaining = filteredRepos.filter((r) => !recentRepos.includes(r.html_url))
    const groups: Record<string, GitHubRepo[]> = {}
    remaining.forEach((repo) => {
      const org = repo.owner?.login || repo.full_name.split("/")[0]
      if (!groups[org]) groups[org] = []
      groups[org].push(repo)
    })
    // Sort groups alphabetically by org
    const sortedEntries = Object.entries(groups).sort((a, b) => a[0].localeCompare(b[0]))
    // Sort repos inside group alphabetically by name
    sortedEntries.forEach(([key, arr]) => arr.sort((a, b) => a.name.localeCompare(b.name)))
    return sortedEntries
  }, [filteredRepos, recentRepos])

  // Debug logging
  console.log('RepositorySelect debug:', { 
    token: !!token, 
    repos: repos.length, 
    loading, 
    error,
    allRepos: allRepos.length,
    filteredRepos: filteredRepos.length,
    recentFiltered: recentFiltered.length,
    groupedRepos: groupedRepos.length
  })

  return (
    <Select 
      value={value || ""} 
      onValueChange={handleValueChange} 
      disabled={disabled || loading}
      onOpenChange={(open) => {
        if (!open) {
          // Clear search when dropdown closes (after any selection)
          setSearch("")
        }
      }}
    >
      <SelectTrigger className={cn("w-auto flex gap-2", triggerClassName)}>
        <Github className="w-4 h-4 opacity-80" />
        <SelectValue placeholder={loading ? "Loading repos..." : "Select repository"} />
      </SelectTrigger>
      <SelectContent className="max-w-sm p-0">
        {/* Fixed Search Input */}
        <div className="p-2 bg-popover border-b border-border">
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground/50" />
            <input
              ref={searchInputRef}
              key="search-input"
              autoFocus
              type="text"
              value={search}
              onChange={(e) => {
                e.stopPropagation()
                setSearch(e.target.value)
              }}
              onKeyDown={(e) => {
                e.stopPropagation()
              }}
              placeholder="Search repositories..."
              className="w-full rounded-md border border-input bg-background pl-8 pr-3 py-1 text-[11px] placeholder:text-muted-foreground/50 focus:outline-none focus:ring-1 focus:ring-ring focus:border-ring"
            />
          </div>
        </div>
        
        {/* Scrollable Viewport */}
        <div className="max-h-[300px] overflow-y-auto overflow-x-hidden [&::-webkit-scrollbar]:w-[4px] [&::-webkit-scrollbar-track]:bg-popover [&::-webkit-scrollbar-thumb]:bg-muted-foreground/20 [&::-webkit-scrollbar-thumb]:rounded-[2px] [&::-webkit-scrollbar-thumb:hover]:bg-muted-foreground/30" style={{scrollbarWidth: 'thin', scrollbarColor: 'hsl(var(--muted-foreground) / 0.2) hsl(var(--popover))'}}>
          {/* Loading/Error States */}
          {loading && (
            <div className="p-2 text-sm text-muted-foreground">
              Loading repositories...
            </div>
          )}
          
          {error && (
            <div className="p-2 text-sm text-red-500">
              Error: {error}
            </div>
          )}
          
          {!token && !loading && (
            <div className="p-2 text-sm text-muted-foreground">
              Sign in with GitHub to see your repositories
            </div>
          )}
          
          {token && !loading && repos.length === 0 && !error && (
            <div className="p-2 text-sm text-muted-foreground">
              No repositories found
            </div>
          )}
        {/* Recents */}
        {recentFiltered.length > 0 && (
          <SelectGroup>
            <SelectLabel className="text-xs font-normal text-muted-foreground/50 uppercase tracking-wide px-2 py-1 text-[10px]">Recent</SelectLabel>
            {recentFiltered.map((repo) => (
              <SelectItem key={repo.html_url} value={repo.html_url} className="relative py-1 pl-2 pr-8 text-xs hover:bg-accent/50 [&>span:first-child]:hidden" onPointerDown={handleItemPointerDown}>
                <div className="flex flex-col text-left min-w-0 flex-1">
                  <span className="font-medium text-foreground truncate leading-tight text-[11px]">
                    {highlightMatch(repo.name, debouncedSearch)}
                  </span>
                  <span className="text-[10px] text-muted-foreground/70 truncate leading-tight">
                    {highlightMatch(repo.owner?.login || repo.full_name.split("/")[0], debouncedSearch)}
                  </span>
                </div>
                <span className="absolute right-2 top-1/2 -translate-y-1/2 flex h-3.5 w-3.5 items-center justify-center">
                  <SelectPrimitive.ItemIndicator>
                    <Check className="h-3 w-3" />
                  </SelectPrimitive.ItemIndicator>
                </span>
              </SelectItem>
            ))}
            <SelectSeparator className="bg-popover" />
          </SelectGroup>
        )}

        {/* Grouped by organisation */}
        {groupedRepos.map(([org, repos]) => (
          <SelectGroup key={org}>
            <SelectLabel className="text-xs font-normal text-muted-foreground/50 uppercase tracking-wide px-2 py-1 text-[10px]">{org}</SelectLabel>
            {repos.map((repo) => (
              <SelectItem key={repo.html_url} value={repo.html_url} className="relative py-1 pl-2 pr-8 text-xs hover:bg-accent/50 [&>span:first-child]:hidden" onPointerDown={handleItemPointerDown}>
                <div className="flex flex-col text-left min-w-0 flex-1">
                  <span className="font-medium text-foreground truncate leading-tight text-[11px]">
                    {highlightMatch(repo.name, debouncedSearch)}
                  </span>
                  <span className="text-[10px] text-muted-foreground/70 truncate leading-tight">
                    {highlightMatch(org, debouncedSearch)}
                  </span>
                </div>
                <span className="absolute right-2 top-1/2 -translate-y-1/2 flex h-3.5 w-3.5 items-center justify-center">
                  <SelectPrimitive.ItemIndicator>
                    <Check className="h-3 w-3" />
                  </SelectPrimitive.ItemIndicator>
                </span>
              </SelectItem>
            ))}
            <SelectSeparator className="bg-popover" />
          </SelectGroup>
        ))}
        </div>
      </SelectContent>
    </Select>
  )
}