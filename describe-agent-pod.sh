#!/bin/bash

# Get the first pod that starts with "agent-run-" in the aideator namespace
POD_ID=$(kubectl get pods -n aideator --no-headers | grep '^agent-run-' | head -1 | awk '{print $1}')

if [ -z "$POD_ID" ]; then
    echo "No pod found starting with 'agent-run-' in namespace 'aideator'"
    exit 1
fi

echo "Found pod: $POD_ID"
echo "---"

# Describe the pod
kubectl describe pod "$POD_ID" -n aideator