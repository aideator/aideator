'use client';

import { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Key, Shield, AlertCircle, CheckCircle, Eye, EyeOff } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';

// Types
interface ProviderCredential {
  id: string;
  provider: string;
  name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_used_at?: string;
  total_requests: number;
  total_cost_usd?: number;
}

interface ProviderSummary {
  provider: string;
  display_name: string;
  description: string;
  requires_api_key: boolean;
  model_count: number;
  user_has_credentials: boolean;
}

interface CredentialManagerProps {
  onCredentialChange?: () => void;
}

const providerColors = {
  openai: 'bg-emerald-500',
  anthropic: 'bg-orange-500',
  gemini: 'bg-blue-500',
  vertex_ai: 'bg-blue-600',
  mistral: 'bg-purple-500',
  cohere: 'bg-indigo-500',
  bedrock: 'bg-amber-500',
  azure: 'bg-cyan-500',
  huggingface: 'bg-yellow-500',
  groq: 'bg-red-500',
  perplexity: 'bg-pink-500',
  deepseek: 'bg-gray-500',
  together: 'bg-green-500',
  ollama: 'bg-slate-500',
};

const providerFieldConfigs = {
  openai: [
    { name: 'api_key', label: 'API Key', type: 'password', required: true, placeholder: 'sk-...' }
  ],
  anthropic: [
    { name: 'api_key', label: 'API Key', type: 'password', required: true, placeholder: 'sk-ant-...' }
  ],
  gemini: [
    { name: 'api_key', label: 'API Key', type: 'password', required: true, placeholder: 'AI...' }
  ],
  vertex_ai: [
    { name: 'project_id', label: 'Project ID', type: 'text', required: true, placeholder: 'my-project-id' },
    { name: 'service_account_key', label: 'Service Account Key (JSON)', type: 'textarea', required: true, placeholder: '{ "type": "service_account", ... }' }
  ],
  mistral: [
    { name: 'api_key', label: 'API Key', type: 'password', required: true, placeholder: 'mistral-...' }
  ],
  cohere: [
    { name: 'api_key', label: 'API Key', type: 'password', required: true, placeholder: 'cohere-...' }
  ],
  bedrock: [
    { name: 'aws_access_key_id', label: 'AWS Access Key ID', type: 'text', required: true, placeholder: 'AKIA...' },
    { name: 'aws_secret_access_key', label: 'AWS Secret Access Key', type: 'password', required: true, placeholder: 'secret-key' },
    { name: 'region', label: 'AWS Region', type: 'text', required: true, placeholder: 'us-east-1' }
  ],
  azure: [
    { name: 'api_key', label: 'API Key', type: 'password', required: true, placeholder: 'azure-api-key' },
    { name: 'api_base', label: 'API Base URL', type: 'text', required: true, placeholder: 'https://your-resource.openai.azure.com' },
    { name: 'api_version', label: 'API Version', type: 'text', required: true, placeholder: '2023-07-01-preview' }
  ],
  groq: [
    { name: 'api_key', label: 'API Key', type: 'password', required: true, placeholder: 'gsk_...' }
  ],
  deepseek: [
    { name: 'api_key', label: 'API Key', type: 'password', required: true, placeholder: 'deepseek-...' }
  ],
  together: [
    { name: 'api_key', label: 'API Key', type: 'password', required: true, placeholder: 'together-...' }
  ],
  perplexity: [
    { name: 'api_key', label: 'API Key', type: 'password', required: true, placeholder: 'pplx-...' }
  ],
};

export default function CredentialManager({ onCredentialChange }: CredentialManagerProps) {
  const [credentials, setCredentials] = useState<ProviderCredential[]>([]);
  const [providers, setProviders] = useState<ProviderSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Modal states
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingCredential, setEditingCredential] = useState<ProviderCredential | null>(null);
  
  // Form states
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [credentialName, setCredentialName] = useState('');
  const [credentialFields, setCredentialFields] = useState<Record<string, string>>({});
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});
  const [submitting, setSubmitting] = useState(false);

  // Load credentials and providers
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load credentials
      const credentialsResponse = await fetch('/api/v1/credentials');
      if (!credentialsResponse.ok) {
        throw new Error('Failed to load credentials');
      }
      const credentialsData = await credentialsResponse.json();
      setCredentials(credentialsData);
      
      // Load providers
      const providersResponse = await fetch('/api/v1/models/providers');
      if (!providersResponse.ok) {
        throw new Error('Failed to load providers');
      }
      const providersData = await providersResponse.json();
      setProviders(providersData);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const openAddModal = () => {
    setSelectedProvider('');
    setCredentialName('');
    setCredentialFields({});
    setShowSecrets({});
    setIsAddModalOpen(true);
  };

  const openEditModal = (credential: ProviderCredential) => {
    setEditingCredential(credential);
    setSelectedProvider(credential.provider);
    setCredentialName(credential.name);
    setCredentialFields({});
    setShowSecrets({});
    setIsEditModalOpen(true);
  };

  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider);
    setCredentialName('');
    setCredentialFields({});
    setShowSecrets({});
  };

  const handleFieldChange = (fieldName: string, value: string) => {
    setCredentialFields(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const toggleSecretVisibility = (fieldName: string) => {
    setShowSecrets(prev => ({
      ...prev,
      [fieldName]: !prev[fieldName]
    }));
  };

  const validateForm = () => {
    if (!selectedProvider || !credentialName) {
      return false;
    }
    
    const config = providerFieldConfigs[selectedProvider as keyof typeof providerFieldConfigs];
    if (config) {
      const requiredFields = config.filter(field => field.required);
      const hasAllRequired = requiredFields.every(field => credentialFields[field.name]);
      return hasAllRequired;
    }
    
    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }
    
    try {
      setSubmitting(true);
      
      const payload = {
        provider: selectedProvider,
        name: credentialName,
        credentials: credentialFields
      };
      
      const response = await fetch('/api/v1/credentials', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save credentials');
      }
      
      // Reload data
      await loadData();
      
      // Close modal
      setIsAddModalOpen(false);
      
      // Notify parent
      onCredentialChange?.();
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save credentials');
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdate = async () => {
    if (!editingCredential || !validateForm()) {
      return;
    }
    
    try {
      setSubmitting(true);
      
      const payload = {
        name: credentialName,
        credentials: Object.keys(credentialFields).length > 0 ? credentialFields : undefined
      };
      
      const response = await fetch(`/api/v1/credentials/${editingCredential.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update credentials');
      }
      
      // Reload data
      await loadData();
      
      // Close modal
      setIsEditModalOpen(false);
      setEditingCredential(null);
      
      // Notify parent
      onCredentialChange?.();
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update credentials');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (credentialId: string) => {
    if (!confirm('Are you sure you want to delete this credential?')) {
      return;
    }
    
    try {
      const response = await fetch(`/api/v1/credentials/${credentialId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete credential');
      }
      
      // Reload data
      await loadData();
      
      // Notify parent
      onCredentialChange?.();
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete credential');
    }
  };

  const getProviderInfo = (providerId: string) => {
    return providers.find(p => p.provider === providerId);
  };

  const renderCredentialForm = () => {
    const config = providerFieldConfigs[selectedProvider as keyof typeof providerFieldConfigs];
    if (!config) return null;

    return (
      <div className="space-y-4">
        <div>
          <Label htmlFor="credential-name">Credential Name</Label>
          <Input
            id="credential-name"
            value={credentialName}
            onChange={(e) => setCredentialName(e.target.value)}
            placeholder="e.g., My Production API Key"
          />
        </div>
        
        {config.map(field => (
          <div key={field.name}>
            <Label htmlFor={field.name}>
              {field.label}
              {field.required && <span className="text-semantic-error ml-1">*</span>}
            </Label>
            
            {field.type === 'textarea' ? (
              <Textarea
                id={field.name}
                value={credentialFields[field.name] || ''}
                onChange={(e) => handleFieldChange(field.name, e.target.value)}
                placeholder={field.placeholder}
                rows={4}
              />
            ) : (
              <div className="relative">
                <Input
                  id={field.name}
                  type={field.type === 'password' && !showSecrets[field.name] ? 'password' : 'text'}
                  value={credentialFields[field.name] || ''}
                  onChange={(e) => handleFieldChange(field.name, e.target.value)}
                  placeholder={field.placeholder}
                />
                {field.type === 'password' && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0"
                    onClick={() => toggleSecretVisibility(field.name)}
                  >
                    {showSecrets[field.name] ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-ai-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-semantic-error/10 border border-semantic-error rounded-md p-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-semantic-error" />
            <span className="text-semantic-error">{error}</span>
          </div>
        </div>
      )}
      
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              API Credentials
            </CardTitle>
            <Button onClick={openAddModal}>
              <Plus className="h-4 w-4 mr-2" />
              Add Credential
            </Button>
          </div>
        </CardHeader>
        
        <CardContent>
          {credentials.length === 0 ? (
            <div className="text-center py-8 text-neutral-shadow">
              <Key className="h-12 w-12 mx-auto mb-4 text-neutral-fog" />
              <p>No API credentials configured yet.</p>
              <p className="text-sm">Add credentials to start using models from different providers.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {credentials.map(credential => {
                const providerInfo = getProviderInfo(credential.provider);
                
                return (
                  <div key={credential.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={cn(
                          "w-4 h-4 rounded-full",
                          providerColors[credential.provider as keyof typeof providerColors] || 'bg-gray-500'
                        )}></div>
                        <div>
                          <h4 className="font-medium">{credential.name}</h4>
                          <p className="text-sm text-neutral-shadow">
                            {providerInfo?.display_name || credential.provider}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Badge variant={credential.is_active ? "default" : "secondary"}>
                          {credential.is_active ? (
                            <>
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Active
                            </>
                          ) : (
                            'Inactive'
                          )}
                        </Badge>
                        
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openEditModal(credential)}
                          className="h-8 w-8 p-0"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(credential.id)}
                          className="h-8 w-8 p-0 text-semantic-error hover:bg-semantic-error/10"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    
                    {credential.total_requests > 0 && (
                      <div className="mt-2 text-sm text-neutral-shadow">
                        <span>{credential.total_requests} requests</span>
                        {credential.total_cost_usd && (
                          <span className="ml-4">${credential.total_cost_usd.toFixed(2)} total cost</span>
                        )}
                        {credential.last_used_at && (
                          <span className="ml-4">
                            Last used: {new Date(credential.last_used_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add Credential Modal */}
      <Dialog open={isAddModalOpen} onOpenChange={setIsAddModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Add API Credential</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label htmlFor="provider-select">Provider</Label>
              <Select value={selectedProvider} onValueChange={handleProviderChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a provider" />
                </SelectTrigger>
                <SelectContent>
                  {providers
                    .filter(p => p.requires_api_key)
                    .map(provider => (
                      <SelectItem key={provider.provider} value={provider.provider}>
                        <div className="flex items-center gap-2">
                          <div className={cn(
                            "w-3 h-3 rounded-full",
                            providerColors[provider.provider as keyof typeof providerColors] || 'bg-gray-500'
                          )}></div>
                          {provider.display_name}
                        </div>
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
            
            {selectedProvider && renderCredentialForm()}
            
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setIsAddModalOpen(false)}>
                Cancel
              </Button>
              <Button 
                onClick={handleSubmit} 
                disabled={!validateForm() || submitting}
              >
                {submitting ? 'Saving...' : 'Save Credential'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Credential Modal */}
      <Dialog open={isEditModalOpen} onOpenChange={setIsEditModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Edit API Credential</DialogTitle>
          </DialogHeader>
          
          {editingCredential && (
            <div className="space-y-4">
              <div>
                <Label>Provider</Label>
                <div className="flex items-center gap-2 p-2 bg-neutral-fog rounded-md">
                  <div className={cn(
                    "w-3 h-3 rounded-full",
                    providerColors[editingCredential.provider as keyof typeof providerColors] || 'bg-gray-500'
                  )}></div>
                  {getProviderInfo(editingCredential.provider)?.display_name || editingCredential.provider}
                </div>
              </div>
              
              <div>
                <Label htmlFor="edit-credential-name">Credential Name</Label>
                <Input
                  id="edit-credential-name"
                  value={credentialName}
                  onChange={(e) => setCredentialName(e.target.value)}
                  placeholder="e.g., My Production API Key"
                />
              </div>
              
              <div className="space-y-3">
                <Label>Update Credentials (leave empty to keep existing)</Label>
                {renderCredentialForm()}
              </div>
              
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setIsEditModalOpen(false)}>
                  Cancel
                </Button>
                <Button 
                  onClick={handleUpdate} 
                  disabled={!credentialName || submitting}
                >
                  {submitting ? 'Updating...' : 'Update Credential'}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}