#!/bin/bash
# Create a run and immediately stream its output

echo "Creating run and connecting to stream..."

# Create run and extract stream URL
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/runs \
  -H "Content-Type: application/json" \
  -d '{
    "github_url": "https://github.com/octocat/Hello-World",
    "prompt": "Analyze this repository and list all files",
    "variations": 1,
    "use_claude_code": false
  }')

RUN_ID=$(echo $RESPONSE | jq -r .run_id)
STREAM_URL=$(echo $RESPONSE | jq -r .stream_url)

echo "Run ID: $RUN_ID"
echo "Connecting to stream..."
echo "----------------------------------------"

# Immediately connect to the stream
curl -N "http://localhost:8000${STREAM_URL}"