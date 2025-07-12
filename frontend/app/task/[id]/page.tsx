"use client"

import { useState, use } from "react"
import { FileCode, Terminal, AlertTriangle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Input } from "@/components/ui/input"
import { useTaskDetail } from "@/hooks/use-task-detail"
import { notFound } from "next/navigation"

export default function TaskPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const [activeVersion, setActiveVersion] = useState(1)
  const { task, loading, error } = useTaskDetail(id)

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center bg-gray-950 text-gray-200">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
          <p>Loading task details...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-1 items-center justify-center bg-gray-950 text-gray-200">
        <div className="text-center">
          <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-4" />
          <p className="text-red-300 mb-2">Failed to load task</p>
          <p className="text-gray-400 text-sm">{error}</p>
        </div>
      </div>
    )
  }

  if (!task || !task.taskDetails) {
    return notFound()
  }

  const versionData = task.taskDetails.versions.find((v) => v.id === activeVersion)

  if (!versionData) {
    // Fallback to first version if active version not found
    const firstVersion = task.taskDetails.versions[0]
    if (!firstVersion) return notFound()
    setActiveVersion(firstVersion.id)
    return null // Re-render will handle it
  }

  return (
    <div className="flex flex-1 overflow-hidden bg-gray-950 text-gray-200">
      {/* Left Sidebar */}
      <aside className="w-80 bg-gray-900/70 border-r border-gray-800 p-4 flex flex-col overflow-y-auto">
          <div className="flex items-center gap-2 mb-4">
            {task.taskDetails.versions.map((v) => (
              <Button
                key={v.id}
                variant={activeVersion === v.id ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setActiveVersion(v.id)}
                className="data-[state=active]:bg-gray-700"
              >
                Version {v.id}
              </Button>
            ))}
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
              <h3 className="font-semibold text-gray-400">Network access</h3>
              <p className="text-gray-300">Some requests were blocked due to network access restrictions.</p>
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
          <div className="mt-auto pt-4">
            <Input placeholder="Request changes or ask a question" className="bg-gray-800 border-gray-700" />
          </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col bg-gray-950">
          <Tabs defaultValue="diff" className="flex-1 flex flex-col">
            <TabsList className="px-4 border-b border-gray-800 bg-transparent justify-start rounded-none">
              <TabsTrigger
                value="diff"
                className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 border-white rounded-none"
              >
                <FileCode className="w-4 h-4 mr-2" />
                Diff
              </TabsTrigger>
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
            <TabsContent value="diff" className="flex-1 overflow-y-auto p-4">
              <Accordion type="single" collapsible className="w-full" defaultValue="item-0">
                {versionData.files.map((file, index) => (
                  <AccordionItem value={`item-${index}`} key={index} className="border-gray-800">
                    <AccordionTrigger className="bg-gray-900 p-2 rounded-md hover:no-underline">
                      <div className="flex justify-between items-center w-full">
                        <span>{file.name}</span>
                        <div className="font-mono text-xs">
                          <span className="text-green-400">+{file.additions}</span>{" "}
                          <span className="text-red-400">-{file.deletions}</span>
                        </div>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="p-0">
                      <pre className="text-sm bg-black rounded-b-md overflow-x-auto">
                        <code>
                          {file.diff.map((line, i) => (
                            <div
                              key={i}
                              className={`relative pl-12 pr-4 py-0.5 ${line.type === "add" ? "diff-add" : line.type === "del" ? "diff-del" : ""}`}
                            >
                              <span className="absolute left-4 select-none text-gray-500">
                                {line.type !== "add" ? line.oldLine : ""}
                              </span>
                              <span className="absolute left-8 select-none text-gray-500">
                                {line.type !== "del" ? line.newLine : ""}
                              </span>
                              <span>{line.content}</span>
                            </div>
                          ))}
                        </code>
                      </pre>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </TabsContent>
            <TabsContent value="logs" className="flex-1 overflow-y-auto p-4 font-mono text-sm">
              <pre>
                {`[INFO] Starting task execution...
[INFO] Cloning repository aideator/helloworld...
[INFO] Repository cloned successfully.
[INFO] Checking out branch 'main'...
[INFO] Branch 'main' checked out.
[INFO] Analyzing task: "make hello world label more ominous"
[AGENT] Understanding the request... The user wants to change the text in README.md.
[AGENT] Planning changes...
[AGENT] 1. Read README.md
[AGENT] 2. Replace "Hello World for Python" with something more ominous.
[AGENT] 3. Write the changes back to README.md.
[EXEC] Reading file: README.md
[EXEC] Applying changes to README.md
[EXEC] Writing file: README.md
[INFO] Changes applied successfully.
[INFO] Running tests...
[TEST] pytest -v
[TEST] ============================= test session starts ==============================
[TEST] collected 0 items
[TEST] ============================ 0 tests ran in 0.01s ==============================
[INFO] Task completed successfully in 2m 1s.`}
              </pre>
            </TabsContent>
            <TabsContent value="errors" className="flex-1 overflow-y-auto p-4">
              <div className="space-y-4">
                <div className="bg-red-950/50 border border-red-800 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className="font-medium text-red-300 mb-2">Type Error in main.py</h4>
                      <p className="text-sm text-red-200 mb-3">
                        Line 42: Argument of type &apos;str&apos; cannot be assigned to parameter of type &apos;int&apos;
                      </p>
                      <pre className="text-xs bg-black/50 p-3 rounded border border-red-700/50 overflow-x-auto">
                        <code className="text-red-300">
{`def process_data(count: int) -> None:
    pass

process_data("hello")  # Error: expected int, got str`}
                        </code>
                      </pre>
                    </div>
                  </div>
                </div>
                
                <div className="bg-amber-950/50 border border-amber-800 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className="font-medium text-amber-300 mb-2">Linting Warning</h4>
                      <p className="text-sm text-amber-200 mb-3">
                        Line 15: Unused import &apos;os&apos; detected
                      </p>
                      <pre className="text-xs bg-black/50 p-3 rounded border border-amber-700/50 overflow-x-auto">
                        <code className="text-amber-300">
{`import os  # This import is never used
import sys

print(sys.version)`}
                        </code>
                      </pre>
                    </div>
                  </div>
                </div>
                
                <div className="bg-red-950/50 border border-red-800 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className="font-medium text-red-300 mb-2">Test Failure</h4>
                      <p className="text-sm text-red-200 mb-3">
                        test_hello_world.py::test_greeting - AssertionError
                      </p>
                      <pre className="text-xs bg-black/50 p-3 rounded border border-red-700/50 overflow-x-auto">
                        <code className="text-red-300">
{`def test_greeting():
    result = get_greeting()
    assert result == "Hello, World!"
    # AssertionError: assert 'An ominous Hello World for Python' == 'Hello, World!'`}
                        </code>
                      </pre>
                    </div>
                  </div>
                </div>
                
                <div className="text-center py-8 text-gray-500">
                  <p className="text-sm">No additional errors found in this task execution.</p>
                </div>
              </div>
            </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
