#!/bin/bash

# AIdeator Bootstrap Script
# Sets up the development environment for AIdeator

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if running on supported platform
check_platform() {
    case "$(uname -s)" in
        Darwin*)
            PLATFORM="macos"
            ;;
        Linux*)
            PLATFORM="linux"
            ;;
        *)
            error "Unsupported platform: $(uname -s)"
            exit 1
            ;;
    esac
    log "Detected platform: $PLATFORM"
}

# Check required tools
check_dependencies() {
    log "Checking dependencies..."
    
    local missing_tools=()
    
    # Core tools
    if ! command_exists docker; then
        missing_tools+=("docker")
    fi
    
    if ! command_exists kubectl; then
        missing_tools+=("kubectl")
    fi
    
    if ! command_exists tilt; then
        missing_tools+=("tilt")
    fi
    
    if ! command_exists ctlptl; then
        missing_tools+=("ctlptl")
    fi
    
    if ! command_exists helm; then
        missing_tools+=("helm")
    fi
    
    if ! command_exists node; then
        missing_tools+=("node")
    fi
    
    if ! command_exists python3; then
        missing_tools+=("python3")
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        error "Missing required tools: ${missing_tools[*]}"
        echo
        echo "Install missing tools:"
        echo
        
        if [[ "$PLATFORM" == "macos" ]]; then
            echo "Using Homebrew:"
            for tool in "${missing_tools[@]}"; do
                case "$tool" in
                    docker)
                        echo "  brew install --cask docker"
                        ;;
                    kubectl)
                        echo "  brew install kubectl"
                        ;;
                    tilt)
                        echo "  brew install tilt"
                        ;;
                    ctlptl)
                        echo "  brew install ctlptl"
                        ;;
                    helm)
                        echo "  brew install helm"
                        ;;
                    node)
                        echo "  brew install node"
                        ;;
                    python3)
                        echo "  brew install python3"
                        ;;
                esac
            done
        else
            echo "Using standard package managers or official installers"
            echo "See: https://docs.docker.com/get-docker/"
            echo "See: https://kubernetes.io/docs/tasks/tools/install-kubectl/"
            echo "See: https://tilt.dev/getting_started/"
            echo "See: https://github.com/tilt-dev/ctlptl#installation"
            echo "See: https://helm.sh/docs/intro/install/"
            echo "See: https://nodejs.org/en/download/"
        fi
        
        echo
        echo "Or use Nix (see docs/nix-guide.md for instructions)"
        exit 1
    fi
    
    log "All dependencies are installed"
}

# Setup environment file
setup_env() {
    log "Setting up environment..."
    
    if [[ ! -f .env ]]; then
        if [[ -f .env.example ]]; then
            cp .env.example .env
            log "Created .env file from .env.example"
        else
            cat > .env << 'EOF'
# AIdeator Environment Configuration
# Copy this file to .env and update with your values

# Application settings (required)
SECRET_KEY=""
ENCRYPTION_KEY=""
DEBUG=true
LOG_LEVEL=INFO

# Database
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/aideator"

# Redis
REDIS_URL="redis://localhost:6379"

# Frontend
NEXT_PUBLIC_API_URL="http://localhost:8000"

# AI Provider API Keys (optional - configure via your preferred method)
# OPENAI_API_KEY=""
# ANTHROPIC_API_KEY=""
# GEMINI_API_KEY=""
EOF
            log "Created .env file with defaults"
        fi
    else
        log ".env file already exists"
    fi
    
    # Generate secret key if not set
    if grep -q '^SECRET_KEY=""' .env; then
        SECRET_KEY=$(openssl rand -hex 32)
        if [[ "$PLATFORM" == "macos" ]]; then
            sed -i '' "s/^SECRET_KEY=\"\"/SECRET_KEY=\"$SECRET_KEY\"/" .env
        else
            sed -i "s/^SECRET_KEY=\"\"/SECRET_KEY=\"$SECRET_KEY\"/" .env
        fi
        log "Generated SECRET_KEY"
    fi
    
    # Generate encryption key if not set
    if grep -q '^ENCRYPTION_KEY=""' .env; then
        ENCRYPTION_KEY=$(openssl rand -hex 32)
        if [[ "$PLATFORM" == "macos" ]]; then
            sed -i '' "s/^ENCRYPTION_KEY=\"\"/ENCRYPTION_KEY=\"$ENCRYPTION_KEY\"/" .env
        else
            sed -i "s/^ENCRYPTION_KEY=\"\"/ENCRYPTION_KEY=\"$ENCRYPTION_KEY\"/" .env
        fi
        log "Generated ENCRYPTION_KEY"
    fi
}

# Create cluster using ctlptl
create_cluster() {
    log "Creating Kubernetes cluster..."
    
    # Temporarily disable k3d debug output
    local OLD_LOG_LEVEL="${LOG_LEVEL}"
    unset LOG_LEVEL
    export K3D_LOG_LEVEL=WARN
    
    if ! ctlptl get cluster k3d-aideator >/dev/null 2>&1; then
        log "Creating ctlptl cluster from config..."
        ctlptl apply -f deploy/k3d/aideator-cluster.yaml
    else
        log "Cluster 'k3d-aideator' already exists"
    fi
    
    # Restore log level
    if [[ -n "${OLD_LOG_LEVEL}" ]]; then
        export LOG_LEVEL="${OLD_LOG_LEVEL}"
    fi
    
    # Wait for cluster to be ready
    log "Waiting for cluster to be ready..."
    kubectl wait --for=condition=Ready nodes --all --timeout=300s
    
    log "Cluster is ready"
}

# Install frontend dependencies
setup_frontend() {
    log "Setting up frontend dependencies..."
    
    cd frontend
    
    if [[ ! -d node_modules ]]; then
        log "Installing npm dependencies..."
        npm install
    else
        log "npm dependencies already installed"
    fi
    
    cd ..
}

# Install Python dependencies
setup_python() {
    log "Setting up Python dependencies..."
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d .venv ]]; then
        log "Creating Python virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment and install in editable mode
    source .venv/bin/activate
    
    # Use uv if available, otherwise fall back to pip
    if command -v uv &> /dev/null && [ -f .venv/bin/python ]; then
        log "Using uv to install dependencies"
        uv pip install -e .
    else
        log "Using pip to install dependencies"
        pip install -e .
    fi
    
    log "Python dependencies installed"
}

# Main setup function
main() {
    echo "🚀 AIdeator Bootstrap Script"
    echo "============================"
    echo
    
    check_platform
    check_dependencies
    setup_env
    create_cluster
    setup_frontend
    setup_python
    
    echo
    echo "🎉 Bootstrap complete!"
    echo
    echo "Next steps:"
    echo "1. Update .env with your API keys"
    echo "2. Run: tilt up"
    echo "3. Open http://localhost:8000 in your browser"
    echo
    echo "For Nix users, see docs/nix-guide.md"
    echo "Ready to code, you are! 🧘"
}

# Run main function
main "$@"