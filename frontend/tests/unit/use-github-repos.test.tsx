import { renderHook, waitFor } from '@testing-library/react'
import { useGitHubRepos, GitHubRepo } from '@/hooks/use-github-repos'

function generateRepos(count: number, startId = 1, owner = 'org'): GitHubRepo[] {
  return Array.from({ length: count }).map((_, idx) => ({
    id: startId + idx,
    name: `repo-${startId + idx}`,
    full_name: `${owner}/repo-${startId + idx}`,
    html_url: `https://github.com/${owner}/repo-${startId + idx}`,
    description: null,
    private: false,
    default_branch: 'main',
    updated_at: new Date().toISOString(),
    owner: { login: owner },
  }))
}

describe('useGitHubRepos', () => {
  beforeEach(() => {
    ;(global.fetch as jest.Mock).mockReset()
  })

  it('aggregates paginated results up to 300 repos', async () => {
    // Page 1 returns 100 repos
    const page1 = generateRepos(100, 1, 'org1')
    // Page 2 returns another 100
    const page2 = generateRepos(100, 101, 'org1')
    // Page 3 returns 50 (less than 100) triggers break
    const page3 = generateRepos(50, 201, 'org1')

    ;(global.fetch as jest.Mock)
      .mockResolvedValueOnce({ ok: true, json: async () => page1 })
      .mockResolvedValueOnce({ ok: true, json: async () => page2 })
      .mockResolvedValueOnce({ ok: true, json: async () => page3 })

    const { result } = renderHook(() => useGitHubRepos('fake-token'))

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.error).toBeNull()
    expect(result.current.repos.length).toBe(250)
    // Ensure fetch was called correct number of times
    expect((global.fetch as jest.Mock).mock.calls.length).toBe(3)
  })
})