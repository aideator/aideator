import { useState, useCallback, useEffect } from 'react';
import { useSessionManager } from './useSessionManager';
import { useMultiModelStream } from './useMultiModelStream';
import { type CreatePromptRequest, type Session } from '@/lib/api-client';

export interface AideatorIntegrationState {
  // Session state
  sessions: Session[];
  currentSession: any;
  sessionLoading: boolean;
  sessionError: string | null;
  
  // Streaming state
  promptId: string | null;
  models: string[];
  modelResponses: Map<string, any>;
  isStreaming: boolean;
  streamingError: string | null;
  connectionState: 'disconnected' | 'connecting' | 'connected' | 'error';
  selectedModelId: string | null;
  
  // Overall state
  isInitialized: boolean;
}

export interface AideatorIntegrationHook extends AideatorIntegrationState {
  // Session management
  createNewSession: (title?: string) => Promise<Session>;
  switchToSession: (sessionId: string) => Promise<void>;
  updateSessionTitle: (sessionId: string, title: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  
  // Multi-model comparison
  startComparison: (prompt: string, models: string[]) => Promise<void>;
  stopComparison: () => void;
  clearResults: () => void;
  selectModel: (modelId: string, feedback?: string) => Promise<void>;
  
  // Stream control
  pauseModel: (modelId: string) => void;
  resumeModel: (modelId: string) => void;
  pauseAll: () => void;
  resumeAll: () => void;
  
  // Utility
  initialize: () => Promise<void>;
  reset: () => void;
}

export function useAideatorIntegration(): AideatorIntegrationHook {
  const [isInitialized, setIsInitialized] = useState(false);
  
  // Use session manager
  const sessionManager = useSessionManager();
  
  // Use multi-model streaming
  const multiModelStream = useMultiModelStream();
  
  // Initialize the integration
  const initialize = useCallback(async () => {
    try {
      await sessionManager.loadSessions();
      setIsInitialized(true);
    } catch (error) {
      console.error('Failed to initialize Aideator integration:', error);
    }
  }, [sessionManager]);
  
  // Initialize on mount
  useEffect(() => {
    initialize();
  }, [initialize]);
  
  // Enhanced startComparison that handles session context
  const startComparison = useCallback(async (prompt: string, models: string[]) => {
    try {
      let sessionId = sessionManager.currentSession?.id;
      
      // Create new session if none exists
      if (!sessionId) {
        const newSession = await sessionManager.createNewSession();
        sessionId = newSession.id;
        await sessionManager.switchToSession(sessionId);
      }
      
      // Start multi-model comparison
      const request: CreatePromptRequest = {
        prompt,
        models,
        session_id: sessionId
      };
      
      await multiModelStream.startComparison(request);
      
    } catch (error) {
      console.error('Failed to start comparison:', error);
      throw error;
    }
  }, [sessionManager, multiModelStream]);
  
  // Enhanced selectModel that refreshes session
  const selectModel = useCallback(async (modelId: string, feedback?: string) => {
    try {
      await multiModelStream.selectModel(modelId, feedback);
      
      // Refresh current session to get updated data
      if (sessionManager.currentSession) {
        await sessionManager.refreshCurrentSession();
      }
      
    } catch (error) {
      console.error('Failed to select model:', error);
      throw error;
    }
  }, [multiModelStream, sessionManager]);
  
  // Enhanced session switching that clears streaming state
  const switchToSession = useCallback(async (sessionId: string) => {
    // Stop any ongoing streaming
    multiModelStream.stopComparison();
    multiModelStream.clearResults();
    
    // Switch to session
    await sessionManager.switchToSession(sessionId);
  }, [sessionManager, multiModelStream]);
  
  // Enhanced session deletion
  const deleteSession = useCallback(async (sessionId: string) => {
    // If deleting current session, clear streaming state
    if (sessionManager.currentSession?.id === sessionId) {
      multiModelStream.stopComparison();
      multiModelStream.clearResults();
    }
    
    await sessionManager.deleteSession(sessionId);
  }, [sessionManager, multiModelStream]);
  
  // Reset everything
  const reset = useCallback(() => {
    multiModelStream.stopComparison();
    multiModelStream.clearResults();
    sessionManager.clearCurrentSession();
    setIsInitialized(false);
  }, [multiModelStream, sessionManager]);
  
  return {
    // Session state
    sessions: sessionManager.sessions,
    currentSession: sessionManager.currentSession,
    sessionLoading: sessionManager.isLoading,
    sessionError: sessionManager.error,
    
    // Streaming state
    promptId: multiModelStream.promptId,
    models: multiModelStream.models,
    modelResponses: multiModelStream.modelResponses,
    isStreaming: multiModelStream.isStreaming,
    streamingError: multiModelStream.error,
    connectionState: multiModelStream.connectionState,
    selectedModelId: multiModelStream.selectedModelId,
    
    // Overall state
    isInitialized,
    
    // Session management
    createNewSession: sessionManager.createNewSession,
    switchToSession,
    updateSessionTitle: sessionManager.updateSessionTitle,
    deleteSession,
    
    // Multi-model comparison
    startComparison,
    stopComparison: multiModelStream.stopComparison,
    clearResults: multiModelStream.clearResults,
    selectModel,
    
    // Stream control
    pauseModel: multiModelStream.pauseModel,
    resumeModel: multiModelStream.resumeModel,
    pauseAll: multiModelStream.pauseAll,
    resumeAll: multiModelStream.resumeAll,
    
    // Utility
    initialize,
    reset,
  };
}