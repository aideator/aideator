#!/usr/bin/env python3
"""
Manual test script to verify API functionality after database fixes.
"""
import json
import subprocess
import sys
import uuid


def run_curl(url, method="GET", data=None, headers=None):
    """Run curl command and return response."""
    cmd = ["curl", "-s"]

    if method != "GET":
        cmd.extend(["-X", method])

    if headers:
        for key, value in headers.items():
            cmd.extend(["-H", f"{key}: {value}"])

    if data:
        cmd.extend(["-H", "Content-Type: application/json"])
        cmd.extend(["-d", json.dumps(data)])

    cmd.append(url)

    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Request timed out"


def test_api_health():
    """Test API health endpoint."""
    print("🔍 Testing API health...")
    code, stdout, stderr = run_curl("http://localhost:8000/api/v1/health")

    if code != 0:
        print(f"❌ Health check failed: {stderr}")
        return False

    try:
        response = json.loads(stdout)
        print("✅ API is healthy")
        return True
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON response: {stdout}")
        return False


def test_user_flow():
    """Test complete user registration and run creation flow."""
    base_url = "http://localhost:8000"

    # Generate unique email
    unique_id = str(uuid.uuid4())[:8]
    email = f"test-{unique_id}@example.com"

    print(f"🔍 Testing user flow with email: {email}")

    # 1. Register user
    print("  → Registering user...")
    user_data = {"email": email, "password": "TestPass123"}
    code, stdout, stderr = run_curl(f"{base_url}/api/v1/auth/register", "POST", user_data)

    if code != 0:
        print(f"❌ Registration failed: {stderr}")
        return False

    try:
        user_response = json.loads(stdout)
        print(f"  ✅ User registered: {user_response.get('id', 'unknown')}")
    except json.JSONDecodeError:
        print(f"❌ Invalid registration response: {stdout}")
        return False

    # 2. Login
    print("  → Logging in...")
    code, stdout, stderr = run_curl(f"{base_url}/api/v1/auth/login", "POST", user_data)

    if code != 0:
        print(f"❌ Login failed: {stderr}")
        return False

    try:
        login_response = json.loads(stdout)
        access_token = login_response["access_token"]
        print("  ✅ Login successful")
    except (json.JSONDecodeError, KeyError):
        print(f"❌ Invalid login response: {stdout}")
        return False

    # 3. Create API key
    print("  → Creating API key...")
    api_key_data = {"name": "Test Key", "description": "For testing"}
    headers = {"Authorization": f"Bearer {access_token}"}
    code, stdout, stderr = run_curl(f"{base_url}/api/v1/auth/api-keys", "POST", api_key_data, headers)

    if code != 0:
        print(f"❌ API key creation failed: {stderr}")
        return False

    try:
        api_key_response = json.loads(stdout)
        api_key = api_key_response["api_key"]
        print(f"  ✅ API key created: {api_key[:20]}...")
    except (json.JSONDecodeError, KeyError):
        print(f"❌ Invalid API key response: {stdout}")
        return False

    # 4. Create run (this tests our database fixes)
    print("  → Creating run with model variants...")
    run_data = {
        "github_url": "https://github.com/octocat/Hello-World",
        "prompt": "Write a creative story about a robot who discovers emotions for the first time.",
        "model_variants": [
            {
                "model_definition_id": "model_gpt_4o_mini_openai",
                "model_parameters": {"temperature": 0.7}
            },
            {
                "model_definition_id": "model_claude_3_5_haiku_anthropic",
                "model_parameters": {"temperature": 0.8}
            }
        ]
    }

    headers = {"X-API-Key": api_key}
    code, stdout, stderr = run_curl(f"{base_url}/api/v1/runs", "POST", run_data, headers)

    if code != 0:
        print(f"❌ Run creation failed: {stderr}")
        return False

    try:
        run_response = json.loads(stdout)
        run_id = run_response["run_id"]
        print(f"  ✅ Run created successfully: {run_id}")

        # Verify response structure
        required_fields = ["run_id", "stream_url", "status", "estimated_duration_seconds", "session_id", "turn_id"]
        for field in required_fields:
            if field not in run_response:
                print(f"❌ Missing field in run response: {field}")
                return False

        print("  ✅ Response structure valid")
        print(f"    - Status: {run_response['status']}")
        print(f"    - Duration estimate: {run_response['estimated_duration_seconds']}s")
        print(f"    - Session ID: {run_response['session_id']}")
        print(f"    - Turn ID: {run_response['turn_id']}")

    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ Invalid run response: {stdout}")
        print(f"Error: {e}")
        return False

    # 5. Verify run appears in list
    print("  → Checking run appears in list...")
    code, stdout, stderr = run_curl(f"{base_url}/api/v1/runs", "GET", None, headers)

    if code != 0:
        print(f"❌ Run list failed: {stderr}")
        return False

    try:
        runs_response = json.loads(stdout)
        runs = runs_response.get("items", [])

        # Find our run
        found_run = None
        for run in runs:
            if run["id"] == run_id:
                found_run = run
                break

        if found_run:
            print("  ✅ Run found in list")
        else:
            print("❌ Run not found in list")
            return False

    except (json.JSONDecodeError, KeyError):
        print(f"❌ Invalid runs list response: {stdout}")
        return False

    # 6. Get run details
    print("  → Fetching run details...")
    code, stdout, stderr = run_curl(f"{base_url}/api/v1/runs/{run_id}", "GET", None, headers)

    if code != 0:
        print(f"❌ Run details failed: {stderr}")
        return False

    try:
        details_response = json.loads(stdout)

        # Verify database schema fields are present (from our migrations)
        schema_fields = [
            "id", "github_url", "prompt", "status", "created_at",
            "winning_variation_id", "started_at", "completed_at",
            "results", "total_tokens_used", "total_cost"
        ]

        missing_fields = []
        for field in schema_fields:
            if field not in details_response:
                missing_fields.append(field)

        if missing_fields:
            print(f"❌ Missing database fields: {missing_fields}")
            return False

        print("  ✅ All database schema fields present")

    except (json.JSONDecodeError, KeyError):
        print(f"❌ Invalid run details response: {stdout}")
        return False

    return True


def main():
    """Run all tests."""
    print("🧪 Running API Tests after Database Schema Fixes")
    print("=" * 60)

    # Test API health
    if not test_api_health():
        print("\n❌ API health test failed!")
        sys.exit(1)

    print()

    # Test complete user flow
    if not test_user_flow():
        print("\n❌ User flow test failed!")
        sys.exit(1)

    print()
    print("🎉 All tests passed! Database schema fixes are working correctly.")
    print("✅ Run creation with model variants is now functional")
    print("✅ Session and Turn creation is working")
    print("✅ Database migrations successfully applied")


if __name__ == "__main__":
    main()
