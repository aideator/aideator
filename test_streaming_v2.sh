#!/bin/bash
# AIdeator Progressive Streaming Test Script v2

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="http://localhost:8000"

# Debug mode
DEBUG=${DEBUG:-0}

# Global variable for run_id
RUN_ID=""

# Function to print colored output
print_color() {
    color=$1
    message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if server is running
check_server() {
    print_color $BLUE "\n🔍 Checking if server is running..."
    
    if curl -s -f "${BASE_URL}/api/v1/health" > /dev/null 2>&1; then
        print_color $GREEN "✅ Server is running"
        
        # Quick Docker check
        if docker ps >/dev/null 2>&1; then
            print_color $GREEN "✅ Docker is running"
        else
            print_color $RED "❌ Docker is not running"
            print_color $YELLOW "Start Docker Desktop or ensure Docker daemon is running"
            return 1
        fi
        return 0
    else
        print_color $RED "❌ Server is not running"
        print_color $YELLOW "\n💡 Start the server with:"
        echo "   cd /Users/cpb/git/aideator"
        echo "   uv run uvicorn app.main:app --reload --port 8000"
        return 1
    fi
}

# Function to create a run and set RUN_ID
create_run() {
    local github_url=$1
    local prompt=$2
    local variations=$3
    
    RUN_ID=""  # Reset global variable
    
    if [[ $DEBUG -eq 1 ]]; then
        print_color $YELLOW "\n📝 Creating run with:"
        echo "   GitHub URL: $github_url"
        echo "   Prompt: $prompt"
        echo "   Variations: $variations"
    fi
    
    # Build the JSON payload
    json_payload=$(cat <<EOF
{
    "github_url": "${github_url}",
    "prompt": "${prompt}",
    "variations": ${variations},
    "agent_config": {
        "model": "claude-3-5-sonnet-20241022",
        "temperature": 0.7,
        "max_tokens": 1000
    }
}
EOF
)
    
    if [[ $DEBUG -eq 1 ]]; then
        print_color $YELLOW "\n📤 Sending request to: ${BASE_URL}/api/v1/runs"
        echo "Payload:"
        echo "$json_payload" | jq .
    fi
    
    # Make the request
    response=$(curl -s -X POST "${BASE_URL}/api/v1/runs" \
        -H "Content-Type: application/json" \
        -d "$json_payload")
    
    # Parse response
    run_id=$(echo "$response" | jq -r '.run_id // empty')
    stream_url=$(echo "$response" | jq -r '.stream_url // empty')
    
    if [ -z "$run_id" ] || [ "$run_id" = "null" ]; then
        print_color $RED "❌ Failed to create run"
        if [[ $DEBUG -eq 1 ]]; then
            echo "Response:"
            echo "$response" | jq . 2>/dev/null || echo "$response"
        fi
        return 1
    fi
    
    RUN_ID="$run_id"  # Set global variable
    
    if [[ $DEBUG -eq 1 ]]; then
        print_color $GREEN "✅ Successfully created run: $run_id"
        echo "   Stream URL: $stream_url"
    fi
    
    return 0
}

# Function to stream with timestamps
stream_with_timestamps() {
    local run_id=$1
    local stream_url="/api/v1/runs/${run_id}/stream"
    
    print_color $BLUE "\n📡 Streaming events (press Ctrl+C to stop)..."
    print_color $YELLOW "URL: ${BASE_URL}${stream_url}\n"
    
    # Start streaming
    event_count=0
    curl -sN "${BASE_URL}${stream_url}" 2>&1 | while IFS= read -r line; do
        if [[ $line == event:* ]]; then
            event_type=${line#event: }
            if [[ $DEBUG -eq 1 ]]; then
                echo -e "\033[90m$line\033[0m"  # Gray for event lines
            fi
        elif [[ $line == data:* ]]; then
            timestamp=$(date +%H:%M:%S.%3N)
            data=${line#data: }
            
            # Parse JSON safely
            if echo "$data" | jq . >/dev/null 2>&1; then
                content=$(echo "$data" | jq -r '.content // empty' 2>/dev/null)
                variation_id=$(echo "$data" | jq -r '.variation_id // empty' 2>/dev/null)
                
                if [[ -n "$content" ]]; then
                    ((event_count++))
                    if [[ $content == *"Count:"* ]]; then
                        echo -e "[$timestamp] \033[1;33m🔢 Agent $variation_id: $content\033[0m"
                    elif [[ $content == *"ERROR:"* ]]; then
                        echo -e "[$timestamp] \033[1;31m❌ Agent $variation_id: $content\033[0m"
                    else
                        echo -e "[$timestamp] 📤 Agent $variation_id: $content"
                    fi
                elif [[ $event_type == "run_complete" ]]; then
                    echo -e "[$timestamp] 🏁 Run complete"
                    break
                elif [[ $event_type == "heartbeat" ]]; then
                    echo -e "[$timestamp] 💓 Heartbeat"
                fi
            fi
        fi
    done
    
    print_color $GREEN "\n✅ Stream ended (received $event_count agent output events)"
}

# Simple test menu
show_menu() {
    echo
    print_color $BLUE "========================================"
    print_color $BLUE "   AIdeator Streaming Test Menu"
    print_color $BLUE "========================================"
    echo "1) Quick test - Analyze Hello-World repo"
    echo "2) Slow test - Count with 1-second delays"
    echo "3) Parallel test - 3 agents"
    echo "4) Exit"
    echo
}

# Main function
main() {
    # Check server
    if ! check_server; then
        exit 1
    fi
    
    while true; do
        show_menu
        read -p "Select an option (1-4): " choice
        
        case $choice in
            1)
                print_color $GREEN "\n🚀 Running quick streaming test..."
                if create_run "https://github.com/octocat/Hello-World" \
                    "Analyze this repository step by step. List each file as you examine it." 1; then
                    print_color $GREEN "✅ Created run: $RUN_ID"
                    stream_with_timestamps "$RUN_ID"
                fi
                ;;
            
            2)
                print_color $GREEN "\n🐌 Running slow agent test..."
                if create_run "https://github.com/octocat/Hello-World" \
                    "SLOW_AGENT_TEST: Count to 5 with 1 second delays" 1; then
                    print_color $GREEN "✅ Created run: $RUN_ID"
                    print_color $YELLOW "⏱️  Watch for 1-second gaps between counts..."
                    stream_with_timestamps "$RUN_ID"
                fi
                ;;
            
            3)
                print_color $GREEN "\n👥 Running parallel agents test..."
                if create_run "https://github.com/fastapi/fastapi" \
                    "List the main Python files in this repository" 3; then
                    print_color $GREEN "✅ Created run: $RUN_ID with 3 agents"
                    stream_with_timestamps "$RUN_ID"
                fi
                ;;
            
            4)
                print_color $BLUE "\nGoodbye! 👋"
                exit 0
                ;;
            
            *)
                print_color $RED "Invalid option"
                ;;
        esac
        
        echo
        read -p "Press Enter to continue..."
    done
}

# Run
main