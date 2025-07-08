#!/bin/bash
# AIdeator Quick Start Script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 AIdeator Quick Start${NC}"
echo "========================="

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo -e "${RED}❌ Error: Not in the AIdeator directory${NC}"
    echo "Please run this script from the project root"
    exit 1
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found${NC}"
    echo "Creating .env from .env.example..."
    
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env file${NC}"
        echo -e "${YELLOW}⚠️  Please add your ANTHROPIC_API_KEY to .env${NC}"
        read -p "Press Enter after adding your API key..."
    else
        echo -e "${RED}❌ No .env.example found${NC}"
        echo "Please create a .env file with:"
        echo "ANTHROPIC_API_KEY=your-api-key-here"
        exit 1
    fi
fi

# Check for Python and uv
echo -e "\n${BLUE}🐍 Checking Python environment...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv not found${NC}"
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo -e "${GREEN}✅ Installed uv${NC}"
fi

# Install dependencies
echo -e "\n${BLUE}📦 Installing dependencies...${NC}"
uv pip install -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Check Docker
echo -e "\n${BLUE}🐳 Checking Docker...${NC}"
if ! docker ps &> /dev/null; then
    echo -e "${RED}❌ Docker is not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"

# Build agent image
echo -e "\n${BLUE}🏗️  Building agent Docker image...${NC}"
echo "This may take a minute on first run..."
uv run python -c "
import asyncio
from app.services.docker_service import DockerService

async def build():
    docker = DockerService()
    await docker.build_agent_image(force_rebuild=True)
    print('✅ Agent image built successfully')

asyncio.run(build())
"

# Start the server
echo -e "\n${GREEN}✅ Everything is ready!${NC}"
echo -e "\n${BLUE}Starting AIdeator server...${NC}"
echo "Server will be available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo -e "\n${YELLOW}Press Ctrl+C to stop the server${NC}\n"

# Run the server
uv run uvicorn app.main:app --reload --port 8000