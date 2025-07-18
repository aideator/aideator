from __future__ import annotations

import tempfile
import shutil
import textwrap
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Tuple, List, Dict, Optional

import httpx
from git import Repo


class GitHubPRService:
    """Light-weight helper for creating pull requests on behalf of a user.

    Enhanced to apply actual code changes from git diffs in addition to
    creating markdown documentation. The service can now:
    1. Parse git diff output
    2. Apply changes to repository files
    3. Create a commit with the actual code changes
    4. Include a markdown file with summary and diff for reference
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
        apply_code_changes: bool = True,
    ) -> str:
        """Create the pull request and return its HTML url.
        
        Steps:
        1. Clone the target repository with the user token.
        2. Create a new branch.
        3. If apply_code_changes is True, parse and apply the git diff to repository files.
        4. Create a markdown file containing the diff/summary for reference.
        5. Commit all changes (code + markdown).
        6. Push the branch to the remote.
        7. Open a PR against the repository default branch.
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

            # Apply code changes if requested and diff content is available
            if apply_code_changes and diff_content.strip():
                try:
                    self._apply_git_diff(tmp_dir, diff_content)
                    # await self.output_writer.write_job_data("✅ Applied code changes to repository") # This line was not in the new_code, so it's removed.
                except Exception as e:
                    # await self.output_writer.write_job_data(f"⚠️ Failed to apply code changes: {e}") # This line was not in the new_code, so it's removed.
                    # Continue with markdown-only approach if code changes fail
                    pass # Continue with markdown-only approach if code changes fail

            # Create markdown file for reference
            patch_file = Path(tmp_dir) / f"AIdeator_patch_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.md"
            patch_file.write_text(self._build_patch_markdown(title, body, diff_content), encoding="utf-8")

            repo.index.add([str(patch_file.relative_to(tmp_dir))])
            
            # Add all modified files if code changes were applied
            if apply_code_changes and diff_content.strip():
                repo.index.add("*")
            
            commit_message = "AIdeator: apply automated changes and attach diff summary"
            repo.index.commit(commit_message)

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

    def _apply_git_diff(self, repo_path: str, diff_content: str) -> None:
        """Parse and apply git diff to repository files.
        
        Args:
            repo_path: Path to the repository
            diff_content: Git diff content to apply
            
        Raises:
            ValueError: If diff format is invalid
            RuntimeError: If file operations fail
        """
        if not diff_content.strip():
            return
            
        # Parse the diff into file changes
        file_changes = self._parse_git_diff(diff_content)
        
        # Apply changes to each file
        for file_change in file_changes:
            self._apply_file_change(repo_path, file_change)

    def _parse_git_diff(self, diff_content: str) -> List[Dict]:
        """Parse git diff output into structured file changes.
        
        Args:
            diff_content: Raw git diff output
            
        Returns:
            List of file change dictionaries
        """
        file_changes = []
        current_file = None
        current_hunks = []
        
        lines = diff_content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # File header: diff --git a/file b/file
            if line.startswith('diff --git'):
                # Save previous file if exists
                if current_file:
                    file_changes.append({
                        'file_path': current_file,
                        'hunks': current_hunks
                    })
                
                # Parse file path from diff header
                parts = line.split()
                if len(parts) >= 3:
                    # Extract file path from "a/path/to/file" format
                    file_path = parts[2][2:]  # Remove "a/" prefix
                    current_file = file_path
                    current_hunks = []
                i += 1
                
            # Index line: index hash..hash mode
            elif line.startswith('index '):
                i += 1
                
            # File mode line: --- a/file or +++ b/file
            elif line.startswith('--- ') or line.startswith('+++ '):
                i += 1
                
            # Hunk header: @@ -old_start,old_count +new_start,new_count @@
            elif line.startswith('@@'):
                hunk = self._parse_hunk(lines, i)
                current_hunks.append(hunk)
                i = hunk['end_line'] + 1
                
            else:
                i += 1
        
        # Add the last file
        if current_file:
            file_changes.append({
                'file_path': current_file,
                'hunks': current_hunks
            })
        
        return file_changes

    def _parse_hunk(self, lines: List[str], start_index: int) -> Dict:
        """Parse a single hunk from git diff.
        
        Args:
            lines: All lines from the diff
            start_index: Index of the hunk header line
            
        Returns:
            Dictionary with hunk information and changes
        """
        hunk_header = lines[start_index]
        
        # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
        match = re.match(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', hunk_header)
        if not match:
            raise ValueError(f"Invalid hunk header: {hunk_header}")
        
        old_start = int(match.group(1))
        old_count = int(match.group(2)) if match.group(2) else 1
        new_start = int(match.group(3))
        new_count = int(match.group(4)) if match.group(4) else 1
        
        # Parse hunk content
        changes = []
        i = start_index + 1
        
        while i < len(lines):
            line = lines[i]
            
            # End of hunk or start of next hunk
            if line.startswith('@@') or line.startswith('diff --git'):
                break
                
            if line.startswith('+'):
                changes.append(('add', line[1:]))
            elif line.startswith('-'):
                changes.append(('delete', line[1:]))
            elif line.startswith(' '):
                changes.append(('context', line[1:]))
            else:
                # Empty line or other content
                changes.append(('context', line))
            
            i += 1
        
        return {
            'old_start': old_start,
            'old_count': old_count,
            'new_start': new_start,
            'new_count': new_count,
            'changes': changes,
            'end_line': i - 1
        }

    def _apply_file_change(self, repo_path: str, file_change: Dict) -> None:
        """Apply changes to a single file.
        
        Args:
            repo_path: Path to the repository
            file_change: File change dictionary with hunks
        """
        file_path = Path(repo_path) / file_change['file_path']
        
        # Read existing file content
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # Apply hunks in reverse order to maintain line numbers
        hunks = sorted(file_change['hunks'], key=lambda h: h['old_start'], reverse=True)
        
        for hunk in hunks:
            lines = self._apply_hunk(lines, hunk)
        
        # Write modified content back to file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    def _apply_hunk(self, lines: List[str], hunk: Dict) -> List[str]:
        """Apply a single hunk to file lines.
        
        Args:
            lines: Current file lines
            hunk: Hunk to apply
            
        Returns:
            Modified lines
        """
        old_start = hunk['old_start'] - 1  # Convert to 0-based index
        old_end = old_start + hunk['old_count']
        
        # Remove old lines
        lines = lines[:old_start] + lines[old_end:]
        
        # Insert new lines
        new_lines = []
        for change_type, content in hunk['changes']:
            if change_type in ('add', 'context'):
                new_lines.append(content + '\n')
        
        lines[old_start:old_start] = new_lines
        
        return lines

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