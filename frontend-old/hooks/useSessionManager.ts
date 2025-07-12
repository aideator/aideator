import { useState, useCallback, useEffect } from 'react';
import { 
  createSession, 
  getSessions, 
  getSessionDetails, 
  updateSession, 
  deleteSession,
  type Session,
  type SessionDetails,
  type CreateSessionRequest 
} from '@/lib/api-client';

export interface SessionManagerState {
  sessions: Session[];
  currentSession: SessionDetails | null;
  isLoading: boolean;
  error: string | null;
}

export interface SessionManagerHook extends SessionManagerState {
  loadSessions: () => Promise<void>;
  createNewSession: (title?: string) => Promise<Session>;
  switchToSession: (sessionId: string) => Promise<void>;
  updateSessionTitle: (sessionId: string, title: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  clearCurrentSession: () => void;
  refreshCurrentSession: () => Promise<void>;
}

// Local storage keys
const CURRENT_SESSION_KEY = 'aideator_current_session';
const SESSION_CACHE_KEY = 'aideator_session_cache';

export function useSessionManager(): SessionManagerHook {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<SessionDetails | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Load sessions from cache on mount
  useEffect(() => {
    const cachedSessions = localStorage.getItem(SESSION_CACHE_KEY);
    if (cachedSessions) {
      try {
        setSessions(JSON.parse(cachedSessions));
      } catch (e) {
        console.error('Failed to parse cached sessions:', e);
      }
    }
    
    // Try to restore current session
    const currentSessionId = localStorage.getItem(CURRENT_SESSION_KEY);
    if (currentSessionId) {
      switchToSession(currentSessionId).catch(console.error);
    }
    
    // Load fresh sessions
    loadSessions().catch(console.error);
  }, []);
  
  // Cache sessions to localStorage
  const cacheSessions = useCallback((sessionList: Session[]) => {
    localStorage.setItem(SESSION_CACHE_KEY, JSON.stringify(sessionList));
  }, []);
  
  // Cache current session ID
  const cacheCurrentSession = useCallback((sessionId: string | null) => {
    if (sessionId) {
      localStorage.setItem(CURRENT_SESSION_KEY, sessionId);
    } else {
      localStorage.removeItem(CURRENT_SESSION_KEY);
    }
  }, []);
  
  const loadSessions = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const sessionList = await getSessions();
      setSessions(sessionList);
      cacheSessions(sessionList);
      
    } catch (error) {
      console.error('Failed to load sessions:', error);
      setError(error instanceof Error ? error.message : 'Failed to load sessions');
    } finally {
      setIsLoading(false);
    }
  }, [cacheSessions]);
  
  const createNewSession = useCallback(async (title?: string): Promise<Session> => {
    try {
      setIsLoading(true);
      setError(null);
      
      const request: CreateSessionRequest = title ? { title } : {};
      const response = await createSession(request);
      
      const newSession: Session = {
        id: response.id,
        title: response.title,
        created_at: response.created_at,
        updated_at: response.created_at,
        total_turns: 0,
        last_activity_at: response.created_at,
        is_active: true,
        is_archived: false
      };
      
      // Add to sessions list
      setSessions(prev => [newSession, ...prev]);
      
      // Update cache
      const updatedSessions = [newSession, ...sessions];
      cacheSessions(updatedSessions);
      
      return newSession;
      
    } catch (error) {
      console.error('Failed to create session:', error);
      setError(error instanceof Error ? error.message : 'Failed to create session');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [sessions, cacheSessions]);
  
  const switchToSession = useCallback(async (sessionId: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const sessionDetails = await getSessionDetails(sessionId);
      setCurrentSession(sessionDetails);
      cacheCurrentSession(sessionId);
      
    } catch (error) {
      console.error('Failed to switch to session:', error);
      setError(error instanceof Error ? error.message : 'Failed to load session');
      
      // If session doesn't exist, clear it from cache
      if (error instanceof Error && error.message.includes('404')) {
        cacheCurrentSession(null);
        setCurrentSession(null);
        
        // Remove from sessions list
        setSessions(prev => prev.filter(s => s.id !== sessionId));
      }
    } finally {
      setIsLoading(false);
    }
  }, [cacheCurrentSession]);
  
  const updateSessionTitle = useCallback(async (sessionId: string, title: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      await updateSession(sessionId, { title });
      
      // Update in sessions list
      setSessions(prev => prev.map(session => 
        session.id === sessionId
          ? { ...session, title, updated_at: new Date().toISOString() }
          : session
      ));
      
      // Update current session if it's the one being updated
      if (currentSession && currentSession.id === sessionId) {
        setCurrentSession(prev => prev ? { ...prev, title } : null);
      }
      
      // Update cache
      const updatedSessions = sessions.map(session => 
        session.id === sessionId
          ? { ...session, title, updated_at: new Date().toISOString() }
          : session
      );
      cacheSessions(updatedSessions);
      
    } catch (error) {
      console.error('Failed to update session title:', error);
      setError(error instanceof Error ? error.message : 'Failed to update session');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [sessions, currentSession, cacheSessions]);
  
  const deleteSessionById = useCallback(async (sessionId: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      await deleteSession(sessionId);
      
      // Remove from sessions list
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      
      // Clear current session if it's the one being deleted
      if (currentSession && currentSession.id === sessionId) {
        setCurrentSession(null);
        cacheCurrentSession(null);
      }
      
      // Update cache
      const updatedSessions = sessions.filter(s => s.id !== sessionId);
      cacheSessions(updatedSessions);
      
    } catch (error) {
      console.error('Failed to delete session:', error);
      setError(error instanceof Error ? error.message : 'Failed to delete session');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [sessions, currentSession, cacheSessions, cacheCurrentSession]);
  
  const clearCurrentSession = useCallback(() => {
    setCurrentSession(null);
    cacheCurrentSession(null);
  }, [cacheCurrentSession]);
  
  const refreshCurrentSession = useCallback(async () => {
    if (currentSession) {
      await switchToSession(currentSession.id);
    }
  }, [currentSession, switchToSession]);
  
  return {
    sessions,
    currentSession,
    isLoading,
    error,
    loadSessions,
    createNewSession,
    switchToSession,
    updateSessionTitle,
    deleteSession: deleteSessionById,
    clearCurrentSession,
    refreshCurrentSession,
  };
}