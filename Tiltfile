# AIdeator Tiltfile - Kubernetes-based development environment

# Phase 1: Check cluster status
local_resource(
    name="cluster-check",
    cmd="kubectl cluster-info",
    labels=["cluster"]
)

# Phase 2: Build containers
# Using k3d registry - ensure registry is configured correctly
default_registry('localhost:5005', host_from_cluster='ctlptl-registry:5000')

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
    # Load environment variables from .env file if it exists
    if [ -f .env ]; then
        echo "Loading environment variables from .env file..."
        export $(grep -v '^#' .env | xargs)
    fi
    
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

# Phase 7: Find an available port for frontend
# Check if user specified a port, otherwise find an available one
user_specified_port = os.getenv('FRONTEND_PORT', '')
if user_specified_port:
    frontend_port = user_specified_port
    print("🔍 Using user-specified frontend port: " + frontend_port)
else:
    # Find an available port starting from 3000
    port_check_result = local('bash -c \'for port in {3000..3010}; do if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then echo $port; break; fi; done\'', quiet=True)
    frontend_port = str(port_check_result).strip()
    if not frontend_port:
        fail("❌ No available ports found between 3000-3010")
    elif frontend_port != '3000':
        print("⚠️  Port 3000 is in use, using port " + frontend_port + " instead")

# Phase 8: Frontend (optional - runs outside container for hot reload)
# Use a script that checks if install is needed before running
frontend_cmd = '''
cd frontend && \
echo "📍 Current directory: $(pwd)" && \
echo "📁 Checking for lib/api.ts: $(ls -la lib/api.ts 2>/dev/null || echo 'NOT FOUND')" && \
if [ ! -d node_modules ] || [ package.json -nt node_modules ]; then \
    echo "📦 Installing dependencies..." && npm install; \
fi && \
if [ ! -d .next ]; then \
    echo "🧹 No Next.js cache found, starting fresh..."; \
fi && \
echo "🚀 Starting Next.js on port ''' + frontend_port + '''..." && \
PORT=''' + frontend_port + ''' npm run dev
'''

local_resource(
    name='frontend',
    serve_cmd=frontend_cmd,
    deps=['frontend/package.json'],  # Only restart when package.json changes
    labels=['frontend'],
    allow_parallel=True,
    readiness_probe=probe(
        http_get=http_get_action(port=int(frontend_port), path='/'),
        period_secs=5,
        failure_threshold=3
    ),
    links=['http://localhost:' + frontend_port]  # Add explicit link in Tilt UI
)

print("🚀 AIdeator development environment ready!")
print("🔗 Frontend: http://localhost:" + frontend_port)
print("🔗 FastAPI: http://localhost:8000")
print("📊 Docs: http://localhost:8000/docs")
if frontend_port != '3000':
    print("ℹ️  Using custom frontend port: " + frontend_port)