"use client"

import React, { useMemo, useState, useCallback } from "react"
import { Github } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectLabel, SelectSeparator, SelectTrigger, SelectValue } from "@/components/ui/select"
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
  const { repos, loading } = useGitHubRepos(token)

  // Search term state
  const [search, setSearch] = useState("")

  // Recent repos are tracked in localStorage
  const [recentRepos, setRecentRepos] = useLocalStorage<string[]>("recent_repos", [])

  // Update recent repos list whenever user selects
  const handleValueChange = useCallback(
    (newValue: string) => {
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
            <mark key={idx} className="bg-yellow-600/40 text-yellow-50 dark:text-yellow-100 rounded-sm">
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

  // Filter based on search
  const filteredRepos = useMemo(() => {
    if (!search) return allRepos
    const lower = search.toLowerCase()
    return allRepos.filter((r) => r.full_name.toLowerCase().includes(lower))
  }, [allRepos, search])

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

  return (
    <Select value={value || ""} onValueChange={handleValueChange} disabled={disabled || loading}>
      <SelectTrigger className={cn("w-auto flex gap-2", triggerClassName)}>
        <Github className="w-4 h-4 opacity-80" />
        <SelectValue placeholder={loading ? "Loading repos..." : "Select repository"} />
      </SelectTrigger>
      <SelectContent className="max-w-sm">
        {/* Search Input */}
        <div className="p-2 sticky top-0 bg-popover z-10">
          <input
            autoFocus
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search repositories..."
            className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        {/* Recents */}
        {recentFiltered.length > 0 && (
          <>
            <SelectLabel>Recent</SelectLabel>
            {recentFiltered.map((repo) => (
              <SelectItem key={repo.html_url} value={repo.html_url}>
                <div className="flex flex-col text-left">
                  {highlightMatch(repo.name, search)}
                  <span className="text-xs opacity-60">
                    {highlightMatch(repo.owner?.login || repo.full_name.split("/")[0], search)}
                  </span>
                </div>
              </SelectItem>
            ))}
            <SelectSeparator />
          </>
        )}

        {/* Grouped by organisation */}
        {groupedRepos.map(([org, repos]) => (
          <React.Fragment key={org}>
            <SelectLabel>{org}</SelectLabel>
            {repos.map((repo) => (
              <SelectItem key={repo.html_url} value={repo.html_url}>
                <div className="flex flex-col text-left">
                  {highlightMatch(repo.name, search)}
                  <span className="text-xs opacity-60">
                    {highlightMatch(org, search)}
                  </span>
                </div>
              </SelectItem>
            ))}
            <SelectSeparator />
          </React.Fragment>
        ))}
      </SelectContent>
    </Select>
  )
}