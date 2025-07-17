"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { 
  RefreshCw, 
  Activity, 
  Database, 
  MessageSquare, 
  Container,
  Key,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle,
  Terminal,
  Play
} from 'lucide-react'
import { formatLogTimestamp, formatUserTimestamp } from '@/utils/timezone'
import { 
  getBodyClasses, 
  getStatusColorClasses,
  getHeadingClasses,
  commonTypographyCombinations,
  componentTokens,
  getPaddingSpacing,
  getGapSpacing,
  getMarginSpacing
} from '@/lib/design-tokens'

interface AdminStats {
  active_runs: number
  total_messages: number
  recent_messages_1h: number
  active_containers: number
}

interface ContainerActivity {
  run_id: string
  variation_id: number
  message_count: number
  latest_timestamp: string
  latest_message: string
}

interface LiveActivityData {
  active_containers: number
  container_activity: ContainerActivity[]
}

interface RunData {
  id: string
  status: string
  created_at: string
  message_count: number
}

interface MessageData {
  run_id: string
  variation_id: number
  output_type: string
  content: string
  timestamp: string
}

const API_BASE = 'http://localhost:8000'

export default function AdminDashboard() {
  const [stats, setStats] = useState<AdminStats>({
    active_runs: 0,
    total_messages: 0,
    recent_messages_1h: 0,
    active_containers: 0
  })
  const [liveActivity, setLiveActivity] = useState<LiveActivityData>({
    active_containers: 0,
    container_activity: []
  })
  const [recentRuns, setRecentRuns] = useState<RunData[]>([])
  const [recentMessages, setRecentMessages] = useState<MessageData[]>([])
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [apiKey, setApiKey] = useState<string>('')
  const [showApiKeyInput, setShowApiKeyInput] = useState(false)

  // Get API key from localStorage on mount
  useEffect(() => {
    const savedKey = localStorage.getItem('admin_api_key')
    if (savedKey) {
      setApiKey(savedKey)
    }
  }, [])

  // Auto-refresh logic
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        refreshAll()
      }, 5000)
      return () => clearInterval(interval)
    }
  }, [autoRefresh])

  // Initial load
  useEffect(() => {
    refreshAll()
  }, [])

  const fetchData = async (endpoint: string) => {
    try {
      const headers: HeadersInit = {}
      
      if (apiKey) {
        headers['X-API-Key'] = apiKey
      }
      
      const response = await fetch(`${API_BASE}/api/v1/admin-messaging${endpoint}`, {
        headers: headers
      })
      
      if (!response.ok) {
        if (response.status === 401) {
          setShowApiKeyInput(true)
          throw new Error('Authentication required')
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      return await response.json()
    } catch (err) {
      console.error(`Error fetching ${endpoint}:`, err)
      throw err
    }
  }

  const refreshAll = async () => {
    setLoading(true)
    setError(null)
    
    try {
      await Promise.all([
        refreshOverview(),
        refreshLiveActivity(),
        refreshRuns(),
        refreshMessages()
      ])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh data')
    } finally {
      setLoading(false)
    }
  }

  const refreshOverview = async () => {
    try {
      const data = await fetchData('/overview')
      setStats({
        active_runs: data.active_runs || 0,
        total_messages: data.total_messages || 0,
        recent_messages_1h: data.recent_messages_1h || 0,
        active_containers: data.active_containers || 0
      })
    } catch (err) {
      console.error('Failed to refresh overview:', err)
    }
  }

  const refreshLiveActivity = async () => {
    try {
      const data = await fetchData('/live')
      setLiveActivity({
        active_containers: data.active_containers || 0,
        container_activity: data.container_activity || []
      })
    } catch (err) {
      console.error('Failed to refresh live activity:', err)
    }
  }

  const refreshRuns = async () => {
    try {
      const data = await fetchData('/admin-messaging/runs?limit=10')
      setRecentRuns(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('Failed to refresh runs:', err)
    }
  }

  const refreshMessages = async () => {
    try {
      const data = await fetchData('/messages?limit=20')
      setRecentMessages(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('Failed to refresh messages:', err)
    }
  }

  const handleApiKeySubmit = () => {
    if (apiKey.trim()) {
      localStorage.setItem('admin_api_key', apiKey.trim())
      setShowApiKeyInput(false)
      refreshAll()
    }
  }

  const clearApiKey = () => {
    localStorage.removeItem('admin_api_key')
    setApiKey('')
    setShowApiKeyInput(true)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Play className={`w-4 h-4 ${getStatusColorClasses('processing')}`} />
      case 'completed':
        return <CheckCircle className={`w-4 h-4 ${getStatusColorClasses('success')}`} />
      case 'failed':
        return <XCircle className={`w-4 h-4 ${getStatusColorClasses('failed')}`} />
      case 'pending':
        return <Clock className={`w-4 h-4 ${getStatusColorClasses('pending')}`} />
      default:
        return <AlertCircle className={`w-4 h-4 ${getBodyClasses('muted')}`} />
    }
  }

  const getStatusColorClass = (status: string) => {
    switch (status) {
      case 'running':
        return getStatusColorClasses('processing')
      case 'completed':
        return getStatusColorClasses('success')
      case 'failed':
        return getStatusColorClasses('failed')
      case 'pending':
        return getStatusColorClasses('pending')
      default:
        return getBodyClasses('muted')
    }
  }

  const getOutputTypeColorClass = (type: string) => {
    switch (type) {
      case 'stdout':
        return getStatusColorClasses('success')
      case 'stderr':
        return getStatusColorClasses('failed')
      case 'logging':
        return getStatusColorClasses('processing')
      case 'status':
        return getStatusColorClasses('pending')
      default:
        return getBodyClasses('secondary')
    }
  }

  if (showApiKeyInput) {
    return (
      <div className={componentTokens.ui.layout.page}>
        <div className={`${componentTokens.ui.layout.container} min-h-screen flex items-center justify-center`}>
          <Card className={`w-full max-w-md ${componentTokens.ui.card.primary}`}>
            <CardHeader>
              <CardTitle className={`${commonTypographyCombinations.cardTitle} flex items-center ${getGapSpacing('sm')}`}>
                <Key className="w-5 h-5" />
                Admin Authentication
              </CardTitle>
            </CardHeader>
            <CardContent className={`${getGapSpacing('md')} space-y-4`}>
              <div>
                <Label htmlFor="apiKey" className={getBodyClasses('secondary')}>
                  API Key
                </Label>
                <Input
                  id="apiKey"
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter your admin API key"
                  onKeyDown={(e) => e.key === 'Enter' && handleApiKeySubmit()}
                  className={`${getMarginSpacing('xs')} ${componentTokens.ui.card.secondary}`}
                />
              </div>
              <Button 
                onClick={handleApiKeySubmit}
                disabled={!apiKey.trim()}
                className="w-full"
              >
                Access Admin Dashboard
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className={componentTokens.ui.layout.page}>
      {/* Header */}
      <div className={`${componentTokens.ui.card.primary} border-b ${componentTokens.ui.layout.border}`}>
        <div className={`${componentTokens.ui.layout.container} ${getPaddingSpacing('lg')}`}>
          <div className="flex items-center justify-between">
            <div>
              <h1 className={`${commonTypographyCombinations.pageTitle} flex items-center ${getGapSpacing('sm')}`}>
                <Activity className="w-8 h-8" />
                AIdeator Admin Dashboard
              </h1>
              <p className={`${getBodyClasses('secondary')} ${getMarginSpacing('xs')}`}>
                Container Messaging & Activity Monitor
              </p>
            </div>
            <div className={`flex items-center ${getGapSpacing('md')}`}>
              <div className={`flex items-center ${getGapSpacing('sm')}`}>
                <Switch 
                  checked={autoRefresh}
                  onCheckedChange={setAutoRefresh}
                />
                <Label className={getBodyClasses('secondary')}>
                  Auto-refresh (5s)
                </Label>
              </div>
              <Button variant="outline" size="sm" onClick={clearApiKey}>
                <Key className="w-4 h-4" />
                Clear API Key
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className={componentTokens.ui.layout.container}>
        <div className={`${getPaddingSpacing('lg')} ${getGapSpacing('lg')} space-y-8`}>
          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className={componentTokens.ui.card.secondary}>
              <CardContent className={`${getPaddingSpacing('lg')} text-center`}>
                <div className={`${commonTypographyCombinations.pageTitle} ${getStatusColorClasses('processing')}`}>
                  {stats.active_runs}
                </div>
                <div className={`${getBodyClasses('secondary')} ${getMarginSpacing('xs')}`}>
                  Active Runs
                </div>
              </CardContent>
            </Card>

            <Card className={componentTokens.ui.card.secondary}>
              <CardContent className={`${getPaddingSpacing('lg')} text-center`}>
                <div className={`${commonTypographyCombinations.pageTitle} ${getStatusColorClasses('processing')}`}>
                  {stats.total_messages}
                </div>
                <div className={`${getBodyClasses('secondary')} ${getMarginSpacing('xs')}`}>
                  Total Messages
                </div>
              </CardContent>
            </Card>

            <Card className={componentTokens.ui.card.secondary}>
              <CardContent className={`${getPaddingSpacing('lg')} text-center`}>
                <div className={`${commonTypographyCombinations.pageTitle} ${getStatusColorClasses('processing')}`}>
                  {stats.recent_messages_1h}
                </div>
                <div className={`${getBodyClasses('secondary')} ${getMarginSpacing('xs')}`}>
                  Recent Messages (1h)
                </div>
              </CardContent>
            </Card>

            <Card className={componentTokens.ui.card.secondary}>
              <CardContent className={`${getPaddingSpacing('lg')} text-center`}>
                <div className={`${commonTypographyCombinations.pageTitle} ${getStatusColorClasses('processing')}`}>
                  {stats.active_containers}
                </div>
                <div className={`${getBodyClasses('secondary')} ${getMarginSpacing('xs')}`}>
                  Active Containers
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Error Display */}
          {error && (
            <Card className={`${componentTokens.ui.card.primary} border-red-500/20`}>
              <CardContent className={`${getPaddingSpacing('md')} flex items-center ${getGapSpacing('sm')}`}>
                <AlertCircle className={`w-5 h-5 ${getStatusColorClasses('failed')}`} />
                <span className={getStatusColorClasses('failed')}>{error}</span>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={refreshAll}
                  className="ml-auto"
                >
                  Retry
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Main Content Tabs */}
          <Tabs defaultValue="activity" className="w-full">
            <TabsList className={`grid w-full grid-cols-3 ${getMarginSpacing('md')}`}>
              <TabsTrigger value="activity">
                <Activity className="w-4 h-4 mr-2" />
                Live Activity
              </TabsTrigger>
              <TabsTrigger value="runs">
                <Database className="w-4 h-4 mr-2" />
                Recent Runs
              </TabsTrigger>
              <TabsTrigger value="messages">
                <MessageSquare className="w-4 h-4 mr-2" />
                Recent Messages
              </TabsTrigger>
            </TabsList>

            <TabsContent value="activity">
              <Card className={componentTokens.ui.card.primary}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className={`${commonTypographyCombinations.cardTitle} flex items-center ${getGapSpacing('sm')}`}>
                      <Container className="w-5 h-5" />
                      Live Activity (Last 5 Minutes)
                    </CardTitle>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={refreshLiveActivity}
                      disabled={loading}
                    >
                      <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                      Refresh
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {liveActivity.container_activity.length === 0 ? (
                    <div className={`text-center ${getPaddingSpacing('lg')} ${getBodyClasses('muted')}`}>
                      <Terminal className="w-8 h-8 mx-auto mb-2" />
                      <p>No recent activity</p>
                    </div>
                  ) : (
                    <div className={`${getGapSpacing('sm')} space-y-3`}>
                      {liveActivity.container_activity.map((activity, index) => (
                        <div 
                          key={index}
                          className={`flex items-center justify-between ${getPaddingSpacing('sm')} rounded-lg ${componentTokens.ui.card.secondary}`}
                        >
                          <div>
                            <div className={`${getBodyClasses('primary')} font-medium`}>
                              {activity.run_id}:{activity.variation_id}
                            </div>
                            <div className={`${getBodyClasses('secondary')} text-sm`}>
                              {activity.message_count} messages
                            </div>
                          </div>
                          <div className="text-right">
                            <div className={`${getBodyClasses('secondary')} text-sm`}>
                              {formatLogTimestamp(activity.latest_timestamp)}
                            </div>
                            <div className={`${getBodyClasses('primary')} text-sm max-w-xs overflow-hidden text-ellipsis`}>
                              {activity.latest_message}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="runs">
              <Card className={componentTokens.ui.card.primary}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className={`${commonTypographyCombinations.cardTitle} flex items-center ${getGapSpacing('sm')}`}>
                      <Database className="w-5 h-5" />
                      Recent Runs
                    </CardTitle>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={refreshRuns}
                      disabled={loading}
                    >
                      <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                      Refresh
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {recentRuns.length === 0 ? (
                    <div className={`text-center ${getPaddingSpacing('lg')} ${getBodyClasses('muted')}`}>
                      <Database className="w-8 h-8 mx-auto mb-2" />
                      <p>No runs found</p>
                    </div>
                  ) : (
                    <div className={`${getGapSpacing('sm')} space-y-3`}>
                      {recentRuns.map((run) => (
                        <div 
                          key={run.id}
                          className={`flex items-center justify-between ${getPaddingSpacing('sm')} rounded-lg ${componentTokens.ui.card.secondary}`}
                        >
                          <div>
                            <div className={`${getBodyClasses('primary')} font-medium`}>
                              {run.id}
                            </div>
                            <div className={`${getBodyClasses('secondary')} text-sm`}>
                              {formatUserTimestamp(run.created_at, undefined, 'full')}
                            </div>
                          </div>
                          <div className={`text-right flex items-center ${getGapSpacing('sm')}`}>
                            <div className={`${getBodyClasses('secondary')} text-sm`}>
                              {run.message_count} messages
                            </div>
                            <Badge variant="outline" className={getStatusColorClass(run.status)}>
                              {getStatusIcon(run.status)}
                              {run.status}
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="messages">
              <Card className={componentTokens.ui.card.primary}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className={`${commonTypographyCombinations.cardTitle} flex items-center ${getGapSpacing('sm')}`}>
                      <MessageSquare className="w-5 h-5" />
                      Recent Messages
                    </CardTitle>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={refreshMessages}
                      disabled={loading}
                    >
                      <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                      Refresh
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {recentMessages.length === 0 ? (
                    <div className={`text-center ${getPaddingSpacing('lg')} ${getBodyClasses('muted')}`}>
                      <MessageSquare className="w-8 h-8 mx-auto mb-2" />
                      <p>No messages found</p>
                    </div>
                  ) : (
                    <div className={`${getGapSpacing('sm')} space-y-3`}>
                      {recentMessages.map((message, index) => (
                        <div 
                          key={index}
                          className={`${getPaddingSpacing('sm')} rounded-lg ${componentTokens.ui.card.secondary}`}
                        >
                          <div className={`flex items-center justify-between ${getMarginSpacing('xs')}`}>
                            <div className={`flex items-center ${getGapSpacing('sm')}`}>
                              <Badge variant="outline" className={getOutputTypeColorClass(message.output_type)}>
                                {message.output_type}
                              </Badge>
                              <span className={`${getBodyClasses('secondary')} text-sm`}>
                                {message.run_id}:{message.variation_id}
                              </span>
                            </div>
                            <span className={`${getBodyClasses('secondary')} text-sm`}>
                              {formatUserTimestamp(message.timestamp, undefined, 'full')}
                            </span>
                          </div>
                          <div className={`${getBodyClasses('primary')} text-sm ${commonTypographyCombinations.codeInline}`}>
                            {message.content}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}