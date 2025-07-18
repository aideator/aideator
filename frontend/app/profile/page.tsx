'use client'
import { useState } from "react"
import { useUserOrgs } from "@/hooks/use-user-orgs"
import { useAuth } from "@/components/auth/auth-provider"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { X, PlusCircle, RefreshCw } from "lucide-react"
import { componentTokens, commonTypographyCombinations, getBodyClasses, getGapSpacing, getMarginSpacing } from "@/lib/design-tokens"

export default function ProfilePage() {
  const { user } = useAuth()
  const { orgs, addOrg, removeOrg } = useUserOrgs()

  const [newOrg, setNewOrg] = useState("")
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Validate & add organisation
  const handleAdd = async () => {
    const org = newOrg.trim()
    if (!org) return
    setAdding(true)
    setError(null)
    try {
      const resp = await fetch(`https://api.github.com/orgs/${org}`)
      if (resp.ok) {
        addOrg(org)
        setNewOrg("")
      } else if (resp.status === 404) {
        setError("Organisation not found on GitHub")
      } else {
        setError("Failed to validate organisation")
      }
    } catch (e) {
      console.error(e)
      setError("Network error validating organisation")
    } finally {
      setAdding(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault()
      handleAdd()
    }
  }

  return (
    <div className={componentTokens.ui.layout.page}>
      <div className={componentTokens.ui.layout.container}>
        <h1 className={`${commonTypographyCombinations.pageTitle} ${getMarginSpacing('lg')}`}>Profile</h1>

        {user && (
          <div className={`${getMarginSpacing('lg')}`}>Logged in as <span className="font-medium">{user.name || user.email}</span></div>
        )}

        <section className={componentTokens.ui.card.primary}>
          <h2 className={`${commonTypographyCombinations.sectionHeader} ${getMarginSpacing('md')}`}>GitHub Organisations</h2>

          <div className={`flex items-center ${getGapSpacing('sm')} ${getMarginSpacing('md')}`}>
            <Input
              placeholder="Add organisation by name"
              value={newOrg}
              onChange={(e) => setNewOrg(e.target.value)}
              onKeyDown={handleKeyDown}
              className="w-64"
              disabled={adding}
            />
            <Button
              variant="outline"
              onClick={handleAdd}
              disabled={adding}
            >
              {adding ? <RefreshCw className="w-4 h-4 animate-spin" /> : <PlusCircle className="w-4 h-4 mr-1" />} Add
            </Button>
          </div>
          {error && <p className={`text-red-500 ${getMarginSpacing('sm')}`}>{error}</p>}

          {orgs.length === 0 ? (
            <p className={getBodyClasses('muted')}>No additional organisations added.</p>
          ) : (
            <ul className={`flex flex-wrap ${getGapSpacing('sm')}`}>
              {orgs.map((org) => (
                <li key={org} className="relative group">
                  <span className={`inline-flex items-center rounded-full border border-gray-700 px-3 py-1 text-sm ${getBodyClasses('secondary')}`}>{org}</span>
                  <button
                    aria-label="Remove organisation"
                    onClick={() => removeOrg(org)}
                    className="absolute -top-2 -right-2 hidden group-hover:block bg-gray-800 rounded-full p-0.5 text-gray-300 hover:text-red-400"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}