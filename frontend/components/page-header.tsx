import { BrainCircuit } from "lucide-react"

export function PageHeader() {
  return (
    <header className="flex items-center space-x-lg">
      <BrainCircuit className="h-12 w-12 text-ai-primary" />
      <div>
        <h1 className="text-h1 font-bold tracking-tight text-neutral-charcoal">AIdeator</h1>
        <p className="text-body text-neutral-shadow">Kubernetes-native LLM orchestration platform</p>
      </div>
    </header>
  )
}
