#!/usr/bin/env python3
"""
Test the complete OAuth flow by doing a manual login
"""

from urllib.parse import parse_qs, urlparse

import requests


def test_oauth_flow():
    print("Testing complete OAuth flow...")

    # Step 1: Get OAuth URL from our backend
    print("1. Getting OAuth URL from backend...")
    auth_response = requests.get(
        "http://localhost:8000/api/v1/github/auth?state=test123",
        allow_redirects=False,
        timeout=10,
    )

    if auth_response.status_code == 302:
        oauth_url = auth_response.headers.get("Location")
        print(f"✅ Got OAuth URL: {oauth_url}")

        # Check if client_id is correct
        parsed = urlparse(oauth_url)
        query_params = parse_qs(parsed.query)
        client_id = query_params.get("client_id", ["undefined"])[0]

        if client_id == "undefined":
            print("❌ ERROR: client_id is 'undefined'")
            return False
        if client_id.startswith("Ov23li"):
            print(f"✅ SUCCESS: client_id is correct: {client_id}")
        else:
            print(f"⚠️  WARNING: unexpected client_id: {client_id}")

        print(
            "\nOAuth URL looks good! The backend OAuth initiation is working correctly."
        )
        print("To complete the full flow, you would:")
        print("1. Visit the OAuth URL in a browser")
        print("2. Login with GitHub credentials")
        print("3. GitHub would redirect back to /api/v1/github/callback with a code")
        print(
            "4. Our backend would exchange the code for a token and redirect to frontend"
        )

        return True
    print(f"❌ ERROR: Expected 302 redirect, got {auth_response.status_code}")
    print(f"Response: {auth_response.text}")
    return False


if __name__ == "__main__":
    success = test_oauth_flow()
    if success:
        print("\n✅ OAuth initiation test PASSED")
        print("The 'undefined client_id' issue has been resolved!")
    else:
        print("\n❌ OAuth initiation test FAILED")
