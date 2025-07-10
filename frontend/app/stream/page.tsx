"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { 
  BrainCircuit, 
  Play, 
  Square, 
  Settings, 
  Zap, 
  CheckCircle2, 
  Clock, 
  AlertCircle,
  ChevronUp,
  ChevronDown,
  History,
  BarChart3,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SessionSidebar } from "@/components/sessions/SessionSidebar";
import { SessionTranscript } from "@/components/sessions/SessionTranscript";
import { SessionProvider, useSession } from "@/context/SessionContext";
import { ComparisonGrid } from "@/components/models/ComparisonGrid";
import { PreferenceFeedback } from "@/components/models/PreferenceFeedback";
import { ModelInstanceSelector } from "@/components/models/ModelInstanceSelector";
import { usePreferenceStore } from "@/hooks/usePreferenceStore";
import { useModelInstances } from "@/hooks/useModelInstances";
import { useAPIIntegration } from "@/hooks/useAPIIntegration";
import { AuthStatus } from "@/components/AuthStatus";

// Import streaming update type
import { StreamingUpdate } from '@/hooks/useAPIIntegration';

interface ModelResponse {
  id: string;
  name: string;
  provider: string;
  status: 'pending' | 'streaming' | 'completed' | 'error';
  content: string;
  responseTime?: number;
  tokenCount?: number;
  selected?: boolean;
}

function StreamPageContent() {
  // Session state
  const { state, actions } = useSession();
  
  // Auth context
  const { user, apiKey, isAuthenticated, autoLoginDev } = useAuth();
  
  // State management hooks
  const modelInstances = useModelInstances();
  const preferenceStore = usePreferenceStore();
  const apiIntegration = useAPIIntegration();
  
  // Form state
  const [prompt, setPrompt] = useState("Analyze this repository and suggest improvements.");
  const [isComparing, setIsComparing] = useState(false);
  const [isConfigExpanded, setIsConfigExpanded] = useState(true);
  const [formError, setFormError] = useState<string | null>(null);
  const [showTranscript, setShowTranscript] = useState(false);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  
  // Model responses state
  const [modelResponses, setModelResponses] = useState<ModelResponse[]>([]);
  const [selectedResponse, setSelectedResponse] = useState<string | null>(null);
  
  // Preference feedback state
  const [showPreferenceFeedback, setShowPreferenceFeedback] = useState(false);
  const [feedbackModelId, setFeedbackModelId] = useState<string>('');
  
  // Auto-login for development
  useEffect(() => {
    if (!isAuthenticated) {
      autoLoginDev();
    }
  }, [isAuthenticated, autoLoginDev]);
  
  const handleStartComparison = async () => {
    if (!prompt.trim()) {
      setFormError("Please enter a prompt");
      return;
    }
    
    if (modelInstances.selectedInstances.length === 0) {
      setFormError("Please select at least one model");
      return;
    }
    
    if (!apiKey) {
      setFormError("Please wait for authentication...");
      return;
    }
    
    setFormError(null);
    setIsComparing(true);
    setIsConfigExpanded(false);
    
    // Initialize model responses
    const initialResponses: ModelResponse[] = modelInstances.selectedInstances.map(instance => ({
      id: instance.instanceId,
      name: `${instance.modelInfo.name} #${instance.instanceNumber}`,
      provider: instance.modelInfo.provider,
      status: 'pending',
      content: '',
    }));
    
    setModelResponses(initialResponses);
    
    try {
      // Check if we have an API key
      const apiKey = localStorage.getItem('api_key');
      if (!apiKey) {
        setFormError('Please login to use the comparison feature');
        setIsComparing(false);
        return;
      }

      // Use instance IDs for frontend state management, but send base model IDs to backend
      const modelIds = modelInstances.selectedInstances.map(i => i.modelId); // Base IDs for backend
      
      // Generate unique instance IDs that will match the UI components
      const timestamp = Date.now();
      const instanceIds = modelInstances.selectedInstances.map((instance, index) => 
        `${instance.modelId}-${timestamp + index}-${index + 1}`
      );
      
      console.log('🔥 STREAM PAGE: Generated instance IDs:', instanceIds);
      console.log('🔥 STREAM PAGE: Model IDs for backend:', modelIds);
      
      // Update modelResponses to use the same instance IDs
      setModelResponses(prev => prev.map((response, index) => ({
        ...response,
        id: instanceIds[index]
      })));
      
      // Start actual model comparison via API
      if (state.activeSession) {
        const runId = await apiIntegration.startModelComparison({
          sessionId: state.activeSession.id,
          prompt: prompt,
          modelIds: modelIds,
          instanceIds: instanceIds,
        }, handleStreamingUpdate);
        
        setCurrentRunId(runId);
      } else {
        // Create a temporary session if none exists
        const tempSessionId = `temp-${Date.now()}`;
        actions.createSession(tempSessionId);
        
        const runId = await apiIntegration.startModelComparison({
          sessionId: tempSessionId,
          prompt: prompt,
          modelIds: modelIds,
          instanceIds: instanceIds,
        }, handleStreamingUpdate);
        
        setCurrentRunId(runId);
      }
    } catch (error) {
      console.error('Failed to start comparison:', error);
      setFormError(error instanceof Error ? error.message : 'Failed to start comparison');
      setIsComparing(false);
      
      // Reset model responses on error
      setModelResponses([]);
    }
  };
  
  const simulateModelStreaming = (responses: ModelResponse[]) => {
    responses.forEach((response, index) => {
      setTimeout(() => {
        setModelResponses(prev => prev.map(r => 
          r.id === response.id 
            ? { ...r, status: 'streaming' }
            : r
        ));
        
        // Simulate streaming text
        const sampleText = `This is a streaming response from ${response.name}. The analysis shows several key insights about the codebase structure and potential improvements...`;
        let currentText = '';
        
        const streamInterval = setInterval(() => {
          if (currentText.length >= sampleText.length) {
            clearInterval(streamInterval);
            setModelResponses(prev => prev.map(r => 
              r.id === response.id 
                ? { ...r, status: 'completed', responseTime: Math.random() * 5 + 2, tokenCount: Math.floor(Math.random() * 500 + 200) }
                : r
            ));
            return;
          }
          
          currentText += sampleText[currentText.length];
          setModelResponses(prev => prev.map(r => 
            r.id === response.id 
              ? { ...r, content: currentText }
              : r
          ));
        }, 50);
      }, index * 500);
    });
  };
  
  const handleStopComparison = () => {
    if (currentRunId) {
      apiIntegration.stopComparison(currentRunId);
      setCurrentRunId(null);
    }
    setIsComparing(false);
    setModelResponses([]);
    setSelectedResponse(null);
  };
  
  const handleSelectResponse = async (modelId: string) => {
    setSelectedResponse(modelId);
    setModelResponses(prev => prev.map(r => ({
      ...r,
      selected: r.id === modelId
    })));

    // Record preference if we have an active session and current run
    if (state.activeSession && currentRunId) {
      try {
        const selectedInstance = modelInstances.selectedInstances.find(i => i.instanceId === modelId);
        const selectedModel = selectedInstance?.modelInfo;
        const turnId = `turn-${Date.now()}`;
        
        await preferenceStore.recordPreference({
          sessionId: state.activeSession.id,
          turnId,
          selectedModelId: modelId,
          selectedModelName: selectedModel?.name || modelId,
          prompt: prompt,
          modelResponses: modelResponses.map(r => ({
            modelId: r.id,
            modelName: r.name,
            response: r.content,
            responseTime: r.responseTime,
            tokenCount: r.tokenCount,
          })),
        });
        
        // Add turn to session
        actions.addSessionTurn({
          id: turnId,
          sessionId: state.activeSession.id,
          prompt: prompt,
          modelResponses: modelResponses.map(r => ({
            modelId: r.id,
            modelName: r.name,
            response: r.content,
            responseTime: r.responseTime,
            tokenCount: r.tokenCount,
            isSelected: r.id === modelId,
          })),
          preferredModelId: modelId,
          createdAt: new Date().toISOString(),
        });
      } catch (error) {
        console.error('Failed to record preference:', error);
      }
    }
  };
  
  const getAgentColor = (index: number) => {
    const colors = ['agent-1', 'agent-2', 'agent-3', 'agent-4', 'agent-5'];
    return colors[index % colors.length];
  };

  // Show error messages from hooks
  const errorMessages = [
    modelInstances.error,
    preferenceStore.error,
    apiIntegration.lastError,
  ].filter(Boolean);

  const displayError = formError || errorMessages[0];

  const currentSessionTurns = state.activeSessionId 
    ? state.sessionTurns[state.activeSessionId] || []
    : [];

  const handlePreferenceFeedback = (modelId: string) => {
    setFeedbackModelId(modelId);
    setShowPreferenceFeedback(true);
  };

  const handleSubmitFeedback = async (feedback: any) => {
    if (selectedResponse) {
      const preference = preferenceStore.preferences.find(p => p.selectedModelId === selectedResponse);
      if (preference) {
        try {
          await preferenceStore.addFeedback(preference.id, feedback);
        } catch (error) {
          console.error('Failed to submit feedback:', error);
        }
      }
    }
    setShowPreferenceFeedback(false);
  };

  const handleStreamingUpdate = (update: StreamingUpdate) => {
    console.log('🎯 FRONTEND: handleStreamingUpdate called:', update);
    setModelResponses(prev => {
      console.log('🎯 FRONTEND: Current modelResponses IDs:', prev.map(r => ({ id: r.id, name: r.name })));
      console.log('🎯 FRONTEND: Looking for modelId:', update.modelId);
      
      return prev.map(response => {
        // The update modelId is actually the instance ID
        if (response.id === update.modelId) {
          console.log('🎯 FRONTEND: MATCH FOUND! Updating response:', response.id);
          switch (update.type) {
          case 'start':
            return { ...response, status: 'streaming' };
          case 'chunk':
            return { 
              ...response, 
              content: response.content + (update.content || ''),
              status: 'streaming',
            };
          case 'complete':
            return { 
              ...response, 
              status: 'completed',
              responseTime: update.metadata?.responseTime,
              tokenCount: update.metadata?.tokenCount,
            };
          case 'error':
            return { 
              ...response, 
              status: 'error',
              content: update.error || 'An error occurred',
            };
          }
        }
        return response;
      });
    });
  };

  return (
    <div className="min-h-screen bg-gradient-neural-twilight flex">
      {/* Auth Status - Fixed in corner */}
      <div className="fixed top-4 right-4 z-50">
        <AuthStatus />
      </div>
      
      {/* Session Sidebar */}
      <div className="p-4 pl-6 h-screen">
        <SessionSidebar
        sessions={state.sessions}
        activeSessionId={state.activeSessionId || undefined}
        onSessionSelect={actions.setActiveSession}
        onSessionCreate={actions.createSession}
        onSessionUpdate={actions.updateSession}
        onSessionDelete={actions.deleteSession}
        isLoading={state.isLoading}
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <div className="container mx-auto px-lg pt-16 pb-xl max-w-6xl flex-1">
        {/* Header - Compact when comparing */}
        <motion.header
          layout
          className={`text-center ${isComparing && !isConfigExpanded ? "mb-6" : "mb-12"}`}
        >
          <motion.div
            layout
            className={`inline-flex items-center justify-center rounded-2xl bg-gradient-to-br from-ai-primary to-ai-secondary text-white shadow-xl ${
              isComparing && !isConfigExpanded
                ? "w-12 h-12 mb-3"
                : "w-20 h-20 mb-6"
            }`}
          >
            <BrainCircuit
              className={`${
                isComparing && !isConfigExpanded ? "h-6 w-6" : "h-10 w-10"
              }`}
            />
          </motion.div>
          <motion.h1
            layout
            className={`font-bold text-neutral-white ${
              isComparing && !isConfigExpanded
                ? "text-h1 mb-2"
                : "text-display mb-3"
            }`}
          >
            aideator
          </motion.h1>
          <AnimatePresence>
            {(!isComparing || isConfigExpanded) && (
              <motion.p
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="text-body-lg text-neutral-white/80"
              >
                Multi-Model Prompt Comparison Platform
              </motion.p>
            )}
          </AnimatePresence>
        </motion.header>

        {/* Configuration Panel - Collapsible */}
        <div className="bg-neutral-paper rounded-2xl shadow-xl mb-8 transition-all duration-300">
          {/* Header - Always visible */}
          <div
            className="p-lg flex items-center justify-between cursor-pointer hover:bg-neutral-fog transition-colors"
            onClick={() => setIsConfigExpanded(!isConfigExpanded)}
          >
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-ai-primary to-ai-secondary text-white">
                <Settings className="h-6 w-6" />
              </div>
              <div>
                <h2 className="text-h2 font-bold text-neutral-charcoal">
                  Model Comparison Configuration
                </h2>
                {!isConfigExpanded && (
                  <p className="text-neutral-shadow text-body-sm mt-1 line-clamp-1">
                    {modelInstances.selectedInstances.length} instances · {prompt.substring(0, 50)}...
                  </p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                onClick={() => window.location.href = '/analytics'}
                variant="ghost"
                size="sm"
                className="text-neutral-shadow hover:text-ai-primary"
                title="View Analytics"
              >
                <BarChart3 className="w-4 h-4" />
              </Button>
              
              {currentSessionTurns.length > 0 && (
                <Button
                  onClick={() => setShowTranscript(!showTranscript)}
                  variant="ghost"
                  size="sm"
                  className={`${showTranscript ? 'text-ai-primary' : 'text-neutral-shadow'} hover:text-ai-primary`}
                >
                  <History className="w-4 h-4" />
                </Button>
              )}
              
              {!isConfigExpanded && !isComparing && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleStartComparison();
                  }}
                  disabled={!prompt.trim() || modelInstances.selectedInstances.length === 0 || !apiKey}
                  className="px-md py-sm bg-gradient-to-r from-ai-primary to-ai-secondary text-white rounded-lg font-semibold hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Play className="inline w-4 h-4 mr-2" />
                  Start
                </button>
              )}
              {isConfigExpanded ? (
                <ChevronUp className="h-5 w-5 text-neutral-shadow" />
              ) : (
                <ChevronDown className="h-5 w-5 text-neutral-shadow" />
              )}
            </div>
          </div>

          {/* Collapsible Content */}
          <AnimatePresence>
            {isConfigExpanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3, ease: "easeInOut" }}
                style={{ overflow: 'visible' }}
              >
                <div className="p-lg pt-0 space-y-6 relative">
                  {/* Prompt Input */}
                  <div>
                    <label
                      htmlFor="prompt"
                      className="block text-label font-medium text-neutral-charcoal mb-2"
                    >
                      <div className="flex items-center gap-2">
                        <Zap className="h-4 w-4" />
                        Prompt
                      </div>
                    </label>
                    <Textarea
                      id="prompt"
                      placeholder="Enter your prompt to compare across multiple models..."
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      disabled={isComparing}
                      rows={4}
                      className="w-full bg-neutral-white border border-neutral-fog rounded-md px-md py-md text-body placeholder:text-neutral-shadow focus:border-ai-primary focus:ring-2 focus:ring-ai-primary/20 transition-colors resize-none"
                    />
                    <div className="mt-2 flex items-center justify-between">
                      <span className="text-caption text-neutral-shadow">
                        {prompt.length} characters
                      </span>
                      <span className="text-caption text-neutral-shadow">
                        {modelInstances.selectedInstances.length} instances selected
                      </span>
                    </div>
                  </div>

                  {/* Authentication Status */}
                  {!isAuthenticated && (
                    <div className="bg-neutral-fog border border-neutral-fog rounded-md p-md">
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-ai-primary rounded-full animate-pulse"></div>
                        <span className="text-body-sm text-neutral-shadow">
                          Connecting to authentication...
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Model Selection */}
                  <div>
                    <label className="block text-label font-medium text-neutral-charcoal mb-3">
                      Select Models to Compare
                    </label>
                    <ModelInstanceSelector
                      availableModels={modelInstances.availableModels}
                      selectedInstances={modelInstances.selectedInstances}
                      onAddInstance={modelInstances.addInstance}
                      onRemoveInstance={modelInstances.removeInstance}
                      maxInstances={modelInstances.maxInstances}
                      isLoading={modelInstances.isLoading}
                      placeholder="Click to add models (can add same model multiple times)..."
                    />
                  </div>

                  {/* Error Display */}
                  {displayError && (
                    <div className="p-md bg-semantic-error/10 border border-semantic-error/20 rounded-lg">
                      <div className="flex items-center gap-2 text-semantic-error">
                        <AlertCircle className="h-5 w-5" />
                        <span className="font-medium">{displayError}</span>
                      </div>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex items-center gap-4 mt-6">
                    {!isComparing ? (
                      <Button
                        onClick={handleStartComparison}
                        disabled={!prompt.trim() || modelInstances.selectedInstances.length === 0 || !apiKey}
                        className="bg-gradient-to-r from-ai-primary to-ai-secondary text-white px-lg py-md rounded-lg font-semibold hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Play className="inline w-5 h-5 mr-2" />
                        Start Comparison
                      </Button>
                    ) : (
                      <Button
                        onClick={handleStopComparison}
                        className="bg-semantic-error text-white px-lg py-md rounded-lg font-semibold hover:opacity-90 transition-all"
                      >
                        <Square className="inline w-5 h-5 mr-2" />
                        Stop Comparison
                      </Button>
                    )}

                    {modelResponses.length > 0 && (
                      <Button
                        onClick={() => setModelResponses([])}
                        disabled={isComparing}
                        variant="outline"
                        className="border-2 border-neutral-fog text-neutral-charcoal px-lg py-md rounded-lg font-semibold hover:bg-neutral-fog transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Clear Results
                      </Button>
                    )}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Session Transcript Panel */}
        {showTranscript && state.activeSession && (
          <div className="mb-8">
            <SessionTranscript
              sessionId={state.activeSession.id}
              sessionTitle={state.activeSession.title}
              turns={currentSessionTurns}
              onTurnUpdate={(turnId, updates) => 
                actions.updateSessionTurn(state.activeSession!.id, turnId, updates)
              }
              onExport={(format) => {
                // TODO: Implement export functionality
                console.log('Export session as:', format);
              }}
            />
          </div>
        )}

        {/* Model Comparison Grid */}
        {modelResponses.length > 0 && (
          <ComparisonGrid
            responses={modelResponses}
            onSelectResponse={handleSelectResponse}
            onPreferenceFeedback={handlePreferenceFeedback}
          />
        )}

        {/* Preference Feedback Modal */}
        {showPreferenceFeedback && selectedResponse && (
          <PreferenceFeedback
            isOpen={showPreferenceFeedback}
            onClose={() => setShowPreferenceFeedback(false)}
            selectedModelId={selectedResponse}
            selectedModelName={modelResponses.find(r => r.id === selectedResponse)?.name || ''}
            allModels={modelResponses.map(r => ({
              id: r.id,
              name: r.name,
              response: r.content,
            }))}
            onSubmitFeedback={handleSubmitFeedback}
          />
        )}

        {/* Floating Stop Button - shows when comparing and config is collapsed */}
        <AnimatePresence>
          {isComparing && !isConfigExpanded && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.8, y: 20 }}
              transition={{ type: "spring", stiffness: 400, damping: 30 }}
              className="fixed bottom-8 right-8 z-50"
            >
              <button
                onClick={handleStopComparison}
                className="px-lg py-md bg-semantic-error text-white rounded-full font-semibold hover:opacity-90 transition-all shadow-lg hover:shadow-xl flex items-center gap-2"
              >
                <Square className="w-5 h-5" />
                Stop Comparison
              </button>
            </motion.div>
          )}
        </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

// Main export with SessionProvider wrapper
export default function StreamPage() {
  return (
    <SessionProvider>
      <StreamPageContent />
    </SessionProvider>
  );
}