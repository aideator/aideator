'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export type AgentMode = 'litellm' | 'claude-cli' | 'gemini-cli' | 'openai-codex';

export type ExecutionMode = 'text' | 'code';

export interface AgentModeInfo {
  mode: AgentMode;
  executionMode: ExecutionMode;
  label: string;
  description: string;
  requiresRepo: boolean;
}

export const AGENT_MODE_OPTIONS: AgentModeInfo[] = [
  {
    mode: 'litellm',
    executionMode: 'text',
    label: 'Chat',
    description: 'Multi-model text completion and conversation',
    requiresRepo: false,
  },
  {
    mode: 'claude-cli',
    executionMode: 'code',
    label: 'Claude Code',
    description: 'Code analysis and generation using Claude CLI',
    requiresRepo: true,
  },
  {
    mode: 'gemini-cli',
    executionMode: 'code',
    label: 'Gemini Code',
    description: 'Code analysis and generation using Gemini CLI',
    requiresRepo: true,
  },
  {
    mode: 'openai-codex',
    executionMode: 'code',
    label: 'OpenAI Codex',
    description: 'Code analysis and generation using OpenAI Codex',
    requiresRepo: true,
  },
];

interface AgentModeContextType {
  agentMode: AgentMode;
  setAgentMode: (mode: AgentMode) => void;
  currentModeInfo: AgentModeInfo;
  isLiteLLM: boolean;
  isCodeMode: boolean;
  requiresRepo: boolean;
}

const AgentModeContext = createContext<AgentModeContextType | undefined>(undefined);

const STORAGE_KEY = 'aideator-agent-mode';

interface AgentModeProviderProps {
  children: ReactNode;
}

export function AgentModeProvider({ children }: AgentModeProviderProps) {
  const [agentMode, setAgentModeState] = useState<AgentMode>('litellm');

  // Load from LocalStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY) as AgentMode;
      if (stored && AGENT_MODE_OPTIONS.some(option => option.mode === stored)) {
        setAgentModeState(stored);
      }
    } catch (error) {
      console.error('Error loading agent mode from LocalStorage:', error);
    }
  }, []);

  // Save to LocalStorage whenever mode changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, agentMode);
    } catch (error) {
      console.error('Error saving agent mode to LocalStorage:', error);
    }
  }, [agentMode]);

  const setAgentMode = (mode: AgentMode) => {
    setAgentModeState(mode);
  };

  const currentModeInfo = AGENT_MODE_OPTIONS.find(option => option.mode === agentMode) || AGENT_MODE_OPTIONS[0];
  const isLiteLLM = agentMode === 'litellm';
  const isCodeMode = currentModeInfo.executionMode === 'code';
  const requiresRepo = currentModeInfo.requiresRepo;

  const contextValue = {
    agentMode,
    setAgentMode,
    currentModeInfo,
    isLiteLLM,
    isCodeMode,
    requiresRepo,
  };

  return (
    <AgentModeContext.Provider value={contextValue}>
      {children}
    </AgentModeContext.Provider>
  );
}

export function useAgentMode() {
  const context = useContext(AgentModeContext);
  if (context === undefined) {
    throw new Error('useAgentMode must be used within an AgentModeProvider');
  }
  return context;
}