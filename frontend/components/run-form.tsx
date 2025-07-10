"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Loader2 } from "lucide-react"
import { createRun } from "@/lib/api-client"

export function RunForm() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [formData, setFormData] = useState({
    github_url: "",
    prompt: "",
    variations: "3",
    agent_config: {
      model: "claude-3-sonnet-20240229",
      temperature: 0.7,
    },
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSelectChange = (name: string, value: string) => {
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const response = await createRun({
        ...formData,
        variations: Number.parseInt(formData.variations),
      })

      router.push(`/runs/${response.run_id}`)
    } catch (error) {
      console.error("Error creating run:", error)
      // Show error to user - you might want to add a toast or alert here
      alert(`Error: ${error instanceof Error ? error.message : "Unknown error occurred"}`)
      setIsLoading(false)
    }
  }

  return (
    <Card className="p-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-4">
          <div>
            <Label htmlFor="github_url">GitHub Repository URL</Label>
            <Input
              id="github_url"
              name="github_url"
              placeholder="https://github.com/username/repository"
              value={formData.github_url}
              onChange={handleChange}
              required
            />
          </div>

          <div>
            <Label htmlFor="prompt">Prompt</Label>
            <Textarea
              id="prompt"
              name="prompt"
              placeholder="Add comprehensive error handling to all API endpoints"
              value={formData.prompt}
              onChange={handleChange}
              rows={4}
              required
            />
          </div>

          <div>
            <Label htmlFor="variations">Number of Variations</Label>
            <Select value={formData.variations} onValueChange={(value) => handleSelectChange("variations", value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select number of variations" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">1</SelectItem>
                <SelectItem value="2">2</SelectItem>
                <SelectItem value="3">3</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Creating Run...
            </>
          ) : (
            "Create Run"
          )}
        </Button>
      </form>
    </Card>
  )
}
