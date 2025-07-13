"use client"

import { Github } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { BrainCircuit } from "lucide-react"
import { useSearchParams } from "next/navigation"
import { useEffect, useState } from "react"

export default function SignInPage() {
  const searchParams = useSearchParams()
  const [error, setError] = useState<string | null>(null)
  
  useEffect(() => {
    const errorParam = searchParams.get("error")
    if (errorParam) {
      if (errorParam === "access_denied") {
        setError("GitHub authorization was cancelled")
      } else if (errorParam === "no_code") {
        setError("No authorization code received from GitHub")
      } else if (errorParam === "auth_failed") {
        setError("Failed to process authentication data")
      } else if (errorParam === "no_auth_data") {
        setError("No authentication data received")
      } else if (errorParam === "storage_failed") {
        setError("Failed to save authentication data")
      } else {
        setError("Authentication failed. Please try again.")
      }
    }
  }, [searchParams])
  const handleGitHubSignIn = () => {
    // Clear any existing auth data first
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    
    // Use backend OAuth endpoint instead of building URL manually
    const state = Math.random().toString(36).substring(7)
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const githubAuthUrl = `${apiUrl}/api/v1/github/auth?state=${state}`
    
    window.location.href = githubAuthUrl
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-start justify-center p-4 pt-40">
      <Card className="w-full max-w-md bg-gray-900 border-gray-800">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <BrainCircuit className="w-12 h-12 text-gray-300" />
          </div>
          <CardTitle className="text-2xl font-bold text-gray-50">Welcome to AIdeator</CardTitle>
          <CardDescription className="text-gray-400">
            Sign in to access your AI-powered development environment
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <div className="bg-red-900/20 border border-red-900/50 rounded p-3 text-sm text-red-400">
              {error}
            </div>
          )}
          <Button 
            onClick={handleGitHubSignIn}
            className="w-full bg-gray-800 hover:bg-gray-700 text-white border border-gray-700"
            size="lg"
          >
            <Github className="w-5 h-5 mr-2" />
            Sign in with GitHub
          </Button>
          <p className="text-center text-sm text-gray-500">
            By signing in, you agree to our Terms of Service and Privacy Policy
          </p>
        </CardContent>
      </Card>
    </div>
  )
}