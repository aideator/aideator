import React from 'react';
import { Clock, Zap, DollarSign, CheckCircle, AlertCircle, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface ModelMetricsProps {
  modelId: string;
  modelName: string;
  responseTime?: number;
  tokenCount?: number;
  costUsd?: number;
  status: 'pending' | 'streaming' | 'completed' | 'error';
  errorMessage?: string;
  showDetailedMetrics?: boolean;
}

interface ModelPerformanceStats {
  averageResponseTime: number;
  totalTokens: number;
  totalCost: number;
  successRate: number;
  usageCount: number;
}

export function ModelMetrics({ 
  modelId, 
  modelName, 
  responseTime, 
  tokenCount, 
  costUsd, 
  status, 
  errorMessage,
  showDetailedMetrics = false 
}: ModelMetricsProps) {
  
  // Mock historical data - in real implementation, this would come from props or API
  const historicalStats: ModelPerformanceStats = {
    averageResponseTime: 2.8,
    totalTokens: 15420,
    totalCost: 0.0847,
    successRate: 0.96,
    usageCount: 47
  };

  const formatResponseTime = (time?: number) => {
    if (!time) return 'N/A';
    return `${time.toFixed(1)}s`;
  };

  const formatCost = (cost?: number) => {
    if (!cost) return 'N/A';
    return `$${cost.toFixed(4)}`;
  };

  const formatTokens = (tokens?: number) => {
    if (!tokens) return 'N/A';
    return tokens.toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-semantic-success';
      case 'streaming': return 'text-ai-accent';
      case 'error': return 'text-semantic-error';
      default: return 'text-neutral-shadow';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-4 h-4" />;
      case 'streaming': return <div className="w-4 h-4 border-2 border-ai-accent border-t-transparent rounded-full animate-spin" />;
      case 'error': return <AlertCircle className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const getPerformanceRating = (responseTime?: number) => {
    if (!responseTime) return null;
    if (responseTime < 2) return { label: 'Excellent', color: 'bg-semantic-success' };
    if (responseTime < 4) return { label: 'Good', color: 'bg-ai-accent' };
    if (responseTime < 6) return { label: 'Average', color: 'bg-semantic-warning' };
    return { label: 'Slow', color: 'bg-semantic-error' };
  };

  const performanceRating = getPerformanceRating(responseTime);

  return (
    <Card className="bg-neutral-paper border-neutral-fog">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-body font-semibold text-neutral-charcoal">
            {modelName} Metrics
          </CardTitle>
          <div className={`flex items-center gap-2 ${getStatusColor(status)}`}>
            {getStatusIcon(status)}
            <span className="text-body-sm font-medium capitalize">{status}</span>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Current Response Metrics */}
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              <Clock className="w-4 h-4 text-neutral-shadow" />
              <span className="text-body-sm font-medium text-neutral-shadow">Time</span>
            </div>
            <div className="text-body font-semibold text-neutral-charcoal">
              {formatResponseTime(responseTime)}
            </div>
            {performanceRating && (
              <Badge 
                variant="secondary" 
                className={`${performanceRating.color} text-white text-xs mt-1`}
              >
                {performanceRating.label}
              </Badge>
            )}
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              <Zap className="w-4 h-4 text-neutral-shadow" />
              <span className="text-body-sm font-medium text-neutral-shadow">Tokens</span>
            </div>
            <div className="text-body font-semibold text-neutral-charcoal">
              {formatTokens(tokenCount)}
            </div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              <DollarSign className="w-4 h-4 text-neutral-shadow" />
              <span className="text-body-sm font-medium text-neutral-shadow">Cost</span>
            </div>
            <div className="text-body font-semibold text-neutral-charcoal">
              {formatCost(costUsd)}
            </div>
          </div>
        </div>

        {/* Error Message */}
        {status === 'error' && errorMessage && (
          <div className="bg-semantic-error/10 border border-semantic-error/20 rounded-lg p-3">
            <div className="flex items-center gap-2 text-semantic-error">
              <AlertCircle className="w-4 h-4" />
              <span className="text-body-sm font-medium">{errorMessage}</span>
            </div>
          </div>
        )}

        {/* Detailed Historical Metrics */}
        {showDetailedMetrics && (
          <div className="border-t border-neutral-fog pt-4">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-4 h-4 text-neutral-shadow" />
              <span className="text-body-sm font-medium text-neutral-shadow">Historical Performance</span>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-caption text-neutral-shadow mb-1">Average Response Time</div>
                <div className="text-body-sm font-medium text-neutral-charcoal">
                  {formatResponseTime(historicalStats.averageResponseTime)}
                </div>
              </div>
              
              <div>
                <div className="text-caption text-neutral-shadow mb-1">Success Rate</div>
                <div className="text-body-sm font-medium text-neutral-charcoal">
                  {(historicalStats.successRate * 100).toFixed(1)}%
                </div>
              </div>
              
              <div>
                <div className="text-caption text-neutral-shadow mb-1">Total Usage</div>
                <div className="text-body-sm font-medium text-neutral-charcoal">
                  {historicalStats.usageCount} requests
                </div>
              </div>
              
              <div>
                <div className="text-caption text-neutral-shadow mb-1">Total Cost</div>
                <div className="text-body-sm font-medium text-neutral-charcoal">
                  {formatCost(historicalStats.totalCost)}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Performance Comparison */}
        {responseTime && historicalStats.averageResponseTime && (
          <div className="border-t border-neutral-fog pt-4">
            <div className="flex items-center justify-between">
              <span className="text-body-sm text-neutral-shadow">vs. Average</span>
              <div className="flex items-center gap-2">
                {responseTime < historicalStats.averageResponseTime ? (
                  <TrendingUp className="w-4 h-4 text-semantic-success rotate-180" />
                ) : (
                  <TrendingUp className="w-4 h-4 text-semantic-error" />
                )}
                <span className={`text-body-sm font-medium ${
                  responseTime < historicalStats.averageResponseTime 
                    ? 'text-semantic-success' 
                    : 'text-semantic-error'
                }`}>
                  {Math.abs(responseTime - historicalStats.averageResponseTime).toFixed(1)}s
                </span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Compact version for inline display
export function ModelMetricsCompact({ 
  responseTime, 
  tokenCount, 
  costUsd, 
  status 
}: Omit<ModelMetricsProps, 'modelId' | 'modelName'>) {
  return (
    <div className="flex items-center gap-4 text-body-sm text-neutral-shadow">
      {responseTime && (
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          <span>{formatResponseTime(responseTime)}</span>
        </div>
      )}
      
      {tokenCount && (
        <div className="flex items-center gap-1">
          <Zap className="w-3 h-3" />
          <span>{formatTokens(tokenCount)}</span>
        </div>
      )}
      
      {costUsd && (
        <div className="flex items-center gap-1">
          <DollarSign className="w-3 h-3" />
          <span>{formatCost(costUsd)}</span>
        </div>
      )}
    </div>
  );
}

// Helper functions (can be moved to utils if needed)
function formatResponseTime(time?: number): string {
  if (!time) return 'N/A';
  return `${time.toFixed(1)}s`;
}

function formatCost(cost?: number): string {
  if (!cost) return 'N/A';
  return `$${cost.toFixed(4)}`;
}

function formatTokens(tokens?: number): string {
  if (!tokens) return 'N/A';
  return tokens.toLocaleString();
}