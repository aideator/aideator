"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Trash2, Edit2, Eye, EyeOff, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";

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

interface ProviderKeyCardProps {
  providerKey: ProviderKey;
  onEdit: (key: ProviderKey) => void;
  onDelete: (keyId: string) => void;
  onValidate?: (keyId: string) => void;
  className?: string;
}

const PROVIDER_INFO = {
  openai: {
    name: "OpenAI",
    color: "bg-green-500 text-white",
    icon: "🤖",
    docsUrl: "https://platform.openai.com/api-keys"
  },
  anthropic: {
    name: "Anthropic",
    color: "bg-purple-500 text-white",
    icon: "🧠",
    docsUrl: "https://console.anthropic.com/settings/keys"
  },
  google: {
    name: "Google AI",
    color: "bg-blue-500 text-white",
    icon: "🔍",
    docsUrl: "https://makersuite.google.com/app/apikey"
  },
  cohere: {
    name: "Cohere",
    color: "bg-orange-500 text-white",
    icon: "🌟",
    docsUrl: "https://dashboard.cohere.com/api-keys"
  },
  together: {
    name: "Together AI",
    color: "bg-indigo-500 text-white",
    icon: "🚀",
    docsUrl: "https://api.together.xyz/settings/api-keys"
  }
} as const;

export function ProviderKeyCard({
  providerKey,
  onEdit,
  onDelete,
  onValidate,
  className
}: ProviderKeyCardProps) {
  const [showActions, setShowActions] = useState(false);
  
  const providerInfo = PROVIDER_INFO[providerKey.provider as keyof typeof PROVIDER_INFO] || {
    name: providerKey.provider.charAt(0).toUpperCase() + providerKey.provider.slice(1),
    color: "bg-neutral-shadow text-white",
    icon: "🔑",
    docsUrl: "#"
  };

  const getValidationStatus = () => {
    if (providerKey.is_valid === true) {
      return { text: "Valid", color: "bg-semantic-success text-white" };
    } else if (providerKey.is_valid === false) {
      return { text: "Invalid", color: "bg-semantic-error text-white" };
    } else {
      return { text: "Unvalidated", color: "bg-neutral-shadow text-white" };
    }
  };

  const validationStatus = getValidationStatus();
  const lastUsed = providerKey.last_used_at ? 
    new Date(providerKey.last_used_at).toLocaleDateString() : 
    "Never";

  return (
    <Card 
      className={cn(
        "relative transition-all duration-200 hover:shadow-md",
        !providerKey.is_active && "opacity-60",
        className
      )}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <CardHeader className="pb-md">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-sm">
            <span className="text-body-lg">{providerInfo.icon}</span>
            <div>
              <CardTitle className="text-h3 font-semibold">
                {providerKey.name || `${providerInfo.name} Key`}
              </CardTitle>
              <div className="flex items-center gap-xs mt-xs">
                <Badge 
                  variant="secondary" 
                  className={cn("text-caption font-medium", providerInfo.color)}
                >
                  {providerInfo.name}
                </Badge>
                {providerKey.model_name && (
                  <Badge variant="outline" className="text-caption">
                    {providerKey.model_name}
                  </Badge>
                )}
              </div>
            </div>
          </div>
          
          {/* Actions Menu */}
          <div className={cn(
            "flex items-center gap-xs transition-opacity duration-200",
            showActions ? "opacity-100" : "opacity-0"
          )}>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onEdit(providerKey)}
              className="h-8 w-8 p-0"
            >
              <Edit2 className="h-4 w-4" />
            </Button>
            {onValidate && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onValidate(providerKey.id)}
                className="h-8 w-8 p-0"
              >
                <Eye className="h-4 w-4" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDelete(providerKey.id)}
              className="h-8 w-8 p-0 text-semantic-error hover:text-semantic-error"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="space-y-md">
          {/* Key Info */}
          <div className="flex items-center justify-between">
            <span className="text-body-sm text-neutral-shadow">API Key</span>
            <div className="flex items-center gap-xs">
              <code className="text-body-sm bg-neutral-fog px-xs py-1 rounded">
                {providerKey.key_hint}
              </code>
              <Badge 
                variant="secondary"
                className={cn("text-caption", validationStatus.color)}
              >
                {validationStatus.text}
              </Badge>
            </div>
          </div>

          {/* Usage Stats */}
          <div className="grid grid-cols-2 gap-md text-center">
            <div>
              <div className="text-body-lg font-semibold text-neutral-charcoal">
                {providerKey.total_requests.toLocaleString()}
              </div>
              <div className="text-caption text-neutral-shadow">Total Requests</div>
            </div>
            <div>
              <div className="text-body-lg font-semibold text-neutral-charcoal">
                {lastUsed}
              </div>
              <div className="text-caption text-neutral-shadow">Last Used</div>
            </div>
          </div>

          {/* Status and Actions */}
          <div className="flex items-center justify-between pt-sm border-t border-neutral-fog">
            <div className="flex items-center gap-xs">
              <div className={cn(
                "w-2 h-2 rounded-full",
                providerKey.is_active ? "bg-semantic-success" : "bg-neutral-shadow"
              )} />
              <span className="text-body-sm text-neutral-shadow">
                {providerKey.is_active ? "Active" : "Inactive"}
              </span>
            </div>
            
            <Button
              variant="ghost"
              size="sm"
              className="text-body-sm text-neutral-shadow hover:text-ai-primary p-0 h-auto"
              onClick={() => window.open(providerInfo.docsUrl, '_blank')}
            >
              <ExternalLink className="h-3 w-3 mr-1" />
              Docs
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}