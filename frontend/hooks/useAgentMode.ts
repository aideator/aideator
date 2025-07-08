import { useState, useEffect } from 'react';

const STORAGE_KEY = 'aideator-agent-mode';

export type AgentMode = 'litellm' | 'claude-cli';

export function useAgentMode() {
  const [agentMode, setAgentModeState] = useState<AgentMode>('litellm');

  // Load from LocalStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored === 'claude-cli') {
        setAgentModeState('claude-cli');
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

  const isLiteLLM = agentMode === 'litellm';

  return {
    agentMode,
    setAgentMode,
    isLiteLLM,
  };
}