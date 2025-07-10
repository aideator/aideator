"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { 
  AlertCircle, 
  Search, 
  Filter, 
  Key, 
  Trash2,
  Plus,
  RefreshCw,
  ExternalLink
} from "lucide-react";
import { cn } from "@/lib/utils";

import { ProviderKeyCard } from "./ProviderKeyCard";
import { AddProviderKeyDialog } from "./AddProviderKeyDialog";
import { EditProviderKeyDialog } from "./EditProviderKeyDialog";
import { useAuth } from "@/contexts/AuthContext";

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

interface ProviderKeyManagerProps {
  className?: string;
}

export function ProviderKeyManager({ className }: ProviderKeyManagerProps) {
  const { apiKey } = useAuth();
  const [keys, setKeys] = useState<ProviderKey[]>([]);
  const [filteredKeys, setFilteredKeys] = useState<ProviderKey[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterProvider, setFilterProvider] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [editingKey, setEditingKey] = useState<ProviderKey | null>(null);

  // Fetch provider keys
  const fetchKeys = async () => {
    if (!apiKey) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch("/api/v1/provider-keys", {
        headers: {
          "X-API-Key": apiKey,
        },
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch provider keys: ${response.statusText}`);
      }
      
      const data = await response.json();
      setKeys(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch provider keys");
    } finally {
      setIsLoading(false);
    }
  };

  // Filter keys based on search and filters
  useEffect(() => {
    let filtered = keys;

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(key => 
        key.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        key.provider.toLowerCase().includes(searchTerm.toLowerCase()) ||
        key.model_name?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Provider filter
    if (filterProvider !== "all") {
      filtered = filtered.filter(key => key.provider === filterProvider);
    }

    // Status filter
    if (filterStatus === "active") {
      filtered = filtered.filter(key => key.is_active);
    } else if (filterStatus === "inactive") {
      filtered = filtered.filter(key => !key.is_active);
    }

    setFilteredKeys(filtered);
  }, [keys, searchTerm, filterProvider, filterStatus]);

  // Load keys on mount
  useEffect(() => {
    fetchKeys();
  }, [apiKey]);

  // Add new provider key
  const handleAddKey = async (keyData: {
    provider: string;
    api_key: string;
    name?: string;
    model_name?: string;
  }) => {
    if (!apiKey) throw new Error("No API key available");

    const response = await fetch("/api/v1/provider-keys", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey,
      },
      body: JSON.stringify(keyData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to add provider key");
    }

    // Refresh the list
    await fetchKeys();
  };

  // Update provider key
  const handleUpdateKey = async (keyId: string, updates: {
    api_key?: string;
    name?: string;
    is_active?: boolean;
  }) => {
    if (!apiKey) throw new Error("No API key available");

    const response = await fetch(`/api/v1/provider-keys/${keyId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey,
      },
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to update provider key");
    }

    // Refresh the list
    await fetchKeys();
  };

  // Delete provider key
  const handleDeleteKey = async (keyId: string) => {
    if (!confirm("Are you sure you want to delete this provider key? This action cannot be undone.")) {
      return;
    }

    if (!apiKey) {
      setError("No API key available");
      return;
    }

    try {
      const response = await fetch(`/api/v1/provider-keys/${keyId}`, {
        method: "DELETE",
        headers: {
          "X-API-Key": apiKey,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to delete provider key");
      }

      // Refresh the list
      await fetchKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete provider key");
    }
  };

  const providers = Array.from(new Set(keys.map(key => key.provider)));
  const totalRequests = keys.reduce((sum, key) => sum + key.total_requests, 0);
  const activeKeys = keys.filter(key => key.is_active).length;

  if (!apiKey) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Please log in to manage your provider API keys.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className={cn("space-y-lg", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-h1 font-semibold">Provider API Keys</h2>
          <p className="text-body text-neutral-shadow mt-xs">
            Manage your API keys for different model providers
          </p>
        </div>
        <div className="flex items-center gap-sm">
          <Button
            variant="outline"
            onClick={fetchKeys}
            disabled={isLoading}
            className="gap-sm"
            data-testid="refresh-keys-btn"
          >
            <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
            Refresh
          </Button>
          <AddProviderKeyDialog onAdd={handleAddKey} />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-md">
        <Card>
          <CardContent className="p-md" data-testid="total-keys-stat">
            <div className="text-body-lg font-semibold">{keys.length}</div>
            <div className="text-body-sm text-neutral-shadow">Total Keys</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-md" data-testid="active-keys-stat">
            <div className="text-body-lg font-semibold">{activeKeys}</div>
            <div className="text-body-sm text-neutral-shadow">Active Keys</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-md" data-testid="total-requests-stat">
            <div className="text-body-lg font-semibold">{totalRequests.toLocaleString()}</div>
            <div className="text-body-sm text-neutral-shadow">Total Requests</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-md">
          <div className="flex flex-col sm:flex-row gap-md">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-neutral-shadow" />
              <Input
                placeholder="Search keys..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Provider Filter */}
            <Select value={filterProvider} onValueChange={setFilterProvider}>
              <SelectTrigger className="w-full sm:w-40">
                <SelectValue placeholder="All Providers" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Providers</SelectItem>
                {providers.map(provider => (
                  <SelectItem key={provider} value={provider}>
                    {provider.charAt(0).toUpperCase() + provider.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Status Filter */}
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-full sm:w-32">
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-xl">
          <div className="flex items-center gap-sm text-neutral-shadow">
            <RefreshCw className="h-5 w-5 animate-spin" />
            Loading provider keys...
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && filteredKeys.length === 0 && (
        <Card>
          <CardContent className="text-center py-xl">
            <Key className="h-12 w-12 text-neutral-shadow mx-auto mb-md" />
            <h3 className="text-h3 font-semibold mb-sm">
              {keys.length === 0 ? "No Provider Keys" : "No Matching Keys"}
            </h3>
            <p className="text-body text-neutral-shadow mb-lg max-w-md mx-auto">
              {keys.length === 0 
                ? "Add your first provider API key to start using AIdeator with your preferred models."
                : "Try adjusting your search or filters to find the keys you're looking for."
              }
            </p>
            {keys.length === 0 && (
              <AddProviderKeyDialog 
                onAdd={handleAddKey}
                trigger={
                  <Button className="gap-sm">
                    <Plus className="h-4 w-4" />
                    Add Your First Key
                  </Button>
                }
              />
            )}
          </CardContent>
        </Card>
      )}

      {/* Provider Keys Grid */}
      {!isLoading && filteredKeys.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-lg">
          {filteredKeys.map((key) => (
            <ProviderKeyCard
              key={key.id}
              providerKey={key}
              onEdit={setEditingKey}
              onDelete={handleDeleteKey}
            />
          ))}
        </div>
      )}

      {/* Edit Dialog */}
      <EditProviderKeyDialog
        providerKey={editingKey}
        isOpen={!!editingKey}
        onOpenChange={(open) => !open && setEditingKey(null)}
        onUpdate={handleUpdateKey}
      />
    </div>
  );
}