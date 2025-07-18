import { useLocalStorage } from "@/hooks/use-local-storage"

/**
 * Hook for managing additional GitHub organisations that the user manually adds.
 * Organisations are persisted to localStorage so they are available across sessions.
 */
export function useUserOrgs() {
  // Persist list under a stable key
  const [orgs, setOrgs] = useLocalStorage<string[]>("user_orgs", [])

  const addOrg = (org: string) => {
    const normalised = org.trim()
    if (!normalised) return
    setOrgs((prev) => {
      if (prev.includes(normalised)) return prev
      return [...prev, normalised]
    })
  }

  const removeOrg = (org: string) => {
    setOrgs((prev) => prev.filter((o) => o !== org))
  }

  return { orgs, addOrg, removeOrg }
}