# AIdeator 🚀

**Multi-Agent AI Orchestration Platform** - Run multiple AI agents in parallel, compare their outputs, and select the best solution.

![Architecture](https://img.shields.io/badge/Architecture-Kubernetes%20Native-blue)
![Frontend](https://img.shields.io/badge/Frontend-Next.js%2015-black)
![Backend](https://img.shields.io/badge/Backend-FastAPI-green)

## What is AIdeator?

AIdeator runs multiple AI agents simultaneously in isolated Kubernetes containers, streaming their thought processes in real-time. Watch agents work side-by-side, compare different approaches, and select the best solution.

## Quick Start

### Prerequisites
- Docker (required)
- Anthropic API key

Everything else will be installed automatically!

### Setup & Run

```bash
# Clone the repo
git clone https://github.com/yourusername/aideator.git
cd aideator

# Run bootstrap (creates .env, installs dependencies)
./bootstrap.sh

# Edit .env with your API key
# Then run bootstrap again
./bootstrap.sh

# Start development
tilt up
```

That's it! The bootstrap script will:
- Install nix and direnv if needed
- Install kubectl, helm, tilt, k3d via nix
- Create the Kubernetes cluster
- Set up secrets
- Install frontend dependencies

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
pytest                    # Backend tests
cd frontend && npm test   # Frontend tests

# Stop everything
tilt down
```

## Architecture

See [architecture.md](./architecture.md) for detailed technical documentation.

## Key Features

- 🔄 **Parallel Execution** - Run 1-5 agents simultaneously
- 📡 **Real-time Streaming** - Watch agent thoughts via Server-Sent Events
- 🎯 **Side-by-Side Comparison** - Compare outputs in responsive grid
- ☁️ **Cloud-Native** - Kubernetes Jobs with automatic cleanup
- 🔧 **Developer-Friendly** - Hot reload with Tilt

## License

MIT License - see [LICENSE](LICENSE) file for details.