"use client"

import { MessageSquare, Code } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export type Mode = "chat" | "code"

interface ModeSwitcherProps {
  mode: Mode
  onModeChange: (mode: Mode) => void
  className?: string
}

export function ModeSwitcher({ mode, onModeChange, className }: ModeSwitcherProps) {
  return (
    <div className={cn("flex items-center bg-gray-900/50 border border-gray-800 rounded-lg p-1", className)}>
      <Button
        variant={mode === "chat" ? "default" : "ghost"}
        size="sm"
        onClick={() => onModeChange("chat")}
        className={cn(
          "gap-2 rounded-md",
          mode === "chat" 
            ? "bg-gray-700 text-white hover:bg-gray-600" 
            : "text-gray-400 hover:text-gray-200 hover:bg-gray-800"
        )}
      >
        <MessageSquare className="w-4 h-4" />
        Chat
      </Button>
      <Button
        variant={mode === "code" ? "default" : "ghost"}
        size="sm"
        onClick={() => onModeChange("code")}
        className={cn(
          "gap-2 rounded-md",
          mode === "code" 
            ? "bg-gray-700 text-white hover:bg-gray-600" 
            : "text-gray-400 hover:text-gray-200 hover:bg-gray-800"
        )}
      >
        <Code className="w-4 h-4" />
        Code
      </Button>
    </div>
  )
}