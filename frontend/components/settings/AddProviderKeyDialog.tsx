"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Plus, AlertCircle, ExternalLink, Eye, EyeOff } from "lucide-react";
import { cn } from "@/lib/utils";

interface AddProviderKeyDialogProps {
  onAdd: (keyData: {
    provider: string;
    api_key: string;
    name?: string;
    model_name?: string;
  }) => Promise<void>;
  trigger?: React.ReactNode;
  className?: string;
}

const PROVIDERS = [
  {
    id: "openai",
    name: "OpenAI",
    icon: "🤖",
    keyFormat: "sk-proj-...",
    description: "GPT-4, GPT-3.5 Turbo, and other OpenAI models",
    docsUrl: "https://platform.openai.com/api-keys",
    models: ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o"]
  },
  {
    id: "anthropic",
    name: "Anthropic",
    icon: "🧠",
    keyFormat: "sk-ant-...",
    description: "Claude 3 family of models",
    docsUrl: "https://console.anthropic.com/settings/keys",
    models: ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
  },
  {
    id: "google",
    name: "Google AI",
    icon: "🔍",
    keyFormat: "AIza...",
    description: "Gemini Pro and other Google AI models",
    docsUrl: "https://makersuite.google.com/app/apikey",
    models: ["gemini-pro", "gemini-pro-vision"]
  },
  {
    id: "cohere",
    name: "Cohere",
    icon: "🌟",
    keyFormat: "...",
    description: "Command and other Cohere models",
    docsUrl: "https://dashboard.cohere.com/api-keys",
    models: ["command", "command-light", "command-nightly"]
  },
  {
    id: "together",
    name: "Together AI",
    icon: "🚀",
    keyFormat: "...",
    description: "Open source models via Together AI",
    docsUrl: "https://api.together.xyz/settings/api-keys",
    models: ["mixtral-8x7b", "llama-2-70b", "code-llama-34b"]
  }
];

export function AddProviderKeyDialog({ onAdd, trigger, className }: AddProviderKeyDialogProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showKey, setShowKey] = useState(false);
  
  const [formData, setFormData] = useState({
    provider: "",
    api_key: "",
    name: "",
    model_name: ""
  });

  const selectedProvider = PROVIDERS.find(p => p.id === formData.provider);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await onAdd({
        provider: formData.provider,
        api_key: formData.api_key,
        name: formData.name || undefined,
        model_name: formData.model_name || undefined
      });
      
      // Reset form and close dialog
      setFormData({ provider: "", api_key: "", name: "", model_name: "" });
      setIsOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add provider key");
    } finally {
      setIsLoading(false);
    }
  };

  const defaultTrigger = (
    <Button className="gap-sm">
      <Plus className="h-4 w-4" />
      Add Provider Key
    </Button>
  );

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild className={className}>
        {trigger || defaultTrigger}
      </DialogTrigger>
      
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-h2">Add Provider API Key</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-lg">
          {/* Provider Selection */}
          <div className="space-y-sm">
            <Label htmlFor="provider">Provider</Label>
            <Select 
              value={formData.provider} 
              onValueChange={(value) => setFormData(prev => ({ ...prev, provider: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a provider" />
              </SelectTrigger>
              <SelectContent>
                {PROVIDERS.map((provider) => (
                  <SelectItem key={provider.id} value={provider.id}>
                    <div className="flex items-center gap-sm">
                      <span>{provider.icon}</span>
                      <span>{provider.name}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Provider Info */}
          {selectedProvider && (
            <div className="bg-neutral-paper rounded-md p-md space-y-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-sm">
                  <span className="text-body-lg">{selectedProvider.icon}</span>
                  <span className="font-medium">{selectedProvider.name}</span>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => window.open(selectedProvider.docsUrl, '_blank')}
                  className="text-body-sm"
                >
                  <ExternalLink className="h-3 w-3 mr-1" />
                  Get API Key
                </Button>
              </div>
              <p className="text-body-sm text-neutral-shadow">
                {selectedProvider.description}
              </p>
              <div className="flex flex-wrap gap-xs">
                {selectedProvider.models.slice(0, 3).map((model) => (
                  <Badge key={model} variant="secondary" className="text-caption">
                    {model}
                  </Badge>
                ))}
                {selectedProvider.models.length > 3 && (
                  <Badge variant="secondary" className="text-caption">
                    +{selectedProvider.models.length - 3} more
                  </Badge>
                )}
              </div>
              <div className="text-caption text-neutral-shadow">
                Expected format: <code className="bg-neutral-white px-1 py-0.5 rounded">
                  {selectedProvider.keyFormat}
                </code>
              </div>
            </div>
          )}

          {/* API Key Input */}
          <div className="space-y-sm">
            <Label htmlFor="api_key">API Key</Label>
            <div className="relative">
              <Input
                id="api_key"
                type={showKey ? "text" : "password"}
                value={formData.api_key}
                onChange={(e) => setFormData(prev => ({ ...prev, api_key: e.target.value }))}
                placeholder={selectedProvider?.keyFormat || "Enter your API key"}
                required
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
          </div>

          {/* Optional Name */}
          <div className="space-y-sm">
            <Label htmlFor="name">Name (Optional)</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder={selectedProvider ? `My ${selectedProvider.name} Key` : "My API Key"}
            />
          </div>

          {/* Optional Model Override */}
          <div className="space-y-sm">
            <Label htmlFor="model_name">Model Override (Optional)</Label>
            <Select 
              value={formData.model_name} 
              onValueChange={(value) => setFormData(prev => ({ ...prev, model_name: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Use for all models (recommended)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Use for all models (recommended)</SelectItem>
                {selectedProvider?.models.map((model) => (
                  <SelectItem key={model} value={model}>
                    {model}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-caption text-neutral-shadow">
              Leave empty to use this key for all {selectedProvider?.name} models. 
              Use model override for separate billing or rate limits.
            </p>
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
              onClick={() => setIsOpen(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={!formData.provider || !formData.api_key || isLoading}
              className="gap-sm"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Adding...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4" />
                  Add Key
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}