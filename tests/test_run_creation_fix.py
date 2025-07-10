"""
Test for the run creation API fix.

This test verifies that the database schema fixes correctly allow
run creation with model variants.
"""

import httpx
import pytest


class TestRunCreationFix:
    """Test the fix for run creation with proper database schema."""

    @pytest.fixture
    def api_client(self):
        """Create API client for testing."""
        return httpx.Client(base_url="http://localhost:8000")

    @pytest.fixture
    def test_user_data(self):
        """Test user registration data."""
        return {
            "email": "test-run-creation@example.com",
            "password": "TestPass123"
        }

    @pytest.fixture
    def valid_run_request(self):
        """Valid run creation request with model variants."""
        return {
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

    def test_user_registration_and_api_key_creation(self, api_client, test_user_data):
        """Test user registration and API key creation still works."""
        # Register user
        response = api_client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 201
        user_data = response.json()
        assert "id" in user_data
        assert user_data["email"] == test_user_data["email"]

        # Login
        response = api_client.post("/api/v1/auth/login", json=test_user_data)
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data

        # Create API key
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        api_key_data = {"name": "Test Key", "description": "For testing run creation"}
        response = api_client.post("/api/v1/auth/api-keys", json=api_key_data, headers=headers)
        assert response.status_code == 201
        api_key_response = response.json()
        assert "api_key" in api_key_response
        assert api_key_response["api_key"].startswith("aid_sk_")

        return api_key_response["api_key"]

    def test_run_creation_with_model_variants(self, api_client, test_user_data, valid_run_request):
        """Test that run creation works with proper model variants after schema fix."""
        # Get API key
        api_key = self.test_user_registration_and_api_key_creation(api_client, test_user_data)

        # Create run with model variants
        headers = {"X-API-Key": api_key}
        response = api_client.post("/api/v1/runs", json=valid_run_request, headers=headers)

        # Verify successful creation
        assert response.status_code == 202  # HTTP_202_ACCEPTED
        run_data = response.json()

        # Verify response structure
        assert "run_id" in run_data
        assert "stream_url" in run_data
        assert "status" in run_data
        assert "estimated_duration_seconds" in run_data
        assert "session_id" in run_data
        assert "turn_id" in run_data

        # Verify response values
        assert run_data["run_id"].startswith("run-")
        assert run_data["status"] == "accepted"
        assert run_data["estimated_duration_seconds"] == len(valid_run_request["model_variants"]) * 40
        assert "/api/v1/runs/" in run_data["stream_url"]

        return run_data

    def test_run_details_retrieval(self, api_client, test_user_data, valid_run_request):
        """Test that we can retrieve run details after creation."""
        # Create run
        api_key = self.test_user_registration_and_api_key_creation(api_client, test_user_data)
        headers = {"X-API-Key": api_key}

        response = api_client.post("/api/v1/runs", json=valid_run_request, headers=headers)
        assert response.status_code == 202
        run_data = response.json()
        run_id = run_data["run_id"]

        # Retrieve run details
        response = api_client.get(f"/api/v1/runs/{run_id}", headers=headers)
        assert response.status_code == 200

        details = response.json()
        assert details["id"] == run_id
        assert details["github_url"] == valid_run_request["github_url"]
        assert details["prompt"] == valid_run_request["prompt"]
        assert details["status"] in ["pending", "running", "completed", "failed"]

    def test_run_list_contains_created_run(self, api_client, test_user_data, valid_run_request):
        """Test that created runs appear in the run list."""
        # Create run
        api_key = self.test_user_registration_and_api_key_creation(api_client, test_user_data)
        headers = {"X-API-Key": api_key}

        response = api_client.post("/api/v1/runs", json=valid_run_request, headers=headers)
        assert response.status_code == 202
        run_data = response.json()
        run_id = run_data["run_id"]

        # List runs
        response = api_client.get("/api/v1/runs", headers=headers)
        assert response.status_code == 200

        runs_list = response.json()
        assert "items" in runs_list
        assert len(runs_list["items"]) > 0

        # Find our run
        created_run = None
        for run in runs_list["items"]:
            if run["id"] == run_id:
                created_run = run
                break

        assert created_run is not None, f"Created run {run_id} not found in list"
        assert created_run["github_url"] == valid_run_request["github_url"]
        assert created_run["prompt"] == valid_run_request["prompt"]

    def test_database_schema_completeness(self, api_client, test_user_data, valid_run_request):
        """Test that all expected database fields are properly handled."""
        # Create run to test database schema
        api_key = self.test_user_registration_and_api_key_creation(api_client, test_user_data)
        headers = {"X-API-Key": api_key}

        response = api_client.post("/api/v1/runs", json=valid_run_request, headers=headers)
        assert response.status_code == 202
        run_data = response.json()
        run_id = run_data["run_id"]

        # Get run details to verify all schema fields
        response = api_client.get(f"/api/v1/runs/{run_id}", headers=headers)
        assert response.status_code == 200
        details = response.json()

        # Verify key schema fields exist (from our migrations)
        expected_fields = [
            "id", "github_url", "prompt", "status", "created_at",
            "winning_variation_id", "started_at", "completed_at",
            "results", "total_tokens_used", "total_cost"
        ]

        for field in expected_fields:
            assert field in details, f"Expected field '{field}' missing from run details"

        # Verify session and turn IDs are returned
        assert run_data["session_id"] is not None
        assert run_data["turn_id"] is not None

    def test_multiple_model_variants_accepted(self, api_client, test_user_data):
        """Test that multiple model variants are properly accepted."""
        api_key = self.test_user_registration_and_api_key_creation(api_client, test_user_data)
        headers = {"X-API-Key": api_key}

        # Test with 3 different model variants
        run_request = {
            "github_url": "https://github.com/octocat/Hello-World",
            "prompt": "Test multiple models",
            "model_variants": [
                {
                    "model_definition_id": "model_gpt_4o_mini_openai",
                    "model_parameters": {"temperature": 0.5}
                },
                {
                    "model_definition_id": "model_claude_3_5_haiku_anthropic",
                    "model_parameters": {"temperature": 0.7}
                },
                {
                    "model_definition_id": "model_gpt_4o_openai",
                    "model_parameters": {"temperature": 0.9}
                }
            ]
        }

        response = api_client.post("/api/v1/runs", json=run_request, headers=headers)
        assert response.status_code == 202

        run_data = response.json()
        # Estimated duration should reflect 3 variants
        assert run_data["estimated_duration_seconds"] == 3 * 40


if __name__ == "__main__":
    # Simple test runner for manual execution
    import sys

    print("Running Run Creation Fix Tests...")

    # Test basic API availability
    try:
        client = httpx.Client(base_url="http://localhost:8000")
        response = client.get("/api/v1/health")
        if response.status_code != 200:
            print(f"❌ API health check failed: {response.status_code}")
            sys.exit(1)
        print("✅ API is available")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        sys.exit(1)

    # Run a basic test
    test_instance = TestRunCreationFix()

    try:
        # Test user registration flow
        client = httpx.Client(base_url="http://localhost:8000")
        test_data = {"email": "manual-test@example.com", "password": "TestPass123"}

        api_key = test_instance.test_user_registration_and_api_key_creation(client, test_data)
        print("✅ User registration and API key creation works")

        # Test run creation
        run_request = {
            "github_url": "https://github.com/octocat/Hello-World",
            "prompt": "Test run creation after schema fix",
            "model_variants": [
                {
                    "model_definition_id": "model_gpt_4o_mini_openai",
                    "model_parameters": {"temperature": 0.7}
                }
            ]
        }

        run_data = test_instance.test_run_creation_with_model_variants(client, test_data, run_request)
        print(f"✅ Run creation successful: {run_data['run_id']}")

        print("✅ All manual tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
