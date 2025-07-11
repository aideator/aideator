# Multi-stage Dockerfile for AIdeator with optimized image sizes
# Using distroless and minimal base images for security and size

# Build stage for Python dependencies
FROM python:3.11-alpine AS python-builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
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

# Download kubectl
FROM alpine AS kubectl-builder
RUN apk add --no-cache curl && \
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    chmod +x kubectl

# Final API stage using distroless
FROM gcr.io/distroless/python3-debian12:nonroot AS api

# Copy Python virtual environment
COPY --from=python-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

# Copy kubectl
COPY --from=kubectl-builder /kubectl /usr/local/bin/kubectl

# Copy Node.js tools
COPY --from=node-builder /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=node-builder /usr/local/bin/claude-code /usr/local/bin/
COPY --from=node-builder /usr/local/bin/gemini-cli /usr/local/bin/
COPY --from=node-builder /usr/local/bin/codex /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=nonroot:nonroot app/ ./app/
COPY --chown=nonroot:nonroot k8s/ ./k8s/
COPY --chown=nonroot:nonroot alembic/ ./alembic/
COPY --chown=nonroot:nonroot alembic.ini ./
COPY --chown=nonroot:nonroot scripts/ ./scripts/

# Expose port
EXPOSE 8000

# Run FastAPI (distroless includes Python)
ENTRYPOINT ["python", "-m", "uvicorn"]
CMD ["app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Agent stage using minimal Alpine
FROM python:3.11-alpine AS agent

# Install runtime dependencies only
RUN apk add --no-cache \
    git \
    curl \
    nodejs \
    npm \
    ca-certificates \
    && rm -rf /var/cache/apk/*

# Copy Python virtual environment
COPY --from=python-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy kubectl
COPY --from=kubectl-builder /kubectl /usr/local/bin/kubectl

# Copy Node.js tools
COPY --from=node-builder /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=node-builder /usr/local/bin/claude-code /usr/local/bin/
COPY --from=node-builder /usr/local/bin/gemini-cli /usr/local/bin/
COPY --from=node-builder /usr/local/bin/codex /usr/local/bin/

# Create non-root user
RUN adduser -D -u 1000 agentuser

# Set working directory
WORKDIR /app

# Copy agent code
COPY --chown=agentuser:agentuser agent/ ./agent/
COPY --chown=agentuser:agentuser app/models/ ./app/models/
COPY --chown=agentuser:agentuser app/core/config.py ./app/core/config.py

# Switch to non-root user
USER agentuser

# Set working directory to workspace
WORKDIR /workspace

# Add /app to Python path so agent imports work
ENV PYTHONPATH="/app:$PYTHONPATH"

# Run agent
CMD ["python", "-m", "agent.main"]