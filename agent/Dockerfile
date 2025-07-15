# Agent-specific Dockerfile using Python base with Claude CLI
FROM python:3.11-slim AS agent

USER root

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
RUN npm install -g @anthropic-ai/claude-code @google/gemini-cli

# Create nonroot user and directories
RUN useradd -m -u 1000 agentuser
WORKDIR /app
RUN chown agentuser:agentuser /app

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install minimal Python requirements for agent
COPY agent/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code only
COPY --chown=agentuser:agentuser agent/ ./agent/
COPY --chown=agentuser:agentuser app/models/ ./app/models/
COPY --chown=agentuser:agentuser app/core/config.py ./app/core/config.py

# Switch to nonroot user
USER agentuser

# Set working directory to workspace
WORKDIR /workspace

# Add /app to Python path so agent imports work
ENV PYTHONPATH="/app"

# Run agent
CMD ["python", "-m", "agent.main"]