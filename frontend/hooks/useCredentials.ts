'use client';

import { useState, useEffect, useCallback } from 'react';
// Remove unused import

export interface ProviderCredential {
  id: string;
  provider: string;
  name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_used_at?: string;
  total_requests: number;
  total_cost_usd: number;
}

interface UseCredentialsReturn {
  credentials: ProviderCredential[];
  isLoading: boolean;
  error: string | null;
  fetchCredentials: () => Promise<void>;
  getCredentialForProvider: (provider: string) => ProviderCredential | undefined;
}

export function useCredentials(): UseCredentialsReturn {
  const [credentials, setCredentials] = useState<ProviderCredential[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCredentials = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/credentials`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch credentials');
      }

      const data = await response.json();
      setCredentials(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch credentials');
      setCredentials([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getCredentialForProvider = useCallback((provider: string): ProviderCredential | undefined => {
    return credentials.find(cred => 
      cred.provider.toLowerCase() === provider.toLowerCase() && 
      cred.is_active
    );
  }, [credentials]);

  useEffect(() => {
    fetchCredentials();
  }, [fetchCredentials]);

  return {
    credentials,
    isLoading,
    error,
    fetchCredentials,
    getCredentialForProvider,
  };
}