#!/usr/bin/env python3
"""
Comprehensive Development Environment Validation Script

This script validates that the development environment is properly configured
and can run without manual intervention.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import httpx
    import psycopg
    import redis
    from sqlalchemy import text
    
    from app.core.config import get_settings
    from app.core.database import engine
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Run: uv sync")
    sys.exit(1)


class Colors:
    """Terminal colors for output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    ENDC = '\033[0m'  # End color
    BOLD = '\033[1m'


def print_header(title: str):
    """Print section header."""
    print(f"\n{Colors.PURPLE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.PURPLE}{title.center(60)}{Colors.ENDC}")
    print(f"{Colors.PURPLE}{'='*60}{Colors.ENDC}\n")


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}❌ {message}{Colors.ENDC}")


def print_warning(message: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.ENDC}")


def print_info(message: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.ENDC}")


def validate_env_file():
    """Validate .env file exists and has required keys."""
    print_header("Environment File Validation")
    
    env_path = Path(".env")
    if not env_path.exists():
        print_error(".env file not found")
        return False
    
    print_success(".env file found")
    
    # Read and check for required keys
    with open(env_path) as f:
        content = f.read()
    
    required_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
    missing_keys = []
    
    for key in required_keys:
        if key not in content or f"{key}=" not in content:
            missing_keys.append(key)
        else:
            # Extract the value to check it's not empty
            lines = [line for line in content.split('\n') if line.startswith(f"{key}=")]
            if lines:
                value = lines[0].split('=', 1)[1].strip()
                if value and not value.startswith('your-') and not value.startswith('sk-placeholder'):
                    print_success(f"{key} is set and looks valid")
                else:
                    print_warning(f"{key} appears to be a placeholder")
            else:
                missing_keys.append(key)
    
    if missing_keys:
        print_error(f"Missing required keys: {', '.join(missing_keys)}")
        return False
    
    return True


def validate_settings():
    """Validate application settings."""
    print_header("Application Settings Validation")
    
    try:
        settings = get_settings()
        print_success("Settings loaded successfully")
        
        # Check simple dev mode
        if settings.simple_dev_mode:
            print_success("Simple dev mode is ENABLED")
        else:
            print_warning("Simple dev mode is DISABLED - may cause issues")
        
        # Check debug mode
        if settings.debug:
            print_success("Debug mode is ENABLED")
        else:
            print_info("Debug mode is DISABLED")
        
        # Check API keys
        if settings.openai_api_key:
            if settings.openai_api_key.startswith('sk-'):
                print_success("OpenAI API key format is valid")
            else:
                print_warning(f"OpenAI API key has unexpected format: {settings.openai_api_key[:20]}...")
        else:
            print_warning("OpenAI API key is not set")
        
        if settings.anthropic_api_key:
            if settings.anthropic_api_key.startswith('sk-ant-'):
                print_success("Anthropic API key format is valid")
            else:
                print_warning(f"Anthropic API key has unexpected format: {settings.anthropic_api_key[:20]}...")
        else:
            print_warning("Anthropic API key is not set")
        
        # Check URLs
        print_info(f"Database URL: {settings.database_url}")
        print_info(f"Redis URL: {settings.redis_url}")
        
        return True
        
    except Exception as e:
        print_error(f"Failed to load settings: {e}")
        return False


async def test_database():
    """Test database connection and schema."""
    print_header("Database Validation")
    
    try:
        # Test connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print_success(f"Database connected: {version}")
        
        # Check tables exist
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print_success(f"Found {len(tables)} tables: {', '.join(tables)}")
                
                # Check for required tables
                required_tables = ['runs', 'agent_outputs', 'users']
                missing_tables = [t for t in required_tables if t not in tables]
                
                if missing_tables:
                    print_warning(f"Missing tables: {', '.join(missing_tables)}")
                    print_info("Run: tilt trigger database-migrate")
                else:
                    print_success("All required tables present")
                
                # Check runs table schema
                if 'runs' in tables:
                    result = await conn.execute(text("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns 
                        WHERE table_name = 'runs' AND table_schema = 'public'
                        ORDER BY ordinal_position
                    """))
                    columns = {row[0]: row[1] for row in result.fetchall()}
                    
                    required_columns = ['id', 'github_url', 'prompt', 'task_status']
                    missing_columns = [c for c in required_columns if c not in columns]
                    
                    if missing_columns:
                        print_warning(f"Runs table missing columns: {', '.join(missing_columns)}")
                    else:
                        print_success("Runs table schema looks good")
                        
            else:
                print_warning("No tables found - database needs migration")
                
        return True
        
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        return False


async def test_redis():
    """Test Redis connection."""
    print_header("Redis Validation")
    
    try:
        settings = get_settings()
        if not settings.redis_url:
            print_warning("Redis URL not configured")
            return False
        
        # Parse Redis URL for connection
        redis_url = settings.redis_url
        if redis_url.startswith('redis://localhost:'):
            # Extract port for direct connection
            port = int(redis_url.split(':')[-1].split('/')[0])
            r = redis.Redis(host='localhost', port=port, decode_responses=True)
        else:
            r = redis.from_url(redis_url, decode_responses=True)
        
        # Test connection
        r.ping()
        print_success("Redis connection successful")
        
        # Test basic operations
        test_key = f"test_{datetime.now().timestamp()}"
        r.set(test_key, "test_value", ex=10)
        value = r.get(test_key)
        
        if value == "test_value":
            print_success("Redis read/write operations work")
        else:
            print_warning("Redis read/write test failed")
        
        r.delete(test_key)
        return True
        
    except Exception as e:
        print_error(f"Redis connection failed: {e}")
        return False


async def test_api_endpoints():
    """Test API endpoints."""
    print_header("API Endpoints Validation")
    
    base_url = "http://localhost:8000"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test health endpoint
            try:
                response = await client.get(f"{base_url}/health")
                if response.status_code == 200:
                    print_success("Health endpoint responding")
                else:
                    print_warning(f"Health endpoint returned {response.status_code}")
            except Exception as e:
                print_error(f"Health endpoint failed: {e}")
            
            # Test API docs
            try:
                response = await client.get(f"{base_url}/docs")
                if response.status_code == 200:
                    print_success("API docs accessible")
                else:
                    print_warning(f"API docs returned {response.status_code}")
            except Exception as e:
                print_error(f"API docs failed: {e}")
            
            # Test tasks endpoint (should work in dev mode)
            try:
                response = await client.get(f"{base_url}/api/v1/tasks")
                if response.status_code == 200:
                    print_success("Tasks endpoint accessible (auth bypassed)")
                    data = response.json()
                    print_info(f"Returned {len(data.get('tasks', []))} tasks")
                elif response.status_code == 401:
                    print_warning("Tasks endpoint requires auth - dev mode may not be working")
                else:
                    print_warning(f"Tasks endpoint returned {response.status_code}")
            except Exception as e:
                print_warning(f"Tasks endpoint test failed: {e}")
            
        return True
        
    except Exception as e:
        print_error(f"API testing failed: {e}")
        return False


async def test_kubernetes_resources():
    """Test Kubernetes resources."""
    print_header("Kubernetes Resources Validation")
    
    try:
        import subprocess
        
        # Check namespace
        result = subprocess.run(
            ["kubectl", "get", "namespace", "aideator"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print_success("aideator namespace exists")
        else:
            print_error("aideator namespace not found")
            return False
        
        # Check pods
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "aideator", "--no-headers"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            pods = result.stdout.strip().split('\n') if result.stdout.strip() else []
            running_pods = [p for p in pods if 'Running' in p]
            print_success(f"Found {len(pods)} pods, {len(running_pods)} running")
            
            for pod in pods:
                if pod.strip():
                    parts = pod.split()
                    name, ready, status = parts[0], parts[1], parts[2]
                    if status == 'Running' and '/' in ready:
                        ready_count, total_count = ready.split('/')
                        if ready_count == total_count:
                            print_success(f"  {name}: {status} ({ready})")
                        else:
                            print_warning(f"  {name}: {status} ({ready})")
                    else:
                        print_warning(f"  {name}: {status} ({ready})")
        else:
            print_error("Failed to get pods")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Kubernetes validation failed: {e}")
        return False


async def main():
    """Run all validations."""
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("🚀 AIdeator Development Environment Validator")
    print("=" * 50)
    print(f"{Colors.ENDC}")
    
    results = []
    
    # Run all validations
    results.append(validate_env_file())
    results.append(validate_settings())
    results.append(await test_database())
    results.append(await test_redis())
    results.append(await test_api_endpoints())
    results.append(await test_kubernetes_resources())
    
    # Summary
    print_header("Validation Summary")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print_success(f"All {total} validations passed! 🎉")
        print_info("Your development environment is ready to use.")
    else:
        failed = total - passed
        print_warning(f"{passed}/{total} validations passed, {failed} failed")
        print_info("Check the failed validations above for next steps.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)