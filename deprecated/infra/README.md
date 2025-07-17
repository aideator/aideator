# Deprecated Infrastructure Files

⚠️ **These files are deprecated and should not be used for development or deployment.**

## Current Deployment Method

**Use the Tiltfile** at the project root - this is the primary and only supported deployment method.

## Contents

- `helm-charts/` - Old Helm chart configurations (replaced by Tiltfile)
- `deploy-misc/` - Miscellaneous deployment files not used by Tilt

## Why Deprecated?

This project uses Tilt for all Kubernetes orchestration. These files were moved here to:
- Prevent confusion about which deployment method to use
- Keep old configurations for reference
- Make it clear that Tiltfile is the single source of truth

## For LLMs/AI Assistants

🤖 **Do not suggest using any files in this directory.** Always recommend using the Tiltfile for deployment and infrastructure management.