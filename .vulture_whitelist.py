# Vulture whitelist for AIdeator
# This file contains intentionally unused variables and functions that
# should not be reported as dead code

# FastAPI route functions - these are used by the framework via decorators
def register():
    pass  # app/api/v1/auth.py


def login():
    pass  # app/api/v1/auth.py


def get_me():
    pass  # app/api/v1/auth.py


def create_api_key():
    pass  # app/api/v1/auth.py


def list_api_keys():
    pass  # app/api/v1/auth.py


def delete_api_key():
    pass  # app/api/v1/auth.py


def dev_test_login():
    pass  # app/api/v1/auth.py


def decrypt_credentials():
    pass  # app/api/v1/credentials.py


def create_provider_credential():
    pass  # app/api/v1/credentials.py


def get_provider_credentials():
    pass  # app/api/v1/credentials.py


def get_provider_credential():
    pass  # app/api/v1/credentials.py


def update_provider_credential():
    pass  # app/api/v1/credentials.py


def delete_provider_credential():
    pass  # app/api/v1/credentials.py


def trigger_model_sync():
    pass  # app/api/v1/endpoints/admin.py


def get_sync_history():
    pass  # app/api/v1/endpoints/admin.py


def get_sync_status():
    pass  # app/api/v1/endpoints/admin.py


def validate_provider():
    pass  # app/api/v1/endpoints/provider_keys.py


def list_provider_keys():
    pass  # app/api/v1/endpoints/provider_keys.py


def get_provider_key():
    pass  # app/api/v1/endpoints/provider_keys.py


def list_supported_providers():
    pass  # app/api/v1/endpoints/provider_keys.py


def update_provider_key():
    pass  # app/api/v1/endpoints/provider_keys.py


def delete_provider_key():
    pass  # app/api/v1/endpoints/provider_keys.py


def health_check():
    pass  # app/api/v1/health.py


def get_health():
    pass  # app/api/v1/health.py


def get_models_metadata():
    pass  # app/api/v1/models.py


def discover_models():
    pass  # app/api/v1/models.py


def get_model_by_litellm_name():
    pass  # app/api/v1/models.py


def get_model_capabilities():
    pass  # app/api/v1/models.py


def create_preference():
    pass  # app/api/v1/preferences.py


def get_preferences():
    pass  # app/api/v1/preferences.py


def get_preference():
    pass  # app/api/v1/preferences.py


def get_preference_analytics():
    pass  # app/api/v1/preferences.py


def update_preference():
    pass  # app/api/v1/preferences.py


def delete_preference():
    pass  # app/api/v1/preferences.py


def get_preference_summary():
    pass  # app/api/v1/preferences.py


def create_run():
    pass  # app/api/v1/runs.py


def get_runs():
    pass  # app/api/v1/runs.py


def get_run():
    pass  # app/api/v1/runs.py


def update_run():
    pass  # app/api/v1/runs.py


def delete_run():
    pass  # app/api/v1/runs.py


def select_winner():
    pass  # app/api/v1/runs.py


def get_run_status():
    pass  # app/api/v1/runs.py


def cancel_run():
    pass  # app/api/v1/runs.py


def create_session():
    pass  # app/api/v1/sessions.py


def get_sessions():
    pass  # app/api/v1/sessions.py


def get_session():
    pass  # app/api/v1/sessions.py


def update_session():
    pass  # app/api/v1/sessions.py


def delete_session():
    pass  # app/api/v1/sessions.py


def archive_session():
    pass  # app/api/v1/sessions.py


def get_session_analytics():
    pass  # app/api/v1/sessions.py


def get_session_preferences():
    pass  # app/api/v1/sessions.py


def stream_agent_output():
    pass  # app/api/v1/streams.py


def root():
    pass  # app/main.py


# Database session functions that are dependency injected
def get_async_session():
    pass  # app/core/database.py


def get_sync_session():
    pass  # app/core/database.py


# Dependency injection functions used by FastAPI
def get_current_user():
    pass  # app/core/dependencies.py


def get_current_active_user():
    pass  # app/core/dependencies.py


def require_superuser():
    pass  # app/core/dependencies.py


def get_api_key():
    pass  # app/core/deps.py


def get_user_from_token():
    pass  # app/core/deps.py


# Additional FastAPI route functions
def detailed_health_check():
    pass  # app/api/v1/health.py


def get_model_catalog():
    pass  # app/api/v1/models.py


def get_models():
    pass  # app/api/v1/models.py


def get_model():
    pass  # app/api/v1/models.py


def get_model_recommendations():
    pass  # app/api/v1/models.py


def get_available_models():
    pass  # app/api/v1/models.py


def get_user_preferences():
    pass  # app/api/v1/preferences.py


def get_preference_stats():
    pass  # app/api/v1/preferences.py


def get_model_performance():
    pass  # app/api/v1/preferences.py


def get_preference_trends():
    pass  # app/api/v1/preferences.py


def list_runs():
    pass  # app/api/v1/runs.py


def get_session_turns():
    pass  # app/api/v1/sessions.py


def create_turn():
    pass  # app/api/v1/sessions.py


def get_turn():
    pass  # app/api/v1/sessions.py


def export_session():
    pass  # app/api/v1/sessions.py


def stream_run():
    pass  # app/api/v1/streams.py


def stream_debug_logs():
    pass  # app/api/v1/streams.py


# Classes
class OptionalCurrentUser:  # app/core/dependencies.py
    pass


class LoggingMiddleware:  # app/middleware/logging.py
    pass


class RateLimitMiddleware:  # app/middleware/rate_limit.py
    pass


class ErrorResponse:  # app/schemas/common.py
    pass


class SuccessResponse:  # app/schemas/common.py
    pass


class ValidationErrorResponse:  # app/schemas/common.py
    pass


class ValidationErrorDetail:  # app/schemas/common.py
    pass


class PaginatedResponse:  # app/schemas/common.py
    pass


class ModelSelectionRequest:  # app/schemas/models.py
    pass


class KubernetesEnvironment:  # app/core/config.py
    pass


# Validators
def validate_email():
    pass  # app/schemas/auth.py


def validate_github_url():
    pass  # app/schemas/runs.py


def validate_model_variants():
    pass  # app/schemas/runs.py


def validate_quality_scores():
    pass  # app/schemas/session.py


def validate_openai_api_key():
    pass  # app/core/config.py


def validate_anthropic_api_key():
    pass  # app/core/config.py


def validate_gemini_api_key():
    pass  # app/core/config.py


def validate_password():
    pass  # app/schemas/auth.py


def validate_prompt():
    pass  # app/schemas/runs.py


def validate_agent_mode():
    pass  # app/schemas/runs.py


def parse_list_from_json():
    pass  # app/core/config.py


def validate_secret_key():
    pass  # app/core/config.py


def validate_encryption_key():
    pass  # app/core/config.py


def validate_openai_key():
    pass  # app/core/config.py


def validate_anthropic_key():
    pass  # app/core/config.py


def validate_gemini_key():
    pass  # app/core/config.py


def validate_settings():
    pass  # app/core/config.py


# Service methods
def get_run_status_service():
    pass  # app/services/agent_orchestrator.py


def cancel_run_service():
    pass  # app/services/agent_orchestrator.py


def get_active_runs():
    pass  # app/services/agent_orchestrator.py


def generate_master_key():
    pass  # app/services/encryption_service.py


def rotate_key():
    pass  # app/services/encryption_service.py


def get_all_supported_models():
    pass  # app/services/litellm_model_discovery.py


def get_models_by_capability():
    pass  # app/services/model_catalog.py


def get_models_without_api_key():
    pass  # app/services/model_catalog.py


def get_model_by_litellm_name_service():
    pass  # app/services/model_catalog.py


def get_all_possible_models():
    pass  # app/services/model_discovery_service.py


def get_key_for_model():
    pass  # app/services/provider_key_service.py


def custom_openapi():
    pass  # app/utils/openapi.py


def setup_logging():
    pass  # app/core/logging.py


def get_kubernetes_secrets():
    pass  # app/core/config.py


def dispatch():
    pass  # app/middleware/logging.py and app/middleware/rate_limit.py


def get_agent_env():
    pass  # app/core/config.py


def get_build_args():
    pass  # app/core/config.py


# Enum values and constants
ANTHROPIC = "anthropic"
OPENAI = "openai"
GOOGLE = "google"
AZURE = "azure"
VERTEX_AI = "vertex_ai"
BEDROCK = "bedrock"
HUGGINGFACE = "huggingface"
OLLAMA = "ollama"
TOGETHER_AI = "together_ai"
REPLICATE = "replicate"
GROQ = "groq"
MISTRAL = "mistral"
COHERE = "cohere"
DEEPINFRA = "deepinfra"
TEXT_COMPLETION = "text_completion"
CHAT_COMPLETION = "chat_completion"
VISION = "vision"
EMBEDDINGS = "embeddings"
FUNCTION_CALLING = "function_calling"
STREAMING = "streaming"

# Configuration attributes
workers = None
encryption_key = None
kubernetes_job_ttl = None
agent_container_image = None
redis_url = None
upload_max_size_mb = None
model_sync_interval_minutes = None
enable_tracing = None
jaeger_agent_host = None
jaeger_agent_port = None

# Model and schema attributes
model_config = None
Config = None
from_attributes = None
results = None
error_message = None
completed_at = None
total_turns = None
total_cost = None
models_used = None
responses = None
model_parameters = None
provider_credential_id = None
_db = None
helm_chart_path = None
litellm_model_discovery = None
model_discovery_service = None
last_seen_at = None
max_input_tokens = None
extra_metadata = None
last_error = None
json_schema_extra = None
example = None
description = None
api_key_env_var = None
is_recommended = None
is_popular = None
first_seen_at = None
protected_namespaces = None
output = None
tokens_used = None
cost_usd = None
response_time_ms = None
encryption_version = None
total_tokens = None
ip_address = None
user_agent = None
api_key_id = None
total_tokens_used = None
output_type = None
max_runs_per_day = None
max_variations_per_run = None
total_runs = None
token_type = None
expires_in = None
key_info = None
error_code = None
loc = None
msg = None
type = None
pages = None
model_count = None
user_has_credentials = None
reasoning = None
temperature = None
system_prompt = None
stop_sequences = None
stream_url = None
estimated_duration_seconds = None
total_sessions = None
active_sessions = None
archived_sessions = None
average_cost_per_session = None
average_turns_per_session = None
most_used_models = None
average_response_time = None
average_quality_score = None

# Logging attributes - agent/main.py
import agent.main

agent.main.AIdeatorAgent.file_logger.handlers

# Configuration attributes - app/core/config.py
import app.core.config

app.core.config.Settings.access_token_expire_minutes
app.core.config.Settings.enable_tracing
app.core.config.Settings.jaeger_agent_host
app.core.config.Settings.jaeger_agent_port

# Provider key related attributes - app/models/provider.py
import app.models.provider

app.models.provider.ProviderCredential.encrypted_credentials
app.models.provider.ProviderCredential.total_cost_usd

# Session attributes - app/api/v1/sessions.py
import app.api.v1.sessions

app.api.v1.sessions.SessionAnalytics.total_turns

# Model definition attributes - app/models/model_definition.py
import app.models.model_definition

app.models.model_definition.ModelDefinition.max_input_tokens
app.models.model_definition.ModelDefinition.api_key_env_var
app.models.model_definition.ModelDefinition.is_recommended
app.models.model_definition.ModelDefinition.is_popular
app.models.model_definition.ModelDefinition.first_seen_at
app.models.model_definition.ModelDefinition.last_seen_at
app.models.model_definition.ModelDefinition.extra_metadata
app.models.model_definition.ModelVariant.completed_at
app.models.model_definition.ModelVariant.extra_metadata

# Dependencies - app/core/dependencies.py
import app.core.dependencies

app.core.dependencies.OptionalCurrentUser
