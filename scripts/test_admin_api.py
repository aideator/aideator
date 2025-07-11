#!/usr/bin/env python3
"""Test the admin API endpoints to verify they're working with the test data."""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

def test_admin_endpoints():
    """Test all admin endpoints."""
    print("🧪 Testing Admin API Endpoints...\n")
    
    # Test 1: Database Stats
    print("1. Testing /api/v1/admin/stats")
    try:
        response = requests.get(f"{API_BASE}/api/v1/admin/stats")
        if response.status_code == 200:
            stats = response.json()
            print("✅ Stats endpoint working!")
            print(f"   Total runs: {stats.get('total_runs', 0)}")
            print(f"   Total messages: {stats.get('total_messages', 0)}")
            print(f"   Runs by status: {stats.get('runs_by_status', {})}")
        else:
            print(f"❌ Stats endpoint failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Stats endpoint error: {e}")
    
    print()
    
    # Test 2: Active Runs
    print("2. Testing /api/v1/admin/runs/active")
    try:
        response = requests.get(f"{API_BASE}/api/v1/admin/runs/active?include_completed=true&limit=20")
        if response.status_code == 200:
            runs = response.json()
            print(f"✅ Active runs endpoint working! Found {len(runs)} runs")
            for run in runs[:3]:  # Show first 3
                print(f"   - {run['id']}: {run['status']} ({run['total_messages']} messages)")
        else:
            print(f"❌ Active runs endpoint failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Active runs endpoint error: {e}")
    
    print()
    
    # Test 3: Messages
    print("3. Testing /api/v1/admin/messages/stream")
    try:
        response = requests.get(f"{API_BASE}/api/v1/admin/messages/stream?limit=10")
        if response.status_code == 200:
            data = response.json()
            messages = data.get('messages', [])
            total = data.get('total', 0)
            print(f"✅ Messages endpoint working! Total: {total}, Showing: {len(messages)}")
            for msg in messages[:3]:  # Show first 3
                print(f"   - [{msg['output_type']}] {msg['content'][:50]}...")
        else:
            print(f"❌ Messages endpoint failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Messages endpoint error: {e}")
    
    print()
    
    # Test 4: Health Check
    print("4. Testing /api/v1/admin/health")
    try:
        response = requests.get(f"{API_BASE}/api/v1/admin/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Health endpoint working!")
            print(f"   Database connection: {health.get('database_connection', False)}")
            print(f"   Healthy: {health.get('healthy', False)}")
            print(f"   Response time: {health.get('response_time_ms', 0)}ms")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
    
    print("\n" + "="*50)
    print("🎯 Summary: Check if all endpoints show ✅ above")
    print("If any show ❌, the backend might not be running correctly")
    print("="*50)


if __name__ == "__main__":
    test_admin_endpoints()