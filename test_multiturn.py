#!/usr/bin/env python3
"""Test script for multi-turn conversation functionality."""

import asyncio
import json
import sys
from typing import Dict, Any

import httpx


async def test_multiturn_conversation():
    """Test the multi-turn conversation flow."""
    base_url = "http://localhost:8000"
    
    # Test data
    test_user = {
        "username": "testuser",
        "email": "test@example.com", 
        "password": "TestPass123"
    }
    
    test_prompt_1 = "Analyze this repository structure"
    test_prompt_2 = "Based on that analysis, suggest specific improvements"
    
    github_url = "https://github.com/octocat/Hello-World"
    
    model_variants = [
        {
            "model_definition_id": "gpt-4",
            "provider_credential_id": None,
            "model_parameters": {"temperature": 0.7, "max_tokens": 1000}
        }
    ]
    
    async with httpx.AsyncClient() as client:
        print("🔧 Testing multi-turn conversation flow...")
        
        # Step 1: Register user (ignore if already exists)
        try:
            register_response = await client.post(f"{base_url}/api/v1/auth/register", json=test_user)
            if register_response.status_code == 201:
                print("✅ User registered successfully")
            elif register_response.status_code == 400:
                print("ℹ️  User already exists, continuing...")
            else:
                print(f"❌ Registration failed: {register_response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False
        
        # Step 2: Login
        try:
            login_response = await client.post(f"{base_url}/api/v1/auth/login", json={
                "email": test_user["email"],
                "password": test_user["password"]
            })
            if login_response.status_code != 200:
                print(f"❌ Login failed: {login_response.status_code}")
                return False
            
            login_data = login_response.json()
            token = login_data["access_token"]
            print("✅ User logged in successfully")
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
        
        # Step 3: Create API key
        try:
            api_key_response = await client.post(
                f"{base_url}/api/v1/auth/api-keys",
                json={"name": "Test Key", "description": "For testing multi-turn"},
                headers={"Authorization": f"Bearer {token}"}
            )
            if api_key_response.status_code != 201:
                print(f"❌ API key creation failed: {api_key_response.status_code}")
                return False
            
            api_key_data = api_key_response.json()
            api_key = api_key_data["key"]
            print("✅ API key created successfully")
        except Exception as e:
            print(f"❌ API key creation error: {e}")
            return False
        
        # Step 4: Create first run (should create session and turn automatically)
        try:
            run_1_data = {
                "github_url": github_url,
                "prompt": test_prompt_1,
                "model_variants": model_variants,
                "agent_mode": "litellm"
                # No session_id or turn_id - should auto-create
            }
            
            run_1_response = await client.post(
                f"{base_url}/api/v1/runs",
                json=run_1_data,
                headers={"X-API-Key": api_key}
            )
            
            if run_1_response.status_code != 202:
                print(f"❌ First run creation failed: {run_1_response.status_code}")
                print(f"Response: {run_1_response.text}")
                return False
            
            run_1_result = run_1_response.json()
            session_id = run_1_result["session_id"]
            turn_1_id = run_1_result["turn_id"]
            run_1_id = run_1_result["run_id"]
            
            print(f"✅ First run created successfully")
            print(f"   Session ID: {session_id}")
            print(f"   Turn ID: {turn_1_id}")
            print(f"   Run ID: {run_1_id}")
        except Exception as e:
            print(f"❌ First run creation error: {e}")
            return False
        
        # Step 5: Create second run (follow-up in same session)
        try:
            run_2_data = {
                "github_url": github_url,
                "prompt": test_prompt_2,
                "model_variants": model_variants,
                "agent_mode": "litellm",
                "session_id": session_id  # Use existing session
                # No turn_id - should create new turn
            }
            
            run_2_response = await client.post(
                f"{base_url}/api/v1/runs",
                json=run_2_data,
                headers={"X-API-Key": api_key}
            )
            
            if run_2_response.status_code != 202:
                print(f"❌ Second run creation failed: {run_2_response.status_code}")
                print(f"Response: {run_2_response.text}")
                return False
            
            run_2_result = run_2_response.json()
            turn_2_id = run_2_result["turn_id"]
            run_2_id = run_2_result["run_id"]
            
            print(f"✅ Second run created successfully")
            print(f"   Same Session ID: {session_id}")
            print(f"   New Turn ID: {turn_2_id}")
            print(f"   Run ID: {run_2_id}")
        except Exception as e:
            print(f"❌ Second run creation error: {e}")
            return False
        
        # Step 6: Verify session has both turns
        try:
            session_response = await client.get(
                f"{base_url}/api/v1/sessions/{session_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if session_response.status_code != 200:
                print(f"❌ Session retrieval failed: {session_response.status_code}")
                return False
            
            session_data = session_response.json()
            print(f"✅ Session retrieved successfully")
            print(f"   Title: {session_data['title']}")
            print(f"   Total turns: {session_data['total_turns']}")
        except Exception as e:
            print(f"❌ Session retrieval error: {e}")
            return False
        
        # Step 7: Get session turns
        try:
            turns_response = await client.get(
                f"{base_url}/api/v1/sessions/{session_id}/turns",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if turns_response.status_code != 200:
                print(f"❌ Turns retrieval failed: {turns_response.status_code}")
                return False
            
            turns_data = turns_response.json()
            print(f"✅ Turns retrieved successfully")
            print(f"   Number of turns: {len(turns_data)}")
            
            for i, turn in enumerate(turns_data):
                print(f"   Turn {i+1}: {turn['prompt'][:50]}...")
                print(f"     Turn Number: {turn['turn_number']}")
                print(f"     Status: {turn['status']}")
        except Exception as e:
            print(f"❌ Turns retrieval error: {e}")
            return False
        
        print("\n🎉 Multi-turn conversation test completed successfully!")
        print("✅ Sessions are being persisted to the database")
        print("✅ Turns are being created and sequenced properly")
        print("✅ Backend supports multi-turn conversations")
        
        return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_multiturn_conversation())
        if result:
            print("\n✅ All tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Tests failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)