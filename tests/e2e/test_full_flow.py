import asyncio
import json

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestFullFlow:
    """End-to-end tests for complete user flows."""

    @pytest.mark.asyncio
    async def test_complete_run_flow(self, client: AsyncClient):
        """Test complete flow from user registration to run completion."""
        # 1. Register user
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "e2e_user@example.com",
                "password": "E2ETestPass123",
                "full_name": "E2E Test User",
                "company": "Test Corp",
            },
        )
        assert register_response.status_code == 201
        user_id = register_response.json()["id"]

        # 2. Login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "e2e_user@example.com",
                "password": "E2ETestPass123",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # 3. Create API key
        api_key_response = await client.post(
            "/api/v1/auth/api-keys",
            json={
                "name": "E2E Test Key",
                "scopes": ["runs:create", "runs:read"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert api_key_response.status_code == 201
        api_key = api_key_response.json()["api_key"]

        # 4. Create a run
        run_response = await client.post(
            "/api/v1/runs",
            json={
                "github_url": "https://github.com/fastapi/fastapi",
                "prompt": "Add comprehensive error handling to main.py",
                "variations": 2,
                "agent_config": {
                    "model": "claude-3-opus-20240229",
                    "temperature": 0.8,
                },
            },
            headers={"X-API-Key": api_key},
        )
        assert run_response.status_code == 202
        run_id = run_response.json()["run_id"]
        stream_url = run_response.json()["stream_url"]

        # 5. Connect to SSE stream and collect events
        events = []
        async with client.stream("GET", stream_url, headers={"X-API-Key": api_key}) as stream:
            assert stream.status_code == 200
            
            # Collect first 10 events or until complete
            async for line in stream.aiter_lines():
                if line.startswith("data:"):
                    try:
                        event_data = json.loads(line[6:])
                        events.append(event_data)
                    except json.JSONDecodeError:
                        pass
                
                if len(events) >= 10:
                    break

        # 6. Verify events were received
        assert len(events) > 0
        event_types = [e.get("event_type") or e.get("message") for e in events]
        assert any("heartbeat" in str(t).lower() or "connected" in str(t).lower() for t in event_types)

        # 7. Check run status
        status_response = await client.get(
            f"/api/v1/runs/{run_id}",
            headers={"X-API-Key": api_key},
        )
        assert status_response.status_code == 200
        run_data = status_response.json()
        assert run_data["id"] == run_id
        assert run_data["prompt"] == "Add comprehensive error handling to main.py"

        # 8. List user's runs
        list_response = await client.get(
            "/api/v1/runs",
            headers={"X-API-Key": api_key},
        )
        assert list_response.status_code == 200
        runs = list_response.json()["items"]
        assert any(r["id"] == run_id for r in runs)

    @pytest.mark.asyncio
    async def test_api_key_management_flow(self, client: AsyncClient, make_user):
        """Test complete API key management flow."""
        # Create and login user
        user = await make_user(email="key_test@example.com")
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "key_test@example.com",
                "password": "TestPassword123",
            },
        )
        token = login_response.json()["access_token"]
        auth = {"Authorization": f"Bearer {token}"}

        # Create multiple API keys
        key_names = ["Production", "Development", "Testing"]
        created_keys = []
        
        for name in key_names:
            response = await client.post(
                "/api/v1/auth/api-keys",
                json={
                    "name": f"{name} Key",
                    "scopes": ["runs:create", "runs:read"],
                    "expires_in_days": 90,
                },
                headers=auth,
            )
            assert response.status_code == 201
            created_keys.append(response.json())

        # List API keys
        list_response = await client.get("/api/v1/auth/api-keys", headers=auth)
        assert list_response.status_code == 200
        keys = list_response.json()
        assert len(keys) >= 3

        # Use one of the keys to create a run
        test_key = created_keys[0]["api_key"]
        run_response = await client.post(
            "/api/v1/runs",
            json={
                "github_url": "https://github.com/test/repo",
                "prompt": "Test with API key",
                "variations": 1,
            },
            headers={"X-API-Key": test_key},
        )
        assert run_response.status_code == 202

        # Delete a key
        key_id = created_keys[2]["key_info"]["id"]
        delete_response = await client.delete(
            f"/api/v1/auth/api-keys/{key_id}",
            headers=auth,
        )
        assert delete_response.status_code == 204

        # Verify key was deleted
        list_response2 = await client.get("/api/v1/auth/api-keys", headers=auth)
        remaining_keys = list_response2.json()
        assert len(remaining_keys) == len(keys) - 1
        assert not any(k["id"] == key_id for k in remaining_keys)

    @pytest.mark.asyncio
    async def test_concurrent_runs(self, client: AsyncClient, make_user, make_api_key):
        """Test handling multiple concurrent runs."""
        # Setup
        user = await make_user()
        api_key, _ = await make_api_key(user)
        headers = {"X-API-Key": api_key}

        # Create multiple runs concurrently
        async def create_run(index: int):
            response = await client.post(
                "/api/v1/runs",
                json={
                    "github_url": "https://github.com/test/repo",
                    "prompt": f"Concurrent test prompt {index}",
                    "variations": 2,
                },
                headers=headers,
            )
            return response.json()

        # Create 5 runs concurrently
        tasks = [create_run(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # Verify all were created
        assert all(r["status"] == "accepted" for r in results)
        run_ids = [r["run_id"] for r in results]
        assert len(set(run_ids)) == 5  # All unique

        # List runs
        list_response = await client.get("/api/v1/runs", headers=headers)
        runs = list_response.json()["items"]
        
        # Verify all runs are present
        listed_ids = [r["id"] for r in runs]
        for run_id in run_ids:
            assert run_id in listed_ids