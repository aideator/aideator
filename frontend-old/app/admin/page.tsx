"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Database,
  Activity,
  RefreshCw,
  Search,
  Trash2,
  Download,
  AlertCircle,
  CheckCircle,
  Clock,
  MessageSquare,
  TrendingUp,
  Server,
  HardDrive,
} from "lucide-react";
import { format } from "date-fns";

interface DatabaseStats {
  total_runs: number;
  runs_by_status: Record<string, number>;
  total_messages: number;
  messages_by_type: Record<string, number>;
  recent_runs_24h: number;
  recent_messages_24h: number;
  database_size_bytes: number;
  average_messages_per_run: number;
}

interface RunMetrics {
  id: string;
  status: string;
  github_url: string;
  prompt: string;
  variations: number;
  created_at: string;
  started_at: string | null;
  total_messages: number;
  message_rate_per_second: number;
  variation_metrics: Record<string, any>;
  winning_variation_id: number | null;
}

interface Message {
  id: number;
  run_id: string;
  variation_id: number;
  content: string;
  timestamp: string;
  output_type: string;
}

export default function AdminPage() {
  const [stats, setStats] = useState<DatabaseStats | null>(null);
  const [activeRuns, setActiveRuns] = useState<RunMetrics[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [totalMessages, setTotalMessages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [selectedOutputType, setSelectedOutputType] = useState<string | null>(null);
  const [messageOffset, setMessageOffset] = useState(0);
  const [healthStatus, setHealthStatus] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("runs");

  const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
  
  // Mock data for testing when backend is unavailable
  const mockRuns: RunMetrics[] = [
    {
      id: "test-run-001",
      status: "completed",
      github_url: "https://github.com/fastapi/fastapi",
      prompt: "Analyze this FastAPI repository and suggest performance improvements",
      variations: 3,
      created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      started_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      total_messages: 53,
      message_rate_per_second: 0.5,
      variation_metrics: {
        0: { message_count: 17, last_message: new Date(Date.now() - 90 * 60 * 1000).toISOString() },
        1: { message_count: 18, last_message: new Date(Date.now() - 70 * 60 * 1000).toISOString() },
        2: { message_count: 18, last_message: new Date(Date.now() - 50 * 60 * 1000).toISOString() }
      },
      winning_variation_id: 1,
    },
    {
      id: "test-run-002",
      status: "running",
      github_url: "https://github.com/tiangolo/sqlmodel",
      prompt: "Review the codebase and create comprehensive documentation",
      variations: 2,
      created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
      started_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
      total_messages: 8,
      message_rate_per_second: 0.3,
      variation_metrics: {
        0: { message_count: 4, last_message: new Date(Date.now() - 10 * 60 * 1000).toISOString() },
        1: { message_count: 4, last_message: new Date(Date.now() - 5 * 60 * 1000).toISOString() }
      },
      winning_variation_id: null,
    },
    {
      id: "test-run-003",
      status: "failed",
      github_url: "https://github.com/invalid/repo",
      prompt: "This will fail",
      variations: 1,
      created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      started_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      total_messages: 1,
      message_rate_per_second: 0,
      variation_metrics: {
        0: { message_count: 1, last_message: new Date(Date.now() - 295 * 60 * 1000).toISOString() }
      },
      winning_variation_id: null,
    }
  ];

  // Fetch database stats
  const fetchStats = async () => {
    try {
      const response = await fetch(`${apiBase}/api/v1/admin/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      } else {
        console.error("Failed to fetch stats:", response.status, response.statusText);
      }
    } catch (error) {
      console.error("Failed to fetch stats:", error);
      // Don't crash, just log the error
    }
  };

  // Fetch active runs
  const fetchActiveRuns = async () => {
    try {
      const response = await fetch(`${apiBase}/api/v1/admin/runs/active?include_completed=true&limit=20`);
      if (response.ok) {
        const data = await response.json();
        setActiveRuns(data);
      } else {
        console.error("Failed to fetch active runs:", response.status, response.statusText);
      }
    } catch (error) {
      console.error("Failed to fetch active runs:", error);
      // Don't use mock data - show real error
    }
  };

  // Fetch messages
  const fetchMessages = async () => {
    try {
      const params = new URLSearchParams({
        limit: "100",
        offset: messageOffset.toString(),
      });
      
      if (selectedRunId) params.append("run_id", selectedRunId);
      if (selectedOutputType) params.append("output_type", selectedOutputType);
      if (searchQuery) params.append("search", searchQuery);

      const response = await fetch(`${apiBase}/api/v1/admin/messages/stream?${params}`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages);
        setTotalMessages(data.total);
      } else {
        console.error("Failed to fetch messages:", response.status, response.statusText);
      }
    } catch (error) {
      console.error("Failed to fetch messages:", error);
      // Use mock messages when backend is unavailable
      const mockMessages: Message[] = [
        {
          id: 1,
          run_id: selectedRunId || "test-run-001",
          variation_id: 0,
          content: "🔍 Analyzing repository structure...",
          timestamp: new Date(Date.now() - 120 * 60 * 1000).toISOString(),
          output_type: "stdout"
        },
        {
          id: 2,
          run_id: selectedRunId || "test-run-001",
          variation_id: 0,
          content: "📊 Found 127 Python files to analyze",
          timestamp: new Date(Date.now() - 118 * 60 * 1000).toISOString(),
          output_type: "stdout"
        },
        {
          id: 3,
          run_id: selectedRunId || "test-run-001",
          variation_id: 0,
          content: JSON.stringify({
            status: "variation_started",
            variation_id: 0,
            metadata: { model: "gpt-4", temperature: 0.7 }
          }),
          timestamp: new Date(Date.now() - 121 * 60 * 1000).toISOString(),
          output_type: "status"
        },
        {
          id: 4,
          run_id: selectedRunId || "test-run-001",
          variation_id: 1,
          content: "⚡ Found potential optimization: Database connection pooling",
          timestamp: new Date(Date.now() - 100 * 60 * 1000).toISOString(),
          output_type: "stdout"
        },
        {
          id: 5,
          run_id: selectedRunId || "test-run-001",
          variation_id: 1,
          content: JSON.stringify({
            level: "INFO",
            message: "Completed analysis for variation 1",
            files_analyzed: 127,
            issues_found: 8
          }),
          timestamp: new Date(Date.now() - 95 * 60 * 1000).toISOString(),
          output_type: "logging"
        },
        {
          id: 6,
          run_id: selectedRunId || "test-run-001",
          variation_id: 2,
          content: "## Summary\\n\\nKey findings:\\n- Database pooling can improve performance by 40%\\n- Implement Redis caching",
          timestamp: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
          output_type: "summary"
        }
      ];
      
      const filtered = mockMessages.filter(msg => {
        if (selectedRunId && msg.run_id !== selectedRunId) return false;
        if (selectedOutputType && msg.output_type !== selectedOutputType) return false;
        if (searchQuery && !msg.content.toLowerCase().includes(searchQuery.toLowerCase())) return false;
        return true;
      });
      
      // Don't use mock data - show real error
    }
  };

  // Fetch health status
  const fetchHealth = async () => {
    try {
      const response = await fetch(`${apiBase}/api/v1/admin/health`);
      if (response.ok) {
        const data = await response.json();
        setHealthStatus(data);
      } else {
        console.error("Failed to fetch health:", response.status, response.statusText);
      }
    } catch (error) {
      console.error("Failed to fetch health:", error);
      // Don't crash, just log the error
    }
  };

  // Initial load and refresh logic
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        await Promise.all([
          fetchActiveRuns(),
          fetchMessages(),
          fetchHealth(),
        ]);
      } catch (err) {
        setError("Failed to connect to backend. Make sure the API is running on " + apiBase);
      }
      setLoading(false);
    };

    loadData();

    // Auto refresh
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(loadData, refreshInterval);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh, refreshInterval, selectedRunId, selectedOutputType, searchQuery, messageOffset]);

  // Format bytes to human readable
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
        return "bg-blue-500";
      case "completed":
        return "bg-green-500";
      case "failed":
        return "bg-red-500";
      case "pending":
        return "bg-yellow-500";
      case "cancelled":
        return "bg-gray-500";
      default:
        return "bg-gray-400";
    }
  };

  // Get output type color
  const getOutputTypeColor = (type: string) => {
    switch (type) {
      case "stdout":
        return "text-blue-600";
      case "stderr":
        return "text-red-600";
      case "status":
        return "text-purple-600";
      case "logging":
        return "text-green-600";
      case "summary":
        return "text-indigo-600";
      case "diffs":
        return "text-orange-600";
      default:
        return "text-gray-600";
    }
  };

  // Handle cleanup
  const handleCleanup = async (dryRun: boolean = true) => {
    if (!dryRun && !confirm("Are you sure you want to delete old data? This cannot be undone.")) {
      return;
    }

    try {
      const response = await fetch(`${apiBase}/api/v1/admin/cleanup?older_than_days=7&dry_run=${dryRun}`, {
        method: "POST",
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`${result.message}\nRuns affected: ${result.runs_affected}\nMessages affected: ${result.messages_affected}`);
        if (!dryRun) {
          // Refresh data after cleanup
          fetchActiveRuns();
          fetchMessages();
        }
      }
    } catch (error) {
      console.error("Cleanup failed:", error);
      alert("Cleanup failed. Check console for details.");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Database className="h-8 w-8 text-indigo-600 mr-3" />
              <h1 className="text-xl font-semibold">Database Messaging Monitor</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Auto refresh controls */}
              <div className="flex items-center space-x-2">
                <Label htmlFor="auto-refresh">Auto Refresh</Label>
                <Switch
                  id="auto-refresh"
                  checked={autoRefresh}
                  onCheckedChange={setAutoRefresh}
                />
              </div>
              
              <Select value={refreshInterval.toString()} onValueChange={(v) => setRefreshInterval(parseInt(v))}>
                <SelectTrigger className="w-24">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1000">1s</SelectItem>
                  <SelectItem value="5000">5s</SelectItem>
                  <SelectItem value="10000">10s</SelectItem>
                  <SelectItem value="30000">30s</SelectItem>
                </SelectContent>
              </Select>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setLoading(true);
                  Promise.all([
                    fetchActiveRuns(),
                    fetchMessages(),
                    fetchHealth(),
                  ]).finally(() => setLoading(false));
                }}
              >
                <RefreshCw className="h-4 w-4 mr-1" />
                Refresh
              </Button>
              
              {/* Health indicator */}
              {healthStatus && (
                <div className="flex items-center">
                  {healthStatus.healthy ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-500" />
                  )}
                  <span className="ml-1 text-sm text-gray-600">
                    {healthStatus.response_time_ms}ms
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Alert */}
        {error && (
          <Alert className="mb-6 border-red-200 bg-red-50">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              {error}
            </AlertDescription>
          </Alert>
        )}
        
        {/* Loading State */}
        {loading && !error && (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <RefreshCw className="h-8 w-8 text-gray-400 animate-spin mx-auto mb-4" />
              <p className="text-gray-500">Loading dashboard data...</p>
            </div>
          </div>
        )}
        
        {/* Main Grid - Show even while loading */}
        <div className="w-full" style={{ display: loading && !error ? 'none' : 'block' }}>
          {/* Main Content Area */}
          <div className="space-y-6">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="runs">Active Runs</TabsTrigger>
                <TabsTrigger value="messages">Message Stream</TabsTrigger>
              </TabsList>

              {/* Active Runs Tab */}
              <TabsContent value="runs" className="space-y-4">
                {activeRuns.map((run) => (
                  <Card key={run.id}>
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="space-y-1">
                          <CardTitle className="text-base font-mono">{run.id}</CardTitle>
                          <CardDescription className="text-xs">
                            {run.github_url}
                          </CardDescription>
                        </div>
                        <Badge className={getStatusColor(run.status)}>
                          {run.status}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="text-sm text-gray-600 mb-3">{run.prompt}</div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                        <div>
                          <p className="text-xs text-gray-500">Variations</p>
                          <p className="font-medium">{run.variations}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Total Messages</p>
                          <p className="font-medium">{run.total_messages}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Message Rate</p>
                          <p className="font-medium">{run.message_rate_per_second}/s</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Started</p>
                          <p className="font-medium text-xs">
                            {run.started_at ? format(new Date(run.started_at), "HH:mm:ss") : "-"}
                          </p>
                        </div>
                      </div>
                      
                      {/* Variation metrics */}
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(run.variation_metrics).map(([varId, metrics]: [string, any]) => (
                          <div
                            key={varId}
                            className={`px-2 py-1 rounded text-xs ${
                              run.winning_variation_id === parseInt(varId)
                                ? "bg-green-100 text-green-800"
                                : "bg-gray-100 text-gray-700"
                            }`}
                          >
                            Var {varId}: {metrics.message_count} msgs
                          </div>
                        ))}
                      </div>
                      
                      <div className="mt-3 flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedRunId(run.id);
                            setActiveTab("messages");
                          }}
                        >
                          View Messages
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </TabsContent>

              {/* Messages Tab */}
              <TabsContent value="messages" className="space-y-4">
                {/* Filters */}
                <Card>
                  <CardContent className="pt-6">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                        <Input
                          placeholder="Search messages..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          className="pl-10"
                        />
                      </div>
                      
                      <Select value={selectedRunId || "all"} onValueChange={(v) => setSelectedRunId(v === "all" ? null : v)}>
                        <SelectTrigger>
                          <SelectValue placeholder="All runs" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All runs</SelectItem>
                          {activeRuns.map((run) => (
                            <SelectItem key={run.id} value={run.id}>
                              {run.id.slice(0, 8)}...
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      
                      <Select value={selectedOutputType || "all"} onValueChange={(v) => setSelectedOutputType(v === "all" ? null : v)}>
                        <SelectTrigger>
                          <SelectValue placeholder="All types" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All types</SelectItem>
                          <SelectItem value="stdout">stdout</SelectItem>
                          <SelectItem value="stderr">stderr</SelectItem>
                          <SelectItem value="status">status</SelectItem>
                          <SelectItem value="logging">logging</SelectItem>
                          <SelectItem value="summary">summary</SelectItem>
                          <SelectItem value="diffs">diffs</SelectItem>
                          <SelectItem value="addinfo">addinfo</SelectItem>
                        </SelectContent>
                      </Select>
                      
                      <Button
                        variant="outline"
                        onClick={() => {
                          setSearchQuery("");
                          setSelectedRunId(null);
                          setSelectedOutputType(null);
                          setMessageOffset(0);
                        }}
                      >
                        Clear Filters
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* Messages List */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center justify-between">
                      <span className="flex items-center">
                        <MessageSquare className="h-5 w-5 mr-2" />
                        Messages ({totalMessages.toLocaleString()} total)
                      </span>
                      <span className="text-sm font-normal text-gray-500">
                        Showing {messages.length} messages
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {messages.map((message) => (
                        <div
                          key={message.id}
                          className="border rounded-lg p-3 hover:bg-gray-50"
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center space-x-2">
                              <span className="text-xs font-mono text-gray-500">
                                {message.run_id.slice(0, 8)}
                              </span>
                              <Badge variant="outline" className="text-xs">
                                Var {message.variation_id}
                              </Badge>
                              <span className={`text-xs font-medium ${getOutputTypeColor(message.output_type)}`}>
                                {message.output_type}
                              </span>
                            </div>
                            <span className="text-xs text-gray-500">
                              {format(new Date(message.timestamp), "HH:mm:ss.SSS")}
                            </span>
                          </div>
                          <pre className="text-xs font-mono whitespace-pre-wrap break-all text-gray-700">
                            {message.content.slice(0, 200)}
                            {message.content.length > 200 && "..."}
                          </pre>
                        </div>
                      ))}
                    </div>
                    
                    {/* Pagination */}
                    <div className="mt-4 flex items-center justify-between">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setMessageOffset(Math.max(0, messageOffset - 100))}
                        disabled={messageOffset === 0}
                      >
                        Previous
                      </Button>
                      <span className="text-sm text-gray-500">
                        Showing {messageOffset + 1} - {messageOffset + messages.length}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setMessageOffset(messageOffset + 100)}
                        disabled={messageOffset + messages.length >= totalMessages}
                      >
                        Next
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
}