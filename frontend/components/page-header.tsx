"use client"

import { BrainCircuit, ArrowLeft, Archive, Share, GitPullRequest, FileText } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { sessions } from "@/lib/data"
import { useState, useEffect } from "react"

export function PageHeader() {
  const pathname = usePathname()
  const [isPrCreated, setIsPrCreated] = useState(false)
  
  // Check if we're on a session page
  const sessionMatch = pathname.match(/^\/session\/([^/]+)$/)
  const sessionId = sessionMatch?.[1]
  const session = sessionId ? sessions.find((s) => s.id === sessionId) : null
  
  // Reset PR state when navigating away from session
  useEffect(() => {
    if (!sessionId) {
      setIsPrCreated(false)
    }
  }, [sessionId])
  
  if (session) {
    // Session page header
    return (
      <header className="flex items-center justify-between px-4 py-2 border-b border-gray-800 bg-gray-950">
        <div className="flex items-center gap-4">
          <Link href="/">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="w-5 h-5" />
            </Button>
          </Link>
          <h1 className="text-lg font-medium text-gray-50">{session.title}</h1>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" asChild className="text-gray-300 hover:text-gray-50">
            <a 
              href="http://localhost:8000/docs" 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex items-center gap-2"
            >
              <FileText className="w-4 h-4" />
              API Docs
            </a>
          </Button>
          <Button variant="outline" className="bg-gray-800 border-gray-700">
            <Archive className="w-4 h-4 mr-2" />
            Archive
          </Button>
          <Button variant="outline" className="bg-gray-800 border-gray-700">
            <Share className="w-4 h-4 mr-2" />
            Share
          </Button>
          <Button className="bg-white text-black hover:bg-gray-200" onClick={() => setIsPrCreated(true)}>
            <GitPullRequest className="w-4 h-4 mr-2" />
            {isPrCreated ? "View PR" : "Create PR"}
          </Button>
        </div>
      </header>
    )
  }
  
  // Default header for other pages
  return (
    <header className="border-b border-gray-800 bg-gray-950">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 w-fit">
            <BrainCircuit className="w-8 h-8 text-gray-300" />
            <span className="text-xl font-semibold text-gray-50">AIdeator</span>
          </Link>
          <nav className="flex items-center gap-2">
            <Button variant="ghost" size="sm" asChild>
              <a 
                href="http://localhost:8000/docs" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-gray-300 hover:text-gray-50"
              >
                <FileText className="w-4 h-4" />
                API Docs
              </a>
            </Button>
          </nav>
        </div>
      </div>
    </header>
  )
}