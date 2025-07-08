# AIdeator Tiltfile - Kubernetes-based development environment

# Phase 1: Check cluster status
local_resource(
    name="cluster-check",
    cmd="kubectl cluster-info",
    labels=["cluster"]
)

# Phase 2: Build containers
# Using default k3d registry at localhost:5005
default_registry('localhost:5005')

docker_build(
    'localhost:5005/aideator-api',
    context='.',
    dockerfile='./Dockerfile',
    target='api'
)

docker_build(
    'localhost:5005/aideator-agent',
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

# Phase 4: Secrets are created manually via kubectl

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

# Phase 7: Frontend (optional - runs outside container for hot reload)
local_resource(
    name='frontend',
    cmd='cd frontend && npm run dev',
    serve_cmd='cd frontend && npm run dev',
    deps=['frontend/'],
    labels=['frontend'],
    allow_parallel=True,
    readiness_probe=probe(
        http_get=http_get_action(port=3000, path='/'),
        period_secs=5,
        failure_threshold=3
    )
)

print("🚀 AIdeator development environment ready!")
print("🔗 Frontend: http://localhost:3000")
print("🔗 FastAPI: http://localhost:8000")
print("📊 Docs: http://localhost:8000/docs")