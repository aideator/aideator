"use client";

import React, { useState } from 'react';
import { Github, Plus, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useRepositoryList } from '@/hooks/useRepositoryList';
import { cn } from '@/lib/utils';

interface RepositoryPickerProps {
  selectedRepo?: string;
  onRepoSelect: (repo: string) => void;
  disabled?: boolean;
  className?: string;
}

export function RepositoryPicker({ 
  selectedRepo, 
  onRepoSelect, 
  disabled = false, 
  className 
}: RepositoryPickerProps) {
  const { repositories, addRepository, isValidGitHubUrl } = useRepositoryList();
  const [showAddRepo, setShowAddRepo] = useState(false);
  const [newRepoUrl, setNewRepoUrl] = useState('');
  const [addRepoError, setAddRepoError] = useState('');

  const handleAddRepository = () => {
    if (!newRepoUrl.trim()) {
      setAddRepoError('Please enter a repository URL');
      return;
    }

    if (!isValidGitHubUrl(newRepoUrl.trim())) {
      setAddRepoError('Please enter a valid GitHub repository URL');
      return;
    }

    if (addRepository(newRepoUrl.trim())) {
      setNewRepoUrl('');
      setShowAddRepo(false);
      setAddRepoError('');
      onRepoSelect(newRepoUrl.trim());
    } else {
      setAddRepoError('Repository already exists in the list');
    }
  };

  const handleCancelAdd = () => {
    setNewRepoUrl('');
    setShowAddRepo(false);
    setAddRepoError('');
  };

  return (
    <div className={cn('space-y-3', className)}>
      <Label className="flex items-center gap-2 text-label font-medium text-neutral-charcoal">
        <Github className="h-4 w-4" />
        GitHub Repository
      </Label>
      
      <div className="space-y-2">
        <Select 
          value={selectedRepo || ''} 
          onValueChange={onRepoSelect}
          disabled={disabled}
        >
          <SelectTrigger className="w-full bg-neutral-white border border-neutral-fog rounded-md px-md py-md text-body focus:border-ai-primary focus:ring-2 focus:ring-ai-primary/20 transition-colors">
            <SelectValue placeholder="Select a repository..." />
          </SelectTrigger>
          <SelectContent>
            {repositories.map((repo) => (
              <SelectItem key={repo} value={repo}>
                <div className="flex items-center gap-2">
                  <Github className="h-4 w-4 text-neutral-shadow" />
                  <span className="font-mono text-sm">{repo}</span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {!showAddRepo ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setShowAddRepo(true)}
            disabled={disabled}
            className="w-full border-2 border-dashed border-neutral-fog hover:border-ai-primary hover:bg-ai-primary/5 transition-colors text-neutral-shadow hover:text-ai-primary"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add New Repository
          </Button>
        ) : (
          <div className="border border-neutral-fog rounded-md p-md bg-neutral-paper">
            <div className="space-y-3">
              <div>
                <Label htmlFor="new-repo-url" className="text-body-sm font-medium text-neutral-charcoal">
                  Repository URL
                </Label>
                <Input
                  id="new-repo-url"
                  type="url"
                  placeholder="https://github.com/username/repository"
                  value={newRepoUrl}
                  onChange={(e) => {
                    setNewRepoUrl(e.target.value);
                    setAddRepoError('');
                  }}
                  className="mt-1 bg-neutral-white border border-neutral-fog rounded-md px-md py-sm text-body placeholder:text-neutral-shadow focus:border-ai-primary focus:ring-2 focus:ring-ai-primary/20 transition-colors"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleAddRepository();
                    } else if (e.key === 'Escape') {
                      handleCancelAdd();
                    }
                  }}
                />
                {addRepoError && (
                  <p className="mt-1 text-body-sm text-semantic-error">{addRepoError}</p>
                )}
              </div>
              
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  size="sm"
                  onClick={handleAddRepository}
                  className="bg-ai-primary text-white hover:bg-ai-primary/90 transition-colors"
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleCancelAdd}
                  className="border-neutral-fog text-neutral-charcoal hover:bg-neutral-fog transition-colors"
                >
                  <X className="h-4 w-4 mr-1" />
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}