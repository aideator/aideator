'use client'

import { useState, useEffect } from 'react'
import { ProviderAPIKey, ProviderAPIKeyCreate, ProviderAPIKeyUpdate, Provider } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { apiClient } from '@/lib/api'

interface ProviderKeyFormProps {
  providerKey?: ProviderAPIKey
  onSubmit: (key: ProviderAPIKeyCreate | ProviderAPIKeyUpdate) => Promise<void>
  onCancel: () => void
}

export function ProviderKeyForm({ providerKey, onSubmit, onCancel }: ProviderKeyFormProps) {
  const [providers, setProviders] = useState<Provider[]>([])
  const [formData, setFormData] = useState({
    provider: providerKey?.provider || '',
    api_key: '',
    model_name: providerKey?.model_name || '',
    name: providerKey?.name || '',
    description: providerKey?.description || '',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    loadProviders()
  }, [])

  const loadProviders = async () => {
    try {
      const providerList = await apiClient.getProviders()
      setProviders(providerList)
    } catch (error) {
      console.error('Failed to load providers:', error)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      if (providerKey) {
        // Update existing key
        const updates: ProviderAPIKeyUpdate = {
          name: formData.name || undefined,
          description: formData.description || undefined,
        }
        if (formData.api_key) {
          updates.api_key = formData.api_key
        }
        await onSubmit(updates)
      } else {
        // Create new key
        if (!formData.provider || !formData.api_key) {
          setError('Provider and API key are required')
          setIsSubmitting(false)
          return
        }
        const newKey: ProviderAPIKeyCreate = {
          provider: formData.provider,
          api_key: formData.api_key,
          model_name: formData.model_name || undefined,
          name: formData.name || undefined,
          description: formData.description || undefined,
        }
        await onSubmit(newKey)
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to save API key')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="provider">Provider</Label>
        <Select
          value={formData.provider}
          onValueChange={(value) => setFormData({ ...formData, provider: value })}
          disabled={!!providerKey}
        >
          <SelectTrigger id="provider">
            <SelectValue placeholder="Select a provider" />
          </SelectTrigger>
          <SelectContent>
            {providers.map((provider) => (
              <SelectItem key={provider.name} value={provider.name}>
                {provider.display_name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="api_key">API Key</Label>
        <Input
          id="api_key"
          type="password"
          placeholder={providerKey ? 'Enter new API key to update' : 'Enter your API key'}
          value={formData.api_key}
          onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
          required={!providerKey}
        />
        {providerKey && (
          <p className="text-sm text-muted-foreground">
            Current key: {providerKey.key_hint}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="model_name">Model (optional)</Label>
        <Input
          id="model_name"
          placeholder="e.g., gpt-4, claude-3-opus"
          value={formData.model_name}
          onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
          disabled={!!providerKey}
        />
        <p className="text-sm text-muted-foreground">
          Leave empty to use this key for all models from this provider
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="name">Name (optional)</Label>
        <Input
          id="name"
          placeholder="e.g., Production Key, Personal Key"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description (optional)</Label>
        <Textarea
          id="description"
          placeholder="Add any notes about this API key..."
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          rows={3}
        />
      </div>

      <div className="flex gap-3">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : providerKey ? 'Update Key' : 'Add Key'}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  )
}