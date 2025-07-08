# AIdeator Tiltfile - Kubernetes-based development environment

# Phase 1: Check cluster status
local_resource(
    name="cluster-check",
    cmd="kubectl cluster-info",
    labels=["cluster"]
)

# Phase 2: Build containers
# Using k3d registry - ensure registry is configured correctly
default_registry('localhost:5005', host_from_cluster='aideator-registry:5000')

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

# Phase 4: Create required secrets if they don't exist
local_resource(
    name="create-secrets",
    cmd="""
    # Check if secrets exist, create if not
    if ! kubectl get secret aideator-secret -n aideator 2>/dev/null; then
        echo "Creating aideator-secret..."
        kubectl create secret generic aideator-secret \
            --from-literal=secret-key="$(openssl rand -hex 32)" \
            -n aideator
    else
        echo "aideator-secret already exists"
    fi
    
    if ! kubectl get secret openai-secret -n aideator 2>/dev/null; then
        if [ -z "$OPENAI_API_KEY" ]; then
            echo "ERROR: OPENAI_API_KEY environment variable not set!"
            echo "Please set it with: export OPENAI_API_KEY='your-api-key'"
            echo "Creating openai-secret with placeholder (agents will fail)..."
            kubectl create secret generic openai-secret \
                --from-literal=api-key="sk-placeholder-please-set-OPENAI_API_KEY" \
                -n aideator
            echo ""
            echo "⚠️  WARNING: Agents will not work without a valid OPENAI_API_KEY!"
            echo "⚠️  Set the environment variable and run: tilt up"
            echo ""
        else
            echo "Creating openai-secret..."
            kubectl create secret generic openai-secret \
                --from-literal=api-key="$OPENAI_API_KEY" \
                -n aideator
        fi
    else
        echo "openai-secret already exists"
    fi
    """,
    deps=["deploy/charts/aideator/values.yaml"],
    labels=["setup"],
    resource_deps=["cluster-check"]
)

# Phase 5: Deploy with Helm (depends on secrets)
k8s_yaml(helm(
    'deploy/charts/aideator',
    name='aideator',
    namespace='aideator',
    values=['deploy/values/local.yaml']
))

# Phase 6: Expose services and ensure dependencies
k8s_resource(
    'aideator',
    port_forwards=['8000:8000'],
    labels=['api'],
    resource_deps=['create-secrets']
)

# Phase 7: Check if port 3000 is available
local_resource(
    name='port-check',
    cmd='''
    if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ ERROR: Port 3000 is already in use!"
        echo ""
        echo "Process using port 3000:"
        lsof -Pi :3000 -sTCP:LISTEN || true
        echo ""
        echo "Another process is using port 3000. Please either:"
        echo "1. Stop the other process using port 3000"
        echo "2. Configure Next.js to use a different port:"
        echo "   - Create frontend/.env.local with: PORT=3001"
        echo "   - Update the readiness_probe port in Tiltfile to match"
        echo ""
        exit 1
    else
        echo "✅ Port 3000 is available"
    fi
    ''',
    labels=['frontend']
)

# Phase 8: Frontend setup - ensure packages are installed
local_resource(
    name='frontend-setup',
    cmd='cd frontend && npm install',
    deps=['frontend/package.json', 'frontend/package-lock.json'],
    labels=['frontend'],
    resource_deps=['port-check']  # Check port before installing
)

# Phase 9: Frontend (optional - runs outside container for hot reload)
local_resource(
    name='frontend',
    cmd='cd frontend && npm run dev',
    serve_cmd='cd frontend && PORT=3000 npm run dev',  # Explicitly set port
    deps=['frontend/'],
    labels=['frontend'],
    allow_parallel=True,
    resource_deps=['frontend-setup'],  # Ensure npm install runs first
    readiness_probe=probe(
        http_get=http_get_action(port=3000, path='/'),
        period_secs=5,
        failure_threshold=3
    ),
    links=['http://localhost:3000']  # Add explicit link in Tilt UI
)

# Add a post-startup validation
local_resource(
    name='frontend-validate',
    cmd='''
    echo "Waiting for frontend to start..."
    sleep 5
    if curl -s http://localhost:3000 | grep -q "AIdeator"; then
        echo "✅ Frontend is running correctly on port 3000"
    else
        echo "⚠️  WARNING: Port 3000 is responding but doesn't appear to be AIdeator!"
        echo "Another application may be running on this port."
        echo "Tilt UI link may navigate to the wrong application."
    fi
    ''',
    resource_deps=['frontend'],
    labels=['frontend'],
    auto_init=False,  # Only run after frontend starts
    trigger_mode=TRIGGER_MODE_MANUAL
)

print("🚀 AIdeator development environment ready!")
print("🔗 Frontend: http://localhost:3000")
print("🔗 FastAPI: http://localhost:8000")
print("📊 Docs: http://localhost:8000/docs")