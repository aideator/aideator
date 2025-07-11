# Multi-stage Dockerfile for AIdeator using Wolfi base images
# Following patterns from manifold build-config

# Build stage for Python dependencies using Wolfi
FROM cgr.dev/chainguard/wolfi-base:latest AS python-builder

USER root

# Install Python build dependencies
RUN apk --no-cache --update upgrade && apk --no-cache add \
    python-3.12 \
    py3.12-pip \
    python-3.12-dev \
    build-base \
    git \
    curl \
    nodejs \
    npm \
    ca-certificates \
    openssl \
    bash

# Install uv for faster Python package management
RUN pip install -Iv "uv==0.7.10"

# Set Python environment variables
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1
ENV UV_PYTHON_DOWNLOADS=never
ENV UV_PYTHON=python3.12
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

# Create virtual environment
RUN python3.12 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy Python requirements
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Claude Code and AI CLI tools globally
RUN npm install -g @anthropic-ai/claude-code

# Download kubectl
FROM cgr.dev/chainguard/wolfi-base:latest AS kubectl-builder
RUN apk add --no-cache curl && \
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    chmod +x kubectl

# Final API stage using Wolfi base
FROM cgr.dev/chainguard/wolfi-base:latest AS api

USER root

# Install runtime dependencies
RUN apk --no-cache --update upgrade && apk --no-cache add \
    python-3.12 \
    bash \
    git \
    ca-certificates \
    openssl

# Create nonroot user and directories
RUN adduser -D -u 1000 nonroot
WORKDIR /app
RUN chown nonroot:nonroot /app

# Copy Python virtual environment
COPY --from=python-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

# Copy kubectl
COPY --from=kubectl-builder /kubectl /usr/local/bin/kubectl

# Copy Node.js tools
COPY --from=python-builder /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=python-builder /usr/local/bin/claude-code /usr/local/bin/claude-code

# Copy application code
COPY --chown=nonroot:nonroot app/ ./app/
COPY --chown=nonroot:nonroot k8s/ ./k8s/
COPY --chown=nonroot:nonroot alembic/ ./alembic/
COPY --chown=nonroot:nonroot alembic.ini ./
COPY --chown=nonroot:nonroot scripts/ ./scripts/

# Switch to nonroot user
USER nonroot

# Expose port
EXPOSE 8000

# Run FastAPI
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Agent stage using Wolfi base
FROM cgr.dev/chainguard/wolfi-base:latest AS agent

USER root

# Install runtime dependencies
RUN apk --no-cache --update upgrade && apk --no-cache add \
    python-3.12 \
    bash \
    git \
    ca-certificates \
    openssl

# Create nonroot user and directories
RUN adduser -D -u 1000 agentuser
WORKDIR /app
RUN chown agentuser:agentuser /app

# Copy Python virtual environment
COPY --from=python-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy kubectl
COPY --from=kubectl-builder /kubectl /usr/local/bin/kubectl

# Copy Node.js tools
COPY --from=python-builder /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=python-builder /usr/local/bin/claude-code /usr/local/bin/claude-code

# Copy agent code
COPY --chown=agentuser:agentuser agent/ ./agent/
COPY --chown=agentuser:agentuser app/models/ ./app/models/
COPY --chown=agentuser:agentuser app/core/config.py ./app/core/config.py

# Switch to nonroot user
USER agentuser

# Set working directory to workspace
WORKDIR /workspace

# Add /app to Python path so agent imports work
ENV PYTHONPATH="/app:$PYTHONPATH"

# Run agent
CMD ["python", "-m", "agent.main"]