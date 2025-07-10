#\!/usr/bin/env python3
"""
Manual test to verify the React hooks fix in the stream page
"""


import requests


# Test that the frontend loads without React hooks errors
def test_frontend_loads():
    """Test that the stream page loads without React hooks errors"""
    try:
        # Check if frontend is accessible
        response = requests.get("http://localhost:3003/stream", timeout=5)

        if response.status_code == 200:
            print("✅ Frontend stream page loads successfully")
            print(f"   Status: {response.status_code}")

            # Check for common React error indicators in the response
            html_content = response.text

            # Look for React error indicators
            if "updateHookTypesDev" in html_content:
                print(r"❌ React hooks error found in page\!")
                return False

            if "Invalid hook call" in html_content:
                print(r"❌ Invalid hook call error found\!")
                return False

            if "Rendered more hooks than during the previous render" in html_content:
                print(r"❌ Hook order error found\!")
                return False

            print("✅ No React hooks errors detected in page content")
            return True

        print(f"❌ Frontend returned error: {response.status_code}")
        return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to frontend: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing React hooks fix...")
    print("-" * 50)

    # Test frontend
    frontend_ok = test_frontend_loads()

    print("-" * 50)

    if frontend_ok:
        print(r"✅ React hooks fix appears to be working\!")
    else:
        print("❌ React hooks issue may still be present.")
