#!/bin/bash
# Test streaming by connecting immediately after creating run

# Create run and get run_id
echo "Creating run..."
RUN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/runs \
  -H "Content-Type: application/json" \
  -d '{
    "github_url": "https://github.com/octocat/Hello-World",
    "prompt": "Analyze this repository in detail, explain what each file does, and suggest improvements",
    "variations": 2
  }')

RUN_ID=$(echo $RUN_RESPONSE | jq -r .run_id)
STREAM_URL=$(echo $RUN_RESPONSE | jq -r .stream_url)

echo "Run ID: $RUN_ID"
echo "Immediately connecting to stream..."
echo "========================================="

# Connect to stream immediately (no delay)
curl -N "http://localhost:8000${STREAM_URL}" 2>/dev/null | while IFS= read -r line; do
    if [[ $line == event:* ]]; then
        echo -e "\n\033[1;34m$line\033[0m"  # Blue for events
    elif [[ $line == data:* ]]; then
        # Extract just the content from JSON
        content=$(echo "${line#data: }" | jq -r '.content // empty' 2>/dev/null)
        if [ -n "$content" ]; then
            echo -e "\033[0;32m$content\033[0m"  # Green for agent output
        else
            echo "$line"
        fi
    elif [[ ! -z "$line" ]]; then
        echo "$line"
    fi
done