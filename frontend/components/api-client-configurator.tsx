"use client"

import { useEffect } from "react"
import { useAuth } from "@/lib/auth-context"
import { apiClient } from "@/lib/api"

// Component to auto-configure API client with auth context
export function ApiClientConfigurator() {
  const { token, apiKey } = useAuth()
  
  useEffect(() => {
    console.log('🔧 Configuring API client with:', { 
      hasToken: !!token, 
      hasApiKey: !!apiKey,
      tokenStart: token ? token.substring(0, 20) + '...' : 'null',
      apiKeyStart: apiKey ? apiKey.substring(0, 10) + '...' : 'null'
    })
    
    if (token) {
      apiClient.setAuthToken(token)
      console.log('✅ Set JWT token on API client')
    }
    
    if (apiKey) {
      apiClient.setApiKey(apiKey)
      console.log('✅ Set API key on API client')
    }
  }, [token, apiKey])
  
  return null
} 