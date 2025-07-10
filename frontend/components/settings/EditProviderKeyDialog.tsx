"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, Save, Eye, EyeOff } from "lucide-react";

interface ProviderKey {
  id: string;
  provider: string;
  model_name?: string;
  name?: string;
  key_hint: string;
  is_active: boolean;
  is_valid?: boolean;
  last_validated_at?: string;
  last_used_at?: string;
  total_requests: number;
  created_at: string;
}

interface EditProviderKeyDialogProps {
  providerKey: ProviderKey | null;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdate: (keyId: string, updates: {
    api_key?: string;
    name?: string;
    is_active?: boolean;
  }) => Promise<void>;
}

export function EditProviderKeyDialog({
  providerKey,
  isOpen,
  onOpenChange,
  onUpdate
}: EditProviderKeyDialogProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showKey, setShowKey] = useState(false);
  
  const [formData, setFormData] = useState({
    name: "",
    api_key: "",
    is_active: true
  });

  // Update form data when provider key changes
  useEffect(() => {
    if (providerKey) {
      setFormData({
        name: providerKey.name || "",
        api_key: "",
        is_active: providerKey.is_active
      });
      setError(null);
      setShowKey(false);
    }
  }, [providerKey]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!providerKey) return;
    
    setError(null);
    setIsLoading(true);

    try {
      const updates: any = {};
      
      // Only include changed fields
      if (formData.name !== (providerKey.name || "")) {
        updates.name = formData.name;
      }
      
      if (formData.api_key.trim()) {
        updates.api_key = formData.api_key;
      }
      
      if (formData.is_active !== providerKey.is_active) {
        updates.is_active = formData.is_active;
      }

      await onUpdate(providerKey.id, updates);
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update provider key");
    } finally {
      setIsLoading(false);
    }
  };

  if (!providerKey) return null;

  const providerName = providerKey.provider.charAt(0).toUpperCase() + providerKey.provider.slice(1);

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="text-h2">Edit {providerName} Key</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-lg">
          {/* Provider Info (Read-only) */}
          <div className="bg-neutral-paper rounded-md p-md space-y-sm">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">{providerName}</div>
                {providerKey.model_name && (
                  <div className="text-body-sm text-neutral-shadow">
                    Model: {providerKey.model_name}
                  </div>
                )}
              </div>
              <div className="text-right">
                <div className="text-body-sm font-mono">{providerKey.key_hint}</div>
                <div className="text-caption text-neutral-shadow">
                  Created {new Date(providerKey.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          </div>

          {/* Name */}
          <div className="space-y-sm">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder={`My ${providerName} Key`}
            />
          </div>

          {/* API Key (Optional Update) */}
          <div className="space-y-sm">
            <Label htmlFor="api_key">New API Key (Optional)</Label>
            <div className="relative">
              <Input
                id="api_key"
                type={showKey ? "text" : "password"}
                value={formData.api_key}
                onChange={(e) => setFormData(prev => ({ ...prev, api_key: e.target.value }))}
                placeholder="Leave empty to keep current key"
                className="pr-10"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                onClick={() => setShowKey(!showKey)}
              >
                {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
            <p className="text-caption text-neutral-shadow">
              Only enter a new key if you want to replace the existing one.
            </p>
          </div>

          {/* Active Status */}
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="is_active">Active</Label>
              <p className="text-caption text-neutral-shadow">
                Inactive keys won't be used for model requests
              </p>
            </div>
            <Switch
              id="is_active"
              checked={formData.is_active}
              onCheckedChange={(checked) => setFormData(prev => ({ ...prev, is_active: checked }))}
            />
          </div>

          {/* Usage Stats (Read-only) */}
          <div className="bg-neutral-paper rounded-md p-md">
            <div className="text-body-sm font-medium mb-sm">Usage Statistics</div>
            <div className="grid grid-cols-2 gap-md text-center">
              <div>
                <div className="text-body-lg font-semibold">
                  {providerKey.total_requests.toLocaleString()}
                </div>
                <div className="text-caption text-neutral-shadow">Total Requests</div>
              </div>
              <div>
                <div className="text-body-lg font-semibold">
                  {providerKey.last_used_at ? 
                    new Date(providerKey.last_used_at).toLocaleDateString() : 
                    "Never"
                  }
                </div>
                <div className="text-caption text-neutral-shadow">Last Used</div>
              </div>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-sm">
            <Button 
              type="button" 
              variant="outline" 
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={isLoading}
              className="gap-sm"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  Save Changes
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}