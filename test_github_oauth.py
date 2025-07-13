#!/usr/bin/env python3
"""
Test GitHub OAuth login flow using Playwright
"""

import time

from playwright.sync_api import sync_playwright


def test_github_oauth():
    with sync_playwright() as p:
        # Launch browser in headed mode to see what's happening
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            print("Navigating to localhost:3000...")
            page.goto("http://localhost:3000")

            # Wait for page to load
            page.wait_for_load_state("networkidle")

            # Look for GitHub login button
            print("Looking for GitHub login button...")

            # Try different selectors for GitHub login
            github_selectors = [
                'button:has-text("Login with GitHub")',
                'a:has-text("Login with GitHub")',
                'button:has-text("GitHub")',
                'a:has-text("GitHub")',
                '[data-testid="github-login"]',
                ".github-login",
                'button[type="button"]:has(svg)',  # Button with SVG (likely GitHub icon)
            ]

            github_button = None
            for selector in github_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        github_button = page.locator(selector).first
                        print(f"Found GitHub button with selector: {selector}")
                        break
                except Exception as e:
                    # Ignore locator errors and try next selector
                    print(f"Selector {selector} failed: {e}")
                    continue

            if not github_button:
                # Try to find any button with GitHub in text or SVG
                print("Searching all buttons for GitHub-related content...")
                buttons = page.locator("button, a").all()
                for i, button in enumerate(buttons):
                    try:
                        text = button.text_content() or ""
                        inner_html = button.inner_html()
                        print(
                            f"Button {i}: text='{text}', has_github_svg={('github' in inner_html.lower())}"
                        )

                        if "github" in text.lower() or "github" in inner_html.lower():
                            github_button = button
                            print(f"Found GitHub button: {text}")
                            break
                    except Exception as e:
                        # Ignore button text extraction errors
                        print(f"Button {i} text extraction failed: {e}")
                        continue

            if github_button:
                print("Clicking GitHub login button...")

                # Set up request interception to capture the OAuth URL
                requests = []

                def handle_request(request):
                    if "github.com" in request.url or "oauth" in request.url:
                        requests.append(request.url)
                        print(f"Captured OAuth request: {request.url}")

                page.on("request", handle_request)

                # Click the button
                github_button.click()

                # Wait a bit for navigation or popup
                time.sleep(2)

                # Check if we were redirected to GitHub
                current_url = page.url
                print(f"Current URL: {current_url}")

                if "github.com" in current_url:
                    print("Successfully redirected to GitHub OAuth!")
                    print(f"OAuth URL: {current_url}")

                    # Parse the URL to check client_id
                    from urllib.parse import parse_qs, urlparse

                    parsed = urlparse(current_url)
                    query_params = parse_qs(parsed.query)

                    client_id = query_params.get("client_id", ["undefined"])[0]
                    redirect_uri = query_params.get("redirect_uri", [""])[0]
                    scope = query_params.get("scope", [""])[0]
                    state = query_params.get("state", [""])[0]

                    print(f"client_id: {client_id}")
                    print(f"redirect_uri: {redirect_uri}")
                    print(f"scope: {scope}")
                    print(f"state: {state}")

                    if client_id == "undefined":
                        print("❌ ERROR: client_id is still 'undefined'!")
                        return False
                    if client_id.startswith("Ov23li"):
                        print("✅ SUCCESS: client_id is correctly set!")
                        return True
                    print(f"⚠️  WARNING: client_id has unexpected value: {client_id}")
                    return False
                print("Did not redirect to GitHub. Checking for errors...")
                # Check if there are any error messages on the page
                error_text = page.text_content()
                if "error" in error_text.lower() or "undefined" in error_text.lower():
                    print(f"Found error on page: {error_text[:500]}...")
                return False

            print("Could not find GitHub login button!")
            # Take a screenshot for debugging
            page.screenshot(path="github_oauth_debug.png")
            print("Screenshot saved as github_oauth_debug.png")
            return False

        except Exception as e:
            print(f"Error during test: {e}")
            page.screenshot(path="github_oauth_error.png")
            return False
        finally:
            browser.close()


if __name__ == "__main__":
    success = test_github_oauth()
    if success:
        print("\n✅ GitHub OAuth test PASSED")
    else:
        print("\n❌ GitHub OAuth test FAILED")
