# Tiltfile for AIdeator development - Student-Friendly Version (One Command!)
load('ext://namespace', 'namespace_create')
load('ext://dotenv', 'dotenv')

# Load environment variables
dotenv(fn='.env')

# Create k3d cluster automatically (Student-Friendly: One Command!)
# Docker Desktop compatible configuration
local_resource(
    'k3d-cluster',
    cmd='''
    if ! k3d cluster list | grep -q aideator; then
        echo "🚀 Creating k3d registry..."
        k3d registry create registry.localhost --port 5001 || echo "Registry may already exist"
        echo "🚀 Creating k3d cluster 'aideator' (Docker Desktop mode)..."
        k3d cluster create aideator \
            --api-port 6550 \
            --port "8000:8000@loadbalancer" \
            --port "5432:5432@loadbalancer" \
            --k3s-arg "--disable=traefik@server:0" \
            --registry-use k3d-registry.localhost:5001 \
            --wait \
            --timeout 120s \
            --agents 1
        echo "🔧 Fixing kubectl context to use localhost..."
        kubectl config set-cluster k3d-aideator --server=https://localhost:6550
        echo "✅ k3d cluster 'aideator' created successfully!"
    else
        echo "✅ k3d cluster 'aideator' already exists"
    fi
    ''',
    labels=['infrastructure'],
)

# Configuration
update_settings(max_parallel_updates=3, suppress_unused_image_warnings=["aideator-agent"])
allow_k8s_contexts(['k3d-aideator'])

# Configure default registry to use k3d's built-in registry
default_registry('localhost:5001')

# Create namespace
namespace_create('aideator')

# Build container images (push to k3d registry)
docker_build(
    'aideator-api',
    context='.',
    dockerfile='Dockerfile',
    only=[
        'app/',
        'pyproject.toml', 
        'requirements.txt',
        'scripts/',
        'prompts/',
        'alembic/',
        'alembic.ini',
        'k8s/',
    ],
)

# Build agent container image (push to k3d registry)
docker_build(
    'aideator-agent',
    context='.',
    dockerfile='agent/Dockerfile',
    only=[
        'agent/',
        'app/models/',
        'app/core/config.py',
        'pyproject.toml',
    ],
)

# Ensure cluster is ready (k3d cluster created automatically above)
local_resource(
    'cluster-ready',
    cmd='kubectl cluster-info',
    labels=['infrastructure'],
    resource_deps=[],  # No dependencies - cluster created by k3d_cluster()
)

# Ensure persistent data directory exists
local_resource(
    'setup-persistence',
    cmd='mkdir -p /tmp/aideator-postgres-data && echo "✅ Persistent database directory created at /tmp/aideator-postgres-data"',
    labels=['infrastructure'],
)

# Deploy simple Kubernetes resources - No Helm!
k8s_yaml(['k8s/database.yaml', 'k8s/api.yaml', 'k8s/rbac.yaml', 'k8s/pvc.yaml', 'k8s/agent-job-configmap.yaml'])

# Configure port forwards - Simple and Predictable
k8s_resource('aideator-api', port_forwards='8000:8000', labels=['backend'])
k8s_resource('aideator-database', port_forwards='5432:5432', labels=['database'], resource_deps=['setup-persistence'])

# Frontend development (runs locally)
local_resource(
    'frontend',
    serve_cmd='cd frontend && npm run dev',
    serve_env={
        'NEXT_PUBLIC_API_URL': 'http://localhost:8000',
    },
    deps=['frontend/'],
    ignore=[
        'frontend/node_modules/',
        'frontend/.next/',
        'frontend/out/',
        'frontend/coverage/',
    ],
    labels=['frontend'],
)

# Database migration (run automatically after database is ready)
local_resource(
    'database-migrate',
    cmd='DATABASE_URL="postgresql+asyncpg://aideator:aideator123@localhost:5432/aideator" uv run alembic upgrade head',
    deps=['alembic/'],
    resource_deps=['aideator-database'],
    labels=['database'],
    auto_init=True,
)

# Add test data after migration completes
local_resource(
    'add-test-data',
    cmd='DATABASE_URL="postgresql+asyncpg://aideator:aideator123@localhost:5432/aideator" uv run python scripts/add_mock_task_data.py',
    deps=['scripts/'],
    resource_deps=['database-migrate'],
    labels=['database'],
    auto_init=True,
)

# Print helpful information
print("""
✨ AIdeator Development Environment ✨

🎯 Student-Friendly Setup - No Helm Complexity!

🌐 Services:
  Frontend:  http://localhost:3000
  API:       http://localhost:8000
  API Docs:  http://localhost:8000/docs
  Database:  localhost:5432

💾 Persistence:
  Database data: /tmp/aideator-postgres-data (survives tilt down)
  Auto-migration: Runs on startup
  Test data: Added automatically on first run

🔧 Commands:
  Manual migration: tilt trigger database-migrate
  Manual test data: tilt trigger add-test-data
  
🧘 Wise the Force be with you - Simple development, this is!
""")