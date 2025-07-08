#!/bin/bash

echo "=== Automated SSE Verification Script ==="
echo "This script will create a run and immediately stream the results"
echo ""

# Create a run and capture the response
echo "Creating new run..."
RUN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/runs \
  -H "Content-Type: application/json" \
  -d '{
    "github_url": "https://github.com/octocat/Hello-World",
    "prompt": "Write a haiku about this repository",
    "variations": 1
  }')

# Extract run_id and stream_url
RUN_ID=$(echo "$RUN_RESPONSE" | jq -r '.run_id')
STREAM_URL=$(echo "$RUN_RESPONSE" | jq -r '.stream_url')

echo "✓ Created run: $RUN_ID"
echo "✓ Stream URL: $STREAM_URL"
echo ""
echo "=== Starting SSE Stream ==="
echo "Press Ctrl+C to stop"
echo ""

# Immediately connect to the SSE stream with pretty formatting
curl -N "http://localhost:8000${STREAM_URL}" 2>/dev/null | while IFS= read -r line; do
    if [[ $line == event:* ]]; then
        # Highlight event types in yellow
        echo -e "\033[1;33m$line\033[0m"
    elif [[ $line == data:* ]]; then
        # Extract JSON data
        json_data=$(echo "$line" | sed 's/^data: //')
        
        # Try to parse and display content field if it exists
        if content=$(echo "$json_data" | jq -r '.content' 2>/dev/null) && [ "$content" != "null" ]; then
            # Check if content is JSON (agent logs)
            if echo "$content" | jq . >/dev/null 2>&1; then
                # It's JSON, extract the message
                if msg=$(echo "$content" | jq -r '.message' 2>/dev/null) && [ "$msg" != "null" ]; then
                    echo -e "\033[1;36m[Agent]\033[0m $msg"
                else
                    echo -e "\033[1;32m[Output]\033[0m $content"
                fi
            else
                # It's plain text, just display it
                echo -e "\033[1;32m[Output]\033[0m $content"
            fi
        else
            # Can't parse content, show the full data line
            echo -e "\033[1;36mdata:\033[0m $json_data"
        fi
    elif [[ $line == id:* ]] || [[ $line == retry:* ]]; then
        # Show these in gray
        echo -e "\033[90m$line\033[0m"
    else
        # Empty lines or other content
        echo "$line"
    fi
done