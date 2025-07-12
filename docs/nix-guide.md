# Nix Development Environment Guide

This guide provides instructions for setting up AIdeator using Nix and direnv for a declarative development environment.

## Prerequisites

- [Nix](https://nixos.org/download.html) (with flakes enabled)
- [direnv](https://direnv.net/docs/installation.html)
- [nix-direnv](https://github.com/nix-community/nix-direnv)

## Installation

### 1. Install Nix

**macOS:**
```bash
curl -L https://nixos.org/nix/install | sh
```

**Linux:**
```bash
curl -L https://nixos.org/nix/install | sh
```

### 2. Enable Flakes

Add to your `~/.config/nix/nix.conf` (create if it doesn't exist):
```
experimental-features = nix-command flakes
```

### 3. Install direnv

**macOS:**
```bash
brew install direnv
```

**Linux:**
```bash
# Using your package manager, e.g.:
sudo apt install direnv      # Ubuntu/Debian
sudo dnf install direnv      # Fedora
sudo pacman -S direnv        # Arch
```

### 4. Configure direnv

Add to your shell profile (`.bashrc`, `.zshrc`, etc.):
```bash
eval "$(direnv hook bash)"    # For bash
eval "$(direnv hook zsh)"     # For zsh
```

### 5. Install nix-direnv

```bash
nix profile install nixpkgs#nix-direnv
```

Then add to your `~/.config/direnv/direnvrc`:
```bash
source_url "https://raw.githubusercontent.com/nix-community/nix-direnv/master/direnvrc" "sha256-0123456789abcdef"
```

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/aideator.git
   cd aideator
   ```

2. **Enable direnv:**
   ```bash
   direnv allow
   ```
   
   This will automatically install all development dependencies via Nix.

3. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Create cluster:**
   ```bash
   ctlptl apply -f deploy/k3d/aideator-cluster.yaml
   ```

5. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

6. **Install Python dependencies:**
   ```bash
   pip install -e .
   ```

## Development Workflow

Once set up, the development workflow is identical to the standard setup:

```bash
# Start development environment
tilt up

# In another terminal, view logs
tilt logs

# Stop environment
tilt down
```

## Available Tools

The Nix environment provides all necessary tools:

- **Container & Kubernetes:** Docker, k3d, kubectl, helm, ctlptl
- **Development:** tilt, git, direnv
- **Languages:** python3, node, npm
- **Utilities:** jq, curl, age, sops

## Troubleshooting

### direnv not loading

If direnv isn't automatically loading the environment:

1. Check if direnv is properly hooked in your shell
2. Run `direnv allow` in the project directory
3. Try `direnv reload`

### Nix build failures

If you encounter build failures:

1. Try updating your Nix channel:
   ```bash
   nix-channel --update
   ```

2. Clean the Nix store:
   ```bash
   nix-collect-garbage -d
   ```

3. Rebuild the environment:
   ```bash
   direnv reload
   ```

### Missing flake.lock

If you get errors about missing `flake.lock`:

```bash
nix flake update
```

## Advantages of Nix Setup

- **Reproducible:** Same environment across all machines
- **Isolated:** No conflicts with system packages
- **Declarative:** Environment defined in `flake.nix`
- **Automatic:** direnv loads environment when entering directory
- **Version pinning:** Exact versions of all tools

## Switching Back to Standard Setup

To switch back to the standard setup:

1. Remove the `.envrc` file
2. Follow the standard installation instructions in the main README
3. Use `./bootstrap.sh` instead of the Nix workflow

## Additional Resources

- [Nix Manual](https://nixos.org/manual/nix/stable/)
- [Nix Flakes Documentation](https://nixos.wiki/wiki/Flakes)
- [direnv Documentation](https://direnv.net/docs/)
- [nix-direnv GitHub](https://github.com/nix-community/nix-direnv)

Ready to develop with Nix, you are! 🧘