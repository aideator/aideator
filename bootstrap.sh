#!/bin/bash
set -euo pipefail

# AIdeator Bootstrap Script
# Sets up the complete development environment

echo "🚀 AIdeator Development Setup"
echo "=============================="

# Install nix if not present
if ! command -v nix &> /dev/null; then
    echo "📦 Installing Nix..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sh <(curl -L https://nixos.org/nix/install)
    else
        # Linux
        sh <(curl -L https://nixos.org/nix/install) --daemon
    fi
    
    # Source nix
    if [ -e '/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh' ]; then
        . '/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh'
    elif [ -e "$HOME/.nix-profile/etc/profile.d/nix.sh" ]; then
        . "$HOME/.nix-profile/etc/profile.d/nix.sh"
    fi
    
    echo "✅ Nix installed"
else
    echo "✅ Nix already installed"
fi

# Install direnv if not present
if ! command -v direnv &> /dev/null; then
    echo "📦 Installing direnv..."
    if command -v nix-env &> /dev/null; then
        nix-env -iA nixpkgs.direnv
    elif command -v brew &> /dev/null; then
        brew install direnv
    else
        echo "⚠️  Please install direnv manually: https://direnv.net/docs/installation.html"
    fi
    
    # Add direnv hook to shell (idempotent)
    SHELL_NAME=$(basename "$SHELL")
    HOOK_COMMAND=""
    RC_FILE=""
    
    case "$SHELL_NAME" in
        bash)
            HOOK_COMMAND='eval "$(direnv hook bash)"'
            RC_FILE="$HOME/.bashrc"
            ;;
        zsh)
            HOOK_COMMAND='eval "$(direnv hook zsh)"'
            RC_FILE="$HOME/.zshrc"
            ;;
        fish)
            HOOK_COMMAND='direnv hook fish | source'
            RC_FILE="$HOME/.config/fish/config.fish"
            ;;
    esac
    
    # Only add if not already present
    if [ -n "$RC_FILE" ] && [ -f "$RC_FILE" ]; then
        if ! grep -q "direnv hook" "$RC_FILE"; then
            echo "$HOOK_COMMAND" >> "$RC_FILE"
            echo "✅ direnv hook added to $RC_FILE (restart your shell or source your rc file)"
        fi
    fi
else
    echo "✅ direnv already installed"
fi

# Enable direnv for this project
if [ -f .envrc ]; then
    echo "🔧 Enabling direnv for this project..."
    direnv allow .
    eval "$(direnv export bash)"
fi

# Check for required tools
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "❌ $1 is not installed. Please install it first."
        echo "   Visit: $2"
        exit 1
    fi
}

echo "📋 Checking prerequisites..."
check_command "docker" "https://docs.docker.com/get-docker/"
check_command "kubectl" "https://kubernetes.io/docs/tasks/tools/"
check_command "helm" "https://helm.sh/docs/intro/install/"
check_command "tilt" "https://docs.tilt.dev/install.html"
check_command "k3d" "https://k3d.io/v5.6.0/#installation"
check_command "npm" "https://nodejs.org/"

# Create k3d cluster if it doesn't exist
if ! k3d cluster list | grep -q "k3d-aideator"; then
    echo "🔧 Creating k3d cluster with registry..."
    
    # Check if ctlptl-registry exists
    if k3d registry list | grep -q "ctlptl-registry"; then
        echo "📦 Found existing ctlptl-registry, using it..."
        k3d cluster create aideator --registry-use ctlptl-registry:5005
    else
        echo "📦 Creating new aideator-registry..."
        k3d cluster create aideator --registry-create aideator-registry:0.0.0.0:5005
    fi
else
    echo "✅ k3d cluster already exists"
fi

# Set kubectl context
echo "🔧 Setting kubectl context..."
kubectl config use-context k3d-aideator

# Check for .env file or create one
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
    echo "   Then run this script again."
    echo ""
    exit 1
fi

# Load .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check for required API key
if [ -z "${OPENAI_API_KEY:-}" ] || [ "${OPENAI_API_KEY}" = "your-anthropic-api-key-here" ]; then
    echo "❌ OPENAI_API_KEY not set in .env file"
    echo "   Please edit .env and add your Anthropic API key"
    exit 1
fi

# Create namespace if it doesn't exist
if ! kubectl get namespace aideator &> /dev/null; then
    echo "🔧 Creating aideator namespace..."
    kubectl create namespace aideator
fi

# Create secrets if they don't exist
if ! kubectl get secret openai-secret -n aideator &> /dev/null; then
    if [ -n "${OPENAI_API_KEY:-}" ]; then
        echo "🔧 Creating openai-secret..."
        kubectl create secret generic openai-secret \
            --from-literal=api-key="$OPENAI_API_KEY" \
            -n aideator
    else
        echo "⚠️  Skipping openai-secret creation (OPENAI_API_KEY not set)"
    fi
else
    echo "✅ openai-secret already exists"
fi

if ! kubectl get secret aideator-secret -n aideator &> /dev/null; then
    echo "🔧 Creating aideator-secret..."
    kubectl create secret generic aideator-secret \
        --from-literal=secret-key="$(openssl rand -hex 32)" \
        -n aideator
else
    echo "✅ aideator-secret already exists"
fi

# Install frontend dependencies (only if needed)
echo "📦 Checking frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
else
    echo "✅ Frontend dependencies up to date"
fi
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start development, run:"
echo "   tilt up"
echo ""
echo "This will start:"
echo "   ✓ Kubernetes cluster"
echo "   ✓ FastAPI backend with hot reload"
echo "   ✓ Frontend with hot reload"
echo "   ✓ Agent containers"
echo ""
echo "📍 Services will be available at:"
echo "   Frontend:  http://localhost:3000 (or next available port)"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   Tilt UI:   http://localhost:10350"
echo ""
echo "💡 Note: If port 3000 is busy, Tilt will automatically find the next available port"
echo ""
echo "🔧 Troubleshooting:"
echo "   Module resolution errors? Try:"
echo "     cd frontend && rm -rf .next node_modules && npm install"
echo "     tilt up"