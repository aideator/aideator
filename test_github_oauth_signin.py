#!/usr/bin/env python3
"""
Test GitHub OAuth login using the signin page
"""

import os
import time

from playwright.sync_api import sync_playwright


def test_github_oauth_signin():
    # Load credentials from environment
    # github_username = os.getenv("GITHUB_TEST_USERNAME", "aideator-bot")  # Unused
    # github_password = os.getenv(
    #     "GITHUB_TEST_PASSWORD", "Zzf!uVPetdhfu4WxPRd_zPt@Y!DviR9GwdADQLzV.2cctLcgDm"
    # )  # Unused

    with sync_playwright() as p:
        # Launch browser in headed mode to see what's happening
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            print("1. Navigating to signin page...")
            page.goto("http://localhost:3000/signin")
            page.wait_for_load_state("networkidle")

            print("2. Looking for GitHub sign in button...")
            github_button = page.locator('button:has-text("Sign in with GitHub")').first
            if github_button.count() == 0:
                print("❌ Could not find GitHub sign in button")
                return False

            # Set up request interception to capture OAuth URL
            oauth_requests = []

            def handle_request(request):
                if "github.com" in request.url and "oauth" in request.url:
                    oauth_requests.append(request.url)
                    print(f"📨 Captured OAuth request: {request.url}")

            page.on("request", handle_request)

            print("3. Clicking GitHub sign in button...")
            github_button.click()

            # Wait for GitHub login page
            page.wait_for_url("**/github.com/**", timeout=10000)
            current_url = page.url
            print(f"4. Redirected to GitHub: {current_url}")

            # Check OAuth URL from our requests
            if oauth_requests:
                oauth_url = oauth_requests[0]
                print(f"5. Analyzing OAuth URL: {oauth_url}")

                if "client_id=Ov23li" in oauth_url:
                    print("✅ SUCCESS: OAuth URL has correct client_id!")
                    print(f"   Full OAuth URL: {oauth_url}")
                    return True
                if "client_id=undefined" in oauth_url:
                    print("❌ ERROR: client_id is still 'undefined'!")
                    print(f"   Full OAuth URL: {oauth_url}")
                    return False
                print("⚠️  WARNING: Unexpected client_id in OAuth URL")
                print(f"   Full OAuth URL: {oauth_url}")
                return False
            # Check the current URL for client_id
            if "client_id=Ov23li" in current_url:
                print("✅ SUCCESS: Current URL has correct client_id!")
                return True
            if "client_id=undefined" in current_url:
                print("❌ ERROR: client_id is still 'undefined'!")
                return False
            print(f"⚠️  No OAuth requests captured, current URL: {current_url}")
            return False

        except Exception as e:
            print(f"Error during test: {e}")
            page.screenshot(path="github_oauth_signin_error.png")
            return False
        finally:
            time.sleep(2)  # Brief pause before closing
            browser.close()


if __name__ == "__main__":
    # Load environment variables from .env file
    try:
        from pathlib import Path

        with Path(".env").open() as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value
    except FileNotFoundError:
        print("Warning: .env file not found")

    success = test_github_oauth_signin()
    if success:
        print("\n✅ GitHub OAuth signin test PASSED")
    else:
        print("\n❌ GitHub OAuth signin test FAILED")
