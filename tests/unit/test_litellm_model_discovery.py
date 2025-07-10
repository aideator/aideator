"""
Unit tests for LiteLLM model discovery service.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.services.litellm_model_discovery import LiteLLMModelDiscovery


class TestLiteLLMModelDiscovery:
    """Test cases for LiteLLM model discovery service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.discovery_service = LiteLLMModelDiscovery()

    @patch('app.services.litellm_model_discovery.litellm')
    def test_get_all_supported_models_success(self, mock_litellm):
        """Test successful model discovery from LiteLLM catalog."""
        # Mock LiteLLM models_by_provider
        mock_models_by_provider = {
            'openai': ['gpt-4o', 'gpt-4', 'gpt-3.5-turbo'],
            'anthropic': ['claude-3-opus', 'claude-3-sonnet'],
            'groq': ['groq/llama3-8b-8192', 'groq/mixtral-8x7b-32768'],
        }
        mock_litellm.models_by_provider = mock_models_by_provider
        
        # Test model discovery
        models = self.discovery_service.get_all_supported_models()
        
        # Verify results
        assert len(models) == 7  # Total models across all providers
        assert self.discovery_service.last_discovery_time is not None
        assert len(self.discovery_service.discovered_models) == 7
        
        # Check specific models exist
        model_names = [m['model_name'] for m in models]
        assert 'gpt-4o' in model_names
        assert 'claude-3-opus' in model_names
        assert 'groq/llama3-8b-8192' in model_names

    @patch('app.services.litellm_model_discovery.LITELLM_AVAILABLE', False)
    def test_get_all_supported_models_litellm_not_available(self):
        """Test behavior when LiteLLM is not available."""
        models = self.discovery_service.get_all_supported_models()
        assert models == []

    @patch('app.services.litellm_model_discovery.litellm')
    def test_get_all_supported_models_no_models_by_provider(self, mock_litellm):
        """Test behavior when models_by_provider attribute is missing."""
        # Remove models_by_provider attribute
        del mock_litellm.models_by_provider
        
        models = self.discovery_service.get_all_supported_models()
        assert models == []

    def test_create_model_info_openai(self):
        """Test model info creation for OpenAI model."""
        model_info = self.discovery_service._create_model_info('gpt-4o', 'openai')
        
        assert model_info['model_name'] == 'gpt-4o'
        assert model_info['litellm_provider'] == 'openai'
        assert model_info['display_name'] == 'GPT 4O'
        assert model_info['category'] == 'advanced'
        assert model_info['requires_api_key'] is True
        assert model_info['api_key_env_var'] == 'OPENAI_API_KEY'
        assert model_info['supports_function_calling'] is True
        assert model_info['supports_vision'] is True
        assert 'powerful' in model_info['tags']
        assert 'openai' in model_info['tags']

    def test_create_model_info_anthropic(self):
        """Test model info creation for Anthropic model."""
        model_info = self.discovery_service._create_model_info('claude-3-sonnet', 'anthropic')
        
        assert model_info['model_name'] == 'claude-3-sonnet'
        assert model_info['litellm_provider'] == 'anthropic'
        assert model_info['display_name'] == 'Claude 3 Sonnet'
        assert model_info['category'] == 'advanced'
        assert model_info['description'] == 'Balanced performance and cost from Anthropic'
        assert model_info['is_recommended'] is True
        assert model_info['api_key_env_var'] == 'ANTHROPIC_API_KEY'

    def test_create_model_info_embedding(self):
        """Test model info creation for embedding model."""
        model_info = self.discovery_service._create_model_info('text-embedding-3-large', 'openai')
        
        assert model_info['category'] == 'embedding'
        assert model_info['description'] == 'Embedding model for semantic search and similarity'
        assert 'embedding' in model_info['tags']

    def test_create_model_info_vision(self):
        """Test model info creation for vision model."""
        model_info = self.discovery_service._create_model_info('gpt-4-vision-preview', 'openai')
        
        assert model_info['category'] == 'vision'
        assert model_info['supports_vision'] is True
        assert 'vision' in model_info['tags']

    def test_create_model_info_code(self):
        """Test model info creation for code model."""
        model_info = self.discovery_service._create_model_info('codex-mini-latest', 'openai')
        
        assert model_info['category'] == 'code'
        assert model_info['description'] == 'Code generation and analysis model'
        assert 'code' in model_info['tags']

    def test_create_model_info_whisper(self):
        """Test model info creation for speech model."""
        model_info = self.discovery_service._create_model_info('whisper-large-v3', 'groq')
        
        assert model_info['category'] == 'speech-to-text'
        assert model_info['description'] == 'Speech-to-text transcription model'
        assert 'speech' in model_info['tags']

    def test_create_model_info_tts(self):
        """Test model info creation for TTS model."""
        model_info = self.discovery_service._create_model_info('tts-1-hd', 'openai')
        
        assert model_info['category'] == 'text-to-speech'
        assert model_info['description'] == 'Text-to-speech synthesis model'
        assert 'audio' in model_info['tags']

    def test_create_model_info_ollama_no_api_key(self):
        """Test model info creation for Ollama (no API key required)."""
        model_info = self.discovery_service._create_model_info('llama2:7b', 'ollama')
        
        assert model_info['requires_api_key'] is False
        assert model_info['api_key_env_var'] is None

    def test_deduplicate_models(self):
        """Test model deduplication with provider priority."""
        models = [
            {'model_name': 'gpt-4', 'litellm_provider': 'openai'},
            {'model_name': 'gpt-4', 'litellm_provider': 'azure'},  # Duplicate
            {'model_name': 'claude-3-opus', 'litellm_provider': 'anthropic'},
            {'model_name': 'claude-3-opus', 'litellm_provider': 'bedrock'},  # Duplicate
        ]
        
        unique_models = self.discovery_service._deduplicate_models(models)
        
        assert len(unique_models) == 2
        model_names = [m['model_name'] for m in unique_models]
        assert 'gpt-4' in model_names
        assert 'claude-3-opus' in model_names
        
        # Verify provider priority (openai preferred over azure)
        gpt4_model = next(m for m in unique_models if m['model_name'] == 'gpt-4')
        assert gpt4_model['litellm_provider'] == 'openai'
        
        # Verify provider priority (anthropic preferred over bedrock)
        claude_model = next(m for m in unique_models if m['model_name'] == 'claude-3-opus')
        assert claude_model['litellm_provider'] == 'anthropic'

    def test_generate_display_name_basic(self):
        """Test display name generation for basic models."""
        assert self.discovery_service._generate_display_name('gpt-4o') == 'GPT 4O'
        assert self.discovery_service._generate_display_name('claude-3-sonnet') == 'Claude 3 Sonnet'
        assert self.discovery_service._generate_display_name('gemini-1.5-pro') == 'Gemini 1.5 Pro'

    def test_generate_display_name_with_prefixes(self):
        """Test display name generation with provider prefixes."""
        assert self.discovery_service._generate_display_name('openai/gpt-4') == 'GPT 4'
        assert self.discovery_service._generate_display_name('anthropic/claude-3-opus') == 'Claude 3 Opus'
        assert self.discovery_service._generate_display_name('groq/llama3-8b-8192') == 'Llama3 8B 8192'

    def test_generate_display_name_fireworks(self):
        """Test display name generation for Fireworks models."""
        model_name = 'fireworks_ai/accounts/fireworks/models/llama-v3p1-8b-instruct'
        expected = 'Llama V3P1 8B Instruct'
        assert self.discovery_service._generate_display_name(model_name) == expected

    def test_generate_display_name_special_terms(self):
        """Test display name generation with special terms."""
        assert self.discovery_service._generate_display_name('text-embedding-ada-002') == 'Text Embedding Ada 002'
        assert self.discovery_service._generate_display_name('tts-1-hd') == 'TTS 1 Hd'
        assert self.discovery_service._generate_display_name('whisper-v1') == 'Whisper V1'

    def test_determine_category_embedding(self):
        """Test category determination for embedding models."""
        assert self.discovery_service._determine_category('text-embedding-3-large', 'openai') == 'embedding'
        assert self.discovery_service._determine_category('embed-english-v3.0', 'cohere') == 'embedding'

    def test_determine_category_vision(self):
        """Test category determination for vision models."""
        assert self.discovery_service._determine_category('gpt-4-vision-preview', 'openai') == 'vision'
        assert self.discovery_service._determine_category('gpt-4o-multimodal', 'openai') == 'vision'

    def test_determine_category_code(self):
        """Test category determination for code models."""
        assert self.discovery_service._determine_category('codex-mini', 'openai') == 'code'
        assert self.discovery_service._determine_category('deepseek-coder', 'deepseek') == 'code'

    def test_determine_category_speech(self):
        """Test category determination for speech models."""
        assert self.discovery_service._determine_category('whisper-large-v3', 'openai') == 'speech-to-text'
        assert self.discovery_service._determine_category('tts-1', 'openai') == 'text-to-speech'

    def test_determine_category_advanced(self):
        """Test category determination for advanced models."""
        assert self.discovery_service._determine_category('gpt-4o', 'openai') == 'advanced'
        assert self.discovery_service._determine_category('claude-3-opus', 'anthropic') == 'advanced'
        assert self.discovery_service._determine_category('gemini-pro', 'gemini') == 'advanced'
        assert self.discovery_service._determine_category('grok-beta', 'xai') == 'advanced'

    def test_determine_category_general(self):
        """Test category determination for general models."""
        assert self.discovery_service._determine_category('gpt-3.5-turbo', 'openai') == 'general'
        assert self.discovery_service._determine_category('llama2-7b', 'meta') == 'general'

    def test_generate_tags_fast_models(self):
        """Test tag generation for fast models."""
        tags = self.discovery_service._generate_tags('gpt-3.5-turbo', 'openai')
        assert 'fast' in tags
        assert 'openai' in tags
        
        tags = self.discovery_service._generate_tags('gemini-1.5-flash', 'gemini')
        assert 'fast' in tags

    def test_generate_tags_powerful_models(self):
        """Test tag generation for powerful models."""
        tags = self.discovery_service._generate_tags('gpt-4o', 'openai')
        assert 'powerful' in tags
        
        tags = self.discovery_service._generate_tags('claude-3-opus', 'anthropic')
        assert 'powerful' in tags

    def test_generate_tags_special_features(self):
        """Test tag generation for models with special features."""
        tags = self.discovery_service._generate_tags('gpt-4-vision', 'openai')
        assert 'vision' in tags
        
        tags = self.discovery_service._generate_tags('text-embedding-3-large', 'openai')
        assert 'embedding' in tags
        
        tags = self.discovery_service._generate_tags('codex-mini', 'openai')
        assert 'code' in tags
        
        tags = self.discovery_service._generate_tags('whisper-large', 'openai')
        assert 'speech' in tags
        
        tags = self.discovery_service._generate_tags('tts-1', 'openai')
        assert 'audio' in tags

    def test_is_recommended_models(self):
        """Test recommended model identification."""
        assert self.discovery_service._is_recommended('gpt-4o') is True
        assert self.discovery_service._is_recommended('gpt-4') is True
        assert self.discovery_service._is_recommended('claude-3-opus') is True
        assert self.discovery_service._is_recommended('claude-3-sonnet') is True
        assert self.discovery_service._is_recommended('claude-3-5-sonnet') is True
        assert self.discovery_service._is_recommended('gemini-1.5-pro') is True
        assert self.discovery_service._is_recommended('gemini-1.5-flash') is True
        assert self.discovery_service._is_recommended('grok-beta') is True
        assert self.discovery_service._is_recommended('deepseek-reasoner') is True
        
        # Not recommended
        assert self.discovery_service._is_recommended('gpt-3.5-turbo') is False
        assert self.discovery_service._is_recommended('claude-instant') is False

    def test_is_popular_models(self):
        """Test popular model identification."""
        assert self.discovery_service._is_popular('gpt-4') is True
        assert self.discovery_service._is_popular('gpt-3.5-turbo') is True
        assert self.discovery_service._is_popular('claude-3-opus') is True
        assert self.discovery_service._is_popular('gemini-pro') is True
        assert self.discovery_service._is_popular('grok-beta') is True
        assert self.discovery_service._is_popular('deepseek-chat') is True
        
        # Not popular
        assert self.discovery_service._is_popular('text-embedding-ada-002') is False

    def test_requires_api_key(self):
        """Test API key requirement determination."""
        assert self.discovery_service._requires_api_key('openai') is True
        assert self.discovery_service._requires_api_key('anthropic') is True
        assert self.discovery_service._requires_api_key('groq') is True
        
        # No API key required
        assert self.discovery_service._requires_api_key('ollama') is False
        assert self.discovery_service._requires_api_key('local') is False

    def test_get_api_key_env_var(self):
        """Test API key environment variable mapping."""
        assert self.discovery_service._get_api_key_env_var('openai') == 'OPENAI_API_KEY'
        assert self.discovery_service._get_api_key_env_var('text-completion-openai') == 'OPENAI_API_KEY'
        assert self.discovery_service._get_api_key_env_var('anthropic') == 'ANTHROPIC_API_KEY'
        assert self.discovery_service._get_api_key_env_var('cohere') == 'COHERE_API_KEY'
        assert self.discovery_service._get_api_key_env_var('groq') == 'GROQ_API_KEY'
        assert self.discovery_service._get_api_key_env_var('xai') == 'XAI_API_KEY'
        assert self.discovery_service._get_api_key_env_var('deepseek') == 'DEEPSEEK_API_KEY'
        assert self.discovery_service._get_api_key_env_var('vertex_ai') == 'GOOGLE_APPLICATION_CREDENTIALS'
        assert self.discovery_service._get_api_key_env_var('bedrock') == 'AWS_ACCESS_KEY_ID'
        
        # Unknown provider
        assert self.discovery_service._get_api_key_env_var('unknown_provider') is None

    def test_supports_function_calling(self):
        """Test function calling support detection."""
        assert self.discovery_service._supports_function_calling('gpt-4') is True
        assert self.discovery_service._supports_function_calling('gpt-3.5-turbo') is True
        assert self.discovery_service._supports_function_calling('claude-3-opus') is True
        assert self.discovery_service._supports_function_calling('gemini-pro') is True
        assert self.discovery_service._supports_function_calling('grok-beta') is True
        
        # Models that don't support function calling
        assert self.discovery_service._supports_function_calling('text-embedding-ada-002') is False
        assert self.discovery_service._supports_function_calling('whisper-1') is False

    def test_supports_vision(self):
        """Test vision support detection."""
        assert self.discovery_service._supports_vision('gpt-4o') is True
        assert self.discovery_service._supports_vision('gpt-4-vision-preview') is True
        assert self.discovery_service._supports_vision('claude-3-opus') is True
        assert self.discovery_service._supports_vision('claude-3-sonnet') is True
        assert self.discovery_service._supports_vision('claude-3-5-sonnet') is True
        assert self.discovery_service._supports_vision('gemini-1.5-pro') is True
        assert self.discovery_service._supports_vision('gemini-2.0-flash') is True
        assert self.discovery_service._supports_vision('grok-vision-beta') is True
        
        # Models that don't support vision
        assert self.discovery_service._supports_vision('gpt-3.5-turbo') is False
        assert self.discovery_service._supports_vision('text-embedding-ada-002') is False

    @patch('app.services.litellm_model_discovery.litellm')
    def test_integration_complete_flow(self, mock_litellm):
        """Test complete integration flow with realistic data."""
        # Mock comprehensive models_by_provider data
        mock_models_by_provider = {
            'openai': [
                'gpt-4o', 'gpt-4', 'gpt-3.5-turbo', 'text-embedding-3-large', 
                'whisper-1', 'tts-1', 'gpt-4-vision-preview'
            ],
            'anthropic': ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
            'groq': ['groq/llama3-8b-8192', 'groq/whisper-large-v3'],
            'xai': ['xai/grok-beta', 'xai/grok-vision-beta'],
            'deepseek': ['deepseek/deepseek-reasoner', 'deepseek/deepseek-coder'],
        }
        mock_litellm.models_by_provider = mock_models_by_provider
        
        # Run discovery
        models = self.discovery_service.get_all_supported_models()
        
        # Verify comprehensive results
        assert len(models) == 17  # Total unique models
        
        # Verify different categories are present
        categories = set(m['category'] for m in models)
        expected_categories = {'advanced', 'general', 'embedding', 'speech-to-text', 'text-to-speech', 'vision', 'code'}
        assert categories.intersection(expected_categories) == expected_categories
        
        # Verify different providers are present
        providers = set(m['litellm_provider'] for m in models)
        assert providers == {'openai', 'anthropic', 'groq', 'xai', 'deepseek'}
        
        # Verify specific model characteristics
        gpt4o = next((m for m in models if m['model_name'] == 'gpt-4o'), None)
        assert gpt4o is not None
        assert gpt4o['category'] == 'advanced'
        assert gpt4o['supports_vision'] is True
        assert gpt4o['is_recommended'] is True
        
        embedding_model = next((m for m in models if 'embedding' in m['model_name']), None)
        assert embedding_model is not None
        assert embedding_model['category'] == 'embedding'
        
        # Verify service state
        assert self.discovery_service.last_discovery_time is not None
        assert len(self.discovery_service.discovered_models) == 17