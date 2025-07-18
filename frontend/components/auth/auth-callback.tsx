'use client'

import { useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from './auth-provider'

export function AuthCallback() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { login } = useAuth()

  useEffect(() => {
    const handleCallback = async () => {
      const token = searchParams.get('token')
      const userId = searchParams.get('user_id')
      const email = searchParams.get('email')
      const name = searchParams.get('name')
      const githubUsername = searchParams.get('github_username')
      const error = searchParams.get('error')

      console.log('Callback received:', { 
        token: !!token, 
        userId: !!userId, 
        email: !!email,
        name: !!name,
        githubUsername: !!githubUsername,
        error 
      })

      if (error) {
        console.error('GitHub OAuth error:', error)
        router.push(`/?error=${error}`)
        return
      }

      if (!token || !userId || !email) {
        console.error('Missing required authentication data', { 
          token: !!token, 
          userId: !!userId, 
          email: !!email 
        })
        console.log('All search params:', Object.fromEntries(searchParams.entries()))
        router.push('/?error=missing_data')
        return
      }

      try {
        // Build user data from individual parameters
        const userData = {
          id: userId,
          email: decodeURIComponent(email),
          name: name ? decodeURIComponent(name) : null,
          github_username: githubUsername || null,
          is_active: true,
          is_superuser: false,
        }
        
        console.log('Constructed user data:', userData)
        
        // Store authentication data
        login(token, userData)
        
        // Redirect to home page
        router.push('/')
      } catch (error) {
        console.error('Callback processing error:', error)
        router.push('/?error=callback_failed')
      }
    }

    // Only run if we have search params (prevents running on every render)
    if (searchParams.toString()) {
      handleCallback()
    }
  }, [searchParams, router, login])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4"></div>
        <p className="text-gray-600">Completing sign in...</p>
      </div>
    </div>
  )
}