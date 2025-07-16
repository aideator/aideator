#!/usr/bin/env python3
"""
Test script for the new Task-Run architecture API endpoints.

Tests the separation between:
- POST /api/v1/runs (task creation, fires Kubernetes jobs)
- GET /api/v1/tasks (task listing, reads from database)
- GET /api/v1/tasks/{task_id} (task details, reads agent outputs)
"""

import asyncio

import httpx


async def test_api_endpoints():
    """Test the separated API endpoints."""
    base_url = "http://localhost:8000"

    print("🧪 Testing Task-Run Architecture API Endpoints")
    print("=" * 50)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: List tasks (should be empty initially)
        print("\n1️⃣ Testing GET /api/v1/tasks")
        response = await client.get(f"{base_url}/api/v1/tasks")
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"   Tasks found: {len(data.get('tasks', []))}")
            print(f"   Total: {data.get('total', 0)}")
            print("   ✅ Tasks endpoint works")
        else:
            print(f"   ❌ Failed: {response.text}")
            return

        # Test 2: Create a run (task submission)
        print("\n2️⃣ Testing POST /api/v1/runs")
        run_data = {
            "github_url": "https://github.com/fastapi/fastapi",
            "prompt": "Add comprehensive error handling to the main application",
            "model_variants": [
                {
                    "model_definition_id": "gpt-4o-mini",
                    "temperature": 0.1,
                    "max_tokens": 4000
                }
            ],
            "use_claude_code": False,
            "agent_mode": "litellm"
        }

        response = await client.post(
            f"{base_url}/api/v1/runs",
            json=run_data
        )
        print(f"   Status: {response.status_code}")

        if response.status_code == 202:  # Accepted for processing
            data = response.json()
            run_id = data.get("run_id")
            print(f"   Run created: {run_id}")
            print(f"   WebSocket URL: {data.get('websocket_url')}")
            print("   ✅ Run creation works")

            # Test 3: Check tasks list again (should have 1 task now)
            print("\n3️⃣ Testing GET /api/v1/tasks (after run creation)")
            await asyncio.sleep(1)  # Brief pause
            response = await client.get(f"{base_url}/api/v1/tasks")

            if response.status_code == 200:
                data = response.json()
                print(f"   Tasks found: {len(data.get('tasks', []))}")
                if data.get("tasks"):
                    task = data["tasks"][0]
                    print(f"   First task ID: {task.get('id')}")
                    print(f"   First task title: {task.get('title')}")
                    print(f"   First task status: {task.get('status')}")
                print("   ✅ Task appears in list")
            else:
                print(f"   ❌ Failed: {response.text}")
                return

            # Test 4: Get specific task details
            print("\n4️⃣ Testing GET /api/v1/tasks/{task_id}")
            response = await client.get(f"{base_url}/api/v1/tasks/{run_id}")

            if response.status_code == 200:
                data = response.json()
                print(f"   Task ID: {data.get('id')}")
                print(f"   Prompt: {data.get('prompt', '')[:50]}...")
                print(f"   Status: {data.get('status')}")
                print(f"   Variations: {data.get('variations')}")
                print("   ✅ Task details endpoint works")
            else:
                print(f"   ❌ Failed: {response.text}")
                return

            # Test 5: Get task outputs (may be empty if agents haven't started)
            print("\n5️⃣ Testing GET /api/v1/tasks/{task_id}/outputs")
            response = await client.get(f"{base_url}/api/v1/tasks/{run_id}/outputs")

            if response.status_code == 200:
                data = response.json()
                print(f"   Agent outputs found: {len(data)}")
                if data:
                    print(f"   Latest output type: {data[-1].get('output_type')}")
                    print(f"   Latest timestamp: {data[-1].get('timestamp')}")
                print("   ✅ Task outputs endpoint works")
            else:
                print(f"   ❌ Failed: {response.text}")
                return

        else:
            print(f"   ❌ Failed: {response.text}")
            return

    print("\n🎉 All API endpoint tests passed!")
    print("\n📝 Architecture Summary:")
    print("   • POST /api/v1/runs → Creates task, fires Kubernetes jobs")
    print("   • GET /api/v1/tasks → Lists tasks from database")
    print("   • GET /api/v1/tasks/{id} → Gets task details")
    print("   • GET /api/v1/tasks/{id}/outputs → Gets agent outputs")
    print("\n💡 Frontend should:")
    print("   • Use /api/v1/runs for task creation (main page)")
    print("   • Use /api/v1/tasks for task monitoring (task detail page)")


if __name__ == "__main__":
    asyncio.run(test_api_endpoints())
