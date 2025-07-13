"use client"

import { DiffViewer } from '@/diffs/DiffViewer'

export default function DiffsPage() {
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">Code Diffs</h1>
      <DiffViewer options={{ theme: "dark", highlight: true }} />
    </div>
  )
}