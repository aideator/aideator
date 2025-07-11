#!/bin/bash

# AIdeator Secrets Management Script
# Manages Kubernetes secrets for development and deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="aideator"
ENV_FILE=".env"
SECRETS_CONFIG="deploy/secrets/secrets.yaml"
ENVIRONMENT="${AIDEATOR_ENV:-development}"

# Functions
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Load environment variables
load_env() {
    if [[ -f "$ENV_FILE" ]]; then
        # shellcheck disable=SC1090
        source "$ENV_FILE"
    else
        error "Environment file $ENV_FILE not found"
        exit 1
    fi
}

# Check if kubectl is available
check_kubectl() {
    if ! command -v kubectl >/dev/null 2>&1; then
        error "kubectl not found. Please install kubectl."
        exit 1
    fi
}

# Check if namespace exists
check_namespace() {
    if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
        log "Creating namespace: $NAMESPACE"
        kubectl create namespace "$NAMESPACE"
    fi
}

# Create or update a secret with multiple keys
create_secret() {
    local secret_name="$1"
    shift
    local -a key_value_pairs=("$@")
    
    if [[ ${#key_value_pairs[@]} -eq 0 ]]; then
        error "No key-value pairs provided for secret: $secret_name"
        return 1
    fi
    
    # Check if secret exists
    if kubectl get secret "$secret_name" -n "$NAMESPACE" >/dev/null 2>&1; then
        log "Updating secret: $secret_name"
        
        # Build patch data
        local patch_data="{"
        for ((i=0; i<${#key_value_pairs[@]}; i+=2)); do
            local key="${key_value_pairs[i]}"
            local value="${key_value_pairs[i+1]}"
            
            if [[ -z "$value" ]]; then
                warn "Value for $secret_name.$key is empty, using placeholder"
                value="placeholder"
            fi
            
            if [[ $i -gt 0 ]]; then
                patch_data+=","
            fi
            patch_data+="\"$key\":\"$(echo -n "$value" | base64 -w 0)\""
        done
        patch_data+="}"
        
        kubectl patch secret "$secret_name" -n "$NAMESPACE" \
            --type merge \
            -p "{\"data\":$patch_data}"
    else
        log "Creating secret: $secret_name"
        
        # Build kubectl create command
        local create_args=("kubectl" "create" "secret" "generic" "$secret_name" "-n" "$NAMESPACE")
        
        for ((i=0; i<${#key_value_pairs[@]}; i+=2)); do
            local key="${key_value_pairs[i]}"
            local value="${key_value_pairs[i+1]}"
            
            if [[ -z "$value" ]]; then
                warn "Value for $secret_name.$key is empty, using placeholder"
                value="placeholder"
            fi
            
            create_args+=("--from-literal=$key=$value")
        done
        
        "${create_args[@]}"
    fi
}

# Generate missing environment values
generate_defaults() {
    # Generate secret key if not provided
    if [[ -z "${SECRET_KEY:-}" ]]; then
        export SECRET_KEY=$(openssl rand -hex 32)
        log "Generated SECRET_KEY"
    fi
    
    # Generate encryption key if not provided
    if [[ -z "${ENCRYPTION_KEY:-}" ]]; then
        export ENCRYPTION_KEY=$(openssl rand -hex 32)
        log "Generated ENCRYPTION_KEY"
    fi
    
    # Generate LiteLLM master key if not provided
    if [[ -z "${LITELLM_MASTER_KEY:-}" ]]; then
        export LITELLM_MASTER_KEY="sk-$(openssl rand -hex 16)"
        log "Generated LITELLM_MASTER_KEY"
    fi
    
    # Set default database password if not provided
    if [[ -z "${DATABASE_PASSWORD:-}" ]]; then
        export DATABASE_PASSWORD="aideator123"
    fi
}

# Create all secrets
create_all_secrets() {
    log "Creating/updating all secrets in namespace: $NAMESPACE"
    log "Environment: $ENVIRONMENT"
    
    # Generate any missing defaults
    generate_defaults
    
    # Create FastAPI application secrets (required)
    create_secret "aideator-secret" \
        "secret-key" "${SECRET_KEY}" \
        "encryption-key" "${ENCRYPTION_KEY}"
    
    # Create infrastructure secrets with defaults
    create_secret "database-secret" \
        "url" "${DATABASE_URL:-postgresql://postgres:postgres@aideator-postgresql:5432/aideator}" \
        "password" "${DATABASE_PASSWORD}"
    
    create_secret "redis-secret" \
        "url" "${REDIS_URL:-redis://aideator-redis:6379}"
    
    create_secret "litellm-secret" \
        "master-key" "${LITELLM_MASTER_KEY}"
    
    # Create AI provider secrets with placeholders (optional - configured via other means)
    create_secret "openai-secret" \
        "api-key" "placeholder"
    
    create_secret "anthropic-secret" \
        "api-key" "placeholder"
    
    create_secret "gemini-secret" \
        "api-key" "placeholder"
    
    log "All secrets created/updated successfully"
    log "AI provider API keys set to placeholder - configure via your preferred method"
}

# List all secrets
list_secrets() {
    log "Listing secrets in namespace: $NAMESPACE"
    kubectl get secrets -n "$NAMESPACE" -o custom-columns="NAME:.metadata.name,TYPE:.type,DATA:.data,AGE:.metadata.creationTimestamp"
}

# Delete all secrets
delete_secrets() {
    log "Deleting all secrets in namespace: $NAMESPACE"
    kubectl delete secrets \
        aideator-secret \
        openai-secret \
        anthropic-secret \
        gemini-secret \
        database-secret \
        redis-secret \
        litellm-secret \
        -n "$NAMESPACE" \
        --ignore-not-found=true
    log "All secrets deleted"
}

# Validate secrets
validate_secrets() {
    log "Validating secrets in namespace: $NAMESPACE"
    
    local secrets=("aideator-secret" "openai-secret" "anthropic-secret" "gemini-secret" "database-secret" "redis-secret" "litellm-secret")
    local errors=0
    
    for secret in "${secrets[@]}"; do
        if kubectl get secret "$secret" -n "$NAMESPACE" >/dev/null 2>&1; then
            log "✓ Secret $secret exists"
            
            # Check for required keys
            case "$secret" in
                "aideator-secret")
                    if kubectl get secret "$secret" -n "$NAMESPACE" -o jsonpath='{.data.secret-key}' >/dev/null 2>&1; then
                        log "  ✓ secret-key exists"
                    else
                        error "  ✗ secret-key missing"
                        ((errors++))
                    fi
                    
                    if kubectl get secret "$secret" -n "$NAMESPACE" -o jsonpath='{.data.encryption-key}' >/dev/null 2>&1; then
                        log "  ✓ encryption-key exists"
                    else
                        error "  ✗ encryption-key missing"
                        ((errors++))
                    fi
                    ;;
                "openai-secret"|"anthropic-secret"|"gemini-secret")
                    if kubectl get secret "$secret" -n "$NAMESPACE" -o jsonpath='{.data.api-key}' >/dev/null 2>&1; then
                        log "  ✓ api-key exists"
                    else
                        error "  ✗ api-key missing"
                        ((errors++))
                    fi
                    ;;
                "database-secret")
                    if kubectl get secret "$secret" -n "$NAMESPACE" -o jsonpath='{.data.url}' >/dev/null 2>&1; then
                        log "  ✓ url exists"
                    else
                        error "  ✗ url missing"
                        ((errors++))
                    fi
                    ;;
                "litellm-secret")
                    if kubectl get secret "$secret" -n "$NAMESPACE" -o jsonpath='{.data.master-key}' >/dev/null 2>&1; then
                        log "  ✓ master-key exists"
                    else
                        error "  ✗ master-key missing"
                        ((errors++))
                    fi
                    ;;
            esac
        else
            error "✗ Secret $secret not found"
            ((errors++))
        fi
    done
    
    if [[ $errors -gt 0 ]]; then
        error "Validation failed. $errors secrets or keys are missing."
        exit 1
    else
        log "All secrets validated successfully"
    fi
}

# Show usage
usage() {
    cat << EOF
Usage: $0 [COMMAND]

Commands:
  create     Create or update all secrets from .env file
  list       List all secrets
  delete     Delete all secrets
  validate   Validate that all required secrets exist
  help       Show this help message

Examples:
  $0 create     # Create/update secrets from .env
  $0 list       # List all secrets
  $0 validate   # Check if all secrets exist
  $0 delete     # Delete all secrets

Environment:
  Reads from .env file in the current directory
  Uses namespace: $NAMESPACE

EOF
}

# Main function
main() {
    local command="${1:-help}"
    
    case "$command" in
        create)
            check_kubectl
            load_env
            check_namespace
            create_all_secrets
            ;;
        list)
            check_kubectl
            list_secrets
            ;;
        delete)
            check_kubectl
            delete_secrets
            ;;
        validate)
            check_kubectl
            validate_secrets
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            error "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"