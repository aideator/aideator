# AIdeator Agent Refactoring PRD

## Overview
Refactor the monolithic `main.py` into a modular, pipeline-based architecture that supports multiple job types and standardized output handling.

## Current State vs Target State

### **Current**: Single monolithic agent
- One massive `AIdeatorAgent` class (1400+ lines)
- Mixed responsibilities (config, analysis, LLM calls, streaming)
- Redis streaming + database persistence
- Inconsistent output types

### **Target**: Modular pipeline architecture
- Clean separation of concerns
- Standardized provider interface
- Database-first approach (Redis removal planned)
- Clear job type taxonomy

## Job Pipeline Architecture

### **3-Stage Pipeline**
1. **Stage 1: Main Agent** (`main.py`)
   - LiteLLM, Claude CLI, or Gemini CLI execution
   - Output type: `job_data` 
   - Frontend mapping: **Logs tab**

2. **Stage 2: File Analysis** (future job)
   - File system cleanup and diff generation
   - Output type: `diff`
   - Frontend mapping: **Diffs tab**

3. **Stage 3: Summary Generation** (future job)  
   - Final summary and analysis
   - Output type: `summary`
   - Frontend mapping: **Summary tab**

4. **Cross-cutting: Error Handling**
   - Traditional logging and errors
   - Output type: `error`
   - Frontend mapping: **Errors tab**

## Output Type Taxonomy

| Current Type | New Type | Frontend Tab | Purpose |
|-------------|----------|--------------|---------|
| `logging` | `job_data` | Logs | Main LLM responses |
| `stdout` | `job_data` | Logs | Command output |
| TBD | `diff` | Diffs | File system changes |
| TBD | `summary` | Summary | Final analysis |
| `stderr` | `error` | Errors | Error messages |

## Modular Structure

```
agent/
├── main.py                    # Slim orchestrator (maintains compatibility)
├── main_wrapper.py            # Keep unchanged
├── core/
│   ├── orchestrator.py        # Coordinates services, replaces AIdeatorAgent logic
│   └── pipeline.py            # Job pipeline management
├── config/
│   ├── settings.py            # Environment parsing & validation
│   └── providers.py           # API key management
├── providers/
│   ├── base.py               # Standardized interface
│   ├── litellm.py            # All return "job_data" type
│   ├── claude_cli.py         # All return "job_data" type  
│   └── gemini_cli.py         # All return "job_data" type
├── analyzers/
│   ├── repository.py         # Git operations
│   └── codebase.py          # Code analysis
├── services/
│   ├── database_service.py   # Enhanced, database-first
│   ├── redis.py             # Isolated for easy removal
│   └── output_writer.py     # Standardized output handling
└── utils/
    ├── errors.py            # Centralized error handling
    └── files.py             # File utilities
```

## Design Decisions

### **Configuration Priority**
1. **Environment variables** (highest priority)
2. **API keys** (direct provider keys)
3. **LiteLLM Gateway** (lowest, will be removed)

### **Provider Interface Standardization**
```python
class BaseProvider:
    async def generate_response(self, prompt: str, context: str = None) -> str:
        """All providers return job_data content."""
        pass
```

### **Database-First Architecture**
- **Primary**: All outputs go to `agent_outputs` table
- **Redis**: Isolated service, easily removable
- **Async Management**: Simple context manager pattern

### **Error Handling Strategy**
- **Centralized**: All error formatting in `utils/errors.py`
- **User-friendly**: Maintain current helpful error messages
- **Consistent**: Same error output format across providers

## Implementation Strategy

### **Phase 1: Structure Creation**
- Create modular directory structure
- Extract configuration management
- Implement standardized provider interface

### **Phase 2: Service Extraction**  
- Isolate Redis service (for easy removal)
- Enhance database service
- Centralize error handling

### **Phase 3: Provider Standardization**
- Refactor LiteLLM, Claude CLI, Gemini CLI
- All providers output `job_data` type
- Consistent streaming patterns

### **Phase 4: Integration & Testing**
- Slim down `main.py` to orchestrator
- Maintain `AIdeatorAgent` interface compatibility
- Verify Kubernetes execution

## Complexity Reduction Proposals

### **Async Context Management**
**Proposal**: Simple service manager pattern
```python
class ServiceManager:
    async def __aenter__(self):
        self.db = await DatabaseService.connect()
        return self
    
    async def __aexit__(self, *args):
        await self.db.close()
```

### **Configuration Simplification**
**Proposal**: Single config object with clear precedence
```python
@dataclass
class AgentConfig:
    model: str
    temperature: float
    database_url: str
    # Auto-populated from env vars with fallbacks
```

### **Provider Simplification**
**Proposal**: Remove complex streaming variations, standardize on simple text output
- All providers return plain text
- Output formatting handled by `OutputWriter`
- Consistent error handling across providers

## Success Criteria
- [ ] External interfaces unchanged (Kubernetes, tests work)
- [ ] Clean separation of concerns (each module <200 lines)
- [ ] Redis easily removable (isolated to one service)
- [ ] Standardized output types (`job_data`, `diff`, `summary`, `error`)
- [ ] Centralized configuration and error handling
- [ ] Database-first architecture (no Redis dependencies)

*Clear the path forward, this plan does.*