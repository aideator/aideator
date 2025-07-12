"""GitHub URL parsing utilities."""

import re
from typing import Optional


def parse_repo_name(github_url: str) -> str:
    """
    Parse repository name from GitHub URL.
    
    Args:
        github_url: Full GitHub URL (e.g., "https://github.com/owner/repo")
        
    Returns:
        Repository name in "owner/repo" format, or original URL if parsing fails
        
    Examples:
        >>> parse_repo_name("https://github.com/aideator/helloworld")
        "aideator/helloworld"
        >>> parse_repo_name("https://github.com/vercel/next.js/")
        "vercel/next.js"
        >>> parse_repo_name("git@github.com:owner/repo.git")
        "owner/repo"
    """
    if not github_url:
        return github_url
    
    # Remove trailing slashes and .git extensions
    clean_url = github_url.rstrip('/').replace('.git', '')
    
    # Pattern to match GitHub URLs (both HTTPS and SSH)
    patterns = [
        r'https?://github\.com/([^/]+)/([^/]+)',  # HTTPS URLs
        r'git@github\.com:([^/]+)/([^/]+)',       # SSH URLs
    ]
    
    for pattern in patterns:
        match = re.search(pattern, clean_url)
        if match:
            owner, repo = match.groups()
            return f"{owner}/{repo}"
    
    # If no pattern matches, try to extract from path
    path_match = re.search(r'/([^/]+)/([^/]+)/?$', clean_url)
    if path_match:
        owner, repo = path_match.groups()
        return f"{owner}/{repo}"
    
    # Fallback: return original URL
    return github_url


def extract_branch_from_url(github_url: str) -> Optional[str]:
    """
    Extract branch name from GitHub URL if present.
    
    Args:
        github_url: GitHub URL that might contain branch info
        
    Returns:
        Branch name if found, None otherwise
        
    Examples:
        >>> extract_branch_from_url("https://github.com/owner/repo/tree/feature-branch")
        "feature-branch"
    """
    branch_match = re.search(r'/tree/([^/]+)', github_url)
    return branch_match.group(1) if branch_match else None