Based on my analysis of the frontend-old codebase, here's how GitHub repositories were being loaded:

  GitHub Repository Loading Flow

  1. Client-Side Storage Only

  - Repositories were stored in browser LocalStorage (key: 'aideator-github-repos')
  - No backend API to fetch repositories - it was purely client-side
  - Default repos: octocat/Hello-World and aideator/helloworld.git

  2. Repository Management Hook

  The useRepositoryList hook managed repos with:
  - Add new repository functionality
  - URL validation (must be from github.com)
  - Duplicate prevention
  - Persistence in LocalStorage

  3. UI Component

  The RepositoryPicker component provided:
  - Dropdown selector for saved repos
  - "Add New Repository" option
  - Integration with the task submission form

  4. Backend Integration

  When submitting a task:
  - The selected github_url was sent in the POST request to /api/v1/runs
  - Backend validated the URL and passed it to Kubernetes jobs
  - Each agent cloned the repository independently

  Key Insight

  The system used a simple, client-side approach - no backend repository management or GitHub API integration. Users manually added repository URLs, which were
  saved locally in their browser.

  This is why in your current frontend remake, you have hardcoded repository options in the dropdown. To match the original functionality, you'd need to implement
  client-side repository management with LocalStorage.

---

Based on my analysis, here's what I found about the test-user and what's needed for your GitHub OAuth setup:

  Current Test-User Auto-Login

  The test-user is created with:
  - Email: test@aideator.local
  - Password: testpass123
  - No GitHub association - it's just a local user account
  - Returns JWT token and API key for immediate access

  What You Need for GitHub OAuth Integration

  1. Database Changes

  Add GitHub fields to the User model:
  github_id: str | None
  github_username: str | None
  github_avatar_url: str | None
  github_access_token_encrypted: str | None
  auth_provider: str  # "local" or "github"

  2. GitHub OAuth Flow

  You'll need:
  - GitHub OAuth App registration
  - Client ID & Secret in environment vars
  - OAuth endpoints:
    - /api/v1/auth/github/login - Initiates OAuth
    - /api/v1/auth/github/callback - Handles return

  3. Repository Access Management

  For the repo configuration you want:
  - Store GitHub access token per user
  - Use GitHub API to fetch user's accessible repos
  - API endpoint to list repos: GET /api/v1/users/me/repos
  - Store user's selected repos in database or use GitHub App installation

  4. Frontend Integration

  - "Sign in with GitHub" button
  - Repository/branch selectors populated from API
  - Replace hardcoded repos with dynamic list

  5. Test User as GitHub User

  Instead of test@aideator.local, you could:
  - Create a real GitHub account for testing
  - Grant it access to github.com/aideator repos
  - Use GitHub OAuth even in dev mode

  The current system has all the auth infrastructure (JWT, user management) - you just need to add the GitHub OAuth layer on top. The test-user auto-login could be modified to authenticate with a real GitHub test account.
