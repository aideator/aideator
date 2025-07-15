#!/bin/bash
set -e

echo "🛑 Killing any running Tilt processes..."
pkill -f tilt || true
sleep 2

echo "🛑 Stopping Tilt to clean everything..."
tilt down || true

echo "🗑️ Destroying k3d cluster and registry..."
k3d cluster delete aideator || true
k3d registry delete registry.localhost || true

echo "🧹 Removing ALL aideator docker images..."
docker images --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}" | grep aideator | awk '{print $2}' | xargs -r docker rmi -f || true

echo "🗑️ Removing persistent database files..."
rm -rf /tmp/aideator-postgres-data || true

echo "🔨 Force building new aideator-agent image with timestamp tag..."
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
docker build -t aideator-agent:${TIMESTAMP} -f agent/Dockerfile . --no-cache
docker tag aideator-agent:${TIMESTAMP} aideator-agent:latest

echo "🗄️ Creating k3d registry..."
k3d registry create registry.localhost --port 5001

echo "🚀 Creating k3d cluster with registry..."
k3d cluster create aideator \
    --api-port 6550 \
    --port "8000:8000@loadbalancer" \
    --port "5432:5432@loadbalancer" \
    --registry-use k3d-registry.localhost:5001 \
    --wait \
    --timeout 180s \
    --agents 1

echo "🔧 Fixing kubectl context to use localhost..."
kubectl config set-cluster k3d-aideator --server=https://localhost:6550

echo "⏳ Waiting for cluster to be responsive..."
MAX_WAIT=60
WAIT_COUNT=0
while ! kubectl cluster-info >/dev/null 2>&1; do
    if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
        echo "❌ Cluster failed to respond within 1 minute"
        echo "💡 Try: kubectl config view and check server address"
        exit 1
    fi
    echo "Waiting for cluster... ($WAIT_COUNT/$MAX_WAIT)"
    sleep 3
    WAIT_COUNT=$((WAIT_COUNT + 3))
done

echo "✅ Cluster is ready! Starting Tilt..."
tilt up &
TILT_PID=$!

echo "⏳ Waiting for Tilt to initialize..."
sleep 60

echo "🏷️ Tagging and pushing to k3d registry..."
docker tag aideator-agent:latest localhost:5001/aideator-agent:${TIMESTAMP}
docker tag aideator-agent:latest localhost:5001/aideator-agent:latest
docker push localhost:5001/aideator-agent:${TIMESTAMP} || echo "⚠️ Push failed, continuing..."
docker push localhost:5001/aideator-agent:latest || echo "⚠️ Push failed, continuing..."

echo "🗑️ Cleaning any existing agent jobs..."
kubectl delete jobs -l app=aideator-agent -n aideator --ignore-not-found=true || true

echo "✅ Complete fresh rebuild with timestamp ${TIMESTAMP}!"
echo "🧪 Test with:"
echo "curl -X POST http://localhost:8000/api/v1/runs -H 'Content-Type: application/json' -d '{\"github_url\":\"https://github.com/fastapi/fastapi\",\"prompt\":\"Test fresh build\",\"model_variants\":[{\"model_definition_id\":\"gpt-4o-mini\"}],\"agent_mode\":\"litellm\"}'"