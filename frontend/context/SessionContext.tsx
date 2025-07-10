'use client';

import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { Session } from '@/components/sessions/SessionSidebar';
import * as api from '@/lib/api-client';

// Session Turn interface for conversation history
export interface SessionTurn {
  id: string;
  sessionId: string;
  prompt: string;
  modelResponses: {
    modelId: string;
    modelName: string;
    response: string;
    responseTime?: number;
    tokenCount?: number;
    selected?: boolean;
  }[];
  createdAt: string;
  userFeedback?: string;
  preferredModelId?: string;
}

// Session state interface
interface SessionState {
  sessions: Session[];
  activeSessionId: string | null;
  activeSession: Session | null;
  sessionTurns: Record<string, SessionTurn[]>;
  isLoading: boolean;
  error: string | null;
  lastActiveSessionId: string | null;
}

// Session actions
type SessionAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_SESSIONS'; payload: Session[] }
  | { type: 'SET_ACTIVE_SESSION'; payload: string | null }
  | { type: 'ADD_SESSION'; payload: Session }
  | { type: 'UPDATE_SESSION'; payload: { id: string; updates: Partial<Session> } }
  | { type: 'DELETE_SESSION'; payload: string }
  | { type: 'SET_SESSION_TURNS'; payload: { sessionId: string; turns: SessionTurn[] } }
  | { type: 'ADD_SESSION_TURN'; payload: SessionTurn }
  | { type: 'UPDATE_SESSION_TURN'; payload: { sessionId: string; turnId: string; updates: Partial<SessionTurn> } }
  | { type: 'LOAD_FROM_STORAGE'; payload: { sessions: Session[]; lastActiveSessionId: string | null } };

const initialState: SessionState = {
  sessions: [],
  activeSessionId: null,
  activeSession: null,
  sessionTurns: {},
  isLoading: false,
  error: null,
  lastActiveSessionId: null,
};

function sessionReducer(state: SessionState, action: SessionAction): SessionState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    
    case 'SET_SESSIONS':
      return { ...state, sessions: action.payload };
    
    case 'SET_ACTIVE_SESSION':
      const activeSession = action.payload 
        ? state.sessions.find(s => s.id === action.payload) || null
        : null;
      return { 
        ...state, 
        activeSessionId: action.payload,
        activeSession,
        lastActiveSessionId: action.payload,
      };
    
    case 'ADD_SESSION':
      return { 
        ...state, 
        sessions: [action.payload, ...state.sessions],
      };
    
    case 'UPDATE_SESSION':
      const updatedSessions = state.sessions.map(session =>
        session.id === action.payload.id 
          ? { ...session, ...action.payload.updates }
          : session
      );
      const updatedActiveSession = state.activeSessionId === action.payload.id
        ? updatedSessions.find(s => s.id === action.payload.id) || null
        : state.activeSession;
      
      return { 
        ...state, 
        sessions: updatedSessions,
        activeSession: updatedActiveSession,
      };
    
    case 'DELETE_SESSION':
      const remainingSessions = state.sessions.filter(s => s.id !== action.payload);
      const newActiveSessionId = state.activeSessionId === action.payload 
        ? (remainingSessions.length > 0 ? remainingSessions[0].id : null)
        : state.activeSessionId;
      const newActiveSession = newActiveSessionId 
        ? remainingSessions.find(s => s.id === newActiveSessionId) || null
        : null;
      
      // Remove session turns
      const { [action.payload]: removed, ...remainingTurns } = state.sessionTurns;
      
      return { 
        ...state, 
        sessions: remainingSessions,
        activeSessionId: newActiveSessionId,
        activeSession: newActiveSession,
        sessionTurns: remainingTurns,
      };
    
    case 'SET_SESSION_TURNS':
      return {
        ...state,
        sessionTurns: {
          ...state.sessionTurns,
          [action.payload.sessionId]: action.payload.turns,
        },
      };
    
    case 'ADD_SESSION_TURN':
      const existingTurns = state.sessionTurns[action.payload.sessionId] || [];
      return {
        ...state,
        sessionTurns: {
          ...state.sessionTurns,
          [action.payload.sessionId]: [...existingTurns, action.payload],
        },
      };
    
    case 'UPDATE_SESSION_TURN':
      const sessionTurns = state.sessionTurns[action.payload.sessionId] || [];
      const updatedTurns = sessionTurns.map(turn =>
        turn.id === action.payload.turnId 
          ? { ...turn, ...action.payload.updates }
          : turn
      );
      return {
        ...state,
        sessionTurns: {
          ...state.sessionTurns,
          [action.payload.sessionId]: updatedTurns,
        },
      };
    
    case 'LOAD_FROM_STORAGE':
      return {
        ...state,
        sessions: action.payload.sessions,
        lastActiveSessionId: action.payload.lastActiveSessionId,
      };
    
    default:
      return state;
  }
}

// Session context
interface SessionContextType {
  state: SessionState;
  actions: {
    loadSessions: () => Promise<void>;
    createSession: (title: string) => Promise<void>;
    updateSession: (id: string, updates: Partial<Session>) => Promise<void>;
    deleteSession: (id: string) => Promise<void>;
    setActiveSession: (id: string | null) => void;
    loadSessionTurns: (sessionId: string) => Promise<void>;
    addSessionTurn: (turn: SessionTurn) => void;
    updateSessionTurn: (sessionId: string, turnId: string, updates: Partial<SessionTurn>) => void;
    saveToStorage: () => void;
    loadFromStorage: () => void;
    clearAllSessions: () => void;
  };
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

// Storage keys
const STORAGE_KEYS = {
  SESSIONS: 'aideator_sessions',
  ACTIVE_SESSION: 'aideator_active_session',
  SESSION_TURNS: 'aideator_session_turns',
};

// Real API functions using backend
const sessionAPI = {
  getSessions: async (): Promise<Session[]> => {
    try {
      const backendSessions = await api.getSessions();
      // Transform backend session format to frontend format
      return backendSessions.map(session => ({
        id: session.id,
        title: session.title,
        description: session.description,
        createdAt: session.created_at,
        updatedAt: session.updated_at,
        turnCount: session.total_turns,
        lastActivityAt: session.last_activity_at,
        isActive: session.is_active,
        isArchived: session.is_archived,
      }));
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
      throw error;
    }
  },
  
  createSession: async (title: string): Promise<Session> => {
    try {
      const response = await api.createSession({ title });
      return {
        id: response.id,
        title: response.title,
        description: response.description,
        createdAt: response.created_at,
        updatedAt: response.created_at,
        turnCount: 0,
        lastActivityAt: response.created_at,
        isActive: true,
        isArchived: false,
      };
    } catch (error) {
      console.error('Failed to create session:', error);
      throw error;
    }
  },
  
  updateSession: async (id: string, updates: Partial<Session>): Promise<Session> => {
    try {
      await api.updateSession(id, { title: updates.title || '' });
      // Return the updated session (API doesn't return it, so we construct it)
      return { 
        id, 
        ...updates,
        updatedAt: new Date().toISOString(),
      } as Session;
    } catch (error) {
      console.error('Failed to update session:', error);
      throw error;
    }
  },
  
  deleteSession: async (id: string): Promise<void> => {
    try {
      await api.deleteSession(id);
    } catch (error) {
      console.error('Failed to delete session:', error);
      throw error;
    }
  },
  
  getSessionTurns: async (sessionId: string): Promise<SessionTurn[]> => {
    try {
      // For now, return empty array as the backend doesn't have a direct turns endpoint
      // This would need to be implemented based on the actual backend API
      return [];
    } catch (error) {
      console.error('Failed to fetch session turns:', error);
      throw error;
    }
  },
};

// Session provider component
export function SessionProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(sessionReducer, initialState);

  // Load from localStorage on mount
  useEffect(() => {
    loadFromStorage();
    // Also load fresh sessions from backend to validate localStorage data
    // We need to ensure loadSessions is defined before calling it
    const loadSessionsOnMount = async () => {
      try {
        const sessions = await sessionAPI.getSessions();
        dispatch({ type: 'SET_SESSIONS', payload: sessions });
        
        // Validate active session from localStorage
        const savedActiveSessionId = localStorage.getItem(STORAGE_KEYS.ACTIVE_SESSION);
        if (savedActiveSessionId) {
          const activeSessionExists = sessions.some(s => s.id === savedActiveSessionId);
          if (!activeSessionExists) {
            console.warn('Active session from localStorage not found in backend, clearing...');
            dispatch({ type: 'SET_ACTIVE_SESSION', payload: null });
            localStorage.removeItem(STORAGE_KEYS.ACTIVE_SESSION);
          }
        }
      } catch (error) {
        console.error('Failed to load sessions on mount:', error);
        // Clear invalid localStorage data on error
        localStorage.removeItem(STORAGE_KEYS.SESSIONS);
        localStorage.removeItem(STORAGE_KEYS.ACTIVE_SESSION);
        localStorage.removeItem(STORAGE_KEYS.SESSION_TURNS);
      }
    };
    
    loadSessionsOnMount();
  }, []);

  // Save to localStorage whenever sessions or active session changes
  useEffect(() => {
    saveToStorage();
  }, [state.sessions, state.activeSessionId]);

  // Auto-restore last active session
  useEffect(() => {
    if (state.sessions.length > 0 && !state.activeSessionId && state.lastActiveSessionId) {
      const lastSession = state.sessions.find(s => s.id === state.lastActiveSessionId);
      if (lastSession) {
        dispatch({ type: 'SET_ACTIVE_SESSION', payload: lastSession.id });
      }
    }
  }, [state.sessions, state.activeSessionId, state.lastActiveSessionId]);

  const loadSessions = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'SET_ERROR', payload: null });
      
      const sessions = await sessionAPI.getSessions();
      dispatch({ type: 'SET_SESSIONS', payload: sessions });
      
      // Validate active session - if it doesn't exist in the backend, clear it
      if (state.activeSessionId) {
        const activeSessionExists = sessions.some(s => s.id === state.activeSessionId);
        if (!activeSessionExists) {
          console.warn('Active session from localStorage not found in backend, clearing...');
          dispatch({ type: 'SET_ACTIVE_SESSION', payload: null });
        }
      }
      
    } catch (error) {
      console.error('Failed to load sessions:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load sessions' });
      // Clear localStorage if we can't load sessions (likely auth issue)
      if (typeof window !== 'undefined') {
        localStorage.removeItem(STORAGE_KEYS.SESSIONS);
        localStorage.removeItem(STORAGE_KEYS.ACTIVE_SESSION);
        localStorage.removeItem(STORAGE_KEYS.SESSION_TURNS);
      }
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const createSession = async (title: string) => {
    try {
      dispatch({ type: 'SET_ERROR', payload: null });
      
      const newSession = await sessionAPI.createSession(title);
      dispatch({ type: 'ADD_SESSION', payload: newSession });
      dispatch({ type: 'SET_ACTIVE_SESSION', payload: newSession.id });
      
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to create session' });
    }
  };

  const updateSession = async (id: string, updates: Partial<Session>) => {
    try {
      dispatch({ type: 'SET_ERROR', payload: null });
      
      await sessionAPI.updateSession(id, updates);
      dispatch({ type: 'UPDATE_SESSION', payload: { id, updates } });
      
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to update session' });
    }
  };

  const deleteSession = async (id: string) => {
    try {
      dispatch({ type: 'SET_ERROR', payload: null });
      
      await sessionAPI.deleteSession(id);
      dispatch({ type: 'DELETE_SESSION', payload: id });
      
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to delete session' });
    }
  };

  const setActiveSession = (id: string | null) => {
    dispatch({ type: 'SET_ACTIVE_SESSION', payload: id });
  };

  const loadSessionTurns = async (sessionId: string) => {
    try {
      dispatch({ type: 'SET_ERROR', payload: null });
      
      const turns = await sessionAPI.getSessionTurns(sessionId);
      dispatch({ type: 'SET_SESSION_TURNS', payload: { sessionId, turns } });
      
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load session turns' });
    }
  };

  const addSessionTurn = (turn: SessionTurn) => {
    dispatch({ type: 'ADD_SESSION_TURN', payload: turn });
    
    // Update session turn count
    const session = state.sessions.find(s => s.id === turn.sessionId);
    if (session) {
      const currentTurns = state.sessionTurns[turn.sessionId] || [];
      updateSession(turn.sessionId, { 
        turnCount: currentTurns.length + 1,
        updatedAt: new Date().toISOString(),
        lastPrompt: turn.prompt,
      });
    }
  };

  const updateSessionTurn = (sessionId: string, turnId: string, updates: Partial<SessionTurn>) => {
    dispatch({ type: 'UPDATE_SESSION_TURN', payload: { sessionId, turnId, updates } });
  };

  const saveToStorage = () => {
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem(STORAGE_KEYS.SESSIONS, JSON.stringify(state.sessions));
        localStorage.setItem(STORAGE_KEYS.ACTIVE_SESSION, state.activeSessionId || '');
        localStorage.setItem(STORAGE_KEYS.SESSION_TURNS, JSON.stringify(state.sessionTurns));
      } catch (error) {
        console.error('Failed to save to localStorage:', error);
      }
    }
  };

  const loadFromStorage = () => {
    if (typeof window !== 'undefined') {
      try {
        const savedSessions = localStorage.getItem(STORAGE_KEYS.SESSIONS);
        const savedActiveSessionId = localStorage.getItem(STORAGE_KEYS.ACTIVE_SESSION);
        const savedSessionTurns = localStorage.getItem(STORAGE_KEYS.SESSION_TURNS);
        
        if (savedSessions) {
          const sessions = JSON.parse(savedSessions);
          const lastActiveSessionId = savedActiveSessionId || null;
          
          dispatch({ type: 'LOAD_FROM_STORAGE', payload: { sessions, lastActiveSessionId } });
        }
        
        if (savedSessionTurns) {
          const sessionTurns = JSON.parse(savedSessionTurns);
          Object.entries(sessionTurns).forEach(([sessionId, turns]) => {
            dispatch({ type: 'SET_SESSION_TURNS', payload: { sessionId, turns: turns as SessionTurn[] } });
          });
        }
      } catch (error) {
        console.error('Failed to load from localStorage:', error);
      }
    }
  };

  const clearAllSessions = () => {
    // Clear all session data from state and localStorage
    dispatch({ type: 'SET_SESSIONS', payload: [] });
    dispatch({ type: 'SET_ACTIVE_SESSION', payload: null });
    
    if (typeof window !== 'undefined') {
      localStorage.removeItem(STORAGE_KEYS.SESSIONS);
      localStorage.removeItem(STORAGE_KEYS.ACTIVE_SESSION);
      localStorage.removeItem(STORAGE_KEYS.SESSION_TURNS);
    }
  };

  const contextValue: SessionContextType = {
    state,
    actions: {
      loadSessions,
      createSession,
      updateSession,
      deleteSession,
      setActiveSession,
      loadSessionTurns,
      addSessionTurn,
      updateSessionTurn,
      saveToStorage,
      loadFromStorage,
      clearAllSessions,
    },
  };

  return (
    <SessionContext.Provider value={contextValue}>
      {children}
    </SessionContext.Provider>
  );
}

// Hook to use session context
export function useSession() {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
}

export default SessionContext;