#!/usr/bin/env python3
"""Test the simplified admin messaging interface."""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

def test_simplified_admin():
    """Test the simplified admin messaging endpoints."""
    print("🧪 Testing Simplified Admin Messaging Interface...\n")
    
    # Test 1: Overview
    print("1. Testing /api/v1/admin-messaging/overview")
    try:
        response = requests.get(f"{API_BASE}/api/v1/admin-messaging/overview")
        if response.status_code == 200:
            overview = response.json()
            print("✅ Overview endpoint working!")
            print(f"   Active runs: {overview.get('active_runs', 0)}")
            print(f"   Total messages: {overview.get('total_messages', 0)}")
            print(f"   Recent messages (1h): {overview.get('recent_messages_1h', 0)}")
            print(f"   Message types: {overview.get('message_types', {})}")
        else:
            print(f"❌ Overview endpoint failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Overview endpoint error: {e}")
    
    print()
    
    # Test 2: Runs
    print("2. Testing /api/v1/admin-messaging/runs")
    try:
        response = requests.get(f"{API_BASE}/api/v1/admin-messaging/runs?limit=5")
        if response.status_code == 200:
            runs = response.json()
            print(f"✅ Runs endpoint working! Found {len(runs)} runs")
            for run in runs[:3]:  # Show first 3
                print(f"   - {run['id']}: {run['status']} ({run['message_count']} messages)")
        else:
            print(f"❌ Runs endpoint failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Runs endpoint error: {e}")
    
    print()
    
    # Test 3: Messages
    print("3. Testing /api/v1/admin-messaging/messages")
    try:
        response = requests.get(f"{API_BASE}/api/v1/admin-messaging/messages?limit=10")
        if response.status_code == 200:
            messages = response.json()
            print(f"✅ Messages endpoint working! Found {len(messages)} messages")
            for msg in messages[:3]:  # Show first 3
                print(f"   - [{msg['output_type']}] {msg['content'][:50]}...")
        else:
            print(f"❌ Messages endpoint failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Messages endpoint error: {e}")
    
    print()
    
    # Test 4: Live Activity
    print("4. Testing /api/v1/admin-messaging/live")
    try:
        response = requests.get(f"{API_BASE}/api/v1/admin-messaging/live")
        if response.status_code == 200:
            live = response.json()
            print(f"✅ Live activity endpoint working!")
            print(f"   Active containers: {live.get('active_containers', 0)}")
            print(f"   Messages (5min): {live.get('total_messages_5min', 0)}")
        else:
            print(f"❌ Live activity endpoint failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Live activity endpoint error: {e}")
    
    print()
    
    # Test 5: Health Check
    print("5. Testing /api/v1/admin-messaging/health")
    try:
        response = requests.get(f"{API_BASE}/api/v1/admin-messaging/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Health endpoint working!")
            print(f"   Status: {health.get('status', 'unknown')}")
            print(f"   Database connected: {health.get('database_connected', False)}")
            print(f"   Total messages: {health.get('total_messages', 0)}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
    
    print("\n" + "="*60)
    print("🎯 SIMPLIFIED ADMIN MESSAGING INTERFACE")
    print("="*60)
    print("✅ All endpoints should be working and easy to understand")
    print("📊 Use these endpoints to visualize container messaging:")
    print("   - /overview: Quick stats and message types")
    print("   - /runs: List of runs with message counts")
    print("   - /messages: Recent messages from containers")
    print("   - /live: Live activity (last 5 minutes)")
    print("   - /health: Database health check")
    print("="*60)


if __name__ == "__main__":
    test_simplified_admin()