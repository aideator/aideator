# AIdeator Tiltfile - Kubernetes-based development environment

# Phase 1: Check cluster status
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
    target='api'
)

docker_build(
    'aideator-agent',
    context='.',
    dockerfile='./Dockerfile',
    target='agent'
)

# Phase 3: Create namespace
k8s_yaml(blob("""
apiVersion: v1
kind: Namespace
metadata:
  name: aideator
"""))

# Phase 4: Setup secrets (simple approach)
k8s_yaml(blob("""
apiVersion: v1
kind: Secret
metadata:
  name: anthropic-secret
  namespace: aideator
type: Opaque
stringData:
  api-key: sk-ant-api03-test-key-for-local-development-only
"""))

# Phase 5: Deploy with Helm
k8s_yaml(helm(
    'deploy/charts/aideator',
    name='aideator',
    namespace='aideator',
    values=['deploy/values/local.yaml']
))

# Phase 6: Expose services
k8s_resource(
    'aideator',
    port_forwards=['8000:8000'],
    labels=['api']
)

print("🚀 AIdeator development environment ready!")
print("🔗 FastAPI: http://localhost:8000")
print("📊 Docs: http://localhost:8000/docs")