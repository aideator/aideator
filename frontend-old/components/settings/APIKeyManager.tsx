import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Eye, EyeOff, Copy, Shield, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface APIKey {
  id: string;
  name: string;
  description?: string;
  key: string;
  provider: 'openai' | 'anthropic' | 'google' | 'custom';
  createdAt: string;
  lastUsed?: string;
  isActive: boolean;
  usageCount: number;
  expiresAt?: string;
}

interface APIKeyManagerProps {
  onKeysChange?: (keys: APIKey[]) => void;
  className?: string;
}

// Mock data - in real implementation, this would come from API
const mockAPIKeys: APIKey[] = [
  {
    id: '1',
    name: 'OpenAI Production',
    description: 'Main OpenAI API key for production use',
    key: 'sk-proj-1234567890abcdef...',
    provider: 'openai',
    createdAt: '2024-01-15T10:30:00Z',
    lastUsed: '2024-01-20T14:22:00Z',
    isActive: true,
    usageCount: 1247,
  },
  {
    id: '2',
    name: 'Anthropic Development',
    description: 'Claude API key for development testing',
    key: 'sk-ant-api01-1234567890abcdef...',
    provider: 'anthropic',
    createdAt: '2024-01-10T09:15:00Z',
    lastUsed: '2024-01-19T16:45:00Z',
    isActive: true,
    usageCount: 342,
  },
  {
    id: '3',
    name: 'Google AI Studio',
    description: 'Gemini API key for testing',
    key: 'AIzaSyD1234567890abcdef...',
    provider: 'google',
    createdAt: '2024-01-08T11:20:00Z',
    lastUsed: '2024-01-18T13:10:00Z',
    isActive: false,
    usageCount: 89,
  },
];

export function APIKeyManager({ onKeysChange, className }: APIKeyManagerProps) {
  const [apiKeys, setApiKeys] = useState<APIKey[]>(mockAPIKeys);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [editingKey, setEditingKey] = useState<APIKey | null>(null);
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set());
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Form state for adding/editing keys
  const [formData, setFormData] = useState<{
    name: string;
    description: string;
    key: string;
    provider: 'openai' | 'anthropic' | 'google' | 'custom';
  }>({
    name: '',
    description: '',
    key: '',
    provider: 'openai',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    onKeysChange?.(apiKeys);
  }, [apiKeys, onKeysChange]);

  const handleAddKey = () => {
    if (validateForm()) {
      const newKey: APIKey = {
        id: Date.now().toString(),
        name: formData.name,
        description: formData.description,
        key: formData.key,
        provider: formData.provider,
        createdAt: new Date().toISOString(),
        isActive: true,
        usageCount: 0,
      };

      setApiKeys(prev => [...prev, newKey]);
      setIsAddDialogOpen(false);
      resetForm();
    }
  };

  const handleEditKey = () => {
    if (editingKey && validateForm()) {
      setApiKeys(prev => prev.map(key => 
        key.id === editingKey.id
          ? { ...key, ...formData }
          : key
      ));
      setEditingKey(null);
      resetForm();
    }
  };

  const handleDeleteKey = (keyId: string) => {
    setApiKeys(prev => prev.filter(key => key.id !== keyId));
  };

  const handleToggleActive = (keyId: string) => {
    setApiKeys(prev => prev.map(key => 
      key.id === keyId
        ? { ...key, isActive: !key.isActive }
        : key
    ));
  };

  const handleCopyKey = async (keyId: string, keyValue: string) => {
    try {
      await navigator.clipboard.writeText(keyValue);
      setCopiedKey(keyId);
      setTimeout(() => setCopiedKey(null), 2000);
    } catch (error) {
      console.error('Failed to copy key:', error);
    }
  };

  const toggleKeyVisibility = (keyId: string) => {
    setVisibleKeys(prev => {
      const newSet = new Set(prev);
      if (newSet.has(keyId)) {
        newSet.delete(keyId);
      } else {
        newSet.add(keyId);
      }
      return newSet;
    });
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.key.trim()) {
      newErrors.key = 'API key is required';
    } else if (!validateKeyFormat(formData.key, formData.provider)) {
      newErrors.key = 'Invalid key format for selected provider';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateKeyFormat = (key: string, provider: string): boolean => {
    switch (provider) {
      case 'openai':
        return key.startsWith('sk-') || key.startsWith('sk-proj-');
      case 'anthropic':
        return key.startsWith('sk-ant-');
      case 'google':
        return key.startsWith('AIzaSy');
      default:
        return key.length > 0;
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      key: '',
      provider: 'openai',
    });
    setErrors({});
  };

  const openEditDialog = (key: APIKey) => {
    setFormData({
      name: key.name,
      description: key.description || '',
      key: key.key,
      provider: key.provider,
    });
    setEditingKey(key);
  };

  const maskKey = (key: string): string => {
    if (key.length <= 8) return key;
    return key.substring(0, 8) + '...' + key.substring(key.length - 4);
  };

  const getProviderIcon = (provider: string) => {
    switch (provider) {
      case 'openai': return '🤖';
      case 'anthropic': return '🧠';
      case 'google': return '🔍';
      default: return '🔑';
    }
  };

  const getProviderColor = (provider: string) => {
    switch (provider) {
      case 'openai': return 'bg-green-100 text-green-800';
      case 'anthropic': return 'bg-blue-100 text-blue-800';
      case 'google': return 'bg-amber-100 text-amber-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-h2 font-bold text-neutral-charcoal">API Key Management</h2>
          <p className="text-body-sm text-neutral-shadow mt-1">
            Manage your API keys for different model providers
          </p>
        </div>
        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-ai-primary text-white hover:bg-ai-primary/90">
              <Plus className="w-4 h-4 mr-2" />
              Add API Key
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add New API Key</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="name">Name *</Label>
                <Input
                  id="name"
                  placeholder="e.g., OpenAI Production"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className={errors.name ? 'border-semantic-error' : ''}
                />
                {errors.name && (
                  <p className="text-semantic-error text-caption mt-1">{errors.name}</p>
                )}
              </div>

              <div>
                <Label htmlFor="provider">Provider</Label>
                <Select value={formData.provider} onValueChange={(value: any) => setFormData(prev => ({ ...prev, provider: value }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="openai">OpenAI</SelectItem>
                    <SelectItem value="anthropic">Anthropic</SelectItem>
                    <SelectItem value="google">Google AI Studio</SelectItem>
                    <SelectItem value="custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="key">API Key *</Label>
                <Input
                  id="key"
                  type="password"
                  placeholder="sk-..."
                  value={formData.key}
                  onChange={(e) => setFormData(prev => ({ ...prev, key: e.target.value }))}
                  className={errors.key ? 'border-semantic-error' : ''}
                />
                {errors.key && (
                  <p className="text-semantic-error text-caption mt-1">{errors.key}</p>
                )}
              </div>

              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Optional description..."
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  rows={3}
                />
              </div>

              <div className="flex items-center gap-2 p-3 bg-ai-primary/10 rounded-lg">
                <Shield className="w-4 h-4 text-ai-primary" />
                <span className="text-body-sm text-ai-primary">
                  API keys are encrypted and stored securely
                </span>
              </div>

              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleAddKey} className="bg-ai-primary text-white hover:bg-ai-primary/90">
                  Add Key
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* API Keys List */}
      <div className="space-y-4">
        {apiKeys.map(key => (
          <Card key={key.id} className="bg-neutral-paper border-neutral-fog">
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-body font-semibold text-neutral-charcoal">
                      {key.name}
                    </span>
                    <Badge className={`${getProviderColor(key.provider)} text-xs`}>
                      {getProviderIcon(key.provider)} {key.provider}
                    </Badge>
                    <Badge variant={key.isActive ? "default" : "secondary"} className="text-xs">
                      {key.isActive ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                  
                  {key.description && (
                    <p className="text-body-sm text-neutral-shadow mb-3">
                      {key.description}
                    </p>
                  )}
                  
                  <div className="flex items-center gap-4 mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-body-sm text-neutral-shadow">Key:</span>
                      <code className="text-body-sm font-mono bg-neutral-fog px-2 py-1 rounded">
                        {visibleKeys.has(key.id) ? key.key : maskKey(key.key)}
                      </code>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleKeyVisibility(key.id)}
                        className="h-auto p-1"
                      >
                        {visibleKeys.has(key.id) ? (
                          <EyeOff className="w-4 h-4" />
                        ) : (
                          <Eye className="w-4 h-4" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCopyKey(key.id, key.key)}
                        className="h-auto p-1"
                      >
                        {copiedKey === key.id ? (
                          <CheckCircle2 className="w-4 h-4 text-semantic-success" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-6 text-body-sm text-neutral-shadow">
                    <span>Created: {new Date(key.createdAt).toLocaleDateString()}</span>
                    {key.lastUsed && (
                      <span>Last used: {new Date(key.lastUsed).toLocaleDateString()}</span>
                    )}
                    <span>Usage: {key.usageCount} requests</span>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => openEditDialog(key)}
                  >
                    <Edit2 className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleToggleActive(key.id)}
                    className={key.isActive ? 'text-semantic-warning' : 'text-semantic-success'}
                  >
                    {key.isActive ? 'Deactivate' : 'Activate'}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteKey(key.id)}
                    className="text-semantic-error hover:text-semantic-error"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Edit Dialog */}
      {editingKey && (
        <Dialog open={!!editingKey} onOpenChange={() => setEditingKey(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Edit API Key</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="edit-name">Name *</Label>
                <Input
                  id="edit-name"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className={errors.name ? 'border-semantic-error' : ''}
                />
                {errors.name && (
                  <p className="text-semantic-error text-caption mt-1">{errors.name}</p>
                )}
              </div>

              <div>
                <Label htmlFor="edit-provider">Provider</Label>
                <Select value={formData.provider} onValueChange={(value: any) => setFormData(prev => ({ ...prev, provider: value }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="openai">OpenAI</SelectItem>
                    <SelectItem value="anthropic">Anthropic</SelectItem>
                    <SelectItem value="google">Google AI Studio</SelectItem>
                    <SelectItem value="custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="edit-key">API Key *</Label>
                <Input
                  id="edit-key"
                  type="password"
                  value={formData.key}
                  onChange={(e) => setFormData(prev => ({ ...prev, key: e.target.value }))}
                  className={errors.key ? 'border-semantic-error' : ''}
                />
                {errors.key && (
                  <p className="text-semantic-error text-caption mt-1">{errors.key}</p>
                )}
              </div>

              <div>
                <Label htmlFor="edit-description">Description</Label>
                <Textarea
                  id="edit-description"
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  rows={3}
                />
              </div>

              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setEditingKey(null)}>
                  Cancel
                </Button>
                <Button onClick={handleEditKey} className="bg-ai-primary text-white hover:bg-ai-primary/90">
                  Save Changes
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Empty State */}
      {apiKeys.length === 0 && (
        <Card className="bg-neutral-paper border-neutral-fog">
          <CardContent className="p-12 text-center">
            <Shield className="w-12 h-12 text-neutral-shadow mx-auto mb-4" />
            <h3 className="text-h3 font-semibold text-neutral-charcoal mb-2">No API Keys</h3>
            <p className="text-body-sm text-neutral-shadow mb-6">
              Add your first API key to start using different model providers
            </p>
            <Button 
              onClick={() => setIsAddDialogOpen(true)}
              className="bg-ai-primary text-white hover:bg-ai-primary/90"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add API Key
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}