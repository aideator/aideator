"use client"

import { useState, useEffect, useCallback, useRef } from 'react'

export interface AgentOutput {
  id: number
  run_id: string
  variation_id: number
  content: string
  timestamp: string
  output_type: 'stdout' | 'stderr' | 'status' | 'summary' | 'diffs' | 'logging' | 'addinfo'
}

export interface WebSocketMessage {
  type: string
  message_id?: string
  data: {
    variation_id: string
    content: string
    timestamp: string
    output_type: string
    [key: string]: any
  }
}

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

export interface UseAgentOutputsReturn {
  outputs: AgentOutput[]
  connectionStatus: ConnectionStatus
  reconnect: () => void
  clearOutputs: () => void
  getOutputsByVariation: (variationId: number) => AgentOutput[]
}

/**
 * Hook for managing real-time agent outputs via WebSocket
 * Integrates with the PostgreSQL-based logging system
 */
export function useAgentOutputs(runId: string): UseAgentOutputsReturn {
  const [outputs, setOutputs] = useState<AgentOutput[]>([])
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected')
  const websocketRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const messageIdRef = useRef<string>('0-0') // For resumption

  const connect = useCallback(() => {
    if (!runId) return

    // Clear any existing connection
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.close()
    }

    setConnectionStatus('connecting')
    
    // WebSocket URL - in production this would use the proper host
    const wsUrl = `ws://localhost:8000/ws/runs/${runId}`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log(`[WebSocket] Connected to ${wsUrl}`)
      setConnectionStatus('connected')
      
      // Clear any pending reconnection
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }
    }

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        console.log('[WebSocket] Received message:', message.type, message.data)

        // Handle different message types
        switch (message.type) {
          case 'connected':
            console.log('[WebSocket] Connection confirmed')
            break
            
          case 'stdout':
          case 'stderr':
          case 'status':
          case 'logging':
          case 'summary':
          case 'diffs':
          case 'addinfo':
            // Create AgentOutput from WebSocket message
            const output: AgentOutput = {
              id: Date.now(), // Temporary ID for real-time outputs
              run_id: runId,
              variation_id: parseInt(message.data.variation_id),
              content: message.data.content,
              timestamp: message.data.timestamp || new Date().toISOString(),
              output_type: message.data.output_type as AgentOutput['output_type']
            }
            
            setOutputs(prev => [...prev, output])
            
            // Update message ID for resumption
            if (message.message_id) {
              messageIdRef.current = message.message_id
            }
            break
            
          case 'pong':
            // Handle ping/pong for keepalive
            break
            
          case 'error':
            console.error('[WebSocket] Server error:', message.data)
            break
            
          default:
            console.warn('[WebSocket] Unknown message type:', message.type)
        }
      } catch (error) {
        console.error('[WebSocket] Failed to parse message:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('[WebSocket] Connection error:', error)
      setConnectionStatus('error')
    }

    ws.onclose = (event) => {
      console.log(`[WebSocket] Connection closed (${event.code}): ${event.reason}`)
      setConnectionStatus('disconnected')
      websocketRef.current = null
      
      // Auto-reconnect after 3 seconds if not intentionally closed
      if (event.code !== 1000) {
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('[WebSocket] Attempting reconnection...')
          connect()
        }, 3000)
      }
    }

    websocketRef.current = ws
  }, [runId])

  const reconnect = useCallback(() => {
    connect()
  }, [connect])

  const clearOutputs = useCallback(() => {
    setOutputs([])
    messageIdRef.current = '0-0'
  }, [])

  const getOutputsByVariation = useCallback((variationId: number): AgentOutput[] => {
    return outputs.filter(output => output.variation_id === variationId)
  }, [outputs])

  // Connect on mount and runId change
  useEffect(() => {
    if (runId) {
      connect()
    }

    // Cleanup on unmount
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (websocketRef.current) {
        websocketRef.current.close(1000, 'Component unmounting')
      }
    }
  }, [runId, connect])

  // Ping keepalive every 30 seconds
  useEffect(() => {
    if (connectionStatus === 'connected') {
      const pingInterval = setInterval(() => {
        if (websocketRef.current?.readyState === WebSocket.OPEN) {
          websocketRef.current.send(JSON.stringify({ 
            control: 'ping' 
          }))
        }
      }, 30000)

      return () => clearInterval(pingInterval)
    }
  }, [connectionStatus])

  return {
    outputs,
    connectionStatus,
    reconnect,
    clearOutputs,
    getOutputsByVariation,
  }
}