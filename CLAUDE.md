# AIdeator - Instructions for Claude

## Project Overview

AIdeator is a **Multi-Model Prompt Comparison Platform** that leverages Kubernetes for parallel model execution and LiteLLM Gateway for unified API access and analytics. The platform allows users to run the same prompt across multiple AI models simultaneously, compare their responses side-by-side, and track preferences to learn which models work best for different use cases. By combining Kubernetes Jobs for isolated parallel execution with LiteLLM Gateway for observability, we achieve both scalability and rich analytics. As the primary coding assistant, I help build a sophisticated FastAPI + Kubernetes backend and Next.js 15 frontend that orchestrates containerized model comparisons and delivers real-time insights through Server-Sent Events.

## 🎯 My Role & Capabilities

I am the **primary development assistant** for AIdeator full-stack development. I provide:

- **Production-Ready Code**: No mock data, proper async patterns, comprehensive error handling
- **FastAPI Expertise**: Async route handlers, SSE streaming, proper dependency injection
- **Next.js 15 Frontend**: Modern React 19 with TypeScript 5, Tailwind CSS v4, responsive design, real-time streaming
- **Design System**: Cohesive UI components with AIdeator branding using Tailwind CSS v4 and accessibility
- **Kubernetes Integration**: Job orchestration, kubectl log streaming, Helm charts
- **Real-time Streaming**: Server-Sent Events powered by native Kubernetes logs
- **Cloud-Native Patterns**: Tilt development, local registries, declarative deployments
- **Security First**: RBAC, secret management, resource limits, SQL injection prevention

## 🏗️ Architecture Understanding

### Core Components

- **FastAPI Backend** - Async web framework running as a Kubernetes deployment
- **Next.js 15.2.4 Frontend** - Modern React 19.0.0 frontend with TypeScript 5 and real-time streaming
- **Tailwind CSS v4.1.11** - Utility-first CSS framework with @tailwindcss/postcss v4
- **Kubernetes Jobs** - Isolated parallel model execution with automatic cleanup (TTL)
- **LiteLLM Gateway** - Unified API interface for 100+ LLMs with built-in analytics
- **kubectl Logs** - Native log streaming from agent containers
- **Server-Sent Events (SSE)** - Real-time streaming of model responses
- **PostgreSQL + SQLModel** - Production database with async ORM for sessions and preferences
- **LiteLLM Library** - Unified interface for OpenAI, Anthropic, and other model providers
- **Helm Charts** - Declarative deployment and configuration management
- **AIdeator Design System** - Cohesive UI components and styling patterns using Tailwind CSS v4

### Hybrid Architecture: Kubernetes + LiteLLM Gateway

The architecture combines Kubernetes orchestration with LiteLLM Gateway analytics:

#### Kubernetes Layer (Orchestration)
- **Pods & Jobs**: Each model comparison runs as parallel Kubernetes Jobs
- **Service Accounts**: RBAC for kubectl operations
- **ConfigMaps & Secrets**: Configuration and encrypted API key management
- **Local Registry**: Development with localhost:5005
- **Tilt**: Streamlined local development workflow

#### LiteLLM Gateway Layer (Analytics & API)
- **Unified API**: Single interface for 100+ model providers
- **Built-in Analytics**: Response times, token usage, cost tracking
- **Prometheus Metrics**: Production-grade observability
- **Rate Limiting**: Per-user and per-model controls
- **Caching**: Redis-backed response caching
- **Automatic Retries**: Resilient model calls with fallbacks

### Key Workflows

1. **Multi-Model Comparison Flow**
   - User submits prompt → API creates N Kubernetes Jobs (one per model)
   - Each Job calls LiteLLM Gateway → Gateway routes to appropriate provider
   - Gateway collects metrics → Streams responses back through Jobs
   - Jobs stream logs via kubectl → SSE aggregates to client
   - Client displays side-by-side comparison → User selects preference

2. **Parallel Execution Architecture**
   ```
   User Request → FastAPI → Kubernetes Jobs (Parallel)
                               ├── Job 1: GPT-4 → LiteLLM Gateway → OpenAI
                               ├── Job 2: Claude → LiteLLM Gateway → Anthropic
                               └── Job 3: Gemini → LiteLLM Gateway → Google
   ```

3. **Analytics Pipeline**
   - LiteLLM Gateway tracks: latency, tokens, costs, errors
   - Prometheus exports metrics → Grafana dashboards
   - PostgreSQL stores: preferences, sessions, user choices
   - Real-time metrics displayed during comparison

4. **Development** → Tilt up → Hot reload → Port forwarding (automatic)

### Hybrid Integration Architecture

```python
# FastAPI service orchestrates parallel model comparisons
class ModelComparisonService:
    def __init__(self, k8s_service: KubernetesService):
        self.k8s = k8s_service
        
    async def compare_models(
        self,
        run_id: str,
        prompt: str,
        models: List[str] = ["gpt-4", "claude-3", "gemini-pro"]
    ):
        # Create parallel jobs for each model
        jobs = []
        for idx, model in enumerate(models):
            job_name = await self.k8s.create_model_job(
                run_id=run_id,
                model_id=idx,
                model_name=model,
                prompt=prompt
            )
            jobs.append((job_name, idx, model))
        
        # Stream all outputs in parallel
        tasks = [
            self._stream_model_output(run_id, job_name, model_id, model)
            for job_name, model_id, model in jobs
        ]
        await asyncio.gather(*tasks)

# Agent container calls LiteLLM Gateway
async def call_model_via_gateway(prompt: str, model: str):
    # Point to internal LiteLLM Gateway service
    response = await litellm.acompletion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        api_base="http://litellm-gateway:4000",  # Kubernetes service
        api_key=os.environ["LITELLM_API_KEY"],
        stream=True
    )
    
    # Stream response and let gateway handle analytics
    async for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end='', flush=True)
```

### LiteLLM Gateway Configuration

```yaml
# LiteLLM Gateway config.yaml
model_list:
  - model_name: gpt-4
    litellm_params:
      model: openai/gpt-4
      api_key: os.environ/OPENAI_API_KEY
  - model_name: claude-3
    litellm_params:
      model: anthropic/claude-3-opus-20240229
      api_key: os.environ/ANTHROPIC_API_KEY
  - model_name: gemini-pro
    litellm_params:
      model: vertex_ai/gemini-pro
      vertex_project: os.environ/GCP_PROJECT_ID
      vertex_location: us-central1

litellm_settings:
  callbacks: ["prometheus"]  # Enable metrics export
  cache: true
  cache_params:
    type: redis
    host: redis-service
    port: 6379
  success_callback: ["langfuse"]  # Optional: external observability
  
general_settings:
  completion_model: gpt-4  # Default model
  disable_spend_logs: false  # Track costs
  master_key: os.environ/LITELLM_MASTER_KEY
```

## 🚀 Development Commands

### Local Development with Tilt

```bash
# Start development environment
tilt up

# This will:
# 1. Start/verify k3d cluster
# 2. Build containers locally
# 3. Push to local registry (localhost:5005)
# 4. Deploy via Helm
# 5. Set up port forwarding
# 6. Watch for file changes

# Access services
# FastAPI: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Tilt UI: http://localhost:10350

# Stop environment
tilt down

# Delete namespace too
tilt down --delete-namespaces
```

### Development Testing with Tilt

```bash
# The Helm chart deploys an agent-job-dev-test with defaults:
# - Repository: https://github.com/octocat/Hello-World
# - Prompt: "Analyze this repository and describe what it does"
# - This allows testing agent functionality without the API

# Monitor the test job
kubectl logs -f job/agent-job-dev-test -n aideator

# Delete and recreate to test changes
kubectl delete job agent-job-dev-test -n aideator
# Tilt will automatically recreate it

# To trigger agent rebuild after code changes:
touch agent/main.py
# Wait ~10 seconds for Tilt to rebuild and redeploy
```

### Agent Job Template with Fallback Values

The agent-job.yaml Helm template uses a smart fallback pattern:

```yaml
# Default values for development/testing
env:
  - name: REPO_URL
    value: "{{ .Values.repoUrl | default "https://github.com/octocat/Hello-World" }}"
  - name: PROMPT  
    value: "{{ .Values.prompt | default "Analyze this repository and describe what it does" }}"
  - name: RUN_ID
    value: "{{ .Values.runId | default "test-run" }}"
```

**Benefits:**
1. **Development**: Job runs immediately with sensible defaults for testing
2. **Production**: KubernetesService overrides with real values via Helm
3. **Single Template**: No duplication between dev and prod configurations
4. **Always Testable**: Agent changes can be tested without the full API

### Kubernetes Commands

```bash
# Check pods
kubectl get pods -n aideator

# Check jobs
kubectl get jobs -n aideator

# Stream logs from a specific job
kubectl logs -f job/agent-run123-0 -n aideator

# Describe a job
kubectl describe job agent-run123-0 -n aideator

# Delete completed jobs
kubectl delete jobs --field-selector status.successful=1 -n aideator
```

### Helm Commands

```bash
# Install AIdeator
helm install aideator ./deploy/charts/aideator -n aideator --create-namespace

# Upgrade with new values
helm upgrade aideator ./deploy/charts/aideator -n aideator -f deploy/values/production.yaml

# Check status
helm status aideator -n aideator

# Uninstall
helm uninstall aideator -n aideator
```

### Testing & Quality

```bash
# Backend tests (ALWAYS use uv for Python commands)
uv run pytest                                   # Run all tests
uv run pytest --cov=app --cov-report=html      # With coverage
uv run pytest -m unit                          # Unit tests only  
uv run pytest -m integration                   # Integration tests only
uv run pytest -m e2e                           # E2E tests only

# Frontend tests
cd frontend/
npm run test:e2e                               # Playwright E2E tests (211 test cases)
npm run test:e2e:ui                            # Interactive Playwright UI
npm test                                       # Jest unit tests
npm run type-check                             # TypeScript validation

# Linting and formatting
uv run ruff check .                            # Python linting
uv run ruff format .                           # Python formatting  
uv run mypy app/                               # Type checking

# Run in container for consistency
docker run --rm -v $(pwd):/app \
  -e SECRET_KEY=test-secret-key-32-chars-minimum \
  -e OPENAI_API_KEY=sk-test-key \
  aideator-api:dev uv run pytest
```

## 📋 Quality Standards

### Code Requirements

- **No Mock Data**: All endpoints return real functionality
- **Async Patterns**: Use `async def` for all route handlers
- **Proper Error Handling**: HTTPException for API errors, try/except blocks
- **Type Hints**: Full type annotations with mypy strict mode compliance
- **Runtime Validation**: Pydantic models for all inputs/outputs
- **Security**: RBAC, secrets management, resource limits
- **Cloud-Native**: Follow Kubernetes best practices, use standard tooling

### Kubernetes Best Practices

- **Resource Limits**: Always set memory/CPU limits on containers
- **Health Checks**: Readiness and liveness probes on all deployments
- **Labels**: Consistent labeling for resource selection
- **Namespaces**: Logical separation of resources
- **RBAC**: Minimal permissions for service accounts
- **Secrets**: Never hardcode sensitive data
- **TTL**: Set ttlSecondsAfterFinished on Jobs

### Development Standards

- **Tilt First**: Always use Tilt for local development
- **Hot Reload**: Leverage Tilt's live_update for fast iteration
- **Local Registry**: Use localhost:5005 to avoid remote pushes
- **Helm Values**: Environment-specific configurations
- **GitOps Ready**: Declarative configurations for all environments

## 🎨 AIdeator Design System

### Design Philosophy

AIdeator follows a **broad appeal** design philosophy that balances technical capability with user-friendly accessibility:

- **Broad Appeal**: Clean, modern, accessible to non-technical users
- **Multi-Agent Focus**: Visual hierarchy for up to 5 simultaneous agent streams
- **Trust & Intelligence**: Professional yet approachable AI aesthetic
- **Scalable Layout**: Responsive grid that works on various screen sizes
- **Real-time Feedback**: Subtle animations and visual cues for active streaming
- **Tailwind CSS v4**: Leverages the latest Tailwind CSS features with PostCSS v4 for optimal performance

### Color Palette (Tailwind CSS v4)

Colors are defined as HSL values in `app/globals.css` using CSS custom properties:

```css
/* Primary Brand Colors */
--ai-primary: 239 79% 59%;          /* Deep indigo - trustworthy, intelligent */
--ai-secondary: 258 90% 67%;        /* Purple - creativity, AI magic */
--ai-accent: 188 100% 50%;          /* Cyan - innovation, streaming */

/* Agent Stream Colors (distinct but harmonious) */
--agent-1: 0 84% 60%;               /* Red - attention-grabbing */
--agent-2: 39 96% 51%;              /* Amber - warm, optimistic */
--agent-3: 160 84% 39%;             /* Emerald - growth, success */
--agent-4: 221 83% 53%;             /* Blue - trust, reliability */
--agent-5: 258 90% 67%;             /* Purple - creativity */

/* Neutral Palette */
--neutral-white: 0 0% 100%;         /* Card backgrounds */
--neutral-paper: 210 40% 98%;       /* Subtle backgrounds */
--neutral-fog: 214 32% 91%;         /* Subtle borders */
--neutral-shadow: 215 16% 47%;      /* Secondary text */
--neutral-charcoal: 222 84% 16%;    /* Primary text */

/* Semantic Colors */
--semantic-success: 160 84% 39%;
--semantic-warning: 39 96% 51%;
--semantic-error: 0 84% 60%;
--semantic-info: 221 83% 53%;
```

These colors are configured in `tailwind.config.ts` and can be used with Tailwind classes like `bg-ai-primary`, `text-agent-1`, etc.

### Typography System (Tailwind CSS v4)

Typography sizes are defined as CSS custom properties and integrated with Tailwind:

```css
/* Display & Headers */
--text-display: 3rem;               /* 48px - Hero titles */
--text-h1: 2.25rem;                /* 36px - Page titles */
--text-h2: 1.5rem;                 /* 24px - Section titles */
--text-h3: 1.25rem;                /* 20px - Card titles */

/* Body Text */
--text-body-lg: 1.125rem;          /* 18px - Important content */
--text-body: 1rem;                 /* 16px - Default body */
--text-body-sm: 0.875rem;          /* 14px - Secondary content */

/* Labels & Captions */
--text-label: 0.875rem;            /* 14px - Form labels */
--text-caption: 0.75rem;           /* 12px - Metadata */
```

Use with Tailwind classes: `text-display`, `text-h1`, `text-body-lg`, etc.

### Component Patterns

#### Quick Color Reference

```tsx
// Primary Actions
className="bg-ai-primary text-white"

// Secondary Actions  
className="border-2 border-ai-secondary text-ai-secondary"

// Agent Stream Indicators
className="bg-agent-1 text-white"  // Use agent-1 through agent-5

// Backgrounds
className="bg-neutral-white"        // Main background
className="bg-neutral-paper"        // Card backgrounds
className="bg-neutral-fog"          // Subtle backgrounds
```

#### Agent Stream Card Pattern

```tsx
<div className="bg-neutral-paper rounded-lg p-lg shadow-md border-l-4 border-agent-1">
  <div className="flex items-center justify-between mb-md">
    <div className="flex items-center gap-sm">
      <div className="w-3 h-3 bg-agent-1 rounded-full animate-pulse"></div>
      <span className="text-body-sm font-medium text-neutral-shadow">
        Agent 1
      </span>
    </div>
    <button className="bg-agent-1 text-white px-md py-xs rounded-md text-body-sm font-medium hover:opacity-90">
      Select This
    </button>
  </div>
  <div className="bg-neutral-white rounded-md p-md max-h-96 overflow-y-auto">
    {/* Streaming content */}
  </div>
</div>
```

#### Primary Button Pattern

```tsx
<button className="bg-ai-primary text-white px-lg py-md rounded-md font-semibold hover:bg-ai-primary/90 transition-colors">
  Start Generation
</button>
```

#### Secondary Button Pattern

```tsx
<button className="border-2 border-ai-secondary text-ai-secondary px-lg py-md rounded-md font-semibold hover:bg-ai-secondary/10 transition-colors">
  Configure
</button>
```

#### Input Field Pattern

```tsx
<input 
  className="w-full bg-neutral-white border border-neutral-fog rounded-md px-md py-md text-body placeholder:text-neutral-shadow focus:border-ai-primary focus:ring-2 focus:ring-ai-primary/20 transition-colors"
  placeholder="Enter your prompt..."
/>
```

### Layout Patterns

#### Multi-Agent Stream Layout

```tsx
// Responsive Grid for 5 Agent Streams
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-lg">
  {agents.map((agent, index) => (
    <AgentStreamCard key={index} agent={agent} color={`agent-${index + 1}`} />
  ))}
</div>
```

#### Screen Container Pattern

```tsx
<div className="min-h-screen bg-neutral-white">
  <div className="container mx-auto px-lg py-xl">
    {/* Content */}
  </div>
</div>
```

### Animation System (Tailwind CSS v4)

AIdeator uses `tailwindcss-animate` plugin for smooth animations:

```tsx
// Built-in Tailwind animations
className="transition-all duration-200 ease-in-out"  // Smooth transitions
className="animate-pulse"                            // Pulse animation
className="animate-spin"                             // Loading spinner

// Custom animations can be added to tailwind.config.ts:
// - Stream pulse for active agent indicators
// - Shimmer effect for loading states
// - Accordion animations for collapsible content

// Example usage:
<div className="w-3 h-3 bg-agent-1 rounded-full animate-pulse" />
<div className="animate-accordion-down" />
```

The `tailwindcss-animate` plugin provides additional animation utilities that work seamlessly with Tailwind CSS v4.

### 🚨 Tailwind CSS v4 Gotchas & Important Differences

#### Critical v4 Changes (Breaking from v3)

1. **CSS Import Syntax**
   ```css
   /* ❌ OLD v3 syntax - DOES NOT WORK in v4 */
   @tailwind base;
   @tailwind components;
   @tailwind utilities;
   
   /* ✅ NEW v4 syntax - REQUIRED */
   @import "tailwindcss";
   ```

2. **PostCSS Configuration**
   ```js
   // postcss.config.mjs
   export default {
     plugins: {
       // ❌ OLD v3 - WRONG for v4
       // tailwindcss: {},
       
       // ✅ NEW v4 - REQUIRED
       "@tailwindcss/postcss": {}
     }
   }
   ```

3. **Dynamic Classes & CSS Purging**
   ```tsx
   // ❌ AVOID - Dynamic classes may be purged
   className={`border-${color}`}  // color = "border" → "border-border" gets purged!
   
   // ✅ USE - Complete class names
   className={color === 'primary' ? 'border-ai-primary' : 'border-neutral-fog'}
   
   // ✅ OR - Add to safelist in tailwind.config.ts
   safelist: ['border-border', 'text-border', 'bg-border']
   ```

4. **Custom Utility Classes**
   ```css
   /* ❌ v4 is stricter - custom utilities like these may not work */
   .border-border { border-color: hsl(var(--border)); }
   
   /* ✅ Use standard Tailwind utilities or configure properly */
   className="border-neutral-fog"  // Use defined color
   ```

#### Common Debugging Steps for v4

1. **When colors don't appear:**
   - Check if using Tailwind v4 syntax (`@import "tailwindcss"`)
   - Verify PostCSS uses `@tailwindcss/postcss` not `tailwindcss`
   - Look for dynamic class construction (avoid interpolation)
   - Check if custom classes are in safelist
   - Clear Next.js cache: `rm -rf .next`

2. **Version verification:**
   ```bash
   # Check installed version
   npm list tailwindcss @tailwindcss/postcss
   
   # Should show:
   # tailwindcss@4.x.x
   # @tailwindcss/postcss@4.x.x
   ```

3. **Migration checklist from v3 to v4:**
   - [ ] Update `@import` syntax in CSS files
   - [ ] Update PostCSS config to use `@tailwindcss/postcss`
   - [ ] Review all dynamic class constructions
   - [ ] Add necessary classes to safelist
   - [ ] Test with simple static classes first
   - [ ] Clear build caches after config changes

#### Best Practices for v4

1. **Prefer standard Tailwind utilities:**
   ```tsx
   // ✅ Good - standard utilities
   className="border-gray-200 text-gray-600 bg-white"
   
   // ⚠️ Risky - custom utilities may need safelist
   className="border-border text-muted bg-card"
   ```

2. **Use complete class names:**
   ```tsx
   // ✅ Good - complete classes
   const variants = {
     primary: "bg-ai-primary text-white",
     secondary: "bg-ai-secondary text-white",
     ghost: "bg-transparent hover:bg-neutral-fog"
   }
   
   // ❌ Bad - dynamic construction
   const color = "primary";
   className={`bg-ai-${color}`}  // May be purged!
   ```

3. **Test incrementally:**
   - Start with basic HTML + Tailwind classes
   - Add complexity gradually
   - Use browser DevTools to verify classes are applied
   - Check computed styles match expectations

### Frontend Architecture

#### Next.js 15 + Tailwind CSS v4 Structure

```
frontend/
├── app/                     # Next.js 15 App Router
│   ├── page.tsx            # Homepage with feature showcase
│   ├── stream/page.tsx     # Multi-agent streaming interface
│   └── globals.css         # Tailwind CSS v4 + design system variables
├── components/
│   ├── ui/                  # shadcn/ui components with Tailwind CSS v4
│   │   ├── button.tsx       # Button component using CVA
│   │   ├── card.tsx         # Card component
│   │   ├── label.tsx        # Form label (Radix UI)
│   │   ├── select.tsx       # Select component (Radix UI)
│   │   └── tabs.tsx         # Tabs component (Radix UI)
│   ├── agents/              # Agent-specific components
│   │   ├── StreamCard.tsx   # Individual agent stream display
│   │   ├── StreamGrid.tsx   # Multi-agent grid layout
│   │   └── SelectButton.tsx # Agent selection component
│   └── layout/              # Layout components
│       ├── Header.tsx       # Main navigation
│       └── Container.tsx    # Screen container
├── hooks/
│   ├── useAgentStream.ts    # SSE streaming hook
│   └── useAPI.ts           # FastAPI integration
├── lib/
│   ├── api.ts              # API client
│   ├── utils.ts            # Utility functions (clsx + tailwind-merge)
│   └── types.ts            # TypeScript 5 types
├── tailwind.config.ts      # Tailwind CSS v4 configuration
├── postcss.config.js       # PostCSS with @tailwindcss/postcss v4
└── tests/e2e/              # Playwright end-to-end tests
    ├── homepage.spec.ts    # Homepage functionality tests
    ├── streaming.spec.ts   # Streaming interface tests
    └── smoke-test.spec.ts  # Basic functionality verification
```

#### Custom Streaming Hook

```typescript
// hooks/useAgentStream.ts
import { useState, useEffect } from 'react';

interface AgentStreamHook {
  streams: Map<number, string[]>;
  isStreaming: boolean;
  error: string | null;
  startStream: (runId: string) => void;
  stopStream: () => void;
}

export function useAgentStream(): AgentStreamHook {
  const [streams, setStreams] = useState<Map<number, string[]>>(new Map());
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startStream = (runId: string) => {
    const eventSource = new EventSource(`http://localhost:8000/api/v1/runs/${runId}/stream`);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStreams(prev => {
        const newStreams = new Map(prev);
        const existing = newStreams.get(data.variation_id) || [];
        newStreams.set(data.variation_id, [...existing, data.content]);
        return newStreams;
      });
    };

    eventSource.onerror = (error) => {
      setError('Streaming connection failed');
      setIsStreaming(false);
    };

    setIsStreaming(true);
  };

  return { streams, isStreaming, error, startStream, stopStream };
}
```

### Design System Guidelines (Tailwind CSS v4)

#### Do's ✅
- Use the agent color system (agent-1 through agent-5) for stream differentiation
- Leverage Tailwind CSS v4's built-in utilities and custom properties
- Use the `cn()` utility from `lib/utils` for conditional classes
- Implement smooth transitions with `tailwindcss-animate` plugin
- Design for responsive layouts using Tailwind's breakpoint system
- Maintain consistent spacing using custom spacing scale (xs, sm, md, lg, xl)
- Use semantic colors for status indicators
- Utilize Radix UI components for complex interactions (Select, Tabs, etc.)

#### Don'ts ❌
- Don't use colors outside the defined palette (configure in tailwind.config.ts)
- Don't create jarring animations that interfere with reading
- Don't ignore accessibility requirements (contrast, touch targets)
- Don't hardcode spacing or colors (use Tailwind classes or CSS variables)
- Don't neglect mobile experience for the stream interface
- Don't mix old Tailwind v3 syntax with v4 features

## 🔧 Implementation Patterns

### Kubernetes Service Implementation

```python
# app/services/kubernetes_service.py
import asyncio
import subprocess
import yaml
from typing import AsyncGenerator, Dict, Any

class KubernetesService:
    def __init__(self, namespace: str = "aideator"):
        self.namespace = namespace
        self.job_template_path = "k8s/jobs/agent-job-template.yaml"
        
    async def create_agent_job(
        self,
        run_id: str,
        variation_id: int,
        repo_url: str,
        prompt: str,
    ) -> str:
        """Create a Kubernetes Job for an agent."""
        job_name = f"agent-{run_id}-{variation_id}"
        
        # Load and render template
        with open(self.job_template_path) as f:
            template = f.read()
            
        job_manifest = template.format(
            run_id=run_id,
            variation_id=variation_id,
            repo_url=repo_url,
            prompt=prompt.replace('"', '\\"'),
            job_name=job_name
        )
        
        # Apply via kubectl
        process = subprocess.Popen(
            ["kubectl", "apply", "-f", "-", "--namespace", self.namespace],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=job_manifest)
        
        if process.returncode != 0:
            raise RuntimeError(f"Failed to create job: {stderr}")
            
        return job_name
    
    async def stream_job_logs(
        self,
        job_name: str,
        variation_id: int,
    ) -> AsyncGenerator[str, None]:
        """Stream logs from a Kubernetes Job."""
        # Wait for pod to be ready
        await self._wait_for_pod(job_name)
        
        # Start streaming logs
        cmd = [
            "kubectl", "logs", "-f",
            f"job/{job_name}",
            "--namespace", self.namespace,
            "--tail", "0"  # Only new logs
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        async for line in process.stdout:
            log_line = line.decode().strip()
            if log_line:
                yield json.dumps({
                    "variation_id": variation_id,
                    "content": log_line,
                    "timestamp": datetime.utcnow().isoformat()
                })
```

### Agent Orchestrator with Kubernetes

```python
# app/services/agent_orchestrator.py
class AgentOrchestrator:
    def __init__(self, kubernetes_service: KubernetesService, sse_manager: SSEManager):
        self.k8s = kubernetes_service
        self.sse = sse_manager
        
    async def execute_variations(
        self,
        run_id: str,
        repo_url: str,
        prompt: str,
        variations: int,
    ):
        """Execute N agent variations as Kubernetes Jobs."""
        jobs = []
        
        # Create all jobs
        for i in range(variations):
            job_name = await self.k8s.create_agent_job(
                run_id=run_id,
                variation_id=i,
                repo_url=repo_url,
                prompt=prompt
            )
            jobs.append((job_name, i))
            
        # Stream logs from all jobs concurrently
        tasks = []
        for job_name, variation_id in jobs:
            task = asyncio.create_task(
                self._stream_job_output(run_id, job_name, variation_id)
            )
            tasks.append(task)
            
        await asyncio.gather(*tasks, return_exceptions=True)
        
    async def _stream_job_output(
        self,
        run_id: str,
        job_name: str,
        variation_id: int
    ):
        """Stream output from a single job."""
        try:
            async for log_line in self.k8s.stream_job_logs(job_name, variation_id):
                await self.sse.send_agent_output(run_id, variation_id, log_line)
                
            await self.sse.send_agent_complete(run_id, variation_id)
            
        except Exception as e:
            await self.sse.send_agent_error(run_id, variation_id, str(e))
```

### Tiltfile Configuration

```python
# Tiltfile
# Phase 1: Check cluster
local_resource(
    name="cluster-check",
    cmd="kubectl cluster-info",
    labels=["cluster"]
)

# Phase 2: Build containers
docker_build(
    'aideator-api',
    context='.',
    dockerfile='./Dockerfile',
    target='api',
    live_update=[
        sync('./app', '/app/app'),
        run('pip install -r requirements.txt', trigger=['./requirements.txt'])
    ]
)

docker_build(
    'aideator-agent',
    context='.',
    dockerfile='./Dockerfile',
    target='agent'
)

# Phase 3: Deploy with Helm
k8s_yaml(helm(
    'deploy/charts/aideator',
    name='aideator',
    namespace='aideator',
    values=['deploy/values/local.yaml']
))

# Phase 4: Port forwarding
k8s_resource(
    'aideator',
    port_forwards=['8000:8000'],
    labels=['api']
)
```

### Helm Values Structure

```yaml
# deploy/values/local.yaml
image:
  repository: aideator-api
  tag: dev
  pullPolicy: Always

service:
  type: ClusterIP
  port: 8000

agents:
  image: aideator-agent:dev
  resources:
    requests:
      memory: "256Mi"
      cpu: "100m"
    limits:
      memory: "1Gi"
      cpu: "500m"
  jobTTL: 3600  # 1 hour

# These values are used by agent-job.yaml
# If not provided, template defaults are used
# agentJobName: "agent-run-123-0"  # Optional
# runId: "run-123"                  # Optional
# variationId: "0"                  # Optional  
# repoUrl: "https://github.com/..." # Optional
# prompt: "Analyze this code"       # Optional

env:
  - name: KUBERNETES_NAMESPACE
    valueFrom:
      fieldRef:
        fieldPath: metadata.namespace
        
rbac:
  create: true
  rules:
    - apiGroups: ["batch"]
      resources: ["jobs"]
      verbs: ["create", "get", "list", "delete"]
    - apiGroups: [""]
      resources: ["pods", "pods/log"]
      verbs: ["get", "list"]
```

## 🔐 Security Practices

### Kubernetes Security

```yaml
# Pod Security Context
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  capabilities:
    drop: ["ALL"]

# Network Policies (future)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: aideator-network-policy
spec:
  podSelector:
    matchLabels:
      app: aideator
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: aideator
  egress:
  - to:
    - namespaceSelector: {}
```

### Secret Management

```bash
# Required secrets for deployment
# 1. OpenAI API key (for LiteLLM)
kubectl create secret generic openai-secret \
  --from-literal=api-key="$OPENAI_API_KEY" \
  -n aideator

# 2. Application secret key
kubectl create secret generic aideator-secret \
  --from-literal=secret-key="$(openssl rand -hex 32)" \
  -n aideator

# Verify secrets exist
kubectl get secrets -n aideator
```

### RBAC Configuration

```yaml
# Minimal permissions for the service account
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: aideator-job-manager
rules:
- apiGroups: ["batch"]
  resources: ["jobs"]
  verbs: ["create", "get", "list", "watch", "delete"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]
```

## 🧪 Testing Approach

### End-to-End Testing (Black Box)

Treat the application as a black box when testing. **Do NOT use kubectl port-forward** - rely on Tilt's built-in port forwarding or the exposed service interface.

```bash
# 1. Start the application with Tilt
tilt up

# 2. Wait for services to be ready (Tilt handles port forwarding)
# API available at: http://localhost:8000
# Tilt UI at: http://localhost:10350

# 3. Test API endpoints directly
curl http://localhost:8000/api/v1/health | jq

# 4. When testing SSE streaming, ALWAYS use timeout to avoid hanging
timeout 15 curl -N -H "X-API-Key: $API_KEY" \
  http://localhost:8000/api/v1/runs/${RUN_ID}/stream

# 5. Monitor agent output (kubectl logs are streamed via SSE)
# The streaming works by:
# - API creates Kubernetes Job
# - KubernetesService uses kubectl logs -f to stream pod logs
# - Logs are forwarded to SSE clients in real-time
```

### Testing Checklist

```bash
# Health Check
curl -s http://localhost:8000/api/v1/health | jq

# User Registration
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "email": "test@example.com", "password": "TestPass123"}' | jq

# Login (use email, not username)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "TestPass123"}' | jq

# Create API Key
curl -X POST http://localhost:8000/api/v1/auth/api-keys \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Key", "description": "For testing"}' | jq

# Create Run
curl -X POST http://localhost:8000/api/v1/runs \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/octocat/Hello-World", "prompt": "Add README", "variations": 1}' | jq

# Stream Output (with timeout!)
timeout 20 curl -N -H "X-API-Key: $API_KEY" \
  http://localhost:8000/api/v1/runs/${RUN_ID}/stream | grep -E "(event:|data:)"
```

### Verifying Streaming Works (Compare kubectl vs SSE)

```bash
# CRITICAL: Test that kubectl logs match SSE output
# This verifies the entire streaming pipeline

# Terminal 1: Monitor kubectl logs directly
RUN_ID="run-abc123"
kubectl logs -f job/agent-${RUN_ID}-0 -n aideator | \
  grep -E "Starting LLM streaming|Streaming LLM|chunks_received"

# Terminal 2: Monitor SSE stream from API
timeout 30 curl -N -H "X-API-Key: $API_KEY" \
  http://localhost:8000/api/v1/runs/${RUN_ID}/stream 2>/dev/null | \
  while IFS= read -r line; do
    if [[ $line == data:* ]] && echo "$line" | grep -q "Streaming"; then
      echo "SSE: $line"
    fi
  done

# Both should show the same streaming events!
# If SSE is missing events that kubectl shows, there's a problem
```

### Comprehensive Testing Strategy

#### Backend Testing (pytest + 80% coverage achieved)

```bash
# ALWAYS use uv for Python commands (faster, more reliable)
uv run pytest                                   # All tests (30+ files)
uv run pytest --cov=app --cov-report=html      # Coverage report
uv run pytest -m unit                          # Unit tests only (25+ files)
uv run pytest -m integration                   # Integration tests (6 files) 
uv run pytest -m e2e                           # E2E tests (5 files)
uv run pytest -m slow                          # Long-running tests
uv run pytest --maxfail=1                      # Stop on first failure

# Parallel execution for faster tests
uv run pytest -n auto                          # Use all CPU cores

# Run in Docker for consistency
docker run --rm -v $(pwd):/app \
  -e SECRET_KEY=test-secret-key-32-chars-minimum \
  -e OPENAI_API_KEY=sk-test-key \
  aideator-api:dev uv run pytest
```

#### Frontend Testing (Playwright + Jest)

```bash
cd frontend/

# E2E tests with Playwright (211 test cases across 21 files)
npm run test:e2e                               # Full E2E suite
npm run test:e2e:ui                            # Interactive Playwright UI
npm run test:e2e:debug                         # Debug mode with DevTools
npm run test:e2e -- --headed                   # Run with visible browser

# Specific E2E test categories
npm run test:e2e -- tests/e2e/streaming.spec.ts          # Core streaming tests
npm run test:e2e -- tests/e2e/auth-simple.spec.ts        # Auth workflows  
npm run test:e2e -- tests/e2e/agent-streaming.spec.ts    # Multi-agent tests

# Unit tests with Jest
npm test                                       # All unit tests
npm run test:watch                             # Watch mode
npm run test:coverage                          # Coverage report

# Type checking
npm run type-check                             # TypeScript validation
```

#### Test Structure & Coverage

**Backend Tests (35+ files, 80% coverage):**
- `tests/unit/` - 25+ files (auth, APIs, models, services)
- `tests/integration/` - 6 files (streaming, LiteLLM, parallel execution)  
- `tests/e2e/` - 5 files (full user journeys, error handling)

**Frontend Tests (30+ files, 211 E2E test cases):**
- `tests/e2e/` - 21 files covering all user workflows
- `tests/integration/` - API client integration tests
- `tests/unit/` - React hooks, utilities, model mapping

#### E2E Testing Best Practices

```bash
# 1. ALWAYS start with Tilt (don't use kubectl port-forward)
tilt up
# Wait for services: FastAPI (8000), Frontend (3001), Tilt UI (10350)

# 2. Test complete user journeys with timeouts
timeout 20 curl -N -H "X-API-Key: $API_KEY" \
  http://localhost:8000/api/v1/runs/${RUN_ID}/stream

# 3. Verify streaming pipeline (kubectl logs match SSE output)
# Terminal 1: Monitor kubectl logs
kubectl logs -f job/agent-${RUN_ID}-0 -n aideator | grep "Streaming"

# Terminal 2: Monitor SSE stream  
timeout 30 curl -N -H "X-API-Key: $API_KEY" \
  http://localhost:8000/api/v1/runs/${RUN_ID}/stream | grep "Streaming"
# Both should show identical streaming events!

# 4. Test with realistic data (no mock endpoints)
curl -X POST http://localhost:8000/api/v1/runs \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/octocat/Hello-World", "prompt": "Add README", "variations": 1}'
```

#### Quality Gates

```bash
# Pre-commit checks (REQUIRED before any commit)
uv run ruff check .                            # Python linting must pass
uv run ruff format .                           # Auto-format Python code
uv run mypy app/                               # Type checking must pass
cd frontend/ && npm run type-check             # TypeScript validation

# Coverage requirements
uv run pytest --cov=app --cov-fail-under=80   # 80% minimum backend coverage
cd frontend/ && npm run test:coverage          # Frontend coverage report

# E2E validation (REQUIRED for major features)
npm run test:e2e                               # All 211 E2E tests must pass
```

## 🚨 Common Pitfalls to Avoid

### What I Never Do

- ❌ Use `python` or `python3` commands (ALWAYS use `uv run`)
- ❌ Use `pip` for package management (ALWAYS use `uv`)
- ❌ Skip timeouts on streaming/SSE endpoints (causes hanging tests)
- ❌ Use kubectl port-forward when Tilt is running (conflicts)
- ❌ Test without realistic data (no mock endpoints)
- ❌ Run E2E tests inside containers (treat as black box)
- ❌ Ignore test markers (use `-m unit`, `-m integration`, `-m e2e`)
- ❌ Hardcode cluster URLs or namespaces
- ❌ Skip resource limits on containers
- ❌ Use `kubectl exec` for normal operations
- ❌ Ignore Job TTL settings
- ❌ Mix development and production configs
- ❌ Forget to create required secrets before deployment
- ❌ Use OpenRouter references (we use LiteLLM with OpenAI)
- ❌ Assume Tilt will instantly rebuild (wait 10+ seconds)

### What I Always Do

- ✅ Use `uv run` for ALL Python commands (pytest, ruff, mypy)
- ✅ Use `npm run test:e2e` for Playwright E2E tests (211 test cases)
- ✅ Add timeouts to ALL streaming/SSE tests (prevent hanging)
- ✅ Start with `tilt up` for E2E testing (not kubectl port-forward)
- ✅ Verify kubectl logs match SSE output (streaming pipeline validation)
- ✅ Test with realistic data and real API endpoints
- ✅ Use test markers: `uv run pytest -m unit|integration|e2e`
- ✅ Check coverage with `uv run pytest --cov=app --cov-report=html`
- ✅ Run frontend type checking with `npm run type-check`
- ✅ Use Kubernetes Jobs for batch workloads
- ✅ Set resource requests and limits
- ✅ Implement proper RBAC
- ✅ Use ConfigMaps and Secrets appropriately
- ✅ Add meaningful labels and annotations
- ✅ Test with Tilt before manual deployment
- ✅ Treat the API as a black box for e2e tests
- ✅ Create openai-secret before deployment: `kubectl create secret generic openai-secret --from-literal=api-key=$OPENAI_API_KEY -n aideator`
- ✅ Use agent-job-dev-test for testing agent changes
- ✅ Touch files to trigger Tilt rebuilds when needed

## 🔄 Development Workflow

### Kubernetes Development Flow

1. **Start Tilt**: `tilt up` - Handles everything automatically
2. **Make Changes**: Edit code, Tilt detects and rebuilds
3. **Check Logs**: Use Tilt UI or `kubectl logs`
4. **Debug Jobs**: `kubectl describe job <name>`
5. **Clean Up**: `tilt down` or `kubectl delete jobs --all`

### Deployment Flow

```bash
# Development
tilt up

# Staging
helm upgrade --install aideator ./deploy/charts/aideator \
  -n aideator-staging \
  -f deploy/values/staging.yaml

# Production
helm upgrade --install aideator ./deploy/charts/aideator \
  -n aideator-prod \
  -f deploy/values/production.yaml \
  --atomic \
  --wait
```

## 📚 Key Technologies

### Core Stack

- **FastAPI** - Modern async web framework with automatic OpenAPI
- **Next.js 15.2.4** - React 19 framework with App Router and Turbopack
- **React 19.0.0** - Latest React with improved performance
- **TypeScript 5** - Type-safe JavaScript with latest features
- **Tailwind CSS v4.1.11** - Utility-first CSS with PostCSS v4
- **Kubernetes** - Container orchestration and job management
- **kubectl** - Native log streaming and resource management
- **Helm** - Package manager for Kubernetes applications
- **Tilt** - Local Kubernetes development environment
- **k3d** - Lightweight local Kubernetes clusters
- **PostgreSQL + SQLModel** - Production database with async ORM
- **LiteLLM Gateway** - Unified LLM API with analytics
- **Redis** - Caching layer for LiteLLM Gateway
- **Pydantic** - Data validation and serialization

### Frontend Libraries

- **Radix UI** - Unstyled, accessible component primitives
- **class-variance-authority** - Type-safe component variants
- **tailwind-merge** - Intelligent Tailwind class merging
- **lucide-react** - Beautiful, consistent icon library
- **tailwindcss-animate** - Animation utilities for Tailwind

### Kubernetes Components

- **Jobs** - Batch processing for agent execution
- **Deployments** - FastAPI service hosting
- **Services** - Network access to pods
- **ConfigMaps** - Configuration management
- **Secrets** - Sensitive data storage
- **RBAC** - Access control for kubectl operations

### Development Tools

- **Tilt** - Kubernetes development workflow
- **ctlptl** - Cluster lifecycle management
- **k3d** - Local Kubernetes clusters
- **Local Registry** - Fast container iteration
- **Port Forwarding** - Local service access

## 🎯 MVP Success Criteria

The Multi-Model Comparison Platform successfully:

1. **Parallel Execution**: Creates Kubernetes Jobs for each model in parallel
2. **Unified API Access**: Routes all model calls through LiteLLM Gateway
3. **Rich Analytics**: Captures response times, token usage, costs via Gateway
4. **Real-time Streaming**: Streams model responses via kubectl logs to SSE
5. **Preference Tracking**: Records user choices with optional feedback
6. **Session Management**: Maintains conversation context across turns
7. **Production Deployment**: Deploys via Helm with LiteLLM Gateway included

## 🌟 Key Advantages of Hybrid Approach

### Kubernetes Advantages
1. **True Parallel Execution**: Multiple models process simultaneously
2. **Resource Isolation**: Each model runs in its own container
3. **Scalability**: Leverages Kubernetes scheduling
4. **Security**: RBAC, secrets management, network policies

### LiteLLM Gateway Advantages
1. **Unified Interface**: Single API for 100+ model providers
2. **Built-in Analytics**: Prometheus metrics, cost tracking
3. **Operational Features**: Caching, rate limiting, retries
4. **Zero Development**: Analytics come out-of-the-box

### Combined Benefits
1. **Best of Both Worlds**: Parallel execution + comprehensive analytics
2. **Future Flexibility**: Ready for code analysis and long-running tasks
3. **Rich Data Collection**: Every interaction tracked for insights
4. **Production Ready**: Battle-tested components

______________________________________________________________________

**I am your primary coding assistant for AIdeator. I build production-ready multi-model comparison platforms using Kubernetes for orchestration and LiteLLM Gateway for analytics, ensuring scalability, observability, and rich user insights.**