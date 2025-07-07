
# **Product Requirements Document (PRD): AIdeator MVP**

*   **Version:** 2.0
*   **Focus:** Dagger-Powered LLM Orchestration Platform

### **Changelog from v1.2**

*   **Container-Based Orchestration:** Using Dagger for containerized, isolated agent execution environments
*   **Enhanced Architecture:** Moving from simple BackgroundTasks to sophisticated container orchestration
*   **Better Resource Management:** Each agent runs in its own container with controlled resources
*   **Reproducibility:** Consistent environments across all agent variations

## 1. Introduction & Vision

Software developers and AI engineers are in a constant loop of trial and error when prompting LLMs for code generation. It's difficult to compare different approaches without a structured process. More importantly, the reasoning *behind* an AI's output is often a black box.

**AIdeator** is a tool for developers that accelerates this iterative loop and provides transparency. It allows engineers to prompt an LLM agent on a codebase under multiple, parallel conditions. By streaming the agent's entire thought process for each variation, AIdeator allows developers to not just compare the final results, but to understand *how* the agent arrived at its solution, turning prompt engineering from an art into an observable science.

## 2. MVP Objective

To build a Dagger-powered backend service that orchestrates LLM agents in isolated containers. The service will:
1.  Accept a GitHub repository URL, prompt, and number of variations `N`
2.  Use Dagger to spin up `N` isolated containers, each with:
    - Cloned repository
    - Claude API access
    - Controlled environment
3.  Stream each container's LLM agent output in real-time via SSE
4.  Allow users to select and persist their preferred variation
5.  Leverage Dagger's caching for efficient subsequent runs

Success: A robust API that demonstrates **containerized LLM orchestration** with real-time observability.

## 3. Scope

#### **IN SCOPE (Must-Haves for the MVP)**

*   **Dagger Integration:** Full Dagger SDK integration for container orchestration
*   **Container-Based Agent Execution:** Each LLM agent runs in its own Dagger container with:
    - Isolated filesystem
    - Dedicated resources
    - Cached dependencies
*   **API Endpoints:**
    - `POST /runs` - Submit new run with repo URL, prompt, and variations
    - `GET /runs/{id}/stream` - SSE endpoint for real-time agent output
    - `POST /runs/{id}/select` - Persist winning variation
*   **Real-time Streaming:** Token-by-token streaming from containerized agents via SSE
*   **Parallel Orchestration:** Concurrent container execution for N variations
*   **SQLite + SQLModel:** Async database for run metadata and selections
*   **Environment Isolation:** Each agent gets a fresh environment with cloned repo

#### **OUT OF SCOPE (Post-MVP)**

*   **Sandboxed Code Execution:** We will **not** run or execute any code.
*   **Repository Context Pre-processing:** We will **not** read files or construct a context string. The agent gets the repo path and the prompt, that's it.
*   **Downloading Final Code:** Providing the modified code base for download is a future feature.
*   **Frontend Client:** The UI is out of scope for this backend PRD.
*   **Intelligent Learning / "Super Diff"**
*   **User Authentication & Authorization**
*   **Private Repositories**

## 4. User Stories (Backend Perspective)

*   **As a Frontend Developer,** I want to call a single API endpoint with a repo URL and a prompt, so that I can kick off a new agent comparison job.
*   **As a Frontend Developer,** I want to receive a unique `run_id` after submission, so I can use it to subscribe to a result stream.
*   **As a Frontend Developer,** I want to connect to a streaming endpoint and receive the distinct, real-time thought process from each of the `N` agent variations, so I can display them to the end-user as they happen.
*   **As a Frontend Developer,** I want to call an endpoint with the `run_id` and the `variation_id` that the user selected, so the backend can store this preference.

## 5. Technical Architecture

### Core Stack
*   **FastAPI** - Async web framework with automatic OpenAPI docs
*   **Dagger Python SDK** - Container orchestration and pipeline execution
*   **SQLite + SQLModel** - Async database with Pydantic integration
*   **Server-Sent Events (SSE)** - Real-time streaming protocol
*   **uv** - Fast Python package manager
*   **ruff + mypy** - Linting and type checking

### Orchestration Flow
1.  **Request Handler** returns `202 Accepted` immediately
2.  **Dagger Pipeline** executes:
    ```python
    async with dagger.Connection() as client:
        # Create base container with dependencies
        base = client.container().from_("python:3.11-slim")
        
        # Run N variations in parallel
        containers = [
            create_agent_container(base, repo_url, prompt, i)
            for i in range(variations)
        ]
        
        # Stream outputs concurrently
        await asyncio.gather(*[
            stream_container_output(c, run_id, i) 
            for i, c in enumerate(containers)
        ])
    ```
3.  **SSE Manager** broadcasts container outputs to connected clients
4.  **Database** tracks run metadata and final selections

## 6. API Specification (OpenAPI 3.0 Draft)

```yaml
openapi: 3.0.0
info:
  title: AIdeator MVP API
  version: 1.2.0
  description: API for orchestrating and streaming the thought process of LLM agents.

paths:
  /runs:
    post:
      summary: Create a new agent run
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                github_url:
                  type: string
                  example: "https://github.com/user/repo"
                prompt:
                  type: string
                  example: "Refactor the main.py file to be more modular."
                variations:
                  type: integer
                  description: "Number of variations to generate. Recommended 3, max 5."
                  default: 3
                  example: 3
      responses:
        '202':
          description: Accepted for processing. The client should now connect to the stream_url.
          content:
            application/json:
              schema:
                type: object
                properties:
                  run_id:
                    type: string
                    example: "run_def456"
                  stream_url:
                    type: string
                    example: "/runs/run_def456/stream"

  /runs/{run_id}/stream:
    get:
      summary: Stream the live thought process for all variations of a run
      parameters:
        - name: run_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: A stream of Server-Sent Events containing the agent's live output.
          content:
            text/event-stream:
              schema:
                type: string
                example: |
                  event: message
                  data: {"variation_id": 1, "type": "agent_output", "content": "Okay, I will start by analyzing the structure of `main.py`."}

                  event: message
                  data: {"variation_id": 2, "type": "agent_output", "content": "Understood. First, I need to list the files in the repository to get an overview."}

                  event: completion
                  data: {"variation_id": 1, "status": "completed"}

                  event: error
                  data: {"variation_id": 3, "status": "failed", "message": "API rate limit exceeded."}

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
          description: Selection successfully recorded.
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "success"
```

## 7. Why Dagger?

### Key Benefits
1. **Isolation**: Each agent runs in a completely isolated environment
2. **Reproducibility**: Consistent execution environments across runs
3. **Caching**: Dagger's intelligent caching speeds up subsequent runs
4. **Resource Control**: Fine-grained control over CPU/memory per agent
5. **Observability**: Built-in logging and monitoring of container execution
6. **Scalability**: Easy to distribute across multiple machines later

### Dagger-Specific Features
- **Pipeline as Code**: Define agent execution pipelines in Python
- **Container Reuse**: Base containers cached for faster startup
- **Streaming Output**: Native support for streaming container logs
- **Secret Management**: Secure handling of API keys
- **Parallel Execution**: Built-in primitives for concurrent operations

## 8. Design Decisions & Assumptions

1.  **Core Output is the Process:** The product delivered via the stream is the raw, real-time text output from the LLM agent. This is considered its "thought process."
2.  **Context is a Directory Path:** The backend's sole responsibility for context is to `git clone` the repository and provide the path to the LLM agent. The agent is responsible for its own exploration and file handling.
3.  **Errors are Data:** An error from the LLM API for one variation is a valid result. It will be streamed to the client as an `error` event so the UI can reflect that the variation failed.
4.  **Concurrency is Limited:** The system is designed to handle a small number (`N`, up to 5) of concurrent LLM streams per single user `run`. This is not designed for high-throughput, multi-tenant load in the MVP.