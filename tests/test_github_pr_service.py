import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.github_pr_service import GitHubPRService


class TestGitHubPRService:
    """Test the enhanced GitHub PR service with code change application."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = GitHubPRService("test-token")
        self.sample_diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,5 @@
 def hello():
-    print("Hello")
+    print("Hello, World!")
+    return True
+
+def goodbye():
+    print("Goodbye")
"""

    def test_parse_git_diff_simple(self):
        """Test parsing a simple git diff."""
        file_changes = self.service._parse_git_diff(self.sample_diff)
        
        assert len(file_changes) == 1
        file_change = file_changes[0]
        assert file_change['file_path'] == 'test.py'
        assert len(file_change['hunks']) == 1
        
        hunk = file_change['hunks'][0]
        assert hunk['old_start'] == 1
        assert hunk['old_count'] == 3
        assert hunk['new_start'] == 1
        assert hunk['new_count'] == 5

    def test_parse_hunk_changes(self):
        """Test parsing hunk changes correctly."""
        file_changes = self.service._parse_git_diff(self.sample_diff)
        hunk = file_changes[0]['hunks'][0]
        
        changes = hunk['changes']
        assert len(changes) == 5
        
        # Check that changes are parsed correctly
        change_types = [change[0] for change in changes]
        assert change_types == ['context', 'delete', 'add', 'add', 'add']

    def test_apply_hunk_to_lines(self):
        """Test applying a hunk to file lines."""
        original_lines = [
            "def hello():\n",
            "    print(\"Hello\")\n",
            "    return False\n"
        ]
        
        hunk = {
            'old_start': 1,
            'old_count': 3,
            'new_start': 1,
            'new_count': 5,
            'changes': [
                ('context', 'def hello():'),
                ('delete', '    print("Hello")'),
                ('add', '    print("Hello, World!")'),
                ('add', '    return True'),
                ('add', ''),
                ('add', 'def goodbye():'),
                ('add', '    print("Goodbye")')
            ]
        }
        
        result = self.service._apply_hunk(original_lines, hunk)
        
        expected = [
            "def hello():\n",
            "    print(\"Hello, World!\")\n",
            "    return True\n",
            "\n",
            "def goodbye():\n",
            "    print(\"Goodbye\")\n"
        ]
        
        assert result == expected

    def test_apply_file_change(self):
        """Test applying changes to a file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a test file
            test_file = Path(tmp_dir) / "test.py"
            test_file.write_text("def hello():\n    print(\"Hello\")\n    return False\n")
            
            # Create file change
            file_change = {
                'file_path': 'test.py',
                'hunks': [{
                    'old_start': 1,
                    'old_count': 3,
                    'new_start': 1,
                    'new_count': 5,
                    'changes': [
                        ('context', 'def hello():'),
                        ('delete', '    print("Hello")'),
                        ('add', '    print("Hello, World!")'),
                        ('add', '    return True'),
                        ('add', ''),
                        ('add', 'def goodbye():'),
                        ('add', '    print("Goodbye")')
                    ]
                }]
            }
            
            # Apply changes
            self.service._apply_file_change(tmp_dir, file_change)
            
            # Check result
            result = test_file.read_text()
            expected = "def hello():\n    print(\"Hello, World!\")\n    return True\n\n\ndef goodbye():\n    print(\"Goodbye\")\n"
            assert result == expected

    def test_apply_git_diff_multiple_files(self):
        """Test applying diff with multiple files."""
        multi_file_diff = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,2 +1,3 @@
 def func1():
-    pass
+    return True
+
diff --git a/file2.py b/file2.py
index 1234567..abcdefg 100644
--- a/file2.py
+++ b/file2.py
@@ -0,0 +1,2 @@
+def func2():
+    return False
"""
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create initial file1.py
            file1 = Path(tmp_dir) / "file1.py"
            file1.write_text("def func1():\n    pass\n")
            
            # Apply diff
            self.service._apply_git_diff(tmp_dir, multi_file_diff)
            
            # Check file1.py changes
            file1_content = file1.read_text()
            assert "return True" in file1_content
            
            # Check file2.py was created
            file2 = Path(tmp_dir) / "file2.py"
            assert file2.exists()
            file2_content = file2.read_text()
            assert "def func2():" in file2_content

    def test_parse_git_diff_empty(self):
        """Test parsing empty diff."""
        result = self.service._parse_git_diff("")
        assert result == []

    def test_parse_git_diff_no_changes(self):
        """Test parsing diff with no actual changes."""
        no_change_diff = """diff --git a/test.py b/test.py
index 1234567..1234567 100644
--- a/test.py
+++ b/test.py
@@ -1,1 +1,1 @@
 def hello():
-    print("Hello")
+    print("Hello")
"""
        
        result = self.service._parse_git_diff(no_change_diff)
        assert len(result) == 1
        assert len(result[0]['hunks']) == 1

    def test_invalid_hunk_header(self):
        """Test handling invalid hunk header."""
        invalid_diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ invalid @@
"""
        
        with pytest.raises(ValueError, match="Invalid hunk header"):
            self.service._parse_git_diff(invalid_diff)

    @patch('app.services.github_pr_service.Repo')
    @patch('app.services.github_pr_service.httpx.AsyncClient')
    async def test_create_pr_with_code_changes(self, mock_client, mock_repo):
        """Test creating PR with code changes enabled."""
        # Mock the repository
        mock_repo_instance = MagicMock()
        mock_repo.clone_from.return_value = mock_repo_instance
        mock_repo_instance.git.symbolic_ref.return_value = "refs/remotes/origin/main"
        mock_repo_instance.remote.return_value.push.return_value = None
        
        # Mock the GitHub API response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"html_url": "https://github.com/test/repo/pull/123"}
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance
        
        # Test creating PR with code changes
        result = await self.service.create_pr(
            repo_http_url="https://github.com/test/repo",
            title="Test PR",
            body="Test body",
            diff_content=self.sample_diff,
            apply_code_changes=True
        )
        
        assert result == "https://github.com/test/repo/pull/123"
        
        # Verify that files were added to git index
        mock_repo_instance.index.add.assert_called()

    @patch('app.services.github_pr_service.Repo')
    @patch('app.services.github_pr_service.httpx.AsyncClient')
    async def test_create_pr_without_code_changes(self, mock_client, mock_repo):
        """Test creating PR with code changes disabled."""
        # Mock the repository
        mock_repo_instance = MagicMock()
        mock_repo.clone_from.return_value = mock_repo_instance
        mock_repo_instance.git.symbolic_ref.return_value = "refs/remotes/origin/main"
        mock_repo_instance.remote.return_value.push.return_value = None
        
        # Mock the GitHub API response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"html_url": "https://github.com/test/repo/pull/123"}
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value = mock_client_instance
        
        # Test creating PR without code changes
        result = await self.service.create_pr(
            repo_http_url="https://github.com/test/repo",
            title="Test PR",
            body="Test body",
            diff_content=self.sample_diff,
            apply_code_changes=False
        )
        
        assert result == "https://github.com/test/repo/pull/123"
        
        # Verify that only markdown file was added (no "*" add)
        calls = mock_repo_instance.index.add.call_args_list
        assert len(calls) == 1
        assert "*" not in calls[0][0][0]

    def test_extract_owner_repo(self):
        """Test extracting owner and repo from GitHub URLs."""
        # Test standard HTTPS URL
        owner, repo = self.service._extract_owner_repo("https://github.com/test/repo")
        assert owner == "test"
        assert repo == "repo"
        
        # Test URL with .git suffix
        owner, repo = self.service._extract_owner_repo("https://github.com/test/repo.git")
        assert owner == "test"
        assert repo == "repo"
        
        # Test URL with trailing slash
        owner, repo = self.service._extract_owner_repo("https://github.com/test/repo/")
        assert owner == "test"
        assert repo == "repo"
        
        # Test invalid URL
        with pytest.raises(ValueError):
            self.service._extract_owner_repo("https://github.com/test")

    def test_build_patch_markdown(self):
        """Test building markdown patch file."""
        title = "Test PR"
        summary = "This is a test summary"
        diff = "diff --git a/test.py b/test.py\n@@ -1,1 +1,1 @@\n-def hello():\n+def hello_world():\n"
        
        result = self.service._build_patch_markdown(title, summary, diff)
        
        assert "# Test PR" in result
        assert "## Summary" in result
        assert "This is a test summary" in result
        assert "## Diff" in result
        assert "```diff" in result
        assert "def hello_world():" in result