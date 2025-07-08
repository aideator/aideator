# Claude Code Integration

AIdeator now supports running Claude Code CLI in containerized environments via Dagger. This allows you to execute Claude Code on cloned repositories with specific prompts.

## Features

- ✅ Automatic Claude Code CLI installation in containers
- ✅ Repository cloning and analysis
- ✅ Real-time output streaming via SSE
- ✅ Parallel execution of multiple variations
- ✅ Full API integration

## Usage

### Via API

To run Claude Code on a repository, make a POST request to `/api/v1/runs` with the `use_claude_code` flag:

```json
{
  "github_url": "https://github.com/fastapi/fastapi",
  "prompt": "Add comprehensive docstrings to all functions in main.py",
  "variations": 1,
  "use_claude_code": true
}
```

### Via Dagger CLI

You can also run Claude Code directly using the Dagger module:

```bash
# Run Claude Code on a repository
dagger call \
  -m ./dagger_module \
  run-claude-code \
  --repo-url "https://github.com/fastapi/fastapi" \
  --prompt "Add docstrings to main.py" \
  --anthropic-api-key env:ANTHROPIC_API_KEY
```

### Testing the Integration

A test endpoint is available at `/api/v1/test/test-claude-code`:

```bash
curl -X POST http://localhost:8000/api/v1/test/test-claude-code \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/fastapi/fastapi",
    "prompt": "Add docstrings to main.py"
  }'
```

## Implementation Details

### Container Setup

- Base image: `node:20-slim` (for npm support)
- Includes: Python 3, pip, git, ripgrep, Claude Code CLI
- Memory: 2GB default (configurable)
- CPU: 2.0 cores default (configurable)

### Agent Script

The `claude_code_agent.py` script:
1. Lists repository contents for context
2. Launches Claude Code CLI with the provided prompt
3. Streams output line by line with variation ID prefix
4. Handles errors and retries

### API Integration

- New field `use_claude_code` in `CreateRunRequest` schema
- Orchestrator passes flag to Dagger module service
- Dagger module conditionally runs Claude Code agent

## Configuration

Set these environment variables:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-...

# Optional
DEFAULT_AGENT_MODEL=claude-3-5-sonnet-20241022
AGENT_MEMORY_LIMIT=2g
AGENT_CPU_LIMIT=2.0
```

## Limitations

- Claude Code requires more resources than basic Claude API
- Container startup time is slightly longer due to npm installation
- Output format differs from basic agent (includes Claude Code formatting)

## Future Improvements

- [ ] Add support for Claude Code configuration options
- [ ] Implement caching for faster container startup
- [ ] Add Claude Code-specific output parsing
- [ ] Support for interactive mode (if feasible)