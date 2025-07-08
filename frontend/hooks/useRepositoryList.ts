import { useState, useEffect } from 'react';

const STORAGE_KEY = 'aideator-github-repos';

const DEFAULT_REPOS = [
  'https://github.com/octocat/Hello-World',
  'https://github.com/aideator/helloworld.git',
];

export function useRepositoryList() {
  const [repositories, setRepositories] = useState<string[]>(DEFAULT_REPOS);

  // Load from LocalStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setRepositories(parsed);
        }
      }
    } catch (error) {
      console.error('Error loading repositories from LocalStorage:', error);
    }
  }, []);

  // Save to LocalStorage whenever repositories change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(repositories));
    } catch (error) {
      console.error('Error saving repositories to LocalStorage:', error);
    }
  }, [repositories]);

  const addRepository = (url: string): boolean => {
    // Check for duplicates
    if (repositories.includes(url)) {
      return false;
    }

    // Validate GitHub URL
    if (!isValidGitHubUrl(url)) {
      return false;
    }

    setRepositories(prev => [...prev, url]);
    return true;
  };

  const isValidGitHubUrl = (url: string): boolean => {
    try {
      const parsed = new URL(url);
      return parsed.hostname === 'github.com' || parsed.hostname === 'www.github.com';
    } catch {
      return false;
    }
  };

  return {
    repositories,
    addRepository,
    isValidGitHubUrl,
  };
}