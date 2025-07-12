"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { CheckCircle } from "lucide-react"

export default function AuthSuccessPage() {
  const router = useRouter()
  const { signIn } = useAuth()

  useEffect(() => {
    // Add a small delay to ensure localStorage is set from the OAuth callback
    const timer = setTimeout(() => {
      // Read auth data from localStorage
      const token = localStorage.getItem("access_token")
      const userStr = localStorage.getItem("user")
      
      console.log("Auth success page - token:", token ? "exists" : "missing")
      console.log("Auth success page - user:", userStr ? "exists" : "missing")
      
      if (token && userStr) {
        try {
          const user = JSON.parse(userStr)
          // Use the signIn method to properly set auth state
          signIn(token, user)
        } catch (e) {
          console.error("Failed to parse auth data:", e)
          router.push("/signin?error=auth_failed")
        }
      } else {
        // No auth data found
        console.error("No auth data in localStorage")
        router.push("/signin?error=no_auth_data")
      }
    }, 100)
    
    return () => clearTimeout(timer)
  }, [router, signIn])

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-xl text-gray-50 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            Authentication Successful
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-400">Setting up your account...</p>
        </CardContent>
      </Card>
    </div>
  )
}