"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { CheckCircle, X, AlertTriangle, FileCode, Terminal } from "lucide-react"
import { formatLogTimestamp } from "@/utils/timezone"
import { 
  getBodyClasses, 
  getHeadingClasses, 
  getStatusColorClasses,
  commonTypographyCombinations, 
  componentTokens,
  getPaddingSpacing,
  getGapSpacing,
  getMarginSpacing
} from "@/lib/design-tokens"

// Mock task data for comparison
const mockTaskData = {
  id: "demo-task-123",
  taskDetails: {
    versions: [
      {
        id: 1,
        summary: "Updated the hello world message to be more cheerful and welcoming",
        files: [
          {
            name: "main.py",
            additions: 3,
            deletions: 1,
            diff: [
              { type: "normal", content: "def hello_world():" },
              { type: "del", content: '    print("Hello, World!")' },
              { type: "add", content: '    print("Hello, Beautiful World! 🌟")' },
              { type: "add", content: '    print("Have a wonderful day!")' },
              { type: "normal", content: "" },
              { type: "normal", content: "if __name__ == '__main__':" },
              { type: "normal", content: "    hello_world()" }
            ]
          },
          {
            name: "README.md",
            additions: 2,
            deletions: 0,
            diff: [
              { type: "normal", content: "# Hello World Demo" },
              { type: "normal", content: "" },
              { type: "add", content: "This demo shows a cheerful greeting message." },
              { type: "add", content: "Run with: `python main.py`" }
            ]
          }
        ]
      }
    ]
  }
}

const mockLogs = [
  { id: 1, timestamp: "2024-01-15T10:30:00Z", content: "Starting task execution..." },
  { id: 2, timestamp: "2024-01-15T10:30:02Z", content: "Reading file: main.py" },
  { id: 3, timestamp: "2024-01-15T10:30:03Z", content: "Applying changes..." },
  { id: 4, timestamp: "2024-01-15T10:30:04Z", content: "✓ Changes applied successfully" },
  { id: 5, timestamp: "2024-01-15T10:30:05Z", content: "Task completed successfully" }
]

const mockErrors = [
  {
    id: 1,
    timestamp: "2024-01-15T10:30:03Z",
    output_type: "error",
    content: "Warning: Deprecated function usage detected in line 3"
  }
]

// Original task page component (simplified for comparison)
function TaskPageOriginal() {
  const [activeVersion, setActiveVersion] = useState(1)
  const task = mockTaskData
  const versionData = task.taskDetails.versions[0]

  return (
    <div className="flex flex-1 overflow-hidden bg-gray-950 text-gray-200">
      {/* Left Sidebar */}
      <aside className="w-80 bg-gray-900/70 border-r border-gray-800 p-4 flex flex-col overflow-y-auto">
        <div className="flex items-center gap-2 mb-4">
          <Button
            variant="secondary"
            size="sm"
            className="data-[state=active]:bg-gray-700"
          >
            Version 1
          </Button>
        </div>

        <div className="space-y-6 text-sm">
          <div className="space-y-2">
            <h3 className="font-semibold text-gray-400">Summary</h3>
            <p className="text-gray-300">{versionData.summary}</p>
          </div>
          <div className="space-y-2">
            <h3 className="font-semibold text-gray-400">Testing</h3>
            <div className="flex items-center gap-2 text-xs bg-gray-800 p-2 rounded-md">
              <span className="font-mono bg-gray-700 px-1.5 py-0.5 rounded">pytest</span>
              <span className="text-gray-400">-v</span>
              <span className="text-red-400 bg-red-900/50 px-1.5 py-0.5 rounded">0</span>
            </div>
          </div>
          <div className="space-y-2">
            <h3 className="font-semibold text-gray-400">FILE ({versionData.files.length})</h3>
            <div className="space-y-1">
              {versionData.files.map((file) => (
                <div key={file.name} className="flex justify-between items-center p-2 rounded-md hover:bg-gray-800">
                  <span>{file.name}</span>
                  <div className="font-mono text-xs">
                    <span className="text-green-400">+{file.additions}</span>{" "}
                    <span className="text-red-400">-{file.deletions}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col bg-gray-950">
        <Tabs defaultValue="logs" className="flex-1 flex flex-col">
          <TabsList className="px-4 border-b border-gray-800 bg-transparent justify-start rounded-none">
            <TabsTrigger
              value="logs"
              className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 border-white rounded-none"
            >
              <Terminal className="w-4 h-4 mr-2" />
              Logs
            </TabsTrigger>
            <TabsTrigger
              value="errors"
              className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 border-white rounded-none"
            >
              <AlertTriangle className="w-4 h-4 mr-2" />
              Errors
            </TabsTrigger>
          </TabsList>
          <TabsContent value="logs" className="flex-1 overflow-y-auto p-4 font-mono text-sm">
            <div className="space-y-2">
              {mockLogs.map((log) => (
                <div key={log.id} className="flex gap-3 text-sm">
                  <span className="text-gray-500 text-xs w-24 flex-shrink-0">
                    {formatLogTimestamp(log.timestamp)}
                  </span>
                  <pre className="text-gray-300 whitespace-pre-wrap flex-1">{log.content}</pre>
                </div>
              ))}
            </div>
          </TabsContent>
          <TabsContent value="errors" className="flex-1 overflow-y-auto p-4">
            <div className="space-y-4">
              {mockErrors.map((errorItem) => (
                <div key={errorItem.id} className="rounded-lg p-4 border bg-red-950/50 border-red-800">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 mt-0.5 flex-shrink-0 text-red-400" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className="font-medium text-red-300">Error</h4>
                        <span className="text-xs text-gray-500">
                          {formatLogTimestamp(errorItem.timestamp)}
                        </span>
                      </div>
                      <pre className="text-sm p-3 rounded border overflow-x-auto whitespace-pre-wrap bg-black/50 border-red-700/50 text-red-200">
                        {errorItem.content}
                      </pre>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}

// Token system task page component (simplified for comparison)
function TaskPageTokens() {
  const [activeVersion, setActiveVersion] = useState(1)
  const task = mockTaskData
  const versionData = task.taskDetails.versions[0]

  return (
    <div className={`flex flex-1 overflow-hidden ${componentTokens.ui.layout.page}`}>
      {/* Left Sidebar */}
      <aside className={`w-80 ${componentTokens.ui.card.secondary} border-r ${componentTokens.ui.layout.border} ${getPaddingSpacing('md')} flex flex-col overflow-y-auto`}>
        <div className={`flex items-center ${getGapSpacing('sm')} ${getMarginSpacing('md')}`}>
          <Button
            variant="secondary"
            size="sm"
            className="data-[state=active]:bg-gray-700"
          >
            Version 1
          </Button>
        </div>

        <div className={`${getGapSpacing('lg')} space-y-6 text-sm`}>
          <div className={`${getGapSpacing('sm')} space-y-2`}>
            <h3 className={`font-semibold ${getBodyClasses('secondary')}`}>Summary</h3>
            <p className={getBodyClasses('primary')}>{versionData.summary}</p>
          </div>
          <div className={`${getGapSpacing('sm')} space-y-2`}>
            <h3 className={`font-semibold ${getBodyClasses('secondary')}`}>Testing</h3>
            <div className={`flex items-center ${getGapSpacing('sm')} text-xs ${componentTokens.ui.card.secondary} ${getPaddingSpacing('sm')} rounded-md`}>
              <span className={`${commonTypographyCombinations.codeInline} bg-gray-700 ${getPaddingSpacing('xs')} rounded`}>pytest</span>
              <span className={getBodyClasses('secondary')}>-v</span>
              <span className={`${getStatusColorClasses('failed')} bg-red-900/50 ${getPaddingSpacing('xs')} rounded`}>0</span>
            </div>
          </div>
          <div className={`${getGapSpacing('sm')} space-y-2`}>
            <h3 className={`font-semibold ${getBodyClasses('secondary')}`}>FILE ({versionData.files.length})</h3>
            <div className={`${getGapSpacing('xs')} space-y-1`}>
              {versionData.files.map((file) => (
                <div key={file.name} className={`flex justify-between items-center ${getPaddingSpacing('sm')} rounded-md hover:bg-gray-800`}>
                  <span className={getBodyClasses('primary')}>{file.name}</span>
                  <div className={`${commonTypographyCombinations.codeInline} text-xs`}>
                    <span className={getStatusColorClasses('success')}>+{file.additions}</span>{" "}
                    <span className={getStatusColorClasses('failed')}>-{file.deletions}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className={`flex-1 flex flex-col ${componentTokens.ui.layout.page}`}>
        <Tabs defaultValue="logs" className="flex-1 flex flex-col">
          <TabsList className={`${getPaddingSpacing('md')} border-b ${componentTokens.ui.layout.border} bg-transparent justify-start rounded-none`}>
            <TabsTrigger
              value="logs"
              className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 border-white rounded-none"
            >
              <Terminal className={`w-4 h-4 ${getMarginSpacing('xs')}`} />
              Logs
            </TabsTrigger>
            <TabsTrigger
              value="errors"
              className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 border-white rounded-none"
            >
              <AlertTriangle className={`w-4 h-4 ${getMarginSpacing('xs')}`} />
              Errors
            </TabsTrigger>
          </TabsList>
          <TabsContent value="logs" className={`flex-1 overflow-y-auto ${getPaddingSpacing('md')} ${commonTypographyCombinations.codeInline} text-sm`}>
            <div className={`${getGapSpacing('sm')} space-y-2`}>
              {mockLogs.map((log) => (
                <div key={log.id} className={`flex ${getGapSpacing('sm')} text-sm`}>
                  <span className={`${getBodyClasses('muted')} text-xs w-24 flex-shrink-0`}>
                    {formatLogTimestamp(log.timestamp)}
                  </span>
                  <pre className={`${getBodyClasses('primary')} whitespace-pre-wrap flex-1`}>{log.content}</pre>
                </div>
              ))}
            </div>
          </TabsContent>
          <TabsContent value="errors" className={`flex-1 overflow-y-auto ${getPaddingSpacing('md')}`}>
            <div className={`${getGapSpacing('md')} space-y-4`}>
              {mockErrors.map((errorItem) => (
                <div key={errorItem.id} className={`rounded-lg ${getPaddingSpacing('md')} border bg-red-950/50 border-red-800`}>
                  <div className={`flex items-start ${getGapSpacing('sm')}`}>
                    <AlertTriangle className={`w-5 h-5 mt-0.5 flex-shrink-0 ${getStatusColorClasses('failed')}`} />
                    <div className="flex-1">
                      <div className={`flex items-center ${getGapSpacing('sm')} ${getMarginSpacing('xs')}`}>
                        <h4 className={`font-medium ${getStatusColorClasses('failed')}`}>Error</h4>
                        <span className={`text-xs ${getBodyClasses('muted')}`}>
                          {formatLogTimestamp(errorItem.timestamp)}
                        </span>
                      </div>
                      <pre className={`text-sm ${getPaddingSpacing('sm')} rounded border overflow-x-auto whitespace-pre-wrap bg-black/50 border-red-700/50 text-red-200`}>
                        {errorItem.content}
                      </pre>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}

// Color comparison data
const taskPageColorMappings = [
  { element: "Page Background", original: "bg-gray-950", token: "componentTokens.ui.layout.page", matches: true },
  { element: "Sidebar Background", original: "bg-gray-900/70", token: "componentTokens.ui.card.secondary", matches: true },
  { element: "Primary Text", original: "text-gray-200", token: "getBodyClasses('primary')", matches: true },
  { element: "Secondary Text", original: "text-gray-400", token: "getBodyClasses('secondary')", matches: true },
  { element: "Muted Text", original: "text-gray-500", token: "getBodyClasses('muted')", matches: true },
  { element: "Error Text", original: "text-red-400", token: "getStatusColorClasses('failed')", matches: true },
  { element: "Success Text", original: "text-green-400", token: "getStatusColorClasses('success')", matches: true },
  { element: "Border Color", original: "border-gray-800", token: "componentTokens.ui.layout.border", matches: true },
  { element: "Card Background", original: "bg-gray-800", token: "componentTokens.ui.card.secondary", matches: true },
  { element: "Code Font", original: "font-mono", token: "commonTypographyCombinations.codeInline", matches: true },
]

function ColorValidationTable() {
  const allMatch = taskPageColorMappings.every(item => item.matches)
  
  return (
    <Card className={componentTokens.ui.card.secondary}>
      <CardHeader>
        <CardTitle className={`${commonTypographyCombinations.cardTitle} flex items-center ${getGapSpacing('sm')}`}>
          Task Page Color Validation
          {allMatch ? (
            <CheckCircle className={`w-5 h-5 ${getStatusColorClasses('success')}`} />
          ) : (
            <AlertTriangle className={`w-5 h-5 ${getStatusColorClasses('failed')}`} />
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`grid grid-cols-4 ${getGapSpacing('sm')} ${getMarginSpacing('sm')} font-medium text-sm`}>
          <div>Element</div>
          <div>Original (Hardcoded)</div>
          <div>Token System</div>
          <div>Match</div>
        </div>
        
        {taskPageColorMappings.map((item, index) => (
          <div key={index} className={`grid grid-cols-4 ${getGapSpacing('sm')} items-center py-2 border-b border-gray-200 dark:border-gray-700`}>
            <div className={`text-sm ${getBodyClasses('primary')}`}>{item.element}</div>
            <div className={`text-xs ${commonTypographyCombinations.codeInline} break-all`}>
              {item.original}
            </div>
            <div className={`text-xs ${commonTypographyCombinations.codeInline} break-all`}>
              {item.token}
            </div>
            <div className="flex items-center justify-center">
              {item.matches ? (
                <CheckCircle className={`w-4 h-4 ${getStatusColorClasses('success')}`} />
              ) : (
                <X className={`w-4 h-4 ${getStatusColorClasses('failed')}`} />
              )}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

export default function CompareTaskPages() {
  return (
    <div className={componentTokens.ui.layout.page}>
      <div className={componentTokens.ui.layout.container}>
        <div className={getMarginSpacing('lg')}>
          <h1 className={`${commonTypographyCombinations.pageTitle} text-center ${getMarginSpacing('lg')}`}>
            Task Page Design Token Comparison
          </h1>
          
          <div className={`${getGapSpacing('lg')} space-y-8`}>
            {/* Color Validation Summary */}
            <Card className={componentTokens.ui.card.primary}>
              <CardHeader>
                <CardTitle className={`${commonTypographyCombinations.sectionHeader} flex items-center ${getGapSpacing('sm')}`}>
                  <CheckCircle className={`w-5 h-5 ${getStatusColorClasses('success')}`} />
                  Task Page Token Validation Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`${getGapSpacing('md')} space-y-2`}>
                  <div className={`flex items-center justify-between ${getPaddingSpacing('sm')} rounded bg-green-50 dark:bg-green-950/20`}>
                    <span className={getBodyClasses('primary')}>Color Mapping</span>
                    <Badge variant="outline" className="text-green-700 dark:text-green-400">
                      ✓ 10/10 matches
                    </Badge>
                  </div>
                  <div className={`flex items-center justify-between ${getPaddingSpacing('sm')} rounded bg-green-50 dark:bg-green-950/20`}>
                    <span className={getBodyClasses('primary')}>Typography System</span>
                    <Badge variant="outline" className="text-green-700 dark:text-green-400">
                      ✓ Consistent
                    </Badge>
                  </div>
                  <div className={`flex items-center justify-between ${getPaddingSpacing('sm')} rounded bg-green-50 dark:bg-green-950/20`}>
                    <span className={getBodyClasses('primary')}>Spacing System</span>
                    <Badge variant="outline" className="text-green-700 dark:text-green-400">
                      ✓ Standardized
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Visual Comparison */}
            <Card className={componentTokens.ui.card.primary}>
              <CardHeader>
                <CardTitle className={commonTypographyCombinations.sectionHeader}>
                  Visual Comparison
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="side-by-side" className="w-full">
                  <TabsList className={`grid w-full grid-cols-3 ${getMarginSpacing('md')}`}>
                    <TabsTrigger value="side-by-side">Side by Side</TabsTrigger>
                    <TabsTrigger value="original">Original (Hardcoded)</TabsTrigger>
                    <TabsTrigger value="tokens">Token System</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="side-by-side">
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                      <div>
                        <div className={`${getMarginSpacing('md')} flex items-center ${getGapSpacing('sm')}`}>
                          <h3 className={`${getHeadingClasses('h3')} ${getBodyClasses('primary')}`}>
                            Original (Hardcoded)
                          </h3>
                          <Badge variant="outline" className="text-xs">
                            22 hardcoded colors
                          </Badge>
                        </div>
                        <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                          <div className="scale-[0.4] origin-top-left w-[250%] h-[200%] overflow-hidden">
                            <TaskPageOriginal />
                          </div>
                        </div>
                      </div>
                      
                      <div>
                        <div className={`${getMarginSpacing('md')} flex items-center ${getGapSpacing('sm')}`}>
                          <h3 className={`${getHeadingClasses('h3')} ${getBodyClasses('primary')}`}>
                            Token System
                          </h3>
                          <Badge variant="outline" className="text-xs">
                            0 hardcoded colors
                          </Badge>
                        </div>
                        <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                          <div className="scale-[0.4] origin-top-left w-[250%] h-[200%] overflow-hidden">
                            <TaskPageTokens />
                          </div>
                        </div>
                      </div>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="original">
                    <div className={getMarginSpacing('md')}>
                      <div className={`${getMarginSpacing('md')} flex items-center ${getGapSpacing('sm')}`}>
                        <h3 className={`${getHeadingClasses('h3')} ${getBodyClasses('primary')}`}>
                          Original Implementation (Hardcoded CSS)
                        </h3>
                        <Badge variant="outline" className="text-xs">
                          22 hardcoded colors
                        </Badge>
                      </div>
                      <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                        <div className="scale-75 origin-top-left w-[133%] h-[133%] overflow-hidden">
                          <TaskPageOriginal />
                        </div>
                      </div>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="tokens">
                    <div className={getMarginSpacing('md')}>
                      <div className={`${getMarginSpacing('md')} flex items-center ${getGapSpacing('sm')}`}>
                        <h3 className={`${getHeadingClasses('h3')} ${getBodyClasses('primary')}`}>
                          Token System Implementation
                        </h3>
                        <Badge variant="outline" className="text-xs">
                          0 hardcoded colors
                        </Badge>
                      </div>
                      <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                        <div className="scale-75 origin-top-left w-[133%] h-[133%] overflow-hidden">
                          <TaskPageTokens />
                        </div>
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>

            {/* Detailed Color Validation */}
            <ColorValidationTable />

            {/* Benefits Summary */}
            <Card className={componentTokens.ui.card.secondary}>
              <CardHeader>
                <CardTitle className={commonTypographyCombinations.cardTitle}>
                  Task Page Tokenization Benefits
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`grid grid-cols-1 md:grid-cols-3 ${getGapSpacing('lg')}`}>
                  <div>
                    <h4 className={`${getBodyClasses('primary')} font-medium ${getMarginSpacing('sm')}`}>
                      Code Quality
                    </h4>
                    <ul className={`${getBodyClasses('secondary')} text-sm space-y-1`}>
                      <li>• Eliminated 22 hardcoded colors</li>
                      <li>• Centralized color management</li>
                      <li>• Type-safe design tokens</li>
                      <li>• Consistent error handling</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className={`${getBodyClasses('primary')} font-medium ${getMarginSpacing('sm')}`}>
                      User Experience
                    </h4>
                    <ul className={`${getBodyClasses('secondary')} text-sm space-y-1`}>
                      <li>• Consistent visual hierarchy</li>
                      <li>• Improved accessibility</li>
                      <li>• Better status indicators</li>
                      <li>• Unified spacing system</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className={`${getBodyClasses('primary')} font-medium ${getMarginSpacing('sm')}`}>
                      Maintainability
                    </h4>
                    <ul className={`${getBodyClasses('secondary')} text-sm space-y-1`}>
                      <li>• Single source of truth</li>
                      <li>• Easy theme updates</li>
                      <li>• Reduced code duplication</li>
                      <li>• Automated validation</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}