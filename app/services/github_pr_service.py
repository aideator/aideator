from __future__ import annotations

import tempfile
import shutil
import textwrap
import time
from datetime import datetime
from pathlib import Path
from typing import Tuple

import httpx
from git import Repo


class GitHubPRService:
    """Light-weight helper for creating pull requests on behalf of a user.

    Only minimal functionality required by the application is implemented.
    It purposely avoids dealing with merge conflicts or attempting to
    automatically apply code modifications.  Instead it commits a markdown
    file that contains the AI-generated diff and summary which allows the
    PR to be created without needing to recreate the original code changes
    inside the repository.
    """

    def __init__(self, token: str):
        self.token = token
        self._headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def create_pr(
        self,
        repo_http_url: str,
        title: str,
        body: str,
        diff_content: str,
        branch_prefix: str = "aideator",
    ) -> str:
        """Create the pull request and return its HTML url.
        
        Steps:
        1. Clone the target repository with the user token.
        2. Create a new branch and commit a markdown file containing the
           diff/summary so that the branch differs from *base*.
        3. Push the branch to the remote.
        4. Open a PR against the repository default branch.
        """

        owner, repo_name = self._extract_owner_repo(repo_http_url)

        # Use a personal-access-token authenticated clone URL.  The token
        # is embedded into the HTTPS URL.  Git will strip it from any
        # subsequent log output but we still handle the directory removal
        # carefully.
        remote_with_token = repo_http_url.replace(
            "https://", f"https://{self.token}@", 1
        )
        if not remote_with_token.endswith(".git"):
            remote_with_token += ".git"

        branch_name = f"{branch_prefix}/{int(time.time())}"

        tmp_dir = tempfile.mkdtemp(prefix="aideator-pr-")
        try:
            repo = Repo.clone_from(remote_with_token, tmp_dir, depth=1)

            # Determine the default branch – fall back to `main`.
            try:
                default_ref = (
                    repo.git.symbolic_ref("refs/remotes/origin/HEAD").split("/")[-1]
                )
            except Exception:
                default_ref = "main"

            repo.git.checkout("-b", branch_name)

            patch_file = Path(tmp_dir) / f"AIdeator_patch_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.md"
            patch_file.write_text(self._build_patch_markdown(title, body, diff_content), encoding="utf-8")

            repo.index.add([str(patch_file.relative_to(tmp_dir))])
            repo.index.commit("AIdeator: attach diff & summary from automated task")

            # Push the new branch – include the token in remote URL to authorise.
            repo.remote().push(branch_name)

            # Create PR via GitHub REST API.
            pr_url = await self._open_pull_request(
                owner=owner,
                repo_name=repo_name,
                head=branch_name,
                base=default_ref,
                title=title,
                body=body,
            )
            return pr_url
        finally:
            # Best-effort cleanup of the temporary clone.
            shutil.rmtree(tmp_dir, ignore_errors=True)

    async def _open_pull_request(
        self,
        *,
        owner: str,
        repo_name: str,
        head: str,
        base: str,
        title: str,
        body: str,
    ) -> str:
        url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls"
        payload = {
            "title": title,
            "head": head,
            "base": base,
            "body": body,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=self._headers, json=payload)
            if resp.status_code != 201:
                raise RuntimeError(
                    f"Failed to create PR – GitHub API returned {resp.status_code}: {resp.text}"
                )
            data = resp.json()
            return data["html_url"]

    @staticmethod
    def _build_patch_markdown(title: str, summary: str, diff_block: str) -> str:
        safe_summary = summary or "No summary available."
        safe_diff = diff_block or "No diff available."
        return textwrap.dedent(
            f"""\
            # {title}

            ## Summary
            {safe_summary}

            ## Diff
            ```diff
            {safe_diff}
            ```
            """
        )

    @staticmethod
    def _extract_owner_repo(url: str) -> Tuple[str, str]:
        """Return (owner, repo) extracted from a standard GitHub HTTPS URL."""
        if url.endswith(".git"):
            url = url[:-4]
        parts = url.rstrip("/").split("/")
        if len(parts) < 2:
            raise ValueError("Unable to parse repository owner/name from URL")
        return parts[-2], parts[-1]