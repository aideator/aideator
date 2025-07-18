'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { AlertCircle, X } from 'lucide-react'

export function OAuthError() {
  const [error, setError] = useState<string | null>(null)
  const [isVisible, setIsVisible] = useState(false)
  const searchParams = useSearchParams()

  useEffect(() => {
    const errorParam = searchParams.get('error')
    if (errorParam) {
      setError(errorParam)
      setIsVisible(true)
    }
  }, [searchParams])

  const getErrorMessage = (errorCode: string) => {
    switch (errorCode) {
      case 'oauth_error':
        return 'GitHub OAuth authorization failed. Please try again.'
      case 'no_code':
        return 'No authorization code received from GitHub.'
      case 'token_exchange_failed':
        return 'Failed to exchange code for access token.'
      case 'no_access_token':
        return 'No access token received from GitHub.'
      case 'user_creation_failed':
        return 'Failed to create or find user account.'
      case 'missing_data':
        return 'Missing authentication data from callback.'
      case 'callback_failed':
        return 'OAuth callback processing failed.'
      case 'oauth_callback_failed':
        return 'OAuth callback encountered an error.'
      default:
        return 'An unknown authentication error occurred.'
    }
  }

  if (!isVisible || !error) return null

  return (
    <div className="fixed top-4 right-4 max-w-md bg-red-50 border border-red-200 rounded-lg p-4 shadow-lg z-50">
      <div className="flex items-start">
        <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
        <div className="flex-1">
          <h3 className="text-sm font-medium text-red-800">Authentication Error</h3>
          <p className="text-sm text-red-700 mt-1">{getErrorMessage(error)}</p>
        </div>
        <button
          onClick={() => setIsVisible(false)}
          className="ml-3 flex-shrink-0 text-red-400 hover:text-red-600"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}