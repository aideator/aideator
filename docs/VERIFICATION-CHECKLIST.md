# AIdeator Development Environment Verification

This checklist helps you verify that your AIdeator development environment is correctly set up with simplified authentication.

## 🎯 Quick Verification (5 minutes)

Run these commands in order. Each should succeed before moving to the next.

### ✅ Step 1: Basic Connectivity
```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected output:
# {
#   "status": "healthy",
#   "version": "1.0.0", 
#   "orchestration": "kubernetes",
#   "redis": "healthy"
# }
```

### ✅ Step 2: API Documentation Access
```bash
# Test API docs are available
curl -I http://localhost:8000/docs

# Expected: HTTP/200 OK
```

### ✅ Step 3: Test User Auto-Creation
```bash
# Get development test user credentials
curl http://localhost:8000/api/v1/auth/dev/test-login

# Expected: JSON with user info, access_token, and api_key
# Save the access_token for next steps
```

### ✅ Step 4: Authenticated Request
```bash
# Replace TOKEN with access_token from Step 3
TOKEN="your-access-token-here"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/auth/me

# Expected: User profile information
```

### ✅ Step 5: Database Integration
```bash
# Test database-backed endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/models

# Expected: JSON array (may be empty, but should not error)
```

## 🔍 Detailed Verification

### Environment Configuration Check
```bash
python -c "
from app.core.config import get_settings
settings = get_settings()

print('=== ENVIRONMENT VERIFICATION ===')
print(f'✅ Debug Mode: {settings.debug}')
print(f'✅ Environment: {getattr(settings, \"environment\", \"not set\")}')
print(f'✅ Simple Dev Mode: {getattr(settings, \"simple_dev_mode\", \"not set\")}')
print()

print('=== FEATURE FLAGS ===')
print(f'✅ Auto Test User: {getattr(settings, \"auto_create_test_user\", \"not set\")}')
print(f'✅ Require API Keys for Agents: {getattr(settings, \"require_api_keys_for_agents\", \"not set\")}')
# Removed: require_per_user_keys and enable_kubernetes_secrets flags - simplified
print()

print('=== API KEYS ===')
print(f'✅ OpenAI Key Configured: {bool(settings.openai_api_key)}')
print(f'✅ Anthropic Key Configured: {bool(settings.anthropic_api_key)}')
print(f'✅ Gemini Key Configured: {bool(settings.gemini_api_key)}')
print()

print('=== DATABASE ===')
print(f'✅ Database URL: {settings.database_url}')
print(f'✅ Redis URL: {getattr(settings, \"redis_url\", \"not set\")}')
"
```

**Expected Output:**
```
=== ENVIRONMENT VERIFICATION ===
✅ Debug Mode: True
✅ Environment: development
✅ Simple Dev Mode: True

=== FEATURE FLAGS ===
✅ Auto Test User: True
✅ Require API Keys for Agents: False
✅ Require Per-User Keys: False
✅ Enable Kubernetes Secrets: False

=== API KEYS ===
✅ OpenAI Key Configured: True
✅ Anthropic Key Configured: True
✅ Gemini Key Configured: True

=== DATABASE ===
✅ Database URL: postgresql+asyncpg://aideator:aideator123@localhost:5432/aideator
✅ Redis URL: redis://localhost:6379/0
```

### Application Startup Test
```bash
python -c "
print('Testing application startup...')
try:
    from app.main import create_application
    app = create_application()
    print('✅ Application created successfully')
    
    # Count endpoints
    api_routes = sum(1 for route in app.routes if hasattr(route, 'path') and route.path.startswith('/api/v1'))
    print(f'✅ {api_routes} API endpoints loaded')
    
    # Check middleware
    middleware_names = [mw.cls.__name__ for mw in app.user_middleware]
    if 'DevelopmentAuthMiddleware' in middleware_names:
        print('✅ Development authentication middleware loaded')
    else:
        print('❌ Development middleware missing')
        
    print('✅ Application startup verification complete')
        
except Exception as e:
    print(f'❌ Application startup failed: {e}')
    import traceback
    traceback.print_exc()
"
```

### Database Connection Test
```bash
python -c "
import asyncio
from app.core.database import engine

async def test_db():
    try:
        async with engine.begin() as conn:
            result = await conn.execute('SELECT 1 as test')
            row = result.fetchone()
            if row and row[0] == 1:
                print('✅ Database connection successful')
                return True
            else:
                print('❌ Database query failed')
                return False
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        return False

asyncio.run(test_db())
"
```

### Redis Connection Test
```bash
python -c "
import asyncio
from app.services.redis_service import redis_service

async def test_redis():
    try:
        await redis_service.connect()
        health = await redis_service.health_check()
        if health:
            print('✅ Redis connection successful')
        else:
            print('❌ Redis health check failed')
        await redis_service.disconnect()
    except Exception as e:
        print(f'❌ Redis connection failed: {e}')

asyncio.run(test_redis())
"
```

## 🧪 Functional Tests

### Test Complete Authentication Flow
```bash
#!/bin/bash
echo "=== AUTHENTICATION FLOW TEST ==="

# 1. Get test user token
echo "1. Getting test user token..."
RESPONSE=$(curl -s http://localhost:8000/api/v1/auth/dev/test-login)
TOKEN=$(echo $RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get test user token"
    exit 1
fi
echo "✅ Test user token obtained"

# 2. Test authenticated endpoint
echo "2. Testing authenticated endpoint..."
USER_INFO=$(curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/auth/me)
EMAIL=$(echo $USER_INFO | python -c "import sys, json; print(json.load(sys.stdin)['email'])" 2>/dev/null)

if [ "$EMAIL" = "test@aideator.local" ]; then
    echo "✅ Authenticated request successful"
else
    echo "❌ Authenticated request failed"
    exit 1
fi

# 3. Test API key functionality
echo "3. Testing API key functionality..."
MODELS=$(curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/models)
if echo $MODELS | grep -q "^\[\]$\|^\[.*\]$"; then
    echo "✅ API key functionality working"
else
    echo "❌ API key functionality failed"
    exit 1
fi

echo "✅ All authentication tests passed!"
```

### Test Global API Keys
```bash
python -c "
from app.services.global_key_service import global_key_service

print('=== GLOBAL API KEY SERVICE TEST ===')

# Test key availability
providers = ['openai', 'anthropic', 'google']
for provider in providers:
    key = global_key_service.get_provider_key(provider)
    if key:
        print(f'✅ {provider.capitalize()} key available')
    else:
        print(f'❌ {provider.capitalize()} key missing')

# Test available providers
available = global_key_service.get_available_providers()
print(f'\\n✅ Available providers: {sum(available.values())}/{len(available)}')

# Test Kubernetes env vars generation
env_vars = global_key_service.get_kubernetes_env_vars()
print(f'✅ Kubernetes env vars: {len(env_vars)} configured')
"
```

## 🚨 Common Issues & Solutions

### Issue: "Redis connection failed"
```bash
# Check Redis status
redis-cli ping
# Should return: PONG

# If not running:
brew services start redis  # macOS
sudo systemctl start redis-server  # Linux
```

### Issue: "Database connection failed"
```bash
# Check PostgreSQL status
pg_isready -h localhost -p 5432
# Should return: localhost:5432 - accepting connections

# Test connection manually
psql -h localhost -p 5432 -U aideator -d aideator -c "SELECT 1;"
```

### Issue: "Test user not created"
```bash
# Check if development middleware is loaded
python -c "
from app.core.config import get_settings
settings = get_settings()
print(f'Auto create test user: {settings.auto_create_test_user}')
print(f'Simple dev mode: {settings.simple_dev_mode}')
"

# Should both be True
```

### Issue: "API endpoints missing"
```bash
# Verify all modules are importing correctly
python -c "
try:
    from app.api.v1 import api_router
    print('✅ API router imported successfully')
    
    from app.api.v1 import runs, agent_outputs, auth
    print('✅ All endpoint modules imported')
except ImportError as e:
    print(f'❌ Import error: {e}')
"
```

### Issue: "Application won't start"
```bash
# Check virtual environment
which python
# Should show path to .venv/bin/python

# Check dependencies
pip list | grep -E "(fastapi|sqlalchemy|redis)"

# Reinstall if needed
pip install -e . --force-reinstall
```

## ✅ Success Criteria

Your environment is correctly set up when:

1. **Health check returns "healthy"** ✅
2. **API docs load at /docs** ✅  
3. **Test user auto-login works** ✅
4. **Authenticated requests succeed** ✅
5. **Database queries execute** ✅
6. **Redis connection healthy** ✅
7. **All API keys configured** ✅
8. **70+ endpoints available** ✅
9. **Development middleware loaded** ✅
10. **No encryption barriers** ✅

## 🎯 Quick Validation Script

Save this as `validate_setup.sh` and run it:

```bash
#!/bin/bash
set -e

echo "🚀 AIdeator Development Environment Validation"
echo "=" * 50

# Test 1: Health check
echo "Test 1: Health check..."
curl -sf http://localhost:8000/health > /dev/null && echo "✅ PASS" || echo "❌ FAIL"

# Test 2: API docs
echo "Test 2: API documentation..."
curl -sf http://localhost:8000/docs > /dev/null && echo "✅ PASS" || echo "❌ FAIL"

# Test 3: Test user
echo "Test 3: Test user auto-login..."
TOKEN=$(curl -s http://localhost:8000/api/v1/auth/dev/test-login | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
[ ! -z "$TOKEN" ] && echo "✅ PASS" || echo "❌ FAIL"

# Test 4: Authenticated request
echo "Test 4: Authenticated request..."
curl -sf -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/auth/me > /dev/null && echo "✅ PASS" || echo "❌ FAIL"

# Test 5: Database
echo "Test 5: Database integration..."
curl -sf -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/models > /dev/null && echo "✅ PASS" || echo "❌ FAIL"

echo ""
echo "🎉 Validation complete!"
echo "If all tests show ✅ PASS, your environment is ready!"
```

Run with: `chmod +x validate_setup.sh && ./validate_setup.sh`

---

*This verification ensures your AIdeator development environment is properly configured with simplified authentication and all necessary components working correctly.*