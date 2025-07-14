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
  apiKey: string | null
  loading: boolean
  signIn: (token: string, user: User) => Promise<void>
  signOut: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [apiKey, setApiKey] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  const pathname = usePathname()

  // Function to mint API key using JWT token
  const mintApiKey = async (jwtToken: string): Promise<string> => {
    console.log('🔑 Attempting to mint API key...')
    console.log('JWT token:', jwtToken ? `${jwtToken.substring(0, 20)}...` : 'null')
    
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/api-keys`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${jwtToken}`
      },
      body: JSON.stringify({
        name: 'Web Client API Key',
        scopes: ['runs:create', 'runs:read', 'sessions:create', 'sessions:read']
      })
    })

    console.log('API key creation response status:', response.status)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('Failed to create API key. Response:', errorText)
      throw new Error(`Failed to create API key: ${response.status} - ${errorText}`)
    }

    const data = await response.json()
    console.log('✅ API key created successfully:', data.api_key ? `${data.api_key.substring(0, 10)}...` : 'null')
    return data.api_key
  }

  useEffect(() => {
    // Check for stored auth data
    const storedToken = localStorage.getItem("access_token")
    const storedUser = localStorage.getItem("user")
    const storedApiKey = localStorage.getItem("api_key")

    if (storedToken && storedUser && storedApiKey) {
      setToken(storedToken)
      setApiKey(storedApiKey)
      try {
        setUser(JSON.parse(storedUser))
      } catch (e) {
        console.error("Failed to parse user data:", e)
        localStorage.removeItem("user")
        localStorage.removeItem("access_token")
        localStorage.removeItem("api_key")
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
        const storedApiKey = localStorage.getItem("api_key")
        if (!storedToken || !storedApiKey) {
          router.push("/signin")
        } else {
          // Try to reload user from localStorage
          const storedUser = localStorage.getItem("user")
          if (storedUser) {
            try {
              setUser(JSON.parse(storedUser))
              setToken(storedToken)
              setApiKey(storedApiKey)
            } catch {
              router.push("/signin")
            }
          }
        }
      }, 100)
      
      return () => clearTimeout(timer)
    }
  }, [user, loading, pathname, router])

  const signIn = async (newToken: string, newUser: User) => {
    console.log('🚀 SignIn called with:', { 
      hasToken: !!newToken, 
      tokenStart: newToken ? newToken.substring(0, 20) + '...' : 'null',
      user: newUser.email 
    })
    
    // Prevent redundant updates
    if (token === newToken && user?.id === newUser.id && apiKey) {
      console.log('⏭️ Skipping redundant signIn')
      router.push("/")
      return
    }
    
    try {
      // Mint API key using JWT token - no fallback, fail hard
      console.log('🔄 Minting API key...')
      const newApiKey = await mintApiKey(newToken)
      console.log('✅ API key minted successfully')
      
      console.log('💾 Storing auth data...')
      setToken(newToken)
      setUser(newUser)
      setApiKey(newApiKey)
      
      localStorage.setItem("access_token", newToken)
      localStorage.setItem("user", JSON.stringify(newUser))
      localStorage.setItem("api_key", newApiKey)
      
      console.log('✅ Auth context updated, redirecting to home...')
      // Use replace instead of push to avoid history issues
      router.replace("/")
    } catch (error) {
      console.error('❌ SignIn failed:', error)
      // Set token and user even if API key creation fails
      // This way we can debug the JWT authentication issue
      setToken(newToken)
      setUser(newUser)
      setApiKey(null) // No API key, will rely on JWT only
      
      localStorage.setItem("access_token", newToken)
      localStorage.setItem("user", JSON.stringify(newUser))
      localStorage.removeItem("api_key") // Remove any stale API key
      
      console.log('⚠️ Continuing with JWT-only auth for debugging...')
      router.replace("/")
    }
  }

  const signOut = () => {
    setToken(null)
    setUser(null)
    setApiKey(null)
    localStorage.removeItem("access_token")
    localStorage.removeItem("user")
    localStorage.removeItem("api_key")
    router.push("/signin")
  }

  return (
    <AuthContext.Provider value={{ user, token, apiKey, loading, signIn, signOut }}>
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