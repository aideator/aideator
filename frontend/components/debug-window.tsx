"use client"

import { useEffect, useRef, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { X, Terminal, Download, Trash2, Pause, Play } from "lucide-react"
import { useAuthenticatedWebSocket } from "@/lib/api"
import { cn } from "@/lib/utils"

interface DebugMessage {
  id: string
  timestamp: string
  content: string
  source: string
  is_json: boolean
  metadata?: any
}

interface DebugWindowProps {
  runId: string
  isOpen: boolean
  onClose: () => void
}

export function DebugWindow({ runId, isOpen, onClose }: DebugWindowProps) {
  const [messages, setMessages] = useState<DebugMessage[]>([])
  const [isPaused, setIsPaused] = useState(false)
  const [wsConnected, setWsConnected] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { createWebSocketClient } = useAuthenticatedWebSocket('ws://localhost:8000')
  const wsClientRef = useRef<any>(null)

  useEffect(() => {
    if (!isOpen) return

    // Connect to system debug stream
    const wsUrl = `ws://localhost:8000/api/v1/ws/runs/${runId}/system-debug`
    const client = createWebSocketClient(wsUrl)
    
    client.connect({
      onMessage: (message) => {
        if (!isPaused && message.type === "debug") {
          const debugMessage: DebugMessage = {
            id: message.message_id || Date.now().toString(),
            timestamp: message.data.timestamp,
            content: message.data.content,
            source: message.data.source,
            is_json: message.data.is_json === "true",
            metadata: message.data.metadata
          }
          setMessages(prev => [...prev, debugMessage])
        }
      },
      onOpen: () => {
        setWsConnected(true)
        console.log('Debug WebSocket connected')
      },
      onError: (error) => {
        console.error('Debug WebSocket error:', error)
        setWsConnected(false)
      },
      onClose: () => {
        setWsConnected(false)
        console.log('Debug WebSocket closed')
      }
    })

    wsClientRef.current = client

    return () => {
      if (wsClientRef.current) {
        wsClientRef.current.close()
        wsClientRef.current = null
      }
    }
  }, [isOpen, runId, createWebSocketClient, isPaused])

  // Auto-scroll to bottom
  useEffect(() => {
    if (!isPaused) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages, isPaused])

  const handleClear = () => {
    setMessages([])
  }

  const handleExport = () => {
    const content = messages.map(msg => 
      `[${msg.timestamp}] [${msg.source}] ${msg.content}`
    ).join('\n')
    
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `debug-logs-${runId}-${Date.now()}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const formatMessage = (msg: DebugMessage) => {
    if (msg.is_json) {
      try {
        const parsed = JSON.parse(msg.content)
        // Format JSON logs nicely
        if (parsed.level && parsed.message) {
          const levelEmoji = {
            'DEBUG': '🔧',
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌'
          }[parsed.level] || '📝'
          
          return (
            <span className={cn(
              "font-mono text-xs",
              parsed.level === 'ERROR' && "text-red-500",
              parsed.level === 'WARNING' && "text-yellow-500",
              parsed.level === 'DEBUG' && "text-gray-500"
            )}>
              {levelEmoji} [{parsed.level}] {parsed.message}
              {parsed.variation_id && ` (var: ${parsed.variation_id})`}
            </span>
          )
        }
        return <span className="font-mono text-xs">{JSON.stringify(parsed, null, 2)}</span>
      } catch {
        // Fall through to plain text
      }
    }
    
    return <span className="font-mono text-xs text-gray-300">{msg.content}</span>
  }

  if (!isOpen) return null

  return (
    <div className="fixed bottom-4 right-4 w-[600px] h-[400px] z-50 shadow-2xl">
      <Card className="h-full flex flex-col bg-gray-900 border-gray-700">
        <CardHeader className="flex-shrink-0 pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm flex items-center gap-2">
              <Terminal className="w-4 h-4" />
              System Debug Console
              <span className={cn(
                "w-2 h-2 rounded-full",
                wsConnected ? "bg-green-500" : "bg-red-500"
              )} />
            </CardTitle>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={() => setIsPaused(!isPaused)}
                title={isPaused ? "Resume" : "Pause"}
              >
                {isPaused ? <Play className="w-3 h-3" /> : <Pause className="w-3 h-3" />}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={handleClear}
                title="Clear logs"
              >
                <Trash2 className="w-3 h-3" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={handleExport}
                title="Export logs"
              >
                <Download className="w-3 h-3" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={onClose}
              >
                <X className="w-3 h-3" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="flex-1 overflow-hidden p-0">
          <div className="h-full overflow-y-auto bg-gray-950 p-2">
            {messages.length === 0 ? (
              <div className="text-center py-8 text-gray-500 text-sm">
                {wsConnected ? "Waiting for debug logs..." : "Connecting to debug stream..."}
              </div>
            ) : (
              <div className="space-y-1">
                {messages.map((msg) => (
                  <div key={msg.id} className="text-xs">
                    <span className="text-gray-600">[{msg.source}]</span>{' '}
                    {formatMessage(msg)}
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}