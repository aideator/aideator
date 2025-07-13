'use client'

import { useState } from 'react'
import { ProviderAPIKey } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Trash2, Edit, CheckCircle, XCircle, RefreshCw } from 'lucide-react'
import { apiClient } from '@/lib/api'

interface ProviderKeyCardProps {
  providerKey: ProviderAPIKey
  onEdit: (key: ProviderAPIKey) => void
  onDelete: (key: ProviderAPIKey) => void
  onRefresh: () => void
}

export function ProviderKeyCard({ providerKey, onEdit, onDelete, onRefresh }: ProviderKeyCardProps) {
  const [isValidating, setIsValidating] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const handleValidate = async () => {
    setIsValidating(true)
    try {
      await apiClient.validateProviderKey(providerKey.id)
      // Always refresh to show updated validation status
      onRefresh()
    } catch (error) {
      console.error('Failed to validate key:', error)
    } finally {
      setIsValidating(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this API key?')) return
    
    setIsDeleting(true)
    try {
      await apiClient.deleteProviderKey(providerKey.id)
      onDelete(providerKey)
    } catch (error) {
      console.error('Failed to delete key:', error)
    } finally {
      setIsDeleting(false)
    }
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleDateString()
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">
              {providerKey.name || `${providerKey.provider} API Key`}
            </CardTitle>
            <CardDescription>
              {providerKey.description || `API key for ${providerKey.provider}`}
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Badge variant={providerKey.is_active ? 'default' : 'secondary'}>
              {providerKey.is_active ? 'Active' : 'Inactive'}
            </Badge>
            {providerKey.is_valid !== null && (
              <Badge variant={providerKey.is_valid ? 'success' : 'destructive'}>
                {providerKey.is_valid ? <CheckCircle className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                {providerKey.is_valid ? 'Valid' : 'Invalid'}
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Provider:</span>
            <span className="font-mono">{providerKey.provider}</span>
          </div>
          {providerKey.model_name && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Model:</span>
              <span className="font-mono">{providerKey.model_name}</span>
            </div>
          )}
          <div className="flex justify-between">
            <span className="text-muted-foreground">Key:</span>
            <span className="font-mono">{providerKey.key_hint}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Last used:</span>
            <span>{formatDate(providerKey.last_used_at)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Created:</span>
            <span>{formatDate(providerKey.created_at)}</span>
          </div>
          {providerKey.total_requests > 0 && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Usage:</span>
              <span>{providerKey.total_requests} requests</span>
            </div>
          )}
        </div>
        
        <div className="mt-4 flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={handleValidate}
            disabled={isValidating}
          >
            {isValidating ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                Validating...
              </>
            ) : (
              <>
                <CheckCircle className="mr-2 h-4 w-4" />
                Validate
              </>
            )}
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => onEdit(providerKey)}
          >
            <Edit className="mr-2 h-4 w-4" />
            Edit
          </Button>
          <Button
            size="sm"
            variant="destructive"
            onClick={handleDelete}
            disabled={isDeleting}
          >
            {isDeleting ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                Deleting...
              </>
            ) : (
              <>
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}