'use client'

import { createContext, useContext, useEffect, useState } from 'react'

interface User {
  id: string
  email: string
  name: string | null
  github_username: string | null
  is_active: boolean
  is_superuser: boolean
}

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  login: (token: string, user: User) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Only run once on mount to avoid infinite loops
    let mounted = true
    
    const loadStoredAuth = () => {
      if (!mounted) return
      
      try {
        const storedToken = localStorage.getItem('github_token')
        const storedUser = localStorage.getItem('user')
        
        if (storedToken && storedUser) {
          const parsedUser = JSON.parse(storedUser)
          if (mounted) {
            setToken(storedToken)
            setUser(parsedUser)
          }
        }
      } catch (error) {
        console.error('Failed to parse stored user:', error)
        localStorage.removeItem('github_token')
        localStorage.removeItem('user')
      } finally {
        if (mounted) {
          setIsLoading(false)
        }
      }
    }

    loadStoredAuth()
    
    return () => {
      mounted = false
    }
  }, [])

  const login = (newToken: string, newUser: User) => {
    // Prevent duplicate logins with the same data
    if (token === newToken && user && user.id === newUser.id) {
      return
    }
    
    setToken(newToken)
    setUser(newUser)
    localStorage.setItem('github_token', newToken)
    localStorage.setItem('user', JSON.stringify(newUser))
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('github_token')
    localStorage.removeItem('user')
  }

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}