"use client"

import { useEffect, useRef, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { X, Terminal, Download, Trash2, Pause, Play } from "lucide-react"
import { useAuthenticatedWebSocket } from "@/lib/api"
import { useAuth } from "@/lib/auth-context"
import { cn } from "@/lib/utils"

interface DebugMessage {
  id: string
  timestamp: string
  content: string
  source: string
  is_json: boolean
  variation_id?: number
  metadata?: any
}

interface DebugWindowProps {
  runId: string
  variations: number
  isOpen: boolean
  onClose: () => void
}

export function DebugWindow({ runId, variations, isOpen, onClose }: DebugWindowProps) {
  const [messages, setMessages] = useState<DebugMessage[]>([])
  const [isPaused, setIsPaused] = useState(false)
  const [wsConnected, setWsConnected] = useState(false)
  const [activeTab, setActiveTab] = useState("all")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { createWebSocketClient } = useAuthenticatedWebSocket('ws://localhost:8000')
  const { apiKey } = useAuth()
  const wsClientRef = useRef<any>(null)
  const messageCounterRef = useRef(0)
  const seenMessageIds = useRef<Set<string>>(new Set())

  useEffect(() => {
    if (!isOpen || !apiKey) return

    // Connect to debug stream
    const wsUrl = `ws://localhost:8000/ws/runs/${runId}/debug`
    const client = createWebSocketClient(wsUrl)
    
    client.connect({
      onMessage: (message) => {
        // Set connected on first message
        if (!wsConnected) {
          setWsConnected(true)
          console.log('Debug WebSocket connected successfully')
        }
        
        console.log('Debug WebSocket received message:', message)
        
        if (!isPaused && message.type === "debug") {
          // Generate unique ID using message_id or fallback to timestamp + counter
          const uniqueId = message.message_id || `${Date.now()}-${messageCounterRef.current++}`
          
          // Skip if we've already seen this message ID (handles reconnection duplicates)
          if (seenMessageIds.current.has(uniqueId)) {
            return
          }
          seenMessageIds.current.add(uniqueId)
          
          const debugMessage: DebugMessage = {
            id: uniqueId,
            timestamp: message.data.timestamp,
            content: message.data.content,
            source: message.data.source,
            is_json: message.data.is_json === "true",
            variation_id: message.data.variation_id ? parseInt(message.data.variation_id) : undefined,
            metadata: message.data.metadata
          }
          setMessages(prev => [...prev, debugMessage])
          console.log('Added debug message:', debugMessage)
        } else {
          console.log('Debug message filtered out - type:', message.type, 'paused:', isPaused)
        }
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
  }, [isOpen, runId, createWebSocketClient, isPaused, apiKey])

  // Auto-scroll to bottom
  useEffect(() => {
    if (!isPaused) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages, isPaused])

  const handleClear = () => {
    setMessages([])
    seenMessageIds.current.clear()
    messageCounterRef.current = 0
  }

  const handleExport = () => {
    const filteredMessages = getFilteredMessages()
    const content = filteredMessages.map(msg => 
      `[${msg.timestamp}] [${msg.source}] ${msg.variation_id !== undefined ? `[Model ${msg.variation_id + 1}] ` : ''}${msg.content}`
    ).join('\n')
    
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const tabSuffix = activeTab === "all" ? "all" : `model-${parseInt(activeTab.replace('model-', '')) + 1}`
    a.download = `debug-logs-${runId}-${tabSuffix}-${Date.now()}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const getFilteredMessages = () => {
    if (activeTab === "all") {
      return messages
    }
    const variationId = parseInt(activeTab.replace('model-', ''))
    return messages.filter(msg => msg.variation_id === variationId)
  }

  const formatMessage = (msg: DebugMessage) => {
    if (msg.is_json) {
      try {
        const parsed = JSON.parse(msg.content)
        // Format JSON logs nicely
        if (parsed.level && parsed.message) {
          const levelEmojiMap: Record<string, string> = {
            'DEBUG': '🔧',
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌'
          }
          const levelEmoji = levelEmojiMap[parsed.level as string] || '📝'
          
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

  const filteredMessages = getFilteredMessages()

  return (
    <div className="fixed bottom-4 right-4 w-[800px] h-[500px] z-50 shadow-2xl">
      <Card className="h-full flex flex-col bg-gray-900 border-gray-700">
        <CardHeader className="flex-shrink-0 pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm flex items-center gap-2">
              <Terminal className="w-4 h-4" />
              Debug Console
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
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
            <TabsList className="bg-gray-800 border-b border-gray-700 rounded-none justify-start">
              <TabsTrigger value="all" className="text-xs">All Models</TabsTrigger>
              {Array.from({ length: variations }, (_, i) => (
                <TabsTrigger key={i} value={`model-${i}`} className="text-xs">
                  Model {i + 1}
                </TabsTrigger>
              ))}
            </TabsList>
            
            <TabsContent value="all" className="flex-1 overflow-hidden mt-0">
              <DebugTabContent 
                messages={messages} 
                wsConnected={wsConnected} 
                messagesEndRef={messagesEndRef}
                formatMessage={formatMessage}
              />
            </TabsContent>
            
            {Array.from({ length: variations }, (_, i) => (
              <TabsContent key={i} value={`model-${i}`} className="flex-1 overflow-hidden mt-0">
                <DebugTabContent 
                  messages={messages.filter(msg => msg.variation_id === i)} 
                  wsConnected={wsConnected} 
                  messagesEndRef={messagesEndRef}
                  formatMessage={formatMessage}
                />
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}

interface DebugTabContentProps {
  messages: DebugMessage[]
  wsConnected: boolean
  messagesEndRef: React.RefObject<HTMLDivElement | null>
  formatMessage: (msg: DebugMessage) => React.ReactNode
}

function DebugTabContent({ messages, wsConnected, messagesEndRef, formatMessage }: DebugTabContentProps) {
  return (
    <div className="h-full overflow-y-auto bg-gray-950 p-2">
      {messages.length === 0 ? (
        <div className="text-center py-8 text-gray-500 text-sm">
          {wsConnected ? "Waiting for debug logs..." : "Connecting to debug stream..."}
        </div>
      ) : (
        <div className="space-y-1">
          {messages.map((msg) => (
            <div key={msg.id} className="text-xs">
              <span className="text-gray-600">[{msg.source}]</span>
              {msg.variation_id !== undefined && (
                <span className="text-blue-400 ml-1">[M{msg.variation_id + 1}]</span>
              )}
              {' '}
              {formatMessage(msg)}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      )}
    </div>
  )
}