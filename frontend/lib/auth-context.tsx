"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from "react"
import { useRouter, usePathname } from "next/navigation"

interface User {
  id: string
  email: string
  full_name: string
  github_username?: string
  github_avatar_url?: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  loading: boolean
  signIn: (token: string, user: User) => void
  signOut: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    // Check for stored auth data
    const storedToken = localStorage.getItem("access_token")
    const storedUser = localStorage.getItem("user")

    if (storedToken && storedUser) {
      setToken(storedToken)
      try {
        setUser(JSON.parse(storedUser))
      } catch (e) {
        console.error("Failed to parse user data:", e)
        localStorage.removeItem("user")
        localStorage.removeItem("access_token")
      }
    }

    setLoading(false)
  }, [])

  useEffect(() => {
    // Redirect to sign-in if not authenticated and not already on sign-in page
    if (!loading && !user && pathname !== "/signin" && pathname !== "/auth/callback" && pathname !== "/auth/success" && !pathname.startsWith("/api")) {
      // Add a small delay to allow localStorage to be read after OAuth redirect
      const timer = setTimeout(() => {
        // Re-check localStorage one more time before redirecting
        const storedToken = localStorage.getItem("access_token")
        if (!storedToken) {
          router.push("/signin")
        } else {
          // Try to reload user from localStorage
          const storedUser = localStorage.getItem("user")
          if (storedUser) {
            try {
              setUser(JSON.parse(storedUser))
              setToken(storedToken)
            } catch {
              router.push("/signin")
            }
          }
        }
      }, 100)
      
      return () => clearTimeout(timer)
    }
  }, [user, loading, pathname, router])

  const signIn = (newToken: string, newUser: User) => {
    // Prevent redundant updates
    if (token === newToken && user?.id === newUser.id) {
      router.push("/")
      return
    }
    
    setToken(newToken)
    setUser(newUser)
    localStorage.setItem("access_token", newToken)
    localStorage.setItem("user", JSON.stringify(newUser))
    
    // Use replace instead of push to avoid history issues
    router.replace("/")
  }

  const signOut = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem("access_token")
    localStorage.removeItem("user")
    router.push("/signin")
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}