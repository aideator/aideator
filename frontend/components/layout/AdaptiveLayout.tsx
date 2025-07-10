"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronLeft, 
  ChevronRight, 
  Plus, 
  Search, 
  MessageSquare, 
  BrainCircuit,
  Settings,
  Grid3X3,
  History
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

interface AdaptiveLayoutProps {
  children: React.ReactNode;
  sessions: any[];
  activeSessionId?: string;
  onSessionSelect: (sessionId: string) => void;
  onSessionCreate: () => void;
  onSessionDelete: (sessionId: string) => void;
  currentMode: 'welcome' | 'chat' | 'compare';
  onModeChange: (mode: 'welcome' | 'chat' | 'compare') => void;
}

export function AdaptiveLayout({
  children,
  sessions,
  activeSessionId,
  onSessionSelect,
  onSessionCreate,
  onSessionDelete,
  currentMode,
  onModeChange
}: AdaptiveLayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredSessions, setFilteredSessions] = useState(sessions);

  // Filter sessions based on search
  useEffect(() => {
    if (searchTerm.trim()) {
      setFilteredSessions(
        sessions.filter(session => 
          session.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          session.description?.toLowerCase().includes(searchTerm.toLowerCase())
        )
      );
    } else {
      setFilteredSessions(sessions);
    }
  }, [sessions, searchTerm]);

  // Auto-collapse sidebar on mobile
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setSidebarCollapsed(true);
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const sidebarWidth = sidebarCollapsed ? 'w-16' : 'w-80';

  return (
    <div className="flex h-screen bg-neutral-white overflow-hidden">
      {/* Collapsible Sidebar */}
      <motion.div
        data-testid={sidebarCollapsed ? "sidebar-collapsed" : "sidebar"}
        animate={{ width: sidebarCollapsed ? 64 : 320 }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className={cn(
          "bg-neutral-paper border-r border-neutral-fog flex flex-col",
          "shadow-lg z-20 relative"
        )}
      >
        {/* Sidebar Header */}
        <div className="p-4 border-b border-neutral-fog">
          <div className="flex items-center justify-between">
            {!sidebarCollapsed && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center gap-2"
              >
                <BrainCircuit className="h-6 w-6 text-ai-primary" />
                <h1 className="text-h3 font-bold text-ai-primary">aideator</h1>
              </motion.div>
            )}
            
            <Button
              data-testid="sidebar-toggle"
              variant="ghost"
              size="sm"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-2 hover:bg-neutral-fog"
              aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {sidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
            </Button>
          </div>
        </div>

        {/* Sidebar Content */}
        <div className="flex-1 overflow-hidden">
          {sidebarCollapsed ? (
            /* Collapsed State - Icon Menu */
            <div className="p-2 space-y-2">
              <Button
                data-testid="new-session-btn-collapsed"
                variant="ghost"
                size="sm"
                onClick={onSessionCreate}
                className="w-full p-3 hover:bg-neutral-fog"
                title="New Session"
              >
                <Plus className="h-4 w-4" />
              </Button>
              
              <div className="border-t border-neutral-fog my-2" />
              
              {sessions.slice(0, 8).map((session) => (
                <Button
                  key={session.id}
                  data-testid="session-item-collapsed"
                  variant="ghost"
                  size="sm"
                  onClick={() => onSessionSelect(session.id)}
                  className={cn(
                    "w-full p-3 hover:bg-neutral-fog",
                    activeSessionId === session.id && "bg-ai-primary/10 text-ai-primary"
                  )}
                  title={session.title}
                >
                  <MessageSquare className="h-4 w-4" />
                </Button>
              ))}
            </div>
          ) : (
            /* Expanded State - Full Interface */
            <div className="h-full flex flex-col">
              {/* Search & New Session */}
              <div className="p-4 space-y-3">
                <Button
                  data-testid="new-session-btn"
                  onClick={onSessionCreate}
                  className="w-full bg-gradient-to-r from-ai-primary to-ai-secondary text-white hover:opacity-90"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  New Session
                </Button>
                
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-neutral-shadow" />
                  <Input
                    data-testid="session-search"
                    placeholder="Search sessions..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              {/* Session List */}
              <div data-testid="session-list" className="flex-1 overflow-y-auto px-2">
                <AnimatePresence>
                  {filteredSessions.length > 0 ? (
                    <div className="space-y-1">
                      {filteredSessions.map((session) => (
                        <motion.div
                          key={session.id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -10 }}
                          transition={{ duration: 0.2 }}
                        >
                          <Button
                            data-testid="session-item"
                            variant="ghost"
                            onClick={() => onSessionSelect(session.id)}
                            className={cn(
                              "w-full p-3 text-left hover:bg-neutral-fog rounded-lg",
                              "flex flex-col items-start gap-1",
                              activeSessionId === session.id && "bg-ai-primary/10 text-ai-primary"
                            )}
                          >
                            <div className="flex items-center gap-2 w-full">
                              <MessageSquare className="h-4 w-4 flex-shrink-0" />
                              <span className="text-body-sm font-medium truncate">
                                {session.title}
                              </span>
                            </div>
                            {session.description && (
                              <p className="text-xs text-neutral-shadow truncate w-full">
                                {session.description}
                              </p>
                            )}
                            <div className="flex items-center gap-2 text-xs text-neutral-shadow">
                              <span data-testid="session-turn-count">{session.turnCount || 0} turns</span>
                              <span>•</span>
                              <span data-testid="session-last-activity">{session.lastActivity || 'Never'}</span>
                            </div>
                          </Button>
                        </motion.div>
                      ))}
                    </div>
                  ) : (
                    <div data-testid="empty-sessions" className="text-center py-8 text-neutral-shadow">
                      <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p className="text-body-sm">No sessions found</p>
                    </div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          )}
        </div>

        {/* Mode Selector (Bottom) */}
        {!sidebarCollapsed && (
          <div className="p-4 border-t border-neutral-fog">
            <div className="flex items-center gap-1 bg-neutral-fog rounded-lg p-1">
              <Button
                data-testid="mode-welcome"
                variant={currentMode === 'welcome' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => onModeChange('welcome')}
                className="flex-1 text-xs"
              >
                <Plus className="h-3 w-3 mr-1" />
                New
              </Button>
              <Button
                data-testid="mode-chat"
                variant={currentMode === 'chat' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => onModeChange('chat')}
                className="flex-1 text-xs"
              >
                <History className="h-3 w-3 mr-1" />
                Chat
              </Button>
              <Button
                data-testid="mode-compare"
                variant={currentMode === 'compare' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => onModeChange('compare')}
                className="flex-1 text-xs"
              >
                <Grid3X3 className="h-3 w-3 mr-1" />
                Compare
              </Button>
            </div>
          </div>
        )}
      </motion.div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        {/* Top Bar */}
        <div className="bg-neutral-white border-b border-neutral-fog p-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Mode Indicator */}
            <div data-testid="mode-indicator" className="flex items-center gap-2">
              {currentMode === 'welcome' && <Plus className="h-5 w-5 text-ai-primary" />}
              {currentMode === 'chat' && <History className="h-5 w-5 text-ai-secondary" />}
              {currentMode === 'compare' && <Grid3X3 className="h-5 w-5 text-ai-accent" />}
              <span className="text-h3 font-semibold capitalize">{currentMode}</span>
            </div>
            
            {/* Session Title */}
            {activeSessionId && (
              <div data-testid="active-session-title" className="text-neutral-shadow">
                <span className="text-body-sm">
                  {sessions.find(s => s.id === activeSessionId)?.title || 'Untitled Session'}
                </span>
              </div>
            )}
          </div>

          {/* Top Bar Actions */}
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm">
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden bg-neutral-white min-w-0 w-full max-w-none">
          {children}
        </div>
      </div>
    </div>
  );
}