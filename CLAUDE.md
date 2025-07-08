# AIdeator - Instructions for Claude

## Project Overview

AIdeator is a **Kubernetes-native** LLM orchestration platform that runs multiple AI agents in isolated containers, streaming their thought processes in real-time. By leveraging Kubernetes Jobs and kubectl log streaming, we ensure cloud-native scalability, observability, and standard tooling. As the primary coding assistant, I help build a sophisticated FastAPI + Kubernetes backend that orchestrates containerized Claude agents, captures their reasoning, and delivers insights through Server-Sent Events.

## 🎯 My Role & Capabilities

I am the **primary development assistant** for AIdeator backend development. I provide:

- **Production-Ready Code**: No mock data, proper async patterns, comprehensive error handling
- **FastAPI Expertise**: Async route handlers, SSE streaming, proper dependency injection
- **Kubernetes Integration**: Job orchestration, kubectl log streaming, Helm charts
- **Real-time Streaming**: Server-Sent Events powered by native Kubernetes logs
- **Cloud-Native Patterns**: Tilt development, local registries, declarative deployments
- **Security First**: RBAC, secret management, resource limits, SQL injection prevention

## 🏗️ Architecture Understanding

### Core Components

- **FastAPI Backend** - Async web framework running as a Kubernetes deployment
- **Kubernetes Jobs** - Isolated agent execution with automatic cleanup (TTL)
- **kubectl Logs** - Native log streaming from agent containers
- **Server-Sent Events (SSE)** - Real-time streaming of agent thought processes
- **SQLite + SQLModel** - Async database with Pydantic integration
- **Anthropic Claude API** - LLM agent for code generation tasks
- **Helm Charts** - Declarative deployment and configuration management

### Kubernetes-Native Architecture

The architecture leverages native Kubernetes features:
- **Pods & Jobs**: Each agent runs as a Kubernetes Job
- **Service Accounts**: RBAC for kubectl operations
- **ConfigMaps & Secrets**: Configuration and API key management
- **Local Registry**: Development with localhost:5005
- **Tilt**: Streamlined local development workflow

### Key Workflows

1. **Job Submission** → Create Kubernetes Job → Agent container execution
2. **Log Streaming** → kubectl logs → SSE to client → Real-time output
3. **Job Management** → Status tracking → TTL cleanup → Resource limits
4. **Development** → Tilt up → Hot reload → Port forwarding

### Kubernetes Integration Architecture

```python
# FastAPI service runs in a pod with kubectl access
class KubernetesService:
    async def create_agent_job(self, run_id: str, variation_id: int, repo_url: str, prompt: str):
        # Create Job from template
        job_manifest = self.render_job_template(
            run_id=run_id,
            variation_id=variation_id,
            repo_url=repo_url,
            prompt=prompt
        )
        
        # Apply via kubectl
        subprocess.run(["kubectl", "apply", "-f", "-"], input=job_manifest)
        
    async def stream_job_logs(self, job_name: str) -> AsyncGenerator[str, None]:
        # Stream logs via kubectl
        process = await asyncio.create_subprocess_exec(
            "kubectl", "logs", "-f", f"job/{job_name}",
            stdout=asyncio.subprocess.PIPE
        )
        
        async for line in process.stdout:
            yield line.decode().strip()

# Agent runs in a Kubernetes Job
# Container entrypoint: python /agent/main.py
# Logs streamed via kubectl logs -f
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
# Run tests (same as before)
pytest
pytest --cov=app --cov-report=html

# Linting and formatting
ruff check .
ruff format .
mypy app/

# Run in container for consistency
docker run --rm -v $(pwd):/app aideator-api:dev pytest
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

### Kubernetes Testing

```python
# Test Job creation
@pytest.mark.asyncio
async def test_create_kubernetes_job():
    k8s = KubernetesService()
    
    job_name = await k8s.create_agent_job(
        run_id="test-123",
        variation_id=0,
        repo_url="https://github.com/test/repo",
        prompt="Test prompt"
    )
    
    assert job_name == "agent-test-123-0"
    
    # Verify job exists
    status = await k8s.get_job_status(job_name)
    assert status["status"] in ["pending", "running"]

# Test with kind cluster
@pytest.mark.integration
async def test_with_kind_cluster():
    # Requires kind cluster running
    # kind create cluster --name test-aideator
    pass
```

### Tilt Testing

```bash
# Test Tiltfile syntax
tilt ci

# Run Tilt in CI mode
tilt up --ci

# Validate Helm charts
helm lint deploy/charts/aideator
helm template aideator deploy/charts/aideator --debug
```

## 🚨 Common Pitfalls to Avoid

### What I Never Do

- ❌ Hardcode cluster URLs or namespaces
- ❌ Skip resource limits on containers
- ❌ Use `kubectl exec` for normal operations
- ❌ Ignore Job TTL settings
- ❌ Mix development and production configs

### What I Always Do

- ✅ Use Kubernetes Jobs for batch workloads
- ✅ Set resource requests and limits
- ✅ Implement proper RBAC
- ✅ Use ConfigMaps and Secrets appropriately
- ✅ Add meaningful labels and annotations
- ✅ Test with Tilt before manual deployment

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
- **Kubernetes** - Container orchestration and job management
- **kubectl** - Native log streaming and resource management
- **Helm** - Package manager for Kubernetes applications
- **Tilt** - Local Kubernetes development environment
- **k3d** - Lightweight local Kubernetes clusters
- **SQLite + SQLModel** - Lightweight database with async ORM
- **Pydantic** - Data validation and serialization

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

The Kubernetes-native backend successfully:

1. Creates Kubernetes Jobs for each agent variation
2. Streams logs via kubectl to SSE endpoints
3. Manages Job lifecycle with TTL and cleanup
4. Provides RBAC-secured kubectl operations
5. Deploys via Helm with environment-specific values
6. Enables rapid development with Tilt

## 🌟 Key Advantages of Kubernetes Approach

1. **Native Integration**: Uses standard Kubernetes APIs and tooling
2. **Observability**: Full visibility through kubectl and Kubernetes events
3. **Scalability**: Leverages Kubernetes scheduling and resource management
4. **Portability**: Runs on any Kubernetes cluster (local, cloud, on-prem)
5. **Security**: Built-in RBAC, network policies, and secrets management
6. **Developer Experience**: Tilt provides excellent local development workflow

______________________________________________________________________

**I am your primary coding assistant for AIdeator. I build production-ready Kubernetes-native backends with FastAPI, ensuring cloud-native patterns, proper RBAC, and seamless container orchestration.**