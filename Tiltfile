# Tiltfile for AIdeator development - Student-Friendly Version
load('ext://namespace', 'namespace_create')
load('ext://dotenv', 'dotenv')

# Load environment variables
dotenv(fn='.env')

# Configuration
update_settings(max_parallel_updates=3)
allow_k8s_contexts(['k3d-aideator', 'docker-desktop', 'kind-aideator'])

# Set up registry
default_registry('localhost:5005', host_from_cluster='ctlptl-registry:5000')

# Create namespace
namespace_create('aideator')

# Build container images
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
    live_update=[
        sync('app/', '/app/app/'),
        sync('prompts/', '/app/prompts/'),
        run('cd /app && pip install -e .', trigger=['pyproject.toml', 'requirements.txt']),
    ],
)

# Ensure cluster is ready
local_resource(
    'cluster-ready',
    cmd='kubectl cluster-info',
    labels=['infrastructure'],
)

# Deploy simple Kubernetes resources - No Helm!
k8s_yaml(['k8s/database.yaml', 'k8s/redis.yaml', 'k8s/litellm.yaml', 'k8s/api.yaml', 'k8s/rbac.yaml'])

# Configure port forwards - Simple and Predictable
k8s_resource('aideator-api', port_forwards='8000:8000', labels=['backend'])
k8s_resource('aideator-database', port_forwards='5432:5432', labels=['database'])
k8s_resource('aideator-redis', port_forwards='6379:6379', labels=['cache'])
k8s_resource('aideator-litellm', port_forwards='4000:4000', labels=['ai-gateway'])

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

# Database migration (run once after database is ready)
local_resource(
    'database-migrate',
    cmd='DATABASE_URL="postgresql+asyncpg://aideator:aideator123@localhost:5432/aideator" uv run alembic upgrade head',
    deps=['alembic/'],
    resource_deps=['aideator-database'],
    labels=['database'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
)

# Print helpful information
print("""
✨ AIdeator Development Environment ✨

🎯 Student-Friendly Setup - No Helm Complexity!

🌐 Services:
  Frontend:  http://localhost:3000
  API:       http://localhost:8000
  API Docs:  http://localhost:8000/docs
  Redis:     localhost:6379
  LiteLLM:   http://localhost:4000
  Database:  localhost:5432

🔧 Commands:
  Run migration: tilt trigger database-migrate
  
🧘 Wise the Force be with you - Simple development, this is!
""")