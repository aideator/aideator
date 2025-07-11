import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { GitBranch, MessageSquare, Mic, Github } from "lucide-react"
import Link from "next/link"
import { jobs } from "@/lib/data"

export default function Home() {
  return (
    <div className="bg-gray-950 text-gray-50 min-h-screen">
      <div className="container mx-auto max-w-3xl py-16">
        <h1 className="text-4xl font-medium text-center mb-8">What are we coding next?</h1>

        <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-4 space-y-4">
          <Textarea
            placeholder="Describe a task"
            className="bg-transparent border-0 text-base resize-none focus-visible:ring-0"
            rows={4}
          />
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Select defaultValue="aideator/helloworld">
                <SelectTrigger className="bg-gray-800/60 border-gray-700 w-auto gap-2">
                  <Github className="w-4 h-4 text-gray-400" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="aideator/helloworld">aideator/helloworld</SelectItem>
                  <SelectItem value="vercel/next.js">vercel/next.js</SelectItem>
                  <SelectItem value="shadcn/ui">shadcn/ui</SelectItem>
                </SelectContent>
              </Select>
              <Select defaultValue="main">
                <SelectTrigger className="bg-gray-800/60 border-gray-700 w-auto gap-2">
                  <GitBranch className="w-4 h-4 text-gray-400" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="main">main</SelectItem>
                  <SelectItem value="dev">dev</SelectItem>
                  <SelectItem value="staging">staging</SelectItem>
                </SelectContent>
              </Select>
              <Select defaultValue="3">
                <SelectTrigger className="bg-gray-800/60 border-gray-700 w-auto gap-2">
                  <SelectValue />x
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1x</SelectItem>
                  <SelectItem value="2">2x</SelectItem>
                  <SelectItem value="3">3x</SelectItem>
                  <SelectItem value="4">4x</SelectItem>
                  <SelectItem value="5">5x</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button variant="ghost" size="icon">
              <Mic className="w-5 h-5" />
            </Button>
          </div>
        </div>

        <Tabs defaultValue="tasks" className="mt-10">
          <TabsList className="border-b border-gray-800 rounded-none w-full justify-start bg-transparent p-0">
            <TabsTrigger
              value="tasks"
              className="rounded-none data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 border-white"
            >
              Tasks
            </TabsTrigger>
            <TabsTrigger
              value="archive"
              className="rounded-none data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 border-white"
            >
              Archive
            </TabsTrigger>
          </TabsList>
          <TabsContent value="tasks" className="mt-6 space-y-1">
            {jobs.map((job) => (
              <Link href={`/job/${job.id}`} key={job.id}>
                <div className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-900 transition-colors cursor-pointer">
                  <div className="flex flex-col">
                    <span className="font-medium">{job.title}</span>
                    <span className="text-sm text-gray-400">{job.details}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    {job.status === "Completed" && (
                      <>
                        <div className="flex items-center gap-1 text-sm text-gray-400">
                          <MessageSquare className="w-4 h-4" />
                          <span>{job.versions}</span>
                        </div>
                        <div className="font-mono text-sm">
                          <span className="text-green-400">+{job.additions}</span>{" "}
                          <span className="text-red-400">-{job.deletions}</span>
                        </div>
                      </>
                    )}
                    {job.status === "Open" && (
                      <span className="text-sm text-green-400 bg-green-900/50 px-2 py-1 rounded-md">Open</span>
                    )}
                    {job.status === "Failed" && <span className="text-sm text-red-400">Failed</span>}
                  </div>
                </div>
              </Link>
            ))}
          </TabsContent>
          <TabsContent value="archive" className="mt-6">
            <p className="text-center text-gray-500">Archived tasks will appear here.</p>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
