#!/bin/bash
# AIdeator Progressive Streaming Test Script

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

# Function to print colored output
print_color() {
    color=$1
    message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if server is running
check_server() {
    print_color $BLUE "\n🔍 Checking if server is running..."
    
    # Verbose check with timeout
    health_response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" --connect-timeout 2 "${BASE_URL}/api/v1/health" 2>&1)
    health_status=$(echo "$health_response" | grep "HTTP_STATUS:" | cut -d: -f2)
    health_body=$(echo "$health_response" | sed -e 's/HTTP_STATUS:.*//g')
    
    if [[ $DEBUG -eq 1 ]]; then
        print_color $CYAN "Debug: Health check response:"
        echo "Status: $health_status"
        echo "Body: $health_body"
    fi
    
    if [ "$health_status" = "200" ]; then
        print_color $GREEN "✅ Server is running"
        
        # Check Docker availability
        print_color $BLUE "\n🐳 Checking Docker..."
        if docker ps >/dev/null 2>&1; then
            print_color $GREEN "✅ Docker is running"
        else
            print_color $RED "❌ Docker is not running or not accessible"
            print_color $YELLOW "Start Docker Desktop or ensure Docker daemon is running"
            return 1
        fi
        
        # Check for required files
        print_color $BLUE "\n📁 Checking required files..."
        missing_files=()
        
        if [ ! -f "dagger_module/src/aideator/agent.py" ]; then
            missing_files+=("dagger_module/src/aideator/agent.py")
        fi
        if [ ! -f "dagger_module/src/aideator/slow_agent.py" ]; then
            missing_files+=("dagger_module/src/aideator/slow_agent.py")
        fi
        
        if [ ${#missing_files[@]} -ne 0 ]; then
            print_color $RED "❌ Missing required files:"
            for file in "${missing_files[@]}"; do
                echo "   - $file"
            done
            return 1
        else
            print_color $GREEN "✅ All required files present"
        fi
        
        return 0
    else
        print_color $RED "❌ Server is not running or not accessible"
        
        # Check if something else is using port 8000
        if lsof -i :8000 >/dev/null 2>&1; then
            print_color $YELLOW "⚠️  Port 8000 is in use by another process"
            echo "Processes using port 8000:"
            lsof -i :8000
        fi
        
        return 1
    fi
}

# Function to create a run and get the ID
create_run() {
    local github_url=$1
    local prompt=$2
    local variations=$3
    
    print_color $YELLOW "\n📝 Creating run with:"
    echo "   GitHub URL: $github_url"
    echo "   Prompt: $prompt"
    echo "   Variations: $variations"
    
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
    
    print_color $YELLOW "\n📤 Sending request to: ${BASE_URL}/api/v1/runs"
    echo "Payload:"
    echo "$json_payload" | jq .
    
    # Make the request with verbose output
    response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${BASE_URL}/api/v1/runs" \
        -H "Content-Type: application/json" \
        -d "$json_payload")
    
    # Extract HTTP status code
    http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d: -f2)
    response_body=$(echo "$response" | sed -e 's/HTTP_STATUS:.*//g')
    
    print_color $YELLOW "\n📥 Response status: $http_status"
    echo "Response body:"
    echo "$response_body" | jq . 2>/dev/null || echo "$response_body"
    
    # Parse response
    run_id=$(echo "$response_body" | jq -r '.run_id // empty')
    stream_url=$(echo "$response_body" | jq -r '.stream_url // empty')
    
    if [ -z "$run_id" ] || [ "$run_id" = "null" ]; then
        print_color $RED "❌ Failed to create run"
        
        # Check for specific error messages
        error_detail=$(echo "$response_body" | jq -r '.detail // empty')
        if [ -n "$error_detail" ]; then
            print_color $RED "Error: $error_detail"
        fi
        
        return 1
    fi
    
    print_color $GREEN "✅ Successfully created run: $run_id"
    echo "   Stream URL: $stream_url"
    
    echo $run_id
}

# Function to stream with timestamps
stream_with_timestamps() {
    local stream_url=$1
    print_color $BLUE "\n📡 Streaming events (press Ctrl+C to stop)..."
    print_color $YELLOW "URL: ${BASE_URL}${stream_url}\n"
    
    # Test if the stream URL is accessible
    print_color $YELLOW "🔍 Testing stream endpoint..."
    test_response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "${BASE_URL}${stream_url}" --max-time 2)
    test_status=$(echo "$test_response" | grep "HTTP_STATUS:" | cut -d: -f2)
    
    if [ "$test_status" != "200" ]; then
        print_color $RED "❌ Stream endpoint returned status: $test_status"
        echo "Response: $(echo "$test_response" | sed -e 's/HTTP_STATUS:.*//g')"
        return 1
    fi
    
    print_color $GREEN "✅ Stream endpoint is accessible\n"
    
    # Start streaming with verbose error handling
    curl -sN "${BASE_URL}${stream_url}" 2>&1 | while IFS= read -r line; do
        # Check for curl errors
        if [[ $line == *"curl:"* ]]; then
            print_color $RED "❌ Curl error: $line"
            continue
        fi
        
        if [[ $line == event:* ]]; then
            event_type=${line#event: }
            echo -e "\033[90m$line\033[0m"  # Gray for event lines
        elif [[ $line == data:* ]]; then
            timestamp=$(date +%H:%M:%S.%3N)
            data=${line#data: }
            
            # Parse JSON and extract content
            if command -v jq >/dev/null 2>&1; then
                # Check if data is valid JSON
                if ! echo "$data" | jq . >/dev/null 2>&1; then
                    print_color $RED "⚠️  Invalid JSON data: $data"
                    continue
                fi
                
                content=$(echo "$data" | jq -r '.content // empty' 2>/dev/null)
                variation_id=$(echo "$data" | jq -r '.variation_id // empty' 2>/dev/null)
                event_type=$(echo "$data" | jq -r '.type // empty' 2>/dev/null)
                
                if [[ -n "$content" ]]; then
                    if [[ $content == *"Count:"* ]]; then
                        # Highlight count lines
                        echo -e "[$timestamp] \033[1;33m🔢 Agent $variation_id: $content\033[0m"
                    elif [[ $content == *"ERROR:"* ]]; then
                        # Highlight errors
                        echo -e "[$timestamp] \033[1;31m❌ Agent $variation_id: $content\033[0m"
                    else
                        # Normal output
                        echo -e "[$timestamp] 📤 Agent $variation_id: $content"
                    fi
                elif [[ $event_type == "heartbeat" ]]; then
                    echo -e "[$timestamp] 💓 Heartbeat"
                elif [[ $event_type == "run_complete" ]]; then
                    echo -e "[$timestamp] 🏁 Run complete"
                    break
                else
                    # Other events
                    echo -e "[$timestamp] ℹ️  Event: $data"
                fi
            else
                # Fallback if jq is not available
                echo -e "[$timestamp] $line"
            fi
        elif [[ -n "$line" ]]; then
            echo "[$timestamp] Raw: $line"
        fi
    done
    
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        print_color $RED "\n❌ Stream ended with error code: $exit_code"
    else
        print_color $GREEN "\n✅ Stream completed successfully"
    fi
}

# Main menu
show_menu() {
    echo
    print_color $BLUE "========================================"
    print_color $BLUE "   AIdeator Streaming Test Menu"
    print_color $BLUE "========================================"
    echo "1) Quick test - Analyze Hello-World repo"
    echo "2) Slow test - Count with 1-second delays"
    echo "3) Parallel test - 3 agents analyzing FastAPI"
    echo "4) Custom test - Enter your own parameters"
    echo "5) Watch Docker containers"
    echo "6) Run diagnostics"
    echo "7) Exit"
    echo
    
    if [[ $DEBUG -eq 1 ]]; then
        print_color $CYAN "🐛 Debug mode is ON"
    else
        print_color $CYAN "💡 Tip: Run with DEBUG=1 for verbose output"
    fi
    echo
}

# Main loop
main() {
    # Check if server is running
    if ! check_server; then
        print_color $YELLOW "\n💡 Hint: Start the server in another terminal with:"
        echo "   cd /Users/cpb/git/aideator"
        echo "   uv run uvicorn app.main:app --reload --port 8000"
        exit 1
    fi
    
    while true; do
        show_menu
        read -p "Select an option (1-7): " choice
        
        case $choice in
            1)
                print_color $GREEN "\n🚀 Running quick streaming test..."
                # Capture only the last line (run_id) from create_run output
                run_id=$(create_run "https://github.com/octocat/Hello-World" \
                    "Analyze this repository step by step. List each file as you examine it." 1 | tail -n 1)
                if [ -n "$run_id" ] && [ "$run_id" != "null" ]; then
                    print_color $GREEN "✅ Created run: $run_id"
                    stream_with_timestamps "/api/v1/runs/${run_id}/stream"
                else
                    print_color $RED "❌ Failed to create run"
                fi
                ;;
            
            2)
                print_color $GREEN "\n🐌 Running slow agent test (watch for 1-second delays)..."
                # Capture only the last line (run_id) from create_run output
                run_id=$(create_run "https://github.com/octocat/Hello-World" \
                    "SLOW_AGENT_TEST: Count to 5 with 1 second delays" 1 | tail -n 1)
                if [ -n "$run_id" ] && [ "$run_id" != "null" ]; then
                    print_color $GREEN "✅ Created run: $run_id"
                    print_color $YELLOW "⏱️  Watch for exactly 1-second gaps between counts..."
                    stream_with_timestamps "/api/v1/runs/${run_id}/stream"
                else
                    print_color $RED "❌ Failed to create run"
                fi
                ;;
            
            3)
                print_color $GREEN "\n👥 Running parallel agents test..."
                # Capture only the last line (run_id) from create_run output
                run_id=$(create_run "https://github.com/fastapi/fastapi" \
                    "List the main Python files in this repository" 3 | tail -n 1)
                if [ -n "$run_id" ] && [ "$run_id" != "null" ]; then
                    print_color $GREEN "✅ Created run: $run_id with 3 agents"
                    print_color $YELLOW "📊 Watch for interleaved output from agents 0, 1, and 2..."
                    stream_with_timestamps "/api/v1/runs/${run_id}/stream"
                else
                    print_color $RED "❌ Failed to create run"
                fi
                ;;
            
            4)
                print_color $GREEN "\n🛠️  Custom test"
                read -p "GitHub URL: " github_url
                read -p "Prompt: " prompt
                read -p "Number of variations (1-5): " variations
                
                # Capture only the last line (run_id) from create_run output
                run_id=$(create_run "$github_url" "$prompt" "$variations" | tail -n 1)
                if [ -n "$run_id" ] && [ "$run_id" != "null" ]; then
                    print_color $GREEN "✅ Created run: $run_id"
                    stream_with_timestamps "/api/v1/runs/${run_id}/stream"
                else
                    print_color $RED "❌ Failed to create run"
                fi
                ;;
            
            5)
                print_color $GREEN "\n🐳 Watching Docker containers (press Ctrl+C to stop)..."
                watch -n 1 'docker ps --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}" --filter "label=aideator=true"'
                ;;
            
            6)
                print_color $BLUE "\n🔧 Running diagnostics..."
                
                # Test API endpoints
                print_color $YELLOW "\n📡 Testing API endpoints:"
                
                # Health check
                echo -n "  Health check: "
                health_status=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/v1/health")
                if [ "$health_status" = "200" ]; then
                    print_color $GREEN "✅ OK ($health_status)"
                else
                    print_color $RED "❌ Failed ($health_status)"
                fi
                
                # List runs
                echo -n "  List runs: "
                runs_status=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/v1/runs")
                if [ "$runs_status" = "200" ]; then
                    print_color $GREEN "✅ OK ($runs_status)"
                else
                    print_color $RED "❌ Failed ($runs_status)"
                fi
                
                # Docker check
                print_color $YELLOW "\n🐳 Docker diagnostics:"
                if docker version >/dev/null 2>&1; then
                    print_color $GREEN "✅ Docker is installed"
                    echo "  Version: $(docker version --format '{{.Server.Version}}')"
                    echo "  Running containers: $(docker ps -q | wc -l | tr -d ' ')"
                    echo "  AIdeator containers: $(docker ps -q --filter "label=aideator=true" | wc -l | tr -d ' ')"
                else
                    print_color $RED "❌ Docker is not accessible"
                fi
                
                # Check for agent image
                if docker images aideator-agent:latest -q >/dev/null 2>&1; then
                    print_color $GREEN "✅ Agent image exists"
                else
                    print_color $YELLOW "⚠️  Agent image not built (will be built on first run)"
                fi
                
                # Environment check
                print_color $YELLOW "\n🌍 Environment check:"
                echo "  Current directory: $(pwd)"
                echo "  Python: $(uv run python --version 2>&1)"
                
                # Check for .env file
                if [ -f ".env" ]; then
                    print_color $GREEN "✅ .env file exists"
                    # Check for API key (without showing it)
                    if grep -q "ANTHROPIC_API_KEY" .env; then
                        print_color $GREEN "✅ ANTHROPIC_API_KEY is set"
                    else
                        print_color $RED "❌ ANTHROPIC_API_KEY not found in .env"
                    fi
                else
                    print_color $RED "❌ .env file not found"
                fi
                ;;
            
            7)
                print_color $BLUE "\nGoodbye! 👋"
                exit 0
                ;;
            
            *)
                print_color $RED "Invalid option. Please try again."
                ;;
        esac
        
        echo
        read -p "Press Enter to continue..."
    done
}

# Check dependencies
check_dependencies() {
    local missing=()
    
    command -v curl >/dev/null 2>&1 || missing+=("curl")
    command -v jq >/dev/null 2>&1 || missing+=("jq")
    
    if [ ${#missing[@]} -ne 0 ]; then
        print_color $RED "❌ Missing dependencies: ${missing[*]}"
        print_color $YELLOW "Install with: brew install ${missing[*]}"
        exit 1
    fi
}

# Run the script
check_dependencies
main