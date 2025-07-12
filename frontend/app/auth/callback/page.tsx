"use client"

import { useEffect, useState } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2 } from "lucide-react"

export default function AuthCallbackPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const { signIn, user } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  useEffect(() => {
    // If already authenticated, redirect immediately
    if (user) {
      router.replace("/")
      return
    }
    
    // Prevent double processing
    if (isProcessing) {
      return
    }
    
    const handleCallback = async () => {
      // Check if we have encoded auth data from backend redirect
      const encodedData = searchParams.get("data")
      
      if (encodedData) {
        setIsProcessing(true)
        try {
          // Decode the base64 data
          const decodedData = atob(encodedData)
          const authData = JSON.parse(decodedData)
          
          if (authData.token && authData.user) {
            // Store in localStorage and update auth context
            localStorage.setItem("access_token", authData.token)
            localStorage.setItem("user", JSON.stringify(authData.user))
            
            // Use the signIn method to properly set auth state
            signIn(authData.token, authData.user)
          } else {
            throw new Error("Invalid auth data structure")
          }
        } catch (err) {
          setError("Failed to process authentication data")
          setTimeout(() => {
            router.push("/signin?error=auth_failed")
          }, 2000)
        }
        return
      }

      // Legacy flow - shouldn't happen with current setup
      const code = searchParams.get("code")
      const state = searchParams.get("state")

      if (!code) {
        setError("No authorization code received")
        setTimeout(() => {
          router.push("/signin?error=no_code")
        }, 2000)
        return
      }

      // This shouldn't be reached with the new flow
      setError("Invalid authentication flow")
      setTimeout(() => {
        router.push("/signin?error=invalid_flow")
      }, 2000)
    }

    handleCallback()
  }, [searchParams, router, signIn, user, isProcessing])

  if (error) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
        <Card className="w-full max-w-md bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle className="text-xl text-red-400">Authentication Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-300">{error}</p>
            <p className="text-sm text-gray-500 mt-2">Redirecting to sign in...</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-xl text-gray-50 flex items-center gap-2">
            <Loader2 className="w-5 h-5 animate-spin" />
            Signing you in...
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-400">Please wait while we complete your authentication.</p>
        </CardContent>
      </Card>
    </div>
  )
}