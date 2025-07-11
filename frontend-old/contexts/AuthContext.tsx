'use client'

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'

interface User {
  id: string
  email: string
  full_name: string
  company?: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  apiKey: string | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  autoLoginDev: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  apiKey: null,
  isLoading: true,
  isAuthenticated: false,
  login: async () => {},
  logout: () => {},
  autoLoginDev: async () => {},
})

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [apiKey, setApiKey] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!token && !!user

  const login = useCallback(async (email: string, password: string) => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) {
        throw new Error('Login failed')
      }

      const data = await response.json()
      
      // Store token
      localStorage.setItem('auth_token', data.access_token)
      setToken(data.access_token)

      // Fetch user details
      const userResponse = await fetch('http://localhost:8000/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${data.access_token}`,
        },
      })

      if (userResponse.ok) {
        const userData = await userResponse.json()
        setUser(userData)
      }
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('api_key')
    setToken(null)
    setApiKey(null)
    setUser(null)
  }, [])

  const autoLoginDev = useCallback(async () => {
    try {
      console.log('Attempting development auto-login...')
      
      const response = await fetch('http://localhost:8000/api/v1/auth/dev/test-login')
      
      if (!response.ok) {
        console.error('Dev login failed:', response.status)
        return
      }

      const data = await response.json()
      
      // Store token and API key
      localStorage.setItem('auth_token', data.access_token)
      setToken(data.access_token)
      setUser(data.user)
      
      if (data.api_key) {
        localStorage.setItem('api_key', data.api_key)
        setApiKey(data.api_key)
        console.log('Development API key:', data.api_key)
      }
      
      console.log('Development auto-login successful')
    } catch (error) {
      console.error('Development auto-login error:', error)
    }
  }, [])

  // Check for existing token on mount
  useEffect(() => {
    const checkAuth = async () => {
      const storedToken = localStorage.getItem('auth_token')
      const storedApiKey = localStorage.getItem('api_key')
      
      if (storedToken) {
        setToken(storedToken)
        setApiKey(storedApiKey)
        
        // Verify token by fetching user
        try {
          const response = await fetch('http://localhost:8000/api/v1/auth/me', {
            headers: {
              'Authorization': `Bearer ${storedToken}`,
            },
          })
          
          if (response.ok) {
            const userData = await response.json()
            setUser(userData)
          } else {
            // Token invalid, clear it
            logout()
            // Try auto-login for development
            if (process.env.NODE_ENV === 'development') {
              await autoLoginDev()
            }
          }
        } catch (error) {
          console.error('Auth check error:', error)
          logout()
          // Try auto-login for development
          if (process.env.NODE_ENV === 'development') {
            await autoLoginDev()
          }
        }
      } else if (process.env.NODE_ENV === 'development') {
        // No token, try auto-login for development
        await autoLoginDev()
      }
      
      setIsLoading(false)
    }

    checkAuth()
  }, [logout, autoLoginDev])

  const value = {
    user,
    token,
    apiKey,
    isLoading,
    isAuthenticated,
    login,
    logout,
    autoLoginDev,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}