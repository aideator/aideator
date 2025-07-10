/**
 * @jest-environment jsdom
 */

import { renderHook, waitFor } from '@testing-library/react';
import { useModelInstances } from '@/hooks/useModelInstances';
import { useModelSelection } from '@/hooks/useModelSelection';
import { SessionProvider } from '@/context/SessionContext';
import { useAuth } from '@/contexts/AuthContext';
import React from 'react';

// Mock the auth context
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}));

// Mock the API client
jest.mock('@/lib/api-client', () => ({
  getModels: jest.fn(),
  getSessions: jest.fn(),
}));

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

describe('Auth-dependent Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('useModelInstances', () => {
    it('should not make API calls when auth is loading', async () => {
      // Mock auth loading state
      mockUseAuth.mockReturnValue({
        user: null,
        token: null,
        apiKey: null,
        isLoading: true,
        isAuthenticated: false,
        login: jest.fn(),
        logout: jest.fn(),
        autoLoginDev: jest.fn(),
      });

      const { result } = renderHook(() => useModelInstances());

      // Should start in loading state but not make API calls
      expect(result.current.isLoading).toBe(true);
      
      // Wait a bit to ensure no async calls are made
      await waitFor(() => {
        // Should still be loading since auth hasn't completed
        expect(result.current.isLoading).toBe(true);
      });

      // Verify no API calls were made
      const { getModels } = require('@/lib/api-client');
      expect(getModels).not.toHaveBeenCalled();
    });

    it('should make API calls only after auth completes', async () => {
      // Mock successful auth
      mockUseAuth.mockReturnValue({
        user: { id: '1', email: 'test@example.com', full_name: 'Test User' },
        token: 'mock-token',
        apiKey: 'mock-api-key',
        isLoading: false,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        autoLoginDev: jest.fn(),
      });

      // Mock API response
      const { getModels } = require('@/lib/api-client');
      getModels.mockResolvedValue([
        { id: 'gpt-4', name: 'GPT-4', provider: 'openai', capabilities: ['CHAT_COMPLETION'] },
      ]);

      const { result } = renderHook(() => useModelInstances());

      // Should eventually make API call and load data
      await waitFor(() => {
        expect(getModels).toHaveBeenCalled();
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });

    it('should use default models when not authenticated', async () => {
      // Mock unauthenticated state
      mockUseAuth.mockReturnValue({
        user: null,
        token: null,
        apiKey: null,
        isLoading: false,
        isAuthenticated: false,
        login: jest.fn(),
        logout: jest.fn(),
        autoLoginDev: jest.fn(),
      });

      const { result } = renderHook(() => useModelInstances());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Should have default instances
      expect(result.current.instances.length).toBeGreaterThan(0);
      
      // Should not have made API calls
      const { getModels } = require('@/lib/api-client');
      expect(getModels).not.toHaveBeenCalled();
    });
  });

  describe('useModelSelection', () => {
    it('should not make API calls when auth is loading', async () => {
      mockUseAuth.mockReturnValue({
        user: null,
        token: null,
        apiKey: null,
        isLoading: true,
        isAuthenticated: false,
        login: jest.fn(),
        logout: jest.fn(),
        autoLoginDev: jest.fn(),
      });

      const { result } = renderHook(() => useModelSelection());

      expect(result.current.isLoading).toBe(true);
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(true);
      });

      const { getModels } = require('@/lib/api-client');
      expect(getModels).not.toHaveBeenCalled();
    });

    it('should make API calls after auth completes', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: '1', email: 'test@example.com', full_name: 'Test User' },
        token: 'mock-token',
        apiKey: 'mock-api-key',
        isLoading: false,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        autoLoginDev: jest.fn(),
      });

      const { getModels } = require('@/lib/api-client');
      getModels.mockResolvedValue([
        { id: 'gpt-4', name: 'GPT-4', provider: 'openai', capabilities: ['CHAT_COMPLETION'] },
      ]);

      const { result } = renderHook(() => useModelSelection());

      await waitFor(() => {
        expect(getModels).toHaveBeenCalled();
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });
  });

  describe('SessionContext', () => {
    const createWrapper = () => {
      const Wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => 
        React.createElement(SessionProvider, null, children);
      return Wrapper;
    };

    it('should not make API calls when auth is loading', async () => {
      mockUseAuth.mockReturnValue({
        user: null,
        token: null,
        apiKey: null,
        isLoading: true,
        isAuthenticated: false,
        login: jest.fn(),
        logout: jest.fn(),
        autoLoginDev: jest.fn(),
      });

      renderHook(() => useModelInstances(), { wrapper: createWrapper() });

      // Wait a bit to ensure no async calls are made during loading
      await new Promise(resolve => setTimeout(resolve, 100));

      const { getSessions } = require('@/lib/api-client');
      expect(getSessions).not.toHaveBeenCalled();
    });

    it('should make API calls after auth completes', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: '1', email: 'test@example.com', full_name: 'Test User' },
        token: 'mock-token',
        apiKey: 'mock-api-key',
        isLoading: false,
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
        autoLoginDev: jest.fn(),
      });

      const { getSessions } = require('@/lib/api-client');
      getSessions.mockResolvedValue([]);

      renderHook(() => useModelInstances(), { wrapper: createWrapper() });

      await waitFor(() => {
        expect(getSessions).toHaveBeenCalled();
      });
    });
  });
});