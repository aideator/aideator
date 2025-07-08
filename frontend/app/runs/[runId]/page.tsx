import { RunDetails } from "@/components/run-details"
import { PageHeader } from "@/components/page-header"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { ArrowLeft } from "lucide-react"

export default async function RunPage({ 
  params 
}: { 
  params: Promise<{ runId: string }> 
}) {
  const { runId } = await params;
  
  return (
    <div className="container mx-auto px-4 py-8">
      <PageHeader />

      <div className="mt-4">
        <Button variant="outline" size="sm" asChild>
          <Link href="/">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Home
          </Link>
        </Button>
      </div>

      <main className="mt-6">
        <RunDetails runId={runId} />
      </main>
    </div>
  )
}
