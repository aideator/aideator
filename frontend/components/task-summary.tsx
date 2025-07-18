'use client'

import React from 'react'
import { FileText, AlertCircle, Loader2 } from 'lucide-react'
import { MarkdownRenderer } from '@/components/ui/markdown-renderer'
import { cn } from '@/lib/utils'

interface TaskSummaryProps {
  summary?: string
  isLoading?: boolean
  error?: string | null
  className?: string
}

export function TaskSummary({ summary, isLoading, error, className }: TaskSummaryProps) {
  if (error) {
    return (
      <div className={cn("flex items-start gap-2 p-3 bg-red-900/20 border border-red-500/30 rounded-lg", className)}>
        <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <p className="text-red-300 text-sm font-medium mb-1">Summary Error</p>
          <p className="text-red-200 text-xs leading-relaxed">{error}</p>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className={cn("flex items-center gap-2 p-3 bg-gray-800/50 border border-gray-700 rounded-lg", className)}>
        <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
        <p className="text-gray-400 text-sm">Generating summary...</p>
      </div>
    )
  }

  if (!summary) {
    return (
      <div className={cn("flex items-start gap-2 p-3 bg-gray-800/30 border border-gray-700/50 rounded-lg", className)}>
        <FileText className="w-4 h-4 text-gray-500 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <p className="text-gray-400 text-sm">No summary available</p>
          <p className="text-gray-500 text-xs mt-1">Summary will appear when task completes</p>
        </div>
      </div>
    )
  }

  return (
    <div className={cn("p-3 bg-gray-800/30 border border-gray-700/50 rounded-lg", className)}>
      <div className="flex items-start gap-2">
        <FileText className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <MarkdownRenderer content={summary} />
        </div>
      </div>
    </div>
  )
}