'use client'

import React, { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Loader2, User, Key, LogOut, LogIn, ChevronDown, Copy, Check } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export const AuthStatus: React.FC = () => {
  const { user, token, apiKey, isLoading, isAuthenticated, logout, autoLoginDev } = useAuth()
  const [copiedKey, setCopiedKey] = useState(false)

  useEffect(() => {
    // Log auth state for debugging
    console.log('Auth Status:', {
      isAuthenticated,
      hasToken: !!token,
      hasApiKey: !!apiKey,
      user: user?.email,
    })
  }, [isAuthenticated, token, apiKey, user])

  const copyApiKey = () => {
    if (apiKey) {
      navigator.clipboard.writeText(apiKey)
      setCopiedKey(true)
      setTimeout(() => setCopiedKey(false), 2000)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-neutral-white shadow-lg border border-neutral-fog">
        <Loader2 className="h-4 w-4 animate-spin text-ai-primary" />
        <span className="text-sm text-neutral-shadow">Loading...</span>
      </div>
    )
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="ghost" 
          className="flex items-center gap-2 px-3 py-2 h-auto rounded-lg bg-neutral-white shadow-lg border border-neutral-fog hover:bg-neutral-paper transition-colors"
        >
          <div className="flex items-center gap-2">
            {isAuthenticated ? (
              <>
                <div className="w-2 h-2 rounded-full bg-semantic-success animate-pulse" />
                <User className="h-4 w-4 text-neutral-charcoal" />
                <span className="text-sm font-medium text-neutral-charcoal">
                  {user?.email?.split('@')[0]}
                </span>
              </>
            ) : (
              <>
                <div className="w-2 h-2 rounded-full bg-semantic-error" />
                <span className="text-sm text-neutral-shadow">Not Authenticated</span>
              </>
            )}
          </div>
          <ChevronDown className="h-4 w-4 text-neutral-shadow" />
        </Button>
      </DropdownMenuTrigger>
      
      <DropdownMenuContent align="end" className="w-80 bg-neutral-white shadow-xl border border-neutral-fog">
        {isAuthenticated && user ? (
          <>
            <DropdownMenuLabel>Account Details</DropdownMenuLabel>
            <DropdownMenuSeparator />
            
            <div className="px-2 py-3 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-neutral-shadow">Email:</span>
                <span className="font-medium">{user.email}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-neutral-shadow">Name:</span>
                <span className="font-medium">{user.full_name}</span>
              </div>
              {user.company && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-neutral-shadow">Company:</span>
                  <span className="font-medium">{user.company}</span>
                </div>
              )}
            </div>
            
            <DropdownMenuSeparator />
            
            <div className="px-2 py-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-neutral-shadow flex items-center gap-1">
                  <Key className="h-3 w-3" />
                  API Key
                </span>
                <Badge variant={apiKey ? "secondary" : "outline"} className="text-xs">
                  {apiKey ? 'Active' : 'Not Set'}
                </Badge>
              </div>
              {apiKey && (
                <div className="flex items-center gap-2">
                  <code className="flex-1 bg-neutral-fog rounded px-2 py-1 text-xs font-mono truncate">
                    {apiKey.substring(0, 20)}...
                  </code>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={copyApiKey}
                    className="h-7 w-7 p-0"
                  >
                    {copiedKey ? (
                      <Check className="h-3 w-3 text-semantic-success" />
                    ) : (
                      <Copy className="h-3 w-3" />
                    )}
                  </Button>
                </div>
              )}
            </div>
            
            <DropdownMenuSeparator />
            
            <DropdownMenuItem onClick={logout} className="text-semantic-error">
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </DropdownMenuItem>
          </>
        ) : (
          <>
            <DropdownMenuLabel>Not Authenticated</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem 
              onClick={autoLoginDev}
              disabled={process.env.NODE_ENV !== 'development'}
            >
              <LogIn className="h-4 w-4 mr-2" />
              {process.env.NODE_ENV === 'development' ? 'Dev Auto-Login' : 'Login Required'}
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}