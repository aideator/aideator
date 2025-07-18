'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Icons } from '@/components/ui/icons'

interface GitHubLoginButtonProps {
  className?: string
  onSuccess?: (user: any, token: string) => void
  onError?: (error: string) => void
}

export function GitHubLoginButton({ 
  className, 
  onSuccess, 
  onError 
}: GitHubLoginButtonProps) {
  const [isLoading, setIsLoading] = useState(false)

  const handleGitHubLogin = async () => {
    setIsLoading(true)
    try {
      // Redirect to GitHub OAuth via backend
      window.location.href = 'http://localhost:8000/api/v1/auth/github/login'
    } catch (error) {
      console.error('GitHub login error:', error)
      onError?.('Failed to initiate GitHub login')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Button
      variant="outline"
      onClick={handleGitHubLogin}
      disabled={isLoading}
      className={className}
    >
      {isLoading ? (
        <Icons.spinner className="mr-2 h-4 w-4 animate-spin" />
      ) : (
        <Icons.gitHub className="mr-2 h-4 w-4" />
      )}
      Sign in with GitHub
    </Button>
  )
}