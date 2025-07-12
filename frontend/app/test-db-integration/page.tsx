"use client"

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { AgentOutputViewer } from '@/components/agent-output-viewer'

export default function TestDatabaseIntegrationPage() {
  const [runId, setRunId] = useState('test-db-integration-demo')
  const [isViewerActive, setIsViewerActive] = useState(false)

  return (
    <div className="container mx-auto py-8 space-y-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">Database Integration Test</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Test the PostgreSQL-based agent logging system with real-time WebSocket streaming
          </p>
        </div>

        {/* Configuration */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Test Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="run-id">Run ID</Label>
              <Input
                id="run-id"
                value={runId}
                onChange={(e) => setRunId(e.target.value)}
                placeholder="Enter run ID to monitor"
              />
              <p className="text-sm text-gray-500">
                Use a run ID from a real agent execution to see live outputs
              </p>
            </div>
            
            <div className="flex gap-2">
              <Button 
                onClick={() => setIsViewerActive(true)}
                disabled={!runId || isViewerActive}
              >
                Start Monitoring
              </Button>
              <Button 
                variant="outline"
                onClick={() => setIsViewerActive(false)}
                disabled={!isViewerActive}
              >
                Stop Monitoring
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Integration Status */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Integration Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h4 className="font-medium text-green-600">✅ Completed</h4>
                <ul className="text-sm space-y-1 text-gray-600">
                  <li>• DATABASE_URL configured in agent containers</li>
                  <li>• DatabaseService connected to agent execution</li>
                  <li>• Async/sync compatibility fixed</li>
                  <li>• Database connectivity verified</li>
                  <li>• API endpoints for historical data</li>
                  <li>• WebSocket client implementation</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-blue-600">🔄 Architecture</h4>
                <ul className="text-sm space-y-1 text-gray-600">
                  <li>• Agents write to PostgreSQL via DatabaseService</li>
                  <li>• Real-time streaming via Redis + WebSocket</li>
                  <li>• Frontend consumes both historical & live data</li>
                  <li>• Multiple output types classified</li>
                  <li>• Multi-agent variation support</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Agent Output Viewer */}
        {isViewerActive && (
          <AgentOutputViewer runId={runId} />
        )}

        {/* Instructions */}
        {!isViewerActive && (
          <Card>
            <CardHeader>
              <CardTitle>Testing Instructions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg">
                <h4 className="font-medium mb-2">To test the integration:</h4>
                <ol className="list-decimal list-inside space-y-2 text-sm">
                  <li>Start an agent run through the API or main interface</li>
                  <li>Copy the run ID from the response</li>
                  <li>Paste it into the Run ID field above</li>
                  <li>Click &quot;Start Monitoring&quot; to see real-time outputs</li>
                  <li>Outputs will appear as agents write to the database</li>
                </ol>
              </div>
              
              <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                <h4 className="font-medium mb-2">🎯 What you&apos;ll see:</h4>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li>Real-time agent outputs as they&apos;re written to PostgreSQL</li>
                  <li>Different output types (stdout, status, summary, etc.)</li>
                  <li>Multiple agent variations in separate tabs</li>
                  <li>Connection status and auto-reconnection</li>
                  <li>Output statistics and filtering</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}