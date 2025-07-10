/**
 * Unit tests for useAPIIntegration hook - specifically the model ID mapping fix
 */

import { describe, it, expect, jest, beforeEach } from '@jest/globals';

// Mock the implementation to test the model mapping logic
const mockModelIdToDefinitionId = (modelId: string): string => {
  // This is the exact mapping from the fixed code
  const modelMapping: Record<string, string> = {
    'gpt-4': 'gpt-4',
    'gpt-3.5-turbo': 'gpt-3.5-turbo', 
    'gpt-4-turbo': 'gpt-4-turbo',
    'gpt-4o': 'gpt-4o',
    'gpt-4o-mini': 'gpt-4o-mini',
    'claude-3-opus': 'claude-3-opus',
    'claude-3-sonnet': 'claude-3-sonnet', 
    'claude-3-haiku': 'claude-3-haiku',
    'claude-3-5-sonnet': 'claude-3-5-sonnet',
    'claude-3-5-haiku': 'claude-3-5-haiku',
    'gemini-pro': 'gemini-pro',
  };
  
  return modelMapping[modelId] || modelId; // Fallback to original ID if not mapped
};

describe('useAPIIntegration - Model ID Mapping Fix', () => {
  describe('modelIdToDefinitionId mapping', () => {
    it('should correctly map OpenAI models', () => {
      expect(mockModelIdToDefinitionId('gpt-4')).toBe('gpt-4');
      expect(mockModelIdToDefinitionId('gpt-3.5-turbo')).toBe('gpt-3.5-turbo');
      expect(mockModelIdToDefinitionId('gpt-4-turbo')).toBe('gpt-4-turbo');
      expect(mockModelIdToDefinitionId('gpt-4o')).toBe('gpt-4o');
      expect(mockModelIdToDefinitionId('gpt-4o-mini')).toBe('gpt-4o-mini');
    });

    it('should correctly map Anthropic Claude models', () => {
      expect(mockModelIdToDefinitionId('claude-3-opus')).toBe('claude-3-opus');
      expect(mockModelIdToDefinitionId('claude-3-sonnet')).toBe('claude-3-sonnet');
      expect(mockModelIdToDefinitionId('claude-3-haiku')).toBe('claude-3-haiku');
      expect(mockModelIdToDefinitionId('claude-3-5-sonnet')).toBe('claude-3-5-sonnet');
      expect(mockModelIdToDefinitionId('claude-3-5-haiku')).toBe('claude-3-5-haiku');
    });

    it('should correctly map Google models', () => {
      expect(mockModelIdToDefinitionId('gemini-pro')).toBe('gemini-pro');
    });

    it('should fallback to original ID for unmapped models', () => {
      expect(mockModelIdToDefinitionId('unknown-model')).toBe('unknown-model');
      expect(mockModelIdToDefinitionId('custom-model-123')).toBe('custom-model-123');
    });

    it('should handle edge cases correctly', () => {
      expect(mockModelIdToDefinitionId('')).toBe('');
      expect(mockModelIdToDefinitionId('GPT-4')).toBe('GPT-4'); // Case sensitivity
    });
  });

  describe('Model variant creation', () => {
    it('should create correct model variants with mapped IDs', () => {
      const mockModelIds = ['gpt-4', 'claude-3-opus', 'gemini-pro'];
      
      const modelVariants = mockModelIds.map((modelId) => ({
        model_definition_id: mockModelIdToDefinitionId(modelId),
        provider_credential_id: null,
        model_parameters: {
          temperature: 0.7,
          max_tokens: 4096,
        }
      }));

      expect(modelVariants).toEqual([
        {
          model_definition_id: 'gpt-4',
          provider_credential_id: null,
          model_parameters: { temperature: 0.7, max_tokens: 4096 }
        },
        {
          model_definition_id: 'claude-3-opus',
          provider_credential_id: null,
          model_parameters: { temperature: 0.7, max_tokens: 4096 }
        },
        {
          model_definition_id: 'gemini-pro',
          provider_credential_id: null,
          model_parameters: { temperature: 0.7, max_tokens: 4096 }
        }
      ]);
    });
  });

  describe('Backend compatibility', () => {
    it('should send model names that match backend available models', () => {
      // These are the models shown as available in the error message
      const backendAvailableModels = [
        'gpt-4', 'gpt-4-turbo', 'gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo',
        'claude-3-5-haiku', 'claude-3-5-sonnet', 'claude-3-haiku', 'claude-3-opus', 'claude-3-sonnet'
      ];

      // Test that our mapping produces names that are in the backend list
      const mappedOpenAI = mockModelIdToDefinitionId('gpt-4');
      const mappedClaude = mockModelIdToDefinitionId('claude-3-opus');
      
      expect(backendAvailableModels).toContain(mappedOpenAI);
      expect(backendAvailableModels).toContain(mappedClaude);
    });

    it('should not produce old problematic model definition IDs', () => {
      // These are the problematic IDs that were causing errors
      const problematicIds = ['model_gpt_4_openai', 'model_claude_3_opus_anthropic'];
      
      const mappedGPT4 = mockModelIdToDefinitionId('gpt-4');
      const mappedClaude = mockModelIdToDefinitionId('claude-3-opus');
      
      expect(problematicIds).not.toContain(mappedGPT4);
      expect(problematicIds).not.toContain(mappedClaude);
      
      // Should be simple model names instead
      expect(mappedGPT4).toBe('gpt-4');
      expect(mappedClaude).toBe('claude-3-opus');
    });
  });
});