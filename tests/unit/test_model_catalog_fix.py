"""
Fix for missing methods in ModelCatalogService

This is a temporary fix to add missing stub methods.
"""

# The model catalog has issues with missing methods. Let's patch them for testing.
from unittest.mock import patch

# Define stub methods
def _add_perplexity_models(self):
    pass

def _add_deepseek_models(self):
    pass

def _add_groq_models(self):
    pass

def _add_ollama_models(self):
    pass

def _add_other_providers(self):
    pass

# Patch the ModelCatalogService before importing the app
import sys
if 'app.services.model_catalog' not in sys.modules:
    with patch.multiple('app.services.model_catalog.ModelCatalogService',
                       _add_perplexity_models=_add_perplexity_models,
                       _add_deepseek_models=_add_deepseek_models,
                       _add_groq_models=_add_groq_models,
                       _add_ollama_models=_add_ollama_models,
                       _add_other_providers=_add_other_providers):
        pass