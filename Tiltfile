# Tiltfile for AIdeator development
load('ext://namespace', 'namespace_create', 'namespace_inject')
load('ext://helm_resource', 'helm_resource', 'helm_repo')
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

# Agent image removed from Tilt - will be built separately for dynamic job spawning

# Ensure cluster is ready before creating secrets
local_resource(
    'cluster-ready',
    cmd='kubectl cluster-info',
    labels=['infrastructure'],
)

# Secrets management
local_resource(
    'create-secrets',
    cmd='./scripts/manage-secrets.sh create',
    deps=['.env', 'scripts/manage-secrets.sh'],
    resource_deps=['cluster-ready'],
    labels=['infrastructure'],
)

# Generate and apply Helm chart YAML  
yaml = helm(
    'deploy/charts/aideator',
    namespace='aideator',
    values=['deploy/values/local.yaml']
)
k8s_yaml(yaml)

# Configure individual resources with images and port forwards
# Ensure proper startup ordering: Database -> LiteLLM -> FastAPI
k8s_resource('chart-aideator-postgresql', port_forwards='5432:5432', labels=['database'], new_name='database')
k8s_resource('chart-redis-master', port_forwards='6379:6379', labels=['cache'], new_name='redis')
k8s_resource('chart-aideator-litellm', port_forwards='4000:4000', labels=['ai-gateway'], new_name='litellm', resource_deps=['database'])
k8s_resource('aideator-fastapi', port_forwards='8000:8000', labels=['backend'], new_name='api', resource_deps=['database', 'litellm'])

# Development user initialization is now handled automatically 
# by FastAPI startup events when DEBUG=true and GITHUB_TEST_USERNAME is set

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

# Development job template for testing agents
# k8s_yaml('''
# apiVersion: batch/v1
# kind: Job
# metadata:
#   name: agent-job-dev-test
#   namespace: aideator
#   labels:
#     app: aideator-agent
#     type: dev-test
# spec:
#   ttlSecondsAfterFinished: 300
#   backoffLimit: 0
#   template:
#     metadata:
#       labels:
#         app: aideator-agent
#         type: dev-test
#     spec:
#       serviceAccountName: aideator-agent
#       restartPolicy: Never
#       containers:
#       - name: agent
#         image: aideator-agent:dev
#         imagePullPolicy: IfNotPresent
#         env:
#         - name: RUN_ID
#           value: "dev-test-run"
#         - name: VARIATION_ID
#           value: "dev-test-variation"
#         - name: REDIS_HOST
#           value: "aideator-redis"
#         - name: REDIS_PORT
#           value: "6379"
#         - name: OPENAI_API_KEY
#           valueFrom:
#             secretKeyRef:
#               name: openai-secret
#               key: api-key
#         resources:
#           requests:
#             memory: "512Mi"
#             cpu: "500m"
#           limits:
#             memory: "2Gi"
#             cpu: "2000m"
# ''')

# k8s_resource(
#     'agent-job-dev-test',
#     labels=['dev-tools'],
#     auto_init=False,
#     trigger_mode=TRIGGER_MODE_MANUAL,
# )

# Print helpful information
print("""
✨ AIdeator Development Environment ✨

Frontend: http://localhost:{}
API: http://localhost:8000
API Docs: http://localhost:8000/docs

To create a test agent run:
  tilt trigger agent-job-dev-test

Wise the Force be with you. 🧘
""")