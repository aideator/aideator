"use client"

import * as React from "react"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

interface AutoResizeTextareaProps extends React.ComponentProps<typeof Textarea> {
  minRows?: number
  maxRows?: number
}

export function AutoResizeTextarea({
  className,
  minRows = 5,
  maxRows = 20,
  ...props
}: AutoResizeTextareaProps) {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)
  
  const adjustHeight = React.useCallback(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    
    // Reset height to get the correct scrollHeight
    textarea.style.height = 'auto'
    
    // Get computed styles
    const computed = window.getComputedStyle(textarea)
    const lineHeight = parseInt(computed.lineHeight) || 24
    const paddingTop = parseInt(computed.paddingTop) || 8
    const paddingBottom = parseInt(computed.paddingBottom) || 8
    
    // Calculate heights including padding
    const innerMinHeight = lineHeight * minRows
    const innerMaxHeight = lineHeight * maxRows
    const minHeight = innerMinHeight + paddingTop + paddingBottom
    const maxHeight = innerMaxHeight + paddingTop + paddingBottom
    
    // Set new height
    const newHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight)
    textarea.style.height = `${newHeight}px`
  }, [minRows, maxRows])
  
  React.useEffect(() => {
    adjustHeight()
  }, [adjustHeight])
  
  return (
    <Textarea
      ref={textareaRef}
      className={cn(
        "bg-transparent border-0 text-base resize-none focus-visible:ring-0 focus-visible:ring-offset-0 focus:border-0 focus:outline-none focus-visible:outline-none overflow-y-auto transition-height duration-50",
        className
      )}
      style={{ boxShadow: 'none' }}
      onInput={adjustHeight}
      {...props}
    />
  )
}