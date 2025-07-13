"""GitHub OAuth authentication endpoints."""

import json
import secrets
from datetime import datetime, timedelta
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.api.v1.auth import create_access_token
from app.core.auth import get_password_hash
from app.core.config import get_settings
from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.core.logging import get_logger
from app.models.user import User

settings = get_settings()
logger = get_logger(__name__)
router = APIRouter()


@router.get("/auth")
async def github_auth(state: str = Query(None)) -> RedirectResponse:
    """Initiate GitHub OAuth flow."""
    # Check if GitHub OAuth is configured
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth is not configured",
        )

    # Generate state if not provided
    if not state:
        state = secrets.token_urlsafe(8)

    # Build OAuth URL
    oauth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&redirect_uri=http://localhost:8000/api/v1/github/callback"
        f"&scope={settings.github_oauth_scopes}"
        f"&state={state}"
    )

    return RedirectResponse(url=oauth_url, status_code=302)


@router.get("/callback")
async def github_callback(
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
    error_description: str = Query(None),
    db: AsyncSession = Depends(get_session),
) -> Response:
    """Handle GitHub OAuth callback."""
    # Handle OAuth errors (user cancelled, access denied, etc.)
    if error:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Cancelled</title>
        </head>
        <body>
            <script>
                // Redirect back to sign-in page
                window.location.href = "{settings.frontend_url}/signin?error={error}";
            </script>
            <p>Authentication cancelled. Redirecting...</p>
            <p>If you are not redirected automatically, <a href="{settings.frontend_url}/signin">click here to return to sign in</a>.</p>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    # Check if we have a code
    if not code:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Error</title>
        </head>
        <body>
            <script>
                window.location.href = "{settings.frontend_url}/signin?error=no_code";
            </script>
            <p>No authorization code received. Redirecting...</p>
            <p>If you are not redirected automatically, <a href="{settings.frontend_url}/signin">click here to return to sign in</a>.</p>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    # Check if GitHub OAuth is configured
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth is not configured",
        )

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "state": state,
            },
            headers={"Accept": "application/json"},
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail="Failed to exchange code for token",
            )

        token_data = token_response.json()
        github_access_token = token_data.get("access_token")

        if not github_access_token:
            raise HTTPException(
                status_code=400,
                detail="No access token received from GitHub",
            )

        # Get user information from GitHub
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {github_access_token}",
                "Accept": "application/json",
            },
        )

        if user_response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail="Failed to get user information from GitHub",
            )

        github_user = user_response.json()

        # Get primary email
        email_response = await client.get(
            "https://api.github.com/user/emails",
            headers={
                "Authorization": f"Bearer {github_access_token}",
                "Accept": "application/json",
            },
        )

        primary_email = None
        if email_response.status_code == 200:
            emails = email_response.json()
            for email in emails:
                if email.get("primary") and email.get("verified"):
                    primary_email = email.get("email")
                    break

        if not primary_email:
            primary_email = github_user.get(
                "email", f"{github_user['login']}@github.local"
            )

    # Check if user exists by GitHub ID
    result = await db.execute(
        select(User).where(col(User.github_id) == str(github_user["id"]))
    )
    user = result.scalar_one_or_none()

    if not user:
        # Check if user exists by email
        result = await db.execute(select(User).where(col(User.email) == primary_email))
        user = result.scalar_one_or_none()

        if user:
            # Link existing account with GitHub
            user.github_id = str(github_user["id"])
            user.github_username = github_user["login"]
            user.github_avatar_url = github_user.get("avatar_url")
            user.auth_provider = "github"
        else:
            # Create new user
            user = User(
                id=f"user_{secrets.token_urlsafe(12)}",
                email=primary_email,
                full_name=github_user.get("name", github_user["login"]),
                github_id=str(github_user["id"]),
                github_username=github_user["login"],
                github_avatar_url=github_user.get("avatar_url"),
                auth_provider="github",
                is_active=True,
                created_at=datetime.utcnow(),
                # Set a random password for GitHub users
                hashed_password=get_password_hash(secrets.token_urlsafe(32)),
            )
            db.add(user)

    # Encrypt and store GitHub access token
    from app.core.encryption import encrypt_token

    user.github_access_token_encrypted = encrypt_token(github_access_token)
    user.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(user)

    # Create access token for our app
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=timedelta(days=7),  # Longer expiration for OAuth users
    )

    logger.info(
        "github_oauth_success",
        user_id=user.id,
        github_username=user.github_username,
        new_user=user.created_at == user.updated_at,
    )

    # Create user dictionary for frontend
    user_dict = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "github_username": user.github_username,
        "github_avatar_url": user.github_avatar_url,
    }

    # Create redirect URL with auth data as URL parameters
    import base64
    from urllib.parse import quote

    # Encode the auth data
    auth_data = {"token": access_token, "user": user_dict}
    auth_json = json.dumps(auth_data)
    auth_encoded = base64.urlsafe_b64encode(auth_json.encode()).decode()

    # Redirect to frontend with encoded auth data
    redirect_url = f"{settings.frontend_url or 'http://localhost:3000'}/auth/callback?data={quote(auth_encoded)}"

    return RedirectResponse(url=redirect_url, status_code=302)


@router.get("/repos")
async def list_github_repos(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """List GitHub repositories accessible to the authenticated user."""
    # Check if user has GitHub access token
    if not current_user.github_access_token_encrypted:
        raise HTTPException(
            status_code=400,
            detail="GitHub account not linked. Please authenticate with GitHub first.",
        )

    # Decrypt GitHub access token
    from app.core.encryption import decrypt_token

    github_access_token = decrypt_token(current_user.github_access_token_encrypted)

    # Fetch repositories from GitHub
    async with httpx.AsyncClient() as client:
        repos = []
        page = 1
        per_page = 100

        while True:
            response = await client.get(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"Bearer {github_access_token}",
                    "Accept": "application/json",
                },
                params={
                    "page": page,
                    "per_page": per_page,
                    "sort": "updated",
                    "direction": "desc",
                },
            )

            if response.status_code == 401:
                # Token expired or revoked
                current_user.github_access_token_encrypted = None
                await db.commit()
                raise HTTPException(
                    status_code=401,
                    detail="GitHub token expired. Please re-authenticate.",
                )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch repositories from GitHub",
                )

            page_repos = response.json()
            if not page_repos:
                break

            # Extract relevant information
            for repo in page_repos:
                repos.append(
                    {
                        "id": repo["id"],
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "description": repo.get("description"),
                        "private": repo["private"],
                        "default_branch": repo.get("default_branch", "main"),
                        "clone_url": repo["clone_url"],
                        "ssh_url": repo["ssh_url"],
                        "html_url": repo["html_url"],
                        "language": repo.get("language"),
                        "updated_at": repo["updated_at"],
                        "permissions": repo.get("permissions", {}),
                    }
                )

            # Check if there are more pages
            link_header = response.headers.get("Link", "")
            if 'rel="next"' not in link_header:
                break

            page += 1

            # Limit to prevent excessive API calls
            if page > 10:
                break

    return repos


@router.get("/repos/{owner}/{repo}/branches")
async def list_github_branches(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """List branches for a specific GitHub repository."""
    # Check if user has GitHub access token
    if not current_user.github_access_token_encrypted:
        raise HTTPException(
            status_code=400,
            detail="GitHub account not linked. Please authenticate with GitHub first.",
        )

    # Decrypt GitHub access token
    from app.core.encryption import decrypt_token

    github_access_token = decrypt_token(current_user.github_access_token_encrypted)

    # Fetch branches from GitHub
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/branches",
            headers={
                "Authorization": f"Bearer {github_access_token}",
                "Accept": "application/json",
            },
            params={"per_page": 100},
        )

        if response.status_code == 401:
            # Token expired or revoked
            current_user.github_access_token_encrypted = None
            await db.commit()
            raise HTTPException(
                status_code=401,
                detail="GitHub token expired. Please re-authenticate.",
            )

        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Repository not found or you don't have access",
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch branches from GitHub",
            )

        branches = response.json()

        # Extract relevant information
        return [
            {
                "name": branch["name"],
                "commit": {
                    "sha": branch["commit"]["sha"],
                    "url": branch["commit"]["url"],
                },
                "protected": branch.get("protected", False),
            }
            for branch in branches
        ]
