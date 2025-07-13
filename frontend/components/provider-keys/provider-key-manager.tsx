'use client'

import { useState, useEffect } from 'react'
import { ProviderAPIKey } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Plus, Key, AlertCircle } from 'lucide-react'
import { apiClient } from '@/lib/api'
import { ProviderKeyCard } from './provider-key-card'
import { ProviderKeyForm } from './provider-key-form'

export function ProviderKeyManager() {
  const [keys, setKeys] = useState<ProviderAPIKey[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingKey, setEditingKey] = useState<ProviderAPIKey | undefined>()

  useEffect(() => {
    loadKeys()
  }, [])

  const loadKeys = async () => {
    setIsLoading(true)
    setError('')
    try {
      const providerKeys = await apiClient.getProviderKeys()
      setKeys(providerKeys)
    } catch (error) {
      setError('Failed to load API keys')
      console.error('Failed to load keys:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async (data: any) => {
    try {
      if (editingKey) {
        await apiClient.updateProviderKey(editingKey.id, data)
      } else {
        await apiClient.createProviderKey(data)
      }
      setShowForm(false)
      setEditingKey(undefined)
      await loadKeys()
    } catch (error) {
      throw error
    }
  }

  const handleEdit = (key: ProviderAPIKey) => {
    setEditingKey(key)
    setShowForm(true)
  }

  const handleDelete = (key: ProviderAPIKey) => {
    setKeys(keys.filter(k => k.id !== key.id))
  }

  const handleCancel = () => {
    setShowForm(false)
    setEditingKey(undefined)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">API Keys</h2>
          <p className="text-muted-foreground">
            Manage your provider API keys for AI models
          </p>
        </div>
        <Button onClick={() => setShowForm(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add API Key
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {keys.length === 0 ? (
        <div className="rounded-lg border border-dashed p-8 text-center">
          <Key className="mx-auto h-12 w-12 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-medium">No API keys configured</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Add your provider API keys to start using AI models
          </p>
          <Button className="mt-4" onClick={() => setShowForm(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add your first API key
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {keys.map((key) => (
            <ProviderKeyCard
              key={key.id}
              providerKey={key}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onRefresh={loadKeys}
            />
          ))}
        </div>
      )}

      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>
              {editingKey ? 'Edit API Key' : 'Add API Key'}
            </DialogTitle>
          </DialogHeader>
          <ProviderKeyForm
            providerKey={editingKey}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
          />
        </DialogContent>
      </Dialog>
    </div>
  )
}