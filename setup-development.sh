#!/bin/bash

# AIdeator Development Setup Script
# Sets up a student-friendly development environment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AIdeator Development Setup${NC}"
echo "This script will configure a student-friendly development environment"
echo

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if .env.local exists
if [[ -f ".env.local" ]]; then
    print_warning ".env.local already exists"
    read -p "Do you want to overwrite it? (y/N): " overwrite
    if [[ $overwrite != "y" && $overwrite != "Y" ]]; then
        echo "Setup cancelled. Edit .env.local manually if needed."
        exit 0
    fi
fi

# Copy .env.example to .env.local
cp .env.example .env.local
print_status "Created .env.local from template"

# Check if user wants to add API keys now
echo
echo -e "${BLUE}🔑 API Key Configuration${NC}"
echo "You can add your API keys now or later by editing .env.local"
echo

read -p "Do you want to add your OpenAI API key now? (y/N): " add_openai
if [[ $add_openai == "y" || $add_openai == "Y" ]]; then
    read -p "Enter your OpenAI API key (sk-...): " openai_key
    if [[ $openai_key == sk-* ]]; then
        sed -i.bak "s/OPENAI_API_KEY=sk-your-openai-key-here/OPENAI_API_KEY=$openai_key/" .env.local
        print_status "OpenAI API key configured"
    else
        print_warning "Invalid OpenAI key format (should start with sk-)"
    fi
fi

read -p "Do you want to add your Anthropic API key now? (y/N): " add_anthropic
if [[ $add_anthropic == "y" || $add_anthropic == "Y" ]]; then
    read -p "Enter your Anthropic API key (sk-ant-...): " anthropic_key
    if [[ $anthropic_key == sk-ant-* ]]; then
        sed -i.bak "s/ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here/ANTHROPIC_API_KEY=$anthropic_key/" .env.local
        print_status "Anthropic API key configured"
    else
        print_warning "Invalid Anthropic key format (should start with sk-ant-)"
    fi
fi

# Clean up backup file
rm -f .env.local.bak

echo
echo -e "${GREEN}🎉 Development environment configured!${NC}"
echo
echo "Next steps:"
echo "1. Start the development environment:"
echo -e "   ${BLUE}tilt up${NC}"
echo
echo "2. Or start components individually:"
echo -e "   ${BLUE}cd frontend && npm run dev${NC}  (Frontend only)"
echo
echo "3. Access your application:"
echo "   • Frontend: http://localhost:3000"
echo "   • API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo
echo "4. Test user (auto-created):"
echo "   • Email: test@aideator.local"
echo "   • Password: testpass123"
echo
echo "5. To add more API keys later:"
echo -e "   ${BLUE}nano .env.local${NC}"
echo

# Check if we have Tilt
if command -v tilt >/dev/null 2>&1; then
    echo -e "${BLUE}💡 Tip: Run 'tilt up' to start the full development environment${NC}"
else
    print_warning "Tilt not found. Install from: https://tilt.dev/"
fi

echo
print_status "Setup complete! Happy coding! 🛠️"