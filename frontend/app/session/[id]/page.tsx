"use client"

import { useState } from "react"
import { FileCode, Terminal } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Input } from "@/components/ui/input"
import { sessions } from "@/lib/data"
import { notFound } from "next/navigation"

export default function SessionPage({ params }: { params: { id: string } }) {
  const [activeVersion, setActiveVersion] = useState(1)

  const session = sessions.find((s) => s.id === params.id)

  if (!session || !session.sessionDetails) {
    return notFound()
  }

  const versionData = session.sessionDetails.versions.find((v) => v.id === activeVersion)

  if (!versionData) {
    // Fallback to first version if active version not found
    const firstVersion = session.sessionDetails.versions[0]
    if (!firstVersion) return notFound()
    setActiveVersion(firstVersion.id)
    return null // Re-render will handle it
  }

  return (
    <div className="flex flex-1 overflow-hidden bg-gray-950 text-gray-200">
      {/* Left Sidebar */}
      <aside className="w-80 bg-gray-900/70 border-r border-gray-800 p-4 flex flex-col overflow-y-auto">
          <div className="flex items-center gap-2 mb-4">
            {session.sessionDetails.versions.map((v) => (
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
                {`[INFO] Starting session execution...
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
[INFO] Session completed successfully in 2m 1s.`}
              </pre>
            </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
