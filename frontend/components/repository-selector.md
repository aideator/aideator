# Repository Selector Component

An enhanced repository selector component that provides a searchable dropdown with recent repositories, organization grouping, and improved UX.

## Features

- **Search Functionality**: Real-time search through repositories with highlighted matching text
- **Recent Repositories**: Shows recently used repositories at the top with localStorage persistence
- **Organization Grouping**: Repositories are grouped by organization for better organization
- **Current Selection Indicator**: Shows a checkmark next to the currently selected repository
- **Demo Repository Support**: Includes demo repository for unauthenticated users
- **Responsive Design**: Works well on different screen sizes
- **Dark Mode Support**: Fully compatible with dark mode

## Usage

```tsx
import { RepositorySelector } from '@/components/repository-selector'

function MyComponent() {
  const [selectedRepo, setSelectedRepo] = useState('')
  const { repos, loading } = useGitHubRepos(token)

  return (
    <RepositorySelector
      repos={repos}
      selectedRepo={selectedRepo}
      onRepoSelect={setSelectedRepo}
      loading={loading}
      token={token}
      demoRepoUrl="https://github.com/aideator/helloworld"
    />
  )
}
```

## Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `repos` | `GitHubRepo[]` | Yes | Array of GitHub repositories |
| `selectedRepo` | `string` | Yes | Currently selected repository URL |
| `onRepoSelect` | `(repoUrl: string) => void` | Yes | Callback when a repository is selected |
| `loading` | `boolean` | No | Whether repositories are loading |
| `token` | `string \| null` | No | GitHub token for authentication |
| `demoRepoUrl` | `string` | No | Demo repository URL for unauthenticated users |

## Features in Detail

### Search Functionality
- Real-time filtering as you type
- Searches through repository names, full names, and descriptions
- Highlights matching text with yellow background
- Case-insensitive search

### Recent Repositories
- Automatically tracks recently used repositories
- Stores up to 10 most recent repositories in localStorage
- Shows at the top of the dropdown for quick access
- Includes organization information

### Organization Grouping
- Groups repositories by organization
- Shows organization name with building icon
- Repositories are indented under their organization
- Maintains grouping even when filtering

### Current Selection
- Shows a blue checkmark next to the currently selected repository
- Highlights the selected repository with a blue background
- Works for both recent repositories and organization repositories

### Demo Repository
- Automatically shows demo repository for unauthenticated users
- Can also be shown for authenticated users
- Clearly marked as "(demo)" for clarity

## Styling

The component uses Tailwind CSS classes and follows the AIdeator design system:
- Uses slate color palette for consistency
- Supports dark mode with appropriate color variants
- Responsive design with proper spacing
- Hover states and transitions for better UX

## Accessibility

- Proper ARIA labels and roles
- Keyboard navigation support
- Focus management
- Screen reader friendly

## Testing

The component includes comprehensive tests covering:
- Basic rendering
- Loading states
- Dropdown interaction
- Search functionality
- Repository selection
- Organization grouping
- Demo repository display

Run tests with:
```bash
npm test -- --testPathPatterns=repository-selector
```