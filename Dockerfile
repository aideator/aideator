# Multi-stage Dockerfile for AIdeator
FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
ARG NODE_MAJOR=22
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends curl gnupg ca-certificates; \
    curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | bash -; \
    apt-get install -y --no-install-recommends nodejs; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Claude Code and Gemini CLI globally
RUN npm install -g @anthropic-ai/claude-code @google/gemini-cli @openai/codex

# Install kubectl for Kubernetes operations
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# FastAPI API stage
FROM base AS api

# Copy application code
COPY app/ ./app/
COPY k8s/ ./k8s/

# Create non-root user
RUN useradd -m -u 1000 apiuser && chown -R apiuser:apiuser /app
USER apiuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Agent stage
FROM base AS agent

# Copy agent requirements and install dependencies
COPY agent/requirements.txt ./agent-requirements.txt
RUN pip install --no-cache-dir -r agent-requirements.txt

# Copy agent code
COPY agent/ ./agent/

# Create workspace directory
RUN mkdir -p /workspace && chmod 777 /workspace

# Create non-root user
RUN useradd -m -u 1000 agentuser && chown -R agentuser:agentuser /app /workspace
USER agentuser

# Set working directory to workspace
WORKDIR /workspace

# Run agent
CMD ["python", "-u", "/app/agent/main.py"]
