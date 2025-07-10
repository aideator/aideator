'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  Plus, 
  Search, 
  MoreHorizontal, 
  Edit3, 
  Trash2, 
  Calendar,
  MessageSquare,
  Check,
  X,
  History,
  Clock,
  Filter,
  SortAsc,
  SortDesc
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '@/lib/utils';

export interface Session {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  turnCount: number;
  lastPrompt?: string;
  modelPreferences?: Record<string, number>;
  isActive?: boolean;
}

interface SessionSidebarProps {
  sessions: Session[];
  activeSessionId?: string;
  onSessionSelect: (sessionId: string) => void;
  onSessionCreate: (title: string) => void;
  onSessionUpdate: (sessionId: string, updates: Partial<Session>) => void;
  onSessionDelete: (sessionId: string) => void;
  isLoading?: boolean;
  className?: string;
}

type SortOption = 'recent' | 'oldest' | 'title' | 'turns';

export function SessionSidebar({
  sessions,
  activeSessionId,
  onSessionSelect,
  onSessionCreate,
  onSessionUpdate,
  onSessionDelete,
  isLoading = false,
  className,
}: SessionSidebarProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('recent');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [newSessionTitle, setNewSessionTitle] = useState('');
  const [sessionToDelete, setSessionToDelete] = useState<Session | null>(null);

  // Filter and sort sessions
  const filteredAndSortedSessions = React.useMemo(() => {
    const filtered = sessions.filter(session => 
      session.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      session.lastPrompt?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    switch (sortBy) {
      case 'recent':
        filtered.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
        break;
      case 'oldest':
        filtered.sort((a, b) => new Date(a.updatedAt).getTime() - new Date(b.updatedAt).getTime());
        break;
      case 'title':
        filtered.sort((a, b) => a.title.localeCompare(b.title));
        break;
      case 'turns':
        filtered.sort((a, b) => b.turnCount - a.turnCount);
        break;
    }

    return filtered;
  }, [sessions, searchQuery, sortBy]);

  const handleCreateSession = () => {
    if (newSessionTitle.trim()) {
      onSessionCreate(newSessionTitle.trim());
      setNewSessionTitle('');
      setIsCreateDialogOpen(false);
    }
  };

  const handleStartEditing = (session: Session) => {
    setEditingSessionId(session.id);
    setEditingTitle(session.title);
  };

  const handleSaveEdit = () => {
    if (editingSessionId && editingTitle.trim()) {
      onSessionUpdate(editingSessionId, { title: editingTitle.trim() });
      setEditingSessionId(null);
      setEditingTitle('');
    }
  };

  const handleCancelEdit = () => {
    setEditingSessionId(null);
    setEditingTitle('');
  };

  const handleDeleteConfirm = () => {
    if (sessionToDelete) {
      onSessionDelete(sessionToDelete.id);
      setSessionToDelete(null);
      setIsDeleteDialogOpen(false);
    }
  };

  const handleDeleteClick = (session: Session) => {
    setSessionToDelete(session);
    setIsDeleteDialogOpen(true);
  };

  const getSortIcon = () => {
    switch (sortBy) {
      case 'recent':
      case 'turns':
        return <SortDesc className="w-4 h-4" />;
      case 'oldest':
        return <SortAsc className="w-4 h-4" />;
      case 'title':
        return <SortAsc className="w-4 h-4" />;
      default:
        return <SortDesc className="w-4 h-4" />;
    }
  };

  return (
    <div className={cn("w-80 bg-neutral-paper border border-neutral-fog flex flex-col h-full rounded-xl shadow-lg", className)}>
      {/* Header */}
      <CardHeader className="pt-md pb-sm border-b border-neutral-fog rounded-t-xl">
        <div className="flex items-center justify-between">
          <CardTitle className="text-h3 font-semibold text-neutral-charcoal">
            Sessions
          </CardTitle>
          <Button
            onClick={() => setIsCreateDialogOpen(true)}
            size="sm"
            className="bg-ai-primary text-white hover:bg-ai-primary/90"
          >
            <Plus className="w-4 h-4 mr-1" />
            New
          </Button>
        </div>
      </CardHeader>

      {/* Search and Sort */}
      <div className="p-md space-y-sm border-b border-neutral-fog">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-shadow w-4 h-4" />
          <Input
            placeholder="Search sessions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-neutral-white border-neutral-fog"
          />
        </div>
        
        <div className="flex items-center gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="flex items-center gap-2">
                {getSortIcon()}
                <span className="text-body-sm">
                  {sortBy === 'recent' ? 'Recent' :
                   sortBy === 'oldest' ? 'Oldest' :
                   sortBy === 'title' ? 'Title' : 'Turns'}
                </span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => setSortBy('recent')}>
                <Clock className="w-4 h-4 mr-2" />
                Most Recent
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSortBy('oldest')}>
                <History className="w-4 h-4 mr-2" />
                Oldest First
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSortBy('title')}>
                <Edit3 className="w-4 h-4 mr-2" />
                Title A-Z
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSortBy('turns')}>
                <MessageSquare className="w-4 h-4 mr-2" />
                Most Active
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          
          <Badge variant="outline" className="text-neutral-shadow">
            {filteredAndSortedSessions.length} sessions
          </Badge>
        </div>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto rounded-b-xl">
        {isLoading ? (
          <div className="p-md space-y-sm">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="bg-neutral-fog rounded-lg p-md">
                  <div className="h-4 bg-neutral-shadow rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-neutral-shadow rounded w-1/2"></div>
                </div>
              </div>
            ))}
          </div>
        ) : filteredAndSortedSessions.length === 0 ? (
          <div className="p-md text-center text-neutral-shadow">
            {searchQuery ? (
              <div>
                <Search className="w-12 h-12 mx-auto mb-2 text-neutral-fog" />
                <p className="text-body-sm">No sessions found for "{searchQuery}"</p>
              </div>
            ) : (
              <div>
                <MessageSquare className="w-12 h-12 mx-auto mb-2 text-neutral-fog" />
                <p className="text-body-sm">No sessions yet</p>
                <p className="text-body-sm">Create your first session to get started</p>
              </div>
            )}
          </div>
        ) : (
          <div className="p-md space-y-sm">
            {filteredAndSortedSessions.map((session) => (
              <div
                key={session.id}
                className={`rounded-lg border-2 cursor-pointer transition-all ${
                  session.id === activeSessionId
                    ? 'border-ai-primary bg-ai-primary/10'
                    : 'border-neutral-fog bg-neutral-white hover:border-neutral-shadow'
                }`}
                onClick={() => onSessionSelect(session.id)}
              >
                <div className="p-md">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      {editingSessionId === session.id ? (
                        <div className="flex items-center gap-2 mb-2">
                          <Input
                            value={editingTitle}
                            onChange={(e) => setEditingTitle(e.target.value)}
                            className="text-body-sm font-medium"
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleSaveEdit();
                              if (e.key === 'Escape') handleCancelEdit();
                            }}
                            onClick={(e) => e.stopPropagation()}
                            autoFocus
                          />
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleSaveEdit();
                            }}
                            className="text-semantic-success hover:text-semantic-success"
                          >
                            <Check className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleCancelEdit();
                            }}
                            className="text-semantic-error hover:text-semantic-error"
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      ) : (
                        <h4 className="text-body font-medium text-neutral-charcoal truncate mb-1">
                          {session.title}
                        </h4>
                      )}
                      
                      {session.lastPrompt && (
                        <p className="text-body-sm text-neutral-shadow line-clamp-2 mb-2">
                          {session.lastPrompt}
                        </p>
                      )}
                      
                      <div className="flex items-center gap-3 text-body-sm text-neutral-shadow">
                        <div className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          <span>{formatDistanceToNow(new Date(session.updatedAt), { addSuffix: true })}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <MessageSquare className="w-3 h-3" />
                          <span>{session.turnCount} turns</span>
                        </div>
                      </div>
                    </div>
                    
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-neutral-shadow hover:text-neutral-charcoal"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <MoreHorizontal className="w-4 h-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent>
                        <DropdownMenuItem onClick={() => handleStartEditing(session)}>
                          <Edit3 className="w-4 h-4 mr-2" />
                          Rename
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem 
                          onClick={() => handleDeleteClick(session)}
                          className="text-semantic-error hover:text-semantic-error"
                        >
                          <Trash2 className="w-4 h-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Session Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Create New Session</DialogTitle>
            <DialogDescription>
              Give your session a descriptive title to help you find it later.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <Input
              placeholder="Session title (e.g., 'Code Review', 'Blog Post Ideas')"
              value={newSessionTitle}
              onChange={(e) => setNewSessionTitle(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCreateSession()}
              autoFocus
            />
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsCreateDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={handleCreateSession}
              disabled={!newSessionTitle.trim()}
              className="bg-ai-primary text-white hover:bg-ai-primary/90"
            >
              Create Session
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Session Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Delete Session</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{sessionToDelete?.title}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsDeleteDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={handleDeleteConfirm}
              className="bg-semantic-error text-white hover:bg-semantic-error/90"
            >
              Delete Session
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default SessionSidebar;