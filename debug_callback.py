#!/usr/bin/env python3
"""
Debug the GitHub OAuth callback URL encoding
"""

import base64
import json
from urllib.parse import quote

# Simulate the data structure from backend
auth_data = {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.example",
    "user": {
        "id": "user_JO1EWiqIEosV_wKK",
        "email": "test@example.com",
        "full_name": "Test User",
        "github_username": "test-user",
        "github_avatar_url": "https://avatars.githubusercontent.com/u/123456",
    },
}

# Encode like the backend does
auth_json = json.dumps(auth_data)
auth_encoded = base64.urlsafe_b64encode(auth_json.encode()).decode()

print("Original data:")
print(json.dumps(auth_data, indent=2))
print()

print("JSON string:")
print(repr(auth_json))
print()

print("Base64 encoded:")
print(auth_encoded)
print()

print("URL with quote:")
redirect_url = f"http://localhost:3000/auth/callback?data={quote(auth_encoded)}"
print(redirect_url)
print()

# Test decoding like frontend does
print("Testing decode:")
try:
    decoded_data = base64.urlsafe_b64decode(auth_encoded).decode()
    print("Decoded JSON:", repr(decoded_data))
    parsed_data = json.loads(decoded_data)
    print("Parsed data:")
    print(json.dumps(parsed_data, indent=2))
    print("✅ Encoding/decoding works correctly")
except Exception as e:
    print(f"❌ Error: {e}")
