# AIdeator Quick Start Guide

This guide will get you from zero to running AIdeator in development mode in under 10 minutes.

## 🎯 What You'll Have

- **Full AIdeator API** running locally
- **Simplified authentication** with auto-created test user
- **Global API keys** (no per-user encryption complexity)
- **PostgreSQL database** with all tables
- **All 78 endpoints** available and working

## 📋 Prerequisites

- **Python 3.11+** installed
- **PostgreSQL** running on localhost:5432
- **Redis** running on localhost:6379
- **Git** for cloning the repository
- **API keys** from at least one LLM provider

### Quick PostgreSQL Setup (if needed)
```bash
# macOS with Homebrew
brew install postgresql
brew services start postgresql
createdb aideator

# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb aideator
```

### Quick Redis Setup (if needed)
```bash
# macOS with Homebrew
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server
```

## 🚀 Setup Steps

### 1. Clone and Setup Project
```bash
git clone <your-repo-url>
cd aideator

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 2. Configure Environment
```bash
# Copy the template
cp .env.example .env.local

# Edit .env.local with your API keys
nano .env.local  # or use your preferred editor
```

**Required: Add your API keys to `.env.local`:**
```bash
# At minimum, add one of these:
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
GEMINI_API_KEY=AIza-your-gemini-key-here
```

### 3. Start the Server
```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Verify Setup
Open your browser to: **http://localhost:8000/docs**

You should see the Swagger API documentation with all endpoints available.

## ✅ Verification Checklist

### Test 1: Health Check
```bash
curl http://localhost:8000/health
```
**Expected result:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "orchestration": "kubernetes",
  "redis": "healthy"
}
```

### Test 2: API Documentation
Visit: http://localhost:8000/docs

**Expected result:** Swagger UI showing 70+ endpoints organized by tags:
- System (health check)
- Auth (authentication)
- Runs (agent management)
- Sessions (session management)
- Models (LLM models)
- Provider Keys (API key management)
- And more...

### Test 3: Test User Auto-Creation
```bash
curl http://localhost:8000/api/v1/auth/dev/test-login
```
**Expected result:**
```json
{
  "user": {
    "id": "user_test_...",
    "email": "test@aideator.local",
    "full_name": "Test User",
    "company": "AIdeator Development"
  },
  "access_token": "eyJ...",
  "token_type": "bearer",
  "api_key": "aid_sk_test_...",
  "message": "Development test user login successful"
}
```

### Test 4: Database Connection
```bash
curl http://localhost:8000/api/v1/models
```
**Expected result:** List of available LLM models (may be empty initially, but should not error).

### Test 5: API Key Configuration
Use the token from Test 3 to test authenticated endpoints:
```bash
# Get the access_token from test-login response
TOKEN="your-token-here"

curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/auth/me
```
**Expected result:** User profile information.

## 🐛 Troubleshooting

### Problem: "Redis connection failed"
**Solution:**
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# If not running:
brew services start redis  # macOS
sudo systemctl start redis-server  # Linux
```

### Problem: "Database connection failed"
**Solution:**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432
# Should return: localhost:5432 - accepting connections

# Check if database exists
psql -h localhost -p 5432 -U $USER -l | grep aideator

# Create database if missing
createdb aideator
```

### Problem: "No module named 'app'"
**Solution:**
```bash
# Make sure you're in the project directory and virtual environment is activated
source .venv/bin/activate
pip install -e .
```

### Problem: "Invalid API key format"
**Solution:**
- OpenAI keys start with `sk-`
- Anthropic keys start with `sk-ant-`
- Google keys start with `AIza`

Check your `.env.local` file for correct format.

### Problem: "Application startup failed"
**Solution:**
```bash
# Check Python version (must be 3.11+)
python --version

# Check virtual environment is activated
which python
# Should show path to .venv/bin/python

# Reinstall dependencies
pip install -e . --force-reinstall
```

## 🔧 Development Configuration Details

Your `.env.local` automatically enables these development features:

```bash
# Development mode settings (already configured)
DEBUG=true
ENVIRONMENT=development
SIMPLE_DEV_MODE=true
AUTO_CREATE_TEST_USER=true

# Simplified security (no complex encryption)
REQUIRE_API_KEYS_FOR_AGENTS=false
REQUIRE_PER_USER_KEYS=false
ENABLE_KUBERNETES_SECRETS=false
ENABLE_RATE_LIMITING=false
ENABLE_JWT_EXPIRATION=false
```

**What this means:**
- ✅ **No user registration required** - test user auto-created
- ✅ **Global API keys** - no per-user encryption
- ✅ **Long-lived tokens** - 48-hour JWT expiration
- ✅ **No rate limiting** - unlimited API calls
- ✅ **Simplified auth** - bypass complex workflows

## 🧪 Testing Your Setup

### Test an Agent Run (Full Workflow)
```bash
# 1. Get test user token
TEST_LOGIN=$(curl -s http://localhost:8000/api/v1/auth/dev/test-login)
TOKEN=$(echo $TEST_LOGIN | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 2. Create a test run (if runs endpoint is available)
curl -X POST http://localhost:8000/api/v1/runs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Analyze this codebase and provide a summary",
    "repo_url": "https://github.com/octocat/Hello-World",
    "variations": 2,
    "model": "gpt-4o-mini"
  }'

# 3. List your runs
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/runs
```

### Test Model Management
```bash
# List available models
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/models

# Get model definitions
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/models/definitions
```

## 📚 What's Next?

### For Development
1. **Explore the API** at http://localhost:8000/docs
2. **Check the logs** for any warnings or errors
3. **Test specific endpoints** you'll be working with
4. **Read the code** to understand the architecture

### For Production Later
When ready to deploy:
1. Set `SIMPLE_DEV_MODE=false` in production
2. Configure proper `SECRET_KEY` and `ENCRYPTION_KEY`
3. Enable per-user API key encryption
4. Set up Kubernetes secrets
5. Enable rate limiting and strict CORS

## 🆘 Getting Help

### Check Application Logs
```bash
# Watch logs in real-time
uvicorn app.main:app --reload --log-level debug

# Check for specific errors
grep -i error backend.log
```

### Validate Configuration
```bash
# Test configuration loading
python -c "
from app.core.config import get_settings
settings = get_settings()
print(f'Debug: {settings.debug}')
print(f'Simple Dev Mode: {settings.simple_dev_mode}')
print(f'OpenAI Key Set: {bool(settings.openai_api_key)}')
print(f'Database URL: {settings.database_url}')
"
```

### Reset Everything
```bash
# If things get broken, reset to clean state
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## 🎉 Success!

If all tests pass, you now have:
- ✅ **Full AIdeator API** running locally
- ✅ **Test user** with admin privileges
- ✅ **API keys** configured for LLM providers
- ✅ **Development mode** with simplified authentication
- ✅ **All endpoints** available and tested

**Ready to code!** Your development environment is fully operational.

---

*For more details, see:*
- `DEVELOPMENT-SETUP.md` - Comprehensive setup guide
- `FEATURE-FLAGS.md` - Development vs production configuration
- `CLAUDE.md` - Project-specific development notes