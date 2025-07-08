**Product Requirements Document (PRD): AIdeator MVP**

*   **Version:** 2.0
*   **Status:** Kubernetes-Native Architecture
*   **Focus:** Backend API with Kubernetes Orchestration

### **Changelog from v1.2**

*   **Architecture Pivot:** Replaced Dagger containerization with native Kubernetes Jobs and kubectl log streaming
*   **Development Environment:** Adopted Tilt for local Kubernetes development with k3d clusters
*   **Deployment Strategy:** Helm charts for declarative, reproducible deployments
*   **Streaming Implementation:** Direct kubectl logs integration for real-time agent output
*   **Container Registry:** Local registry pattern (localhost:5005) for development

## 1. Introduction & Vision

Software developers and AI engineers are in a constant loop of trial and error when prompting LLMs for code generation. It's difficult to compare different approaches without a structured process. More importantly, the reasoning *behind* an AI's output is often a black box.

**AIdeator** is a tool for developers that accelerates this iterative loop and provides transparency. It allows engineers to prompt an LLM agent on a codebase under multiple, parallel conditions. By streaming the agent's entire thought process for each variation, AIdeator allows developers to not just compare the final results, but to understand *how* the agent arrived at its solution, turning prompt engineering from an art into an observable science.

## 2. MVP Objective (Kubernetes-Native Goal)

To build and deploy a Kubernetes-native backend service that accepts a public GitHub repository, a user prompt, and a number of variations `N`. The service will then:
1.  Clone the GitHub repository into a containerized, isolated environment.
2.  Create `N` parallel Kubernetes Jobs, each running a containerized LLM agent (Claude) acting on the cloned repository.
3.  Stream the LLM's raw, real-time "thought process" for each variation directly to the client using kubectl logs.
4.  Provide an endpoint to persist the user's "winning" choice.

Success for the MVP is a functional API running in Kubernetes that a frontend can use to demonstrate the core loop: **Prompt -> Observe Agent's Process -> Compare Processes -> Select Favorite Process**.

## 3. Scope

#### **IN SCOPE (Must-Haves for the MVP)**

*   **API Endpoint for Job Submission:** One endpoint to receive a `github_url`, a `prompt`, and a number of variations `N` (up to 5).
*   **Kubernetes Job Orchestration:** Dynamic creation of Kubernetes Jobs for each agent variation using templated manifests.
*   **Container-based Agents:** Each LLM agent runs in its own isolated container with access to the cloned repository.
*   **Real-time Log Streaming:** Direct integration with kubectl logs to stream agent output via Server-Sent Events (SSE).
*   **Helm-based Deployment:** Complete Helm chart for reproducible deployments across environments.
*   **Local Development with Tilt:** Streamlined development workflow using Tilt, k3d, and local container registry.
*   **Result Persistence:** An API endpoint to receive the ID of the "winning" variation chosen by the user and store this selection.
*   **Basic Data Model:** A minimal database schema (SQLite) to store run information and the user's final selection.

#### **OUT OF SCOPE (Post-MVP)**

*   **Sandboxed Code Execution:** We will **not** run or execute any code.
*   **Repository Context Pre-processing:** We will **not** read files or construct a context string. The agent gets the repo path and the prompt, that's it.
*   **Downloading Final Code:** Providing the modified code base for download is a future feature.
*   **Frontend Client:** The UI is out of scope for this backend PRD.
*   **Intelligent Learning / "Super Diff"**
*   **User Authentication & Authorization**
*   **Private Repositories**
*   **Multi-cluster Support**
*   **Horizontal Pod Autoscaling**

## 4. User Stories (Backend Perspective)

*   **As a Frontend Developer,** I want to call a single API endpoint with a repo URL and a prompt, so that I can kick off a new agent comparison job.
*   **As a Frontend Developer,** I want to receive a unique `run_id` after submission, so I can use it to subscribe to a result stream.
*   **As a Frontend Developer,** I want to connect to a streaming endpoint and receive the distinct, real-time thought process from each of the `N` agent variations, so I can display them to the end-user as they happen.
*   **As a Frontend Developer,** I want to call an endpoint with the `run_id` and the `variation_id` that the user selected, so the backend can store this preference.
*   **As a DevOps Engineer,** I want to deploy AIdeator using Helm charts, so I can manage configurations declaratively.
*   **As a Developer,** I want to use Tilt for local development, so I can iterate quickly with hot-reloading and automatic deployments.

## 5. Technical Implementation & Architecture

### **Core Technologies**

*   **Language/Framework:** **Python with FastAPI**. Ideal for rapid development, built-in async support, and automatic OpenAPI documentation.
*   **Container Orchestration:** **Kubernetes** with **Jobs** for agent execution and **kubectl** for log streaming.
*   **Local Development:** **Tilt** with **k3d** for local Kubernetes clusters and **ctlptl** for cluster lifecycle management.
*   **Deployment:** **Helm** charts for declarative, templated Kubernetes manifests.
*   **Container Registry:** Local registry pattern (localhost:5005) for development, cloud registries for production.
*   **Streaming to Client:** **Server-Sent Events (SSE)** powered by kubectl log streams.
*   **Database:** **SQLite** with **SQLModel** for development, PostgreSQL-ready for production.

### **Architecture Overview**

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Tilt Dev Env   │────▶│  k3d Cluster    │────▶│  Local Registry │
│                 │     │                 │     │  (localhost:5005)│
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   FastAPI Service     │
                    │   (Kubernetes Pod)    │
                    └───────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
            ┌──────────────┐       ┌──────────────┐
            │ Kubernetes   │       │   SSE        │
            │ Service API  │       │  Manager     │
            └──────────────┘       └──────────────┘
                    │
                    ▼
            ┌──────────────┐
            │ Agent Jobs   │
            │ (N parallel) │
            └──────────────┘
                    │
                    ▼
            ┌──────────────┐
            │ kubectl logs │
            │  streaming   │
            └──────────────┘
```

### **Key Components**

1. **KubernetesService**: Manages Job lifecycle and log streaming
2. **AgentOrchestrator**: Coordinates parallel agent execution
3. **SSEManager**: Handles real-time event streaming to clients
4. **Helm Charts**: Declarative deployment configuration
5. **Tiltfile**: Local development orchestration

## 6. API Specification (OpenAPI 3.0)

```yaml
openapi: 3.0.0
info:
  title: AIdeator Kubernetes-Native API
  version: 2.0.0
  description: API for orchestrating and streaming the thought process of containerized LLM agents.

servers:
  - url: http://localhost:8000/api/v1
    description: Local development server (via Tilt port-forward)

paths:
  /health:
    get:
      summary: Health check endpoint
      responses:
        '200':
          description: Service is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "healthy"
                  version:
                    type: string
                    example: "2.0.0"
                  kubernetes:
                    type: boolean
                    example: true

  /runs:
    post:
      summary: Create a new agent run with Kubernetes Jobs
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                github_url:
                  type: string
                  format: uri
                  example: "https://github.com/user/repo"
                prompt:
                  type: string
                  example: "Refactor the main.py file to be more modular."
                variations:
                  type: integer
                  description: "Number of Kubernetes Jobs to create. Max 5."
                  default: 3
                  minimum: 1
                  maximum: 5
                agent_config:
                  type: object
                  description: "Optional agent configuration"
                  properties:
                    model:
                      type: string
                      default: "claude-3-sonnet-20240229"
                    temperature:
                      type: number
                      default: 0.7
      responses:
        '202':
          description: Accepted for processing. Kubernetes Jobs are being created.
          content:
            application/json:
              schema:
                type: object
                properties:
                  run_id:
                    type: string
                    example: "run_k8s_abc123"
                  stream_url:
                    type: string
                    example: "/api/v1/runs/run_k8s_abc123/stream"
                  job_names:
                    type: array
                    items:
                      type: string
                    example: ["agent-run_k8s_abc123-0", "agent-run_k8s_abc123-1"]

  /runs/{run_id}/stream:
    get:
      summary: Stream kubectl logs for all agent Jobs
      parameters:
        - name: run_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Server-Sent Events stream of kubectl log output
          content:
            text/event-stream:
              schema:
                type: string
                example: |
                  event: status
                  data: {"run_id": "run_k8s_abc123", "status": "started", "message": "Created 3 Kubernetes Jobs"}

                  event: agent_output
                  data: {"variation_id": 0, "content": "Starting agent variation 0", "pod": "agent-run_k8s_abc123-0-xyz"}

                  event: agent_output
                  data: {"variation_id": 1, "content": "Cloning repository...", "pod": "agent-run_k8s_abc123-1-abc"}

                  event: job_completed
                  data: {"variation_id": 0, "status": "completed", "job_name": "agent-run_k8s_abc123-0"}

                  event: error
                  data: {"variation_id": 2, "error": "Pod failed to start", "job_name": "agent-run_k8s_abc123-2"}

  /runs/{run_id}/status:
    get:
      summary: Get status of Kubernetes Jobs for a run
      parameters:
        - name: run_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Current status of all Jobs
          content:
            application/json:
              schema:
                type: object
                properties:
                  run_id:
                    type: string
                  status:
                    type: string
                    enum: ["starting", "running", "completed", "failed", "cancelled"]
                  jobs:
                    type: array
                    items:
                      type: object
                      properties:
                        job_name:
                          type: string
                        status:
                          type: object
                          properties:
                            active:
                              type: integer
                            succeeded:
                              type: integer
                            failed:
                              type: integer

  /runs/{run_id}/select:
    post:
      summary: Select the winning variation for a run
      parameters:
        - name: run_id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                winning_variation_id:
                  type: integer
                  example: 2
      responses:
        '200':
          description: Selection successfully recorded. Associated Job logs can be retrieved.
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "success"
                  job_name:
                    type: string
                    example: "agent-run_k8s_abc123-2"
```

## 7. Kubernetes Integration Details

### **Job Template Structure**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: agent-{run_id}-{variation_id}
  labels:
    app: aideator-agent
    run-id: {run_id}
    variation-id: {variation_id}
spec:
  ttlSecondsAfterFinished: 3600  # Auto-cleanup after 1 hour
  template:
    spec:
      containers:
      - name: agent
        image: aideator-agent:latest
        env:
        - name: REPO_URL
          value: {repo_url}
        - name: PROMPT
          value: {prompt}
        - name: VARIATION_ID
          value: {variation_id}
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: anthropic-secret
              key: api-key
      restartPolicy: Never
```

### **RBAC Requirements**

The FastAPI service requires the following Kubernetes permissions:
- Create, Get, List, Watch, Delete Jobs
- Get, List Pods
- Get Pod logs

### **Development Workflow with Tilt**

1. `tilt up` - Starts k3d cluster, builds containers, deploys services
2. Automatic hot-reload on code changes
3. Port-forwarding to localhost:8000
4. Integrated log viewing in Tilt UI

## 8. Design Decisions & Rationale

1. **Kubernetes Jobs over Dagger:** Native Kubernetes integration provides better observability, standard tooling, and cloud portability.
2. **kubectl logs for Streaming:** Direct integration with Kubernetes logging eliminates custom streaming infrastructure.
3. **Helm for Deployment:** Industry-standard deployment method with excellent templating and configuration management.
4. **Tilt for Development:** Dramatically improves developer experience with automatic rebuilds and deployments.
5. **Local Registry Pattern:** Speeds up development cycles by avoiding remote registry pushes.
6. **Batch Jobs for Parallelism:** Kubernetes batch Jobs with parallelism settings can efficiently manage multiple agents.

## 9. Security Considerations

1. **RBAC:** Service account with minimal required permissions
2. **Secret Management:** Anthropic API keys stored as Kubernetes Secrets
3. **Network Policies:** (Future) Restrict pod-to-pod communication
4. **Resource Limits:** Memory and CPU limits on agent containers
5. **Job TTL:** Automatic cleanup prevents resource accumulation

## 10. Performance & Scalability

1. **Horizontal Scaling:** FastAPI pods can be scaled horizontally
2. **Job Parallelism:** Kubernetes manages concurrent Job execution
3. **Resource Quotas:** Namespace-level limits prevent runaway resource usage
4. **Log Streaming:** Direct kubectl integration minimizes latency
5. **Local Development:** k3d provides near-production performance locally

## 11. Monitoring & Observability

1. **Kubernetes Events:** Job lifecycle events tracked automatically
2. **Pod Logs:** All agent output captured in standard Kubernetes logs
3. **Metrics:** (Future) Prometheus metrics for Job success/failure rates
4. **Tracing:** (Future) OpenTelemetry for request tracing
5. **Tilt UI:** Real-time visibility during development