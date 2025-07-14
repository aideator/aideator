# DevSwarm (FKA `DevSwarm`) 🚀

**Multi-Agent AI Orchestration Platform** - Run multiple AI agents in parallel, compare their outputs, and select the best solution.

![Architecture](https://img.shields.io/badge/Architecture-Kubernetes%20Native-blue)
![Frontend](https://img.shields.io/badge/Frontend-Next.js%2015-black)
![Backend](https://img.shields.io/badge/Backend-FastAPI-green)

## What is DevSwarm?

DevSwarm runs multiple AI agents simultaneously in isolated Kubernetes containers, streaming their thought processes in real-time via WebSocket + Redis Streams. Compare different approaches in a tabbed interface and select the best solution.

## Quick Start

### Prerequisites (will be installed by ./bootstrap.sh if not already installed)
- [docker](https://www.docker.com/)
- [k3d](https://k3d.io/stable/)
- [ctlptl](https://github.com/tilt-dev/ctlptl)
- [helm](https://helm.sh/)

Developers additionally will need a Node.js (via npm or bun etc) or Python runtime (via uv) if they want to run test suites.


> **Note**: The setup uses `ctlptl` for local registry management. If you already have a k3d cluster or ctlptl registry, the bootstrap script will reuse them.

> **Nix Users**: See [docs/nix-guide.md](docs/nix-guide.md) for a declarative development environment setup.

### Setup & Run

```bash
# Clone the repo
git clone https://github.com/yourusername/devswarm.git
cd devswarm

# Run bootstrap (creates .env, installs dependencies)
./bootstrap.sh

# Start development
tilt up
```

That's it! The bootstrap script will:
- Check for required tools and provide installation instructions
- Create the Kubernetes cluster using ctlptl
- Set up environment variables and secrets
- Install frontend and Python dependencies

### Services

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Tilt UI**: http://localhost:10350

## Usage

1. Open http://localhost:3000
2. Enter a GitHub repository URL and prompt
3. Choose number of agents (1-5)
4. Watch agents work in real-time
5. Select the best solution

## Development

```bash
# Backend + Kubernetes (with hot reload)
tilt up

# Frontend (in separate terminal)
cd frontend && npm run dev

# Run tests
uv run test-all             # Backend tests
cd frontend && npm test:all # Frontend tests

# Stop everything
tilt down
```

## Troubleshooting

### Registry Issues

If you encounter "image not found" errors:

1. **Ensure images are built and pushed**:
   ```bash
   # Tilt should handle this automatically when you run 'tilt up'
   # If you see "image not found" errors, you may need to:
   
   # Option 1: Let Tilt build everything (recommended)
   tilt up
   
   # Option 2: Manually build and tag if Tilt uses dynamic tags
   docker build -t localhost:5005/DevSwarm-api:dev --target api .
   docker push localhost:5005/DevSwarm-api:dev
   
   docker build -t localhost:5005/DevSwarm-agent:dev --target agent .
   docker push localhost:5005/DevSwarm-agent:dev
   ```

2. **Verify registry is running**:
   ```bash
   docker ps | grep ctlptl-registry
   ```

3. **Check registry contents**:
   ```bash
   curl http://localhost:5005/v2/_catalog
   ```

4. **Fix missing :dev tags**:
   ```bash
   # If agent jobs fail with "image not found", run:
   ./scripts/fix-registry-tags.sh
   ```

5. **Reset everything**:
   ```bash
   k3d cluster delete DevSwarm
   docker rm -f ctlptl-registry
   ./bootstrap.sh
   tilt up
   ```

### Known Issues

- **Tilt uses dynamic tags**: Tilt builds images with tags like `tilt-abc123...` but the job templates expect `:dev` tags. The Tiltfile includes a `tag-dev-images` resource that automatically creates these tags, but if it fails, run `./scripts/fix-registry-tags.sh`.

## Architecture

See [architecture.md](_docs/architecture.md) for detailed technical documentation.

## Key Features

- 🔄 **Parallel Execution** - Run 1-5 agents simultaneously
- 📡 **Real-time Streaming** - Watch agent thoughts via WebSocket + Redis Streams
- 🎯 **Tabbed Comparison** - Compare outputs in focused tabbed interface
- 💾 **Dual Persistence** - Real-time streaming + PostgreSQL history
- ☁️ **Cloud-Native** - Kubernetes Jobs with automatic cleanup
- 🔧 **Developer-Friendly** - Hot reload with Tilt

## License

MIT License - see [LICENSE](LICENSE) file for details.