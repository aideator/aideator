"use client"

import { BrainCircuit, ArrowLeft, Archive, Share, RefreshCw, Github } from "lucide-react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { useState, useEffect } from "react"
import { useAuth } from "@/components/auth/auth-provider"
import { GitHubLoginButton } from "@/components/auth/github-login-button"
import { UserMenu } from "@/components/auth/user-menu"
import { useTaskDetail } from "@/hooks/use-task-detail"
import { useArchive } from "@/hooks/use-archive"

export function PageHeader() {
  const pathname = usePathname()
  const router = useRouter()
  const [isPrCreated, setIsPrCreated] = useState(false)
  const [creatingPr, setCreatingPr] = useState(false)
  const [prUrl, setPrUrl] = useState<string | null>(null)
  const { user, isLoading, token } = useAuth()
  
  // Check if we're on a task page
  const taskMatch = pathname.match(/^\/task\/([^/]+)$/)
  const taskId = taskMatch?.[1]
  const { task, loading: taskLoading } = useTaskDetail(taskId || "")
  const { archiving, archiveTask } = useArchive()
  
  // Reset PR state when navigating away from task
  useEffect(() => {
    if (!taskId) {
      setIsPrCreated(false)
    }
  }, [taskId])

  // Handle archive task
  const handleArchiveTask = async () => {
    if (!taskId) return
    
    try {
      await archiveTask(taskId)
      // Navigate back to home page after archiving
      router.push('/')
    } catch (err) {
      alert(`Failed to archive task: ${err}`)
    }
  }
  
  if (taskId) {
    // Task page header (uses real API data)
    return (
      <header className="flex items-center justify-between px-4 py-2 border-b border-gray-800 bg-gray-950">
        <div className="flex items-center gap-4">
          <Link href="/">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="w-5 h-5" />
            </Button>
          </Link>
          <h1 className="text-lg font-medium text-gray-50">
            {taskLoading ? "Loading..." : task?.title || "Task"}
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            className="bg-gray-800 border-gray-700"
            onClick={handleArchiveTask}
            disabled={archiving === taskId}
          >
            {archiving === taskId ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Archive className="w-4 h-4 mr-2" />
            )}
            Archive
          </Button>
          <Button variant="outline" className="bg-gray-800 border-gray-700">
            <Share className="w-4 h-4 mr-2" />
            Share
          </Button>
          <Button 
            className="bg-white text-black hover:bg-gray-200"
            disabled={creatingPr || taskLoading}
            onClick={async () => {
              if (isPrCreated && prUrl) {
                window.open(prUrl, "_blank")
                return
              }

              if (!taskId || !token) return

              // Determine selected version from localStorage (set by TaskPage)
              const savedVersion = localStorage.getItem(`task_selected_version_${taskId}`)
              const version = savedVersion ? parseInt(savedVersion, 10) : 1

              const variationId = version - 1 // API expects 0-indexed

              try {
                setCreatingPr(true)
                const resp = await fetch(
                  `http://localhost:8000/api/v1/tasks/${taskId}/variations/${variationId}/pull-request`,
                  {
                    method: "POST",
                    headers: {
                      "Authorization": `Bearer ${token}`,
                    },
                  }
                )

                if (!resp.ok) {
                  const errorText = await resp.text()
                  throw new Error(`Failed to create PR: ${errorText}`)
                }

                const data: { pr_url: string } = await resp.json()
                setPrUrl(data.pr_url)
                setIsPrCreated(true)
                window.open(data.pr_url, "_blank")
              } catch (err) {
                console.error(err)
                alert(`Failed to create PR: ${err}`)
              } finally {
                setCreatingPr(false)
              }
            }}
          >
            {creatingPr ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Github className="w-4 h-4 mr-2" />
            )}
            {isPrCreated ? "View PR" : "Create PR"}
          </Button>
          {!isLoading && (user ? <UserMenu /> : <GitHubLoginButton />)}
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
            <span className="text-xl font-semibold text-gray-50">DevSwarm</span>
          </Link>
          <nav className="flex items-center gap-2">
            {!isLoading && (user ? <UserMenu /> : <GitHubLoginButton />)}
          </nav>
        </div>
      </div>
    </header>
  )
}