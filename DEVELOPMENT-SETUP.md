# AIdeator Development Setup Guide

This guide explains how to set up AIdeator for student/development use with simplified configuration while maintaining the user registration system for future features.

## 🎯 Quick Start (Student Mode)

### Option 1: Interactive Setup (Recommended)
```bash
./setup-development.sh
```

### Option 2: Manual Setup
```bash
# 1. Copy the environment template
cp .env.example .env.local

# 2. Edit .env.local and add your API keys
nano .env.local

# 3. Start development environment
tilt up
```

## 📋 What You Need

### Required
- **PostgreSQL** running on `localhost:5432` (or use SQLite alternative)
- **Redis** running on `localhost:6379`
- At least one **LLM API key** (OpenAI, Anthropic, or Google)

### API Keys (Get from these links)
- **OpenAI**: https://platform.openai.com/api-keys (format: `sk-...`)
- **Anthropic**: https://console.anthropic.com/settings/keys (format: `sk-ant-...`)
- **Google AI**: https://makersuite.google.com/app/apikey (format: `AIza...`)

## 🔧 Environment Configuration

The development setup uses `.env.local` which takes precedence over `.env`. This file contains feature flags that control what's enabled.

### Feature Flags Explained

```bash
# Authentication Features
REQUIRE_USER_REGISTRATION=true        # ✅ Keep user system (needed for future features)
REQUIRE_API_KEYS_FOR_AGENTS=false     # ❌ Skip per-user API key setup
REQUIRE_PER_USER_KEYS=false           # ❌ Use global keys instead of encrypted per-user
ENABLE_KUBERNETES_SECRETS=false       # ❌ Skip complex K8s secret management

# Security Features (disabled for development)
ENABLE_RATE_LIMITING=false            # ❌ No rate limits
ENABLE_CORS_STRICT=false              # ❌ Allow all origins
ENABLE_JWT_EXPIRATION=false           # ❌ Long-lived tokens (48 hours)

# Development Shortcuts
SIMPLE_DEV_MODE=true                  # ✅ Bypass authentication complexity
AUTO_CREATE_TEST_USER=true            # ✅ Auto-create test@aideator.local
```

### What This Means

**✅ ENABLED (Keep for future features):**
- User registration and login system
- JWT token authentication
- User database tables
- Basic RBAC (admin/user roles)

**❌ DISABLED (Simplified for development):**
- Per-user encrypted API key storage
- Complex Kubernetes secret injection
- Rate limiting and strict CORS
- Short-lived JWT tokens
- API key requirements for agent creation

## 🗄️ Database Setup

### PostgreSQL (Recommended)
```bash
# Using default connection in .env.local
DATABASE_URL=postgresql+asyncpg://aideator:aideator123@localhost:5432/aideator
```

### SQLite (Simpler Alternative)
```bash
# Change in .env.local to:
DATABASE_URL=sqlite+aiosqlite:///./aideator.db
```

## 🔑 API Key Management

### Development Mode (Global Keys)
When `REQUIRE_PER_USER_KEYS=false`, all agents use global environment variables:

```bash
# In .env.local
OPENAI_API_KEY=sk-your-actual-key-here
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
GEMINI_API_KEY=AIza-your-actual-key-here
```

### Production Mode (Per-User Keys)
When `REQUIRE_PER_USER_KEYS=true`, users manage their own encrypted keys via the web interface.

## 🧪 Test User

The system auto-creates a test user when `AUTO_CREATE_TEST_USER=true`:

- **Email**: `test@aideator.local`
- **Password**: `testpass123`
- **Role**: Admin (full access)

Use this for testing instead of creating your own accounts.

## 🚀 Starting the Application

### Full Development Environment (Recommended)
```bash
tilt up
```

Access points:
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Tilt Dashboard**: http://localhost:10350

### Frontend Only (for UI development)
```bash
cd frontend
npm run dev
```

### Backend Only (for API development)
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🔄 How Authentication Works

### Development Flow
```mermaid
graph TD
    A[Request] --> B{SIMPLE_DEV_MODE?}
    B -->|Yes| C[Use Test User]
    B -->|No| D[Normal Auth]
    C --> E[Agent Creation]
    D --> F[JWT/API Key Check]
    F --> E
```

### Production Flow
```mermaid
graph TD
    A[Request] --> B[JWT/API Key Required]
    B --> C[User Lookup]
    C --> D[Get User's Encrypted Keys]
    D --> E[Agent Creation]
```

## 📁 File Structure

### Environment Files
```
.env.example          # Template with all options documented
.env.local           # Your development config (gitignored)
.env                 # Fallback/production config
frontend/.env.local  # Frontend-specific config
```

### Development Infrastructure
```
setup-development.sh              # Interactive setup script
app/middleware/development.py     # Development auth bypass
app/services/global_key_service.py # Global API key management
app/core/config.py               # Enhanced with feature flags
```

## 🔧 Configuration Reference

### Core Settings
```bash
DEBUG=true                    # Enable debug logging
ENVIRONMENT=development       # Set environment mode
HOST=0.0.0.0                 # Server host
PORT=8000                    # Server port
LOG_LEVEL=info              # Logging level
```

### Database & Redis
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
REDIS_URL=redis://localhost:6379/0
```

### Security (Auto-generated in development)
```bash
SECRET_KEY=                  # Auto-generated if empty
ENCRYPTION_KEY=              # Auto-generated if empty
LITELLM_MASTER_KEY=         # Auto-generated if empty
```

### Agent Configuration
```bash
MAX_VARIATIONS=5             # Max agent variations per run
MAX_CONCURRENT_RUNS=10       # Max simultaneous runs
DEFAULT_AGENT_MODEL=gpt-4o-mini # Default LLM model
```

## 🔒 Security Notes

### Development Security
- Uses auto-generated keys (adequate for development)
- Long-lived JWT tokens (48 hours)
- Bypasses rate limiting
- Allows all CORS origins

### Production Security
- Requires manually set strong keys
- Short-lived JWT tokens (30 minutes)
- Enables rate limiting
- Strict CORS configuration
- Per-user encrypted API key storage

## 🚦 Troubleshooting

### Common Issues

**1. Database Connection Errors**
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Or switch to SQLite in .env.local
DATABASE_URL=sqlite+aiosqlite:///./aideator.db
```

**2. Redis Connection Errors**
```bash
# Check Redis is running
redis-cli ping

# Should return: PONG
```

**3. API Key Issues**
```bash
# Verify your API keys work
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

**4. Authentication Problems**
```bash
# Ensure simple dev mode is enabled
grep SIMPLE_DEV_MODE .env.local
# Should show: SIMPLE_DEV_MODE=true
```

### Reset Development Environment
```bash
# Reset everything
rm .env.local
./setup-development.sh

# Or just reset database
docker-compose down -v  # If using Docker
# Then restart: tilt up
```

## 🔄 Switching Between Development and Production

### Development Mode (Default in .env.local)
```bash
SIMPLE_DEV_MODE=true
REQUIRE_API_KEYS_FOR_AGENTS=false
REQUIRE_PER_USER_KEYS=false
ENABLE_KUBERNETES_SECRETS=false
```

### Production Mode
```bash
SIMPLE_DEV_MODE=false
REQUIRE_API_KEYS_FOR_AGENTS=true
REQUIRE_PER_USER_KEYS=true
ENABLE_KUBERNETES_SECRETS=true
ENVIRONMENT=production
```

## 📚 Additional Resources

### AIdeator Documentation
- [Architecture Overview](docs/architecture.md)
- [Frontend Development](frontend/CLAUDE.md)
- [Design System](frontend/DESIGN-SYSTEM.md)
- [API Documentation](http://localhost:8000/docs) (when running)

### External Documentation
- [Tilt Documentation](https://docs.tilt.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)

## 🤝 Contributing

### Development Workflow
1. Copy `.env.example` to `.env.local`
2. Add your API keys
3. Run `tilt up`
4. Make changes
5. Test with the auto-created test user
6. Submit PR

### Before Production Deployment
1. Set all feature flags to production values
2. Configure strong `SECRET_KEY` and `ENCRYPTION_KEY`
3. Set up proper Kubernetes secrets
4. Enable rate limiting and strict CORS
5. Test with real user registration flow

---

**🎯 The goal:** Make development as simple as adding API keys to `.env.local` and running `tilt up`, while preserving all production security features behind feature flags.