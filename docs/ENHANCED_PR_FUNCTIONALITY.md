# Enhanced PR Functionality: Code Changes Support

## Overview

The AIdeator platform now supports creating pull requests with **actual code changes** applied to repository files, in addition to the existing markdown documentation approach. This enhancement enables users to generate fully functional PRs that can be directly reviewed and merged.

## Key Features

### 🔄 Dual Mode Operation
- **Code Changes Mode** (Default): Applies actual git diffs to repository files
- **Documentation Mode**: Creates markdown-only PRs (legacy behavior)

### 📝 Enhanced PR Content
- **Actual Code Changes**: Files are modified according to the AI-generated diff
- **Reference Documentation**: Markdown file with summary and diff for context
- **Git Integration**: Proper git commits with descriptive messages

### 🛡️ Safety Features
- **Fallback Mechanism**: If code changes fail, falls back to markdown-only approach
- **Error Handling**: Comprehensive error handling for diff parsing and file operations
- **Validation**: Git diff format validation before application

## API Changes

### Enhanced Endpoint

The existing PR creation endpoint now supports an optional parameter to control code change application:

```python
POST /api/v1/tasks/{task_id}/variations/{variation_id}/pull-request
```

**Parameters:**
- `task_id` (int): ID of the task
- `variation_id` (int): ID of the task variation
- `apply_code_changes` (bool, optional): Whether to apply actual code changes (default: `true`)
- `current_user`: Current authenticated user
- `credentials`: GitHub token for repository access
- `db`: Database session

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/tasks/123/variations/0/pull-request?apply_code_changes=true" \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  -H "Content-Type: application/json"
```

**Example Response:**
```json
{
  "pr_url": "https://github.com/owner/repo/pull/456"
}
```

## Implementation Details

### Git Diff Parsing

The enhanced `GitHubPRService` includes a robust git diff parser that:

1. **Parses File Headers**: Extracts file paths from `diff --git` lines
2. **Processes Hunks**: Parses `@@` hunk headers with line numbers
3. **Categorizes Changes**: Identifies additions (`+`), deletions (`-`), and context (` `)
4. **Handles Multiple Files**: Supports diffs affecting multiple files

### File Change Application

The service applies changes using a systematic approach:

1. **Read Original File**: Loads existing file content
2. **Parse Hunks**: Extracts change information from diff
3. **Apply Changes**: Modifies file lines according to diff
4. **Write Back**: Saves modified content to file
5. **Handle New Files**: Creates new files when needed

### Error Handling

The system includes comprehensive error handling:

- **Invalid Diff Format**: Validates git diff structure
- **File System Errors**: Handles permission and I/O issues
- **Git Operations**: Manages repository cloning and pushing
- **API Failures**: Handles GitHub API errors gracefully

## Usage Examples

### Creating PR with Code Changes (Default)

```python
from app.services.github_pr_service import GitHubPRService

# Initialize service with GitHub token
pr_service = GitHubPRService(github_token)

# Create PR with code changes (default behavior)
pr_url = await pr_service.create_pr(
    repo_http_url="https://github.com/user/repo",
    title="Add error handling to API endpoints",
    body="This PR adds comprehensive error handling...",
    diff_content=git_diff_output,
    apply_code_changes=True  # Default value
)
```

### Creating Documentation-Only PR

```python
# Create PR with only markdown documentation
pr_url = await pr_service.create_pr(
    repo_http_url="https://github.com/user/repo",
    title="Proposed changes for review",
    body="This PR contains proposed changes...",
    diff_content=git_diff_output,
    apply_code_changes=False  # Disable code changes
)
```

### API Integration

```python
# FastAPI endpoint usage
@router.post("/tasks/{task_id}/variations/{variation_id}/pull-request")
async def create_task_variation_pull_request(
    task_id: int,
    variation_id: int,
    apply_code_changes: bool = Query(default=True),
    current_user: CurrentUser,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_session),
):
    # ... validation logic ...
    
    pr_url = await pr_service.create_pr(
        repo_http_url=task.github_url,
        title=pr_title,
        body=pr_body,
        diff_content=diff_content,
        apply_code_changes=apply_code_changes,
    )
    
    return {"pr_url": pr_url}
```

## Testing

The enhanced functionality includes comprehensive tests:

### Unit Tests
- **Diff Parsing**: Tests for various git diff formats
- **File Operations**: Tests for applying changes to files
- **Error Handling**: Tests for invalid inputs and edge cases
- **URL Parsing**: Tests for GitHub URL extraction

### Integration Tests
- **End-to-End PR Creation**: Tests complete PR creation flow
- **Code Change Application**: Tests actual file modifications
- **Fallback Behavior**: Tests fallback to markdown-only mode

### Test Coverage
```bash
# Run specific tests
uv run pytest tests/test_github_pr_service.py -v

# Run with coverage
uv run pytest tests/test_github_pr_service.py --cov=app.services.github_pr_service
```

## Migration Guide

### For Existing Users

The enhancement is **backward compatible**. Existing code will continue to work:

- **Default Behavior**: Code changes are now applied by default
- **Legacy Support**: Set `apply_code_changes=False` for markdown-only PRs
- **No Breaking Changes**: All existing API contracts remain unchanged

### For New Implementations

1. **Enable Code Changes** (Recommended):
   ```python
   pr_url = await pr_service.create_pr(
       repo_http_url=repo_url,
       title=title,
       body=body,
       diff_content=diff_content,
       # apply_code_changes=True (default)
   )
   ```

2. **Disable Code Changes** (Legacy Mode):
   ```python
   pr_url = await pr_service.create_pr(
       repo_http_url=repo_url,
       title=title,
       body=body,
       diff_content=diff_content,
       apply_code_changes=False
   )
   ```

## Security Considerations

### Token Management
- **GitHub Token**: Required for repository access and PR creation
- **Scope Requirements**: Token must have `repo` scope for private repositories
- **Token Security**: Tokens are handled securely and not logged

### Repository Access
- **Authentication**: Uses GitHub token for repository cloning
- **Permissions**: Respects repository access permissions
- **Branch Protection**: Works with protected branches (requires appropriate permissions)

### Code Safety
- **Validation**: Git diff format is validated before application
- **Isolation**: Changes are applied in temporary clones
- **Rollback**: Failed operations don't affect original repository

## Performance Considerations

### Optimization Features
- **Shallow Cloning**: Uses `depth=1` for faster repository cloning
- **Efficient Parsing**: Optimized diff parsing algorithms
- **Memory Management**: Proper cleanup of temporary resources

### Resource Usage
- **Temporary Storage**: Uses temporary directories for repository clones
- **Cleanup**: Automatic cleanup of temporary files
- **Concurrency**: Supports concurrent PR creation operations

## Troubleshooting

### Common Issues

1. **Invalid Git Diff Format**
   ```
   Error: Invalid hunk header
   Solution: Ensure diff content is valid git diff output
   ```

2. **Repository Access Denied**
   ```
   Error: Failed to create PR – GitHub API returned 403
   Solution: Check GitHub token permissions and repository access
   ```

3. **File Permission Errors**
   ```
   Error: Permission denied when writing files
   Solution: Ensure proper file system permissions
   ```

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.getLogger('app.services.github_pr_service').setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features
- **Conflict Resolution**: Automatic merge conflict detection and resolution
- **Branch Strategy**: Support for different branching strategies
- **Review Integration**: Integration with GitHub review workflows
- **Template Support**: Customizable PR templates

### Performance Improvements
- **Caching**: Cache repository clones for repeated operations
- **Parallel Processing**: Parallel diff application for large changes
- **Incremental Updates**: Support for incremental file updates

## Conclusion

The enhanced PR functionality provides a significant improvement to the AIdeator platform, enabling users to create fully functional pull requests with actual code changes. The implementation maintains backward compatibility while providing new capabilities for automated code generation and review workflows.

For questions or support, please refer to the project documentation or create an issue in the repository.