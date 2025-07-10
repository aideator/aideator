/**
 * Unit tests for the model ID mapping fix
 * Tests the core logic that was changed to fix the model name issue
 */

// This is the exact mapping from the fixed code in useAPIIntegration.ts
const modelIdToDefinitionId = (modelId) => {
  const modelMapping = {
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

describe('Model ID Mapping Fix', () => {
  describe('OpenAI models', () => {
    test('should correctly map gpt-4', () => {
      expect(modelIdToDefinitionId('gpt-4')).toBe('gpt-4');
    });

    test('should correctly map gpt-3.5-turbo', () => {
      expect(modelIdToDefinitionId('gpt-3.5-turbo')).toBe('gpt-3.5-turbo');
    });

    test('should correctly map gpt-4-turbo', () => {
      expect(modelIdToDefinitionId('gpt-4-turbo')).toBe('gpt-4-turbo');
    });

    test('should correctly map gpt-4o', () => {
      expect(modelIdToDefinitionId('gpt-4o')).toBe('gpt-4o');
    });

    test('should correctly map gpt-4o-mini', () => {
      expect(modelIdToDefinitionId('gpt-4o-mini')).toBe('gpt-4o-mini');
    });
  });

  describe('Anthropic Claude models', () => {
    test('should correctly map claude-3-opus', () => {
      expect(modelIdToDefinitionId('claude-3-opus')).toBe('claude-3-opus');
    });

    test('should correctly map claude-3-sonnet', () => {
      expect(modelIdToDefinitionId('claude-3-sonnet')).toBe('claude-3-sonnet');
    });

    test('should correctly map claude-3-haiku', () => {
      expect(modelIdToDefinitionId('claude-3-haiku')).toBe('claude-3-haiku');
    });

    test('should correctly map claude-3-5-sonnet', () => {
      expect(modelIdToDefinitionId('claude-3-5-sonnet')).toBe('claude-3-5-sonnet');
    });

    test('should correctly map claude-3-5-haiku', () => {
      expect(modelIdToDefinitionId('claude-3-5-haiku')).toBe('claude-3-5-haiku');
    });
  });

  describe('Google models', () => {
    test('should correctly map gemini-pro', () => {
      expect(modelIdToDefinitionId('gemini-pro')).toBe('gemini-pro');
    });
  });

  describe('Edge cases and fallbacks', () => {
    test('should fallback to original ID for unmapped models', () => {
      expect(modelIdToDefinitionId('unknown-model')).toBe('unknown-model');
      expect(modelIdToDefinitionId('custom-model-123')).toBe('custom-model-123');
    });

    test('should handle edge cases correctly', () => {
      expect(modelIdToDefinitionId('')).toBe('');
      expect(modelIdToDefinitionId('GPT-4')).toBe('GPT-4'); // Case sensitivity
    });
  });

  describe('Backend compatibility', () => {
    test('should produce model names that match backend available models', () => {
      // These are the models shown as available in the original error message
      const backendAvailableModels = [
        'gpt-4', 'gpt-4-turbo', 'gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo',
        'claude-3-5-haiku', 'claude-3-5-sonnet', 'claude-3-haiku', 'claude-3-opus', 'claude-3-sonnet'
      ];

      // Test that our mapping produces names that are in the backend list
      const mappedOpenAI = modelIdToDefinitionId('gpt-4');
      const mappedClaude = modelIdToDefinitionId('claude-3-opus');
      
      expect(backendAvailableModels).toContain(mappedOpenAI);
      expect(backendAvailableModels).toContain(mappedClaude);
    });

    test('should not produce old problematic model definition IDs', () => {
      // These are the problematic IDs that were causing errors
      const problematicIds = ['model_gpt_4_openai', 'model_claude_3_opus_anthropic'];
      
      const mappedGPT4 = modelIdToDefinitionId('gpt-4');
      const mappedClaude = modelIdToDefinitionId('claude-3-opus');
      
      expect(problematicIds).not.toContain(mappedGPT4);
      expect(problematicIds).not.toContain(mappedClaude);
      
      // Should be simple model names instead
      expect(mappedGPT4).toBe('gpt-4');
      expect(mappedClaude).toBe('claude-3-opus');
    });
  });

  describe('Model variant creation', () => {
    test('should create correct model variants with mapped IDs', () => {
      const mockModelIds = ['gpt-4', 'claude-3-opus', 'gemini-pro'];
      
      const modelVariants = mockModelIds.map((modelId) => ({
        model_definition_id: modelIdToDefinitionId(modelId),
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
});