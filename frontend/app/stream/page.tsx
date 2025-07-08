'use client';

import React, { useState } from 'react';
import { useAgentStream } from '@/hooks/useAgentStream';
import { useRepositoryList } from '@/hooks/useRepositoryList';
import { StreamGrid } from '@/components/agents/StreamGrid';
import { createRun } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { BrainCircuit, Play, Square, Settings, Zap, GitBranch, Users, Sparkles, AlertCircle, Plus } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

export default function StreamPage() {
  // Repository list
  const { repositories, addRepository, isValidGitHubUrl } = useRepositoryList();
  
  // Form state
  const [githubUrl, setGithubUrl] = useState(repositories[0] || 'https://github.com/octocat/Hello-World');
  const [prompt, setPrompt] = useState('Analyze this repository and suggest improvements.');
  const [variations, setVariations] = useState(3);
  const [isStarting, setIsStarting] = useState(false);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  
  // Dialog state
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newRepoUrl, setNewRepoUrl] = useState('');
  const [dialogError, setDialogError] = useState<string | null>(null);

  // Streaming state
  const {
    streams,
    isStreaming,
    error: streamError,
    connectionState,
    startStream,
    stopStream,
    clearStreams,
    selectAgent,
  } = useAgentStream();

  const handleStartGeneration = async () => {
    try {
      setIsStarting(true);
      setFormError(null);
      
      // Validate inputs
      if (!githubUrl.trim()) {
        throw new Error('GitHub URL is required');
      }
      if (!prompt.trim()) {
        throw new Error('Prompt is required');
      }
      if (variations < 1 || variations > 5) {
        throw new Error('Variations must be between 1 and 5');
      }

      // Clear previous streams
      clearStreams();

      // Create run via API
      const response = await createRun({
        github_url: githubUrl,
        prompt: prompt,
        variations: variations,
      });

      console.log('Run created:', response);
      setCurrentRunId(response.run_id);

      // Start streaming
      startStream(response.run_id);

    } catch (error) {
      console.error('Failed to start generation:', error);
      setFormError(error instanceof Error ? error.message : 'Failed to start generation');
    } finally {
      setIsStarting(false);
    }
  };

  const handleStopGeneration = () => {
    stopStream();
    setCurrentRunId(null);
  };

  const handleSelectAgent = async (variationId: number) => {
    if (!currentRunId) {
      console.error('No current run to select from');
      return;
    }

    try {
      await selectAgent(variationId);
      console.log(`Selected agent ${variationId} for run ${currentRunId}`);
    } catch (error) {
      console.error('Failed to select agent:', error);
    }
  };

  const handleAddRepository = () => {
    setDialogError(null);
    
    if (!newRepoUrl.trim()) {
      setDialogError('Please enter a repository URL');
      return;
    }
    
    if (!isValidGitHubUrl(newRepoUrl)) {
      setDialogError('Please enter a valid GitHub URL');
      return;
    }
    
    const success = addRepository(newRepoUrl);
    if (!success) {
      setDialogError('This repository is already in your list');
      return;
    }
    
    // Success - select the new repo and close dialog
    setGithubUrl(newRepoUrl);
    setNewRepoUrl('');
    setIsDialogOpen(false);
    setDialogError(null);
  };

  const handleSelectChange = (value: string) => {
    if (value === 'add-new') {
      setIsDialogOpen(true);
    } else {
      setGithubUrl(value);
    }
  };

  const hasActiveStreams = streams.size > 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <header className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-purple-600 to-indigo-600 text-white mb-6 shadow-xl">
            <BrainCircuit className="h-10 w-10" />
          </div>
          <h1 className="text-5xl font-bold text-gray-900 mb-3">
            AIdeator
          </h1>
          <p className="text-xl text-gray-600">
            Multi-Agent AI Orchestration Platform
          </p>
          
          {/* Connection Status */}
          <div className="flex items-center justify-center gap-4 mt-6">
            {currentRunId && (
              <span className="inline-flex items-center px-4 py-1 rounded-full text-sm bg-purple-100 text-purple-700">
                <Sparkles className="w-4 h-4 mr-2" />
                Run: {currentRunId.slice(0, 8)}...
              </span>
            )}
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${
                connectionState === 'connected' ? 'bg-green-500 animate-pulse' : 
                connectionState === 'connecting' ? 'bg-yellow-500 animate-pulse' : 
                connectionState === 'error' ? 'bg-red-500' : 'bg-gray-400'
              }`} />
              <span className="text-sm text-gray-600">
                {connectionState === 'connected' ? 'Connected' : 
                 connectionState === 'connecting' ? 'Connecting' : 
                 connectionState === 'error' ? 'Error' : 'Disconnected'}
              </span>
            </div>
          </div>
        </header>

        {/* Configuration Panel */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-10">
          <div className="flex items-center gap-3 mb-6">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-500 text-white">
              <Settings className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                Generation Configuration
              </h2>
              <p className="text-gray-600">Configure your multi-agent task parameters</p>
            </div>
          </div>

          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* GitHub URL */}
              <div className="lg:col-span-2">
                <label htmlFor="github-url" className="block text-sm font-medium text-gray-700 mb-2">
                  <div className="flex items-center gap-2">
                    <GitBranch className="h-4 w-4" />
                    GitHub Repository URL
                  </div>
                </label>
                <Select
                  value={githubUrl}
                  onValueChange={handleSelectChange}
                  disabled={isStreaming}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {repositories.map((repo) => (
                      <SelectItem key={repo} value={repo}>
                        {repo}
                      </SelectItem>
                    ))}
                    <SelectItem value="add-new">
                      <div className="flex items-center gap-2">
                        <Plus className="h-4 w-4" />
                        Add New Repository...
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Variations */}
              <div>
                <label htmlFor="variations" className="block text-sm font-medium text-gray-700 mb-2">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4" />
                    Agent Variations
                  </div>
                </label>
                <select 
                  value={variations} 
                  onChange={(e) => setVariations(parseInt(e.target.value))}
                  disabled={isStreaming}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                >
                  {[1, 2, 3, 4, 5].map(num => (
                    <option key={num} value={num}>
                      {num} {num === 1 ? 'Agent' : 'Agents'}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Prompt */}
            <div>
              <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4" />
                  Task Prompt
                </div>
              </label>
              <textarea
                id="prompt"
                placeholder="Describe what you want the agents to do with this repository..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                disabled={isStreaming}
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all resize-none"
              />
            </div>
          </div>

          {/* Error Display */}
          {formError && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center gap-2 text-red-800">
                <AlertCircle className="h-5 w-5" />
                <span className="font-medium">{formError}</span>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center gap-4 mt-6">
            {!isStreaming ? (
              <button
                onClick={handleStartGeneration}
                disabled={isStarting || !githubUrl.trim() || !prompt.trim()}
                className="px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg font-semibold hover:from-purple-700 hover:to-indigo-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Play className="inline w-5 h-5 mr-2" />
                {isStarting ? 'Starting Generation...' : 'Start Generation'}
              </button>
            ) : (
              <button
                onClick={handleStopGeneration}
                className="px-6 py-3 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 transition-all"
              >
                <Square className="inline w-5 h-5 mr-2" />
                Stop Generation
              </button>
            )}
            
            {hasActiveStreams && (
              <button
                onClick={clearStreams}
                disabled={isStreaming}
                className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Clear Results
              </button>
            )}

            {/* Status Indicators */}
            {isStreaming && (
              <div className="ml-auto flex items-center gap-2 px-4 py-2 bg-purple-100 text-purple-700 rounded-lg">
                <div className="w-2 h-2 bg-purple-600 rounded-full animate-pulse" />
                <span className="text-sm font-medium">
                  {streams.size} / {variations} agents active
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Streaming Grid */}
        <StreamGrid
          streams={streams}
          isStreaming={isStreaming}
          connectionState={connectionState}
          error={streamError}
          onSelectAgent={handleSelectAgent}
          maxVariations={variations}
        />
        
        {/* Add Repository Dialog */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Add New Repository</DialogTitle>
              <DialogDescription>
                Enter a GitHub repository URL to add it to your list.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="new-repo">Repository URL</Label>
                <Input
                  id="new-repo"
                  type="url"
                  placeholder="https://github.com/username/repository"
                  value={newRepoUrl}
                  onChange={(e) => setNewRepoUrl(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddRepository()}
                />
                {dialogError && (
                  <p className="text-sm text-red-600">{dialogError}</p>
                )}
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setIsDialogOpen(false);
                  setNewRepoUrl('');
                  setDialogError(null);
                }}
              >
                Cancel
              </Button>
              <Button type="button" onClick={handleAddRepository}>
                Add Repository
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}