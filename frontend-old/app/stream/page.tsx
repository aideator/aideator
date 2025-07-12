"use client";

import React, { useEffect, useState } from "react";

// Auth / global contexts & hooks
import { useAuth } from "@/contexts/AuthContext";
import { useAgentPolling as useAgentStream } from "@/hooks/useAgentPolling";
import { useAgentMode, AgentModeProvider } from "@/contexts/AgentModeContext";
import { SessionProvider, useSession } from "@/context/SessionContext";

// Domain hooks
import { useModelInstances } from "@/hooks/useModelInstances";
import { usePreferenceStore } from "@/hooks/usePreferenceStore";
import { useAPIIntegration } from "@/hooks/useAPIIntegration";

// Layout & UI components
import { AdaptiveLayout } from "@/components/layout/AdaptiveLayout";
import { ComparisonGrid } from "@/components/models/ComparisonGrid";
import { PreferenceFeedback } from "@/components/models/PreferenceFeedback";
import { SessionTranscript } from "@/components/sessions/SessionTranscript";
import { ModelInstanceSelector } from "@/components/models/ModelInstanceSelector";
import { ModeSelector } from "@/components/ModeSelector";
import { RepositoryPicker } from "@/components/RepositoryPicker";
import { AuthStatus } from "@/components/AuthStatus";

// Primitive UI components
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

// Icons
import {
  BrainCircuit,
  Play,
  Square,
  Settings,
  Zap,
  AlertCircle,
  ChevronUp,
  ChevronDown,
  History,
  BarChart3,
  Code,
} from "lucide-react";

import { motion, AnimatePresence } from "framer-motion";

//------------------------------------------------------
// Types
//------------------------------------------------------
interface ModelResponse {
  id: string;
  name: string;
  provider: string;
  status: "pending" | "streaming" | "completed" | "error";
  content: string;
  responseTime?: number;
  tokenCount?: number;
  selected?: boolean;
}

//------------------------------------------------------
// Main Page Content
//------------------------------------------------------
function StreamPageContent() {
  //--------------------------------------------------
  // Contexts & hooks
  //--------------------------------------------------
  const { apiKey, isAuthenticated, autoLoginDev, isLoading } = useAuth();
  const { state, actions } = useSession();

  const modelInstances = useModelInstances();
  const preferenceStore = usePreferenceStore();
  const apiIntegration = useAPIIntegration();
  const agentMode = useAgentMode();

  const {
    streams,
    isPolling,
    startStream,
    stopStream,
    clearStreams,
  } = useAgentStream();

  //--------------------------------------------------
  // Local state
  //--------------------------------------------------
  const defaultPrompt = agentMode.isCodeMode
    ? "Analyze this repository and suggest improvements."
    : "Write a creative story about a robot who discovers emotions for the first time.";

  const [prompt, setPrompt] = useState(defaultPrompt);
  const [selectedRepository, setSelectedRepository] = useState<string>("");
  const [isConfigExpanded, setIsConfigExpanded] = useState(true);
  const [formError, setFormError] = useState<string | null>(null);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);

  // Conversation / preference state from former HEAD
  const [isFollowUp, setIsFollowUp] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<any[]>([]);
  const [currentTurnNumber, setCurrentTurnNumber] = useState(0);
  const [currentTurnPrompt, setCurrentTurnPrompt] = useState("");
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [currentTurnId, setCurrentTurnId] = useState<string | null>(null);

  const [modelResponses, setModelResponses] = useState<ModelResponse[]>([]);
  const [selectedResponse, setSelectedResponse] = useState<string | null>(null);

  const [showPreferenceFeedback, setShowPreferenceFeedback] = useState(false);

  //--------------------------------------------------
  // Auth helper (dev auto-login)
  //--------------------------------------------------
  useEffect(() => {
    if (!isAuthenticated) {
      autoLoginDev();
    }
  }, [isAuthenticated, autoLoginDev]);

  //--------------------------------------------------
  // Prompt template changes when agent mode toggles
  //--------------------------------------------------
  useEffect(() => {
    setPrompt(
      agentMode.isCodeMode
        ? "Analyze this repository and suggest improvements."
        : "Write a creative story about a robot who discovers emotions for the first time."
    );
  }, [agentMode.isCodeMode]);

  //--------------------------------------------------
  // Map streaming data (polling) → modelResponses
  //--------------------------------------------------
  useEffect(() => {
    if (streams.size === 0) return;

    // For each variationId (key of Map) build / update a ModelResponse
    setModelResponses((prev) => {
      const updated: ModelResponse[] = [...prev];

      streams.forEach((chunks, variationId) => {
        const id = variationId.toString();
        const existing = updated.find((m) => m.id === id);
        const content = chunks.join("");
        if (existing) {
          existing.content = content;
          existing.status = "streaming";
        } else {
          updated.push({
            id,
            name: `Agent #${variationId + 1}`,
            provider: "agent",
            status: "streaming",
            content,
          });
        }
      });
      return [...updated];
    });
  }, [streams]);

  //--------------------------------------------------
  // Start / stop comparison helpers (using polling)
  //--------------------------------------------------
  const handleStartComparison = async () => {
    // Basic validation similar to original HEAD
    if (!prompt.trim()) {
      setFormError("Please enter a prompt");
      return;
    }
    if (agentMode.requiresRepo && !selectedRepository) {
      setFormError(
        "Please select a repository for code analysis mode"
      );
      return;
    }
    if (
      !agentMode.isCodeMode &&
      modelInstances.selectedInstances.length === 0
    ) {
      setFormError("Please select at least one model");
      return;
    }
    if (!apiKey) {
      setFormError("Please wait for authentication...");
      return;
    }

    setFormError(null);

    try {
      // Delegate to API integration service which returns runId
      const response = await apiIntegration.startModelComparison(
        {
          sessionId: currentSessionId ?? undefined,
          prompt,
          modelIds: modelInstances.selectedInstances.map((i) => i.modelId),
          agentMode: agentMode.agentMode,
          repositoryUrl: agentMode.requiresRepo
            ? selectedRepository
            : undefined,
        },
        // We no longer rely on SSE callback; empty function fulfils signature
        () => {}
      );

      // Kick off polling for that run
      startStream(response.runId);
      setCurrentRunId(response.runId);

      // Reset UI state
      setIsConfigExpanded(false);
      setCurrentTurnPrompt(prompt);
    } catch (err) {
      console.error(err);
      setFormError(
        err instanceof Error ? err.message : "Failed to start comparison"
      );
    }
  };

  const handleStopComparison = () => {
    if (currentRunId) {
      stopStream();
      setCurrentRunId(null);
    }
    clearStreams();
    setModelResponses([]);
  };

  //--------------------------------------------------
  // UI helpers
  //--------------------------------------------------
  const getAgentColor = (index: number) => {
    const colors = [
      "agent-1",
      "agent-2",
      "agent-3",
      "agent-4",
      "agent-5",
    ];
    return colors[index % colors.length];
  };

  //--------------------------------------------------
  // Early return while auth info loading
  //--------------------------------------------------
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-ai-primary mx-auto mb-4" />
          <p className="text-neutral-shadow">Authenticating...</p>
        </div>
      </div>
    );
  }

  //--------------------------------------------------
  // Render
  //--------------------------------------------------
  const currentSessionTurns = state.activeSessionId
    ? state.sessionTurns[state.activeSessionId] || []
    : [];

  const displayError = formError;

  return (
    <div className="min-h-screen bg-gradient-neural-twilight flex">
      {/* Auth indicator */}
      <div className="fixed top-4 right-4 z-50">
        <AuthStatus />
      </div>

      <AdaptiveLayout
        sessions={state.sessions}
        activeSessionId={state.activeSessionId || undefined}
        onSessionSelect={actions.setActiveSession}
        onSessionCreate={() => actions.createSession("New Session")}
        onSessionDelete={actions.deleteSession}
        currentMode={modelResponses.length > 0 ? "compare" : "welcome"}
        onModeChange={(mode) => {
          if (mode === "welcome") {
            actions.setActiveSession(null);
            setModelResponses([]);
          }
        }}
      >
        <div className="h-full w-full flex flex-col overflow-y-auto p-4 pb-8">
          {/* Comparison Grid */}
          {modelResponses.length > 0 && (
            <ComparisonGrid
              responses={modelResponses}
              onSelectResponse={(modelId) => setSelectedResponse(modelId)}
              onPreferenceFeedback={(id) => {
                setSelectedResponse(id);
                setShowPreferenceFeedback(true);
              }}
            />
          )}

          {/* Config Panel */}
          <div className="bg-neutral-paper rounded-2xl shadow-xl mb-2 w-full">
            <div
              className="p-4 flex items-center justify-between cursor-pointer hover:bg-neutral-fog"
              onClick={() => setIsConfigExpanded(!isConfigExpanded)}
            >
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-ai-primary to-ai-secondary text-white">
                  <Settings className="h-5 w-5" />
                </div>
                <span className="text-h3 font-bold text-neutral-charcoal">
                  Model Comparison Configuration
                </span>
              </div>
              <div className="flex items-center gap-2">
                {isConfigExpanded ? (
                  <ChevronUp className="h-5 w-5 text-neutral-shadow" />
                ) : (
                  <ChevronDown className="h-5 w-5 text-neutral-shadow" />
                )}
              </div>
            </div>
            <AnimatePresence>
              {isConfigExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.25 }}
                  style={{ overflow: "visible" }}
                >
                  <div className="p-4 space-y-4">
                    {/* Mode selector */}
                    <ModeSelector disabled={isPolling} />

                    {/* Repo picker when in code mode */}
                    {agentMode.requiresRepo && (
                      <RepositoryPicker
                        selectedRepo={selectedRepository}
                        onRepoSelect={setSelectedRepository}
                        disabled={isPolling}
                      />
                    )}

                    {/* Prompt input */}
                    <div>
                      <label className="block text-label font-medium mb-2 flex items-center gap-2">
                        <Zap className="h-4 w-4" />
                        {agentMode.isCodeMode ? "Code Analysis Prompt" : "Prompt"}
                      </label>
                      <Textarea
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        rows={4}
                        disabled={isPolling}
                        className="w-full bg-neutral-white border border-neutral-fog rounded-md px-md py-md"
                      />
                    </div>

                    {/* Model selection for text mode */}
                    {!agentMode.isCodeMode && (
                      <div>
                        <label className="block text-label font-medium mb-3">
                          Select Models to Compare
                        </label>
                        <ModelInstanceSelector
                          availableModels={modelInstances.availableModels}
                          selectedInstances={modelInstances.selectedInstances}
                          onAddInstance={modelInstances.addInstance}
                          onRemoveInstance={modelInstances.removeInstance}
                          maxInstances={modelInstances.maxInstances}
                          isLoading={modelInstances.isLoading}
                          placeholder="Click to add models..."
                        />
                      </div>
                    )}

                    {/* Error */}
                    {displayError && (
                      <div className="p-md bg-semantic-error/10 border border-semantic-error/20 rounded-lg flex items-center gap-2 text-semantic-error">
                        <AlertCircle className="h-5 w-5" />
                        <span className="font-medium">{displayError}</span>
                      </div>
                    )}

                    {/* Action buttons */}
                    <div className="flex items-center gap-4">
                      {!isPolling ? (
                        <Button onClick={handleStartComparison}>
                          <Play className="inline w-4 h-4 mr-2" /> Start
                        </Button>
                      ) : (
                        <Button onClick={handleStopComparison} variant="destructive">
                          <Square className="inline w-4 h-4 mr-2" /> Stop
                        </Button>
                      )}

                      {modelResponses.length > 0 && !isPolling && (
                        <Button
                          variant="outline"
                          onClick={() => {
                            setModelResponses([]);
                            clearStreams();
                          }}
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

          {/* Preference feedback modal */}
          {showPreferenceFeedback && selectedResponse && (
            <PreferenceFeedback
              isOpen={showPreferenceFeedback}
              onClose={() => setShowPreferenceFeedback(false)}
              selectedModelId={selectedResponse}
              selectedModelName={
                modelResponses.find((r) => r.id === selectedResponse)?.name ||
                ""
              }
              allModels={modelResponses.map((r) => ({
                id: r.id,
                name: r.name,
                response: r.content,
              }))}
              onSubmitFeedback={async () => setShowPreferenceFeedback(false)}
            />
          )}
        </div>
      </AdaptiveLayout>
    </div>
  );
}

//------------------------------------------------------
// Export wrapped with providers
//------------------------------------------------------
export default function StreamPage() {
  return (
    <SessionProvider>
      <AgentModeProvider>
        <StreamPageContent />
      </AgentModeProvider>
    </SessionProvider>
  );
} 