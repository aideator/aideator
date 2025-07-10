"use client";

import React from 'react';
import { Settings2, Code, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { useAgentMode, AGENT_MODE_OPTIONS, AgentMode } from '@/contexts/AgentModeContext';
import { cn } from '@/lib/utils';

interface ModeSelectorProps {
  disabled?: boolean;
  className?: string;
}

export function ModeSelector({ disabled = false, className }: ModeSelectorProps) {
  const { agentMode, setAgentMode, currentModeInfo } = useAgentMode();

  const handleModeChange = (value: string) => {
    const mode = value as AgentMode;
    setAgentMode(mode);
  };

  const getExecutionModeIcon = (executionMode: 'text' | 'code') => {
    return executionMode === 'code' ? Code : MessageSquare;
  };

  const getExecutionModeColor = (executionMode: 'text' | 'code') => {
    return executionMode === 'code' ? 'text-ai-secondary' : 'text-ai-primary';
  };

  const ExecutionModeIcon = getExecutionModeIcon(currentModeInfo.executionMode);

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <Label className="text-label font-medium text-neutral-charcoal">
        Execution Mode
      </Label>
      
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            disabled={disabled}
            className="border-2 border-neutral-fog hover:border-ai-primary hover:bg-ai-primary/5 transition-colors"
          >
            <ExecutionModeIcon className={cn('h-4 w-4 mr-2', getExecutionModeColor(currentModeInfo.executionMode))} />
            <span className="font-medium">{currentModeInfo.label}</span>
            <Settings2 className="h-4 w-4 ml-2 text-neutral-shadow" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80 p-0" align="start">
          <div className="p-lg">
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold text-neutral-charcoal text-body">
                  Select Execution Mode
                </h4>
                <p className="text-body-sm text-neutral-shadow mt-1">
                  Choose how you want to interact with AI models
                </p>
              </div>

              <RadioGroup 
                value={agentMode} 
                onValueChange={handleModeChange}
                className="space-y-3"
              >
                {AGENT_MODE_OPTIONS.map((option) => {
                  const Icon = getExecutionModeIcon(option.executionMode);
                  const iconColor = getExecutionModeColor(option.executionMode);
                  
                  return (
                    <div key={option.mode} className="flex items-start space-x-3">
                      <RadioGroupItem
                        value={option.mode}
                        id={option.mode}
                        className="mt-1"
                      />
                      <div className="flex-1 space-y-1">
                        <Label
                          htmlFor={option.mode}
                          className="flex items-center gap-2 cursor-pointer text-body font-medium text-neutral-charcoal"
                        >
                          <Icon className={cn('h-4 w-4', iconColor)} />
                          {option.label}
                          {option.requiresRepo && (
                            <span className="text-xs bg-ai-accent/10 text-ai-accent px-2 py-0.5 rounded">
                              Requires Repo
                            </span>
                          )}
                        </Label>
                        <p className="text-body-sm text-neutral-shadow">
                          {option.description}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </RadioGroup>

              <div className="pt-3 border-t border-neutral-fog">
                <div className="flex items-center justify-between text-body-sm">
                  <span className="text-neutral-shadow">Current Mode:</span>
                  <span className="font-medium text-neutral-charcoal">
                    {currentModeInfo.executionMode === 'code' ? 'Code Analysis' : 'Text Completion'}
                  </span>
                </div>
                {currentModeInfo.requiresRepo && (
                  <div className="mt-2 p-2 bg-ai-accent/5 border border-ai-accent/20 rounded-md">
                    <p className="text-body-sm text-ai-accent">
                      📝 Repository selection will be required for this mode
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}