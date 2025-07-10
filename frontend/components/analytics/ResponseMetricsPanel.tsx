'use client';

import React, { useState, useEffect } from 'react';
import { 
  Clock, 
  Zap, 
  DollarSign, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Activity,
  TrendingUp,
  TrendingDown
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export interface RealTimeMetrics {
  modelId: string;
  modelName: string;
  status: 'idle' | 'streaming' | 'completed' | 'error';
  responseTime?: number;
  tokenCount?: number;
  cost?: number;
  error?: string;
  startTime: string;
  endTime?: string;
  color: string;
}

export interface HistoricalMetrics {
  modelId: string;
  modelName: string;
  averageResponseTime: number;
  averageTokenCount: number;
  averageCost: number;
  successRate: number;
  totalRequests: number;
  totalErrors: number;
  trend: 'up' | 'down' | 'stable';
  trendPercentage: number;
  color: string;
}

interface ResponseMetricsPanelProps {
  realTimeMetrics: RealTimeMetrics[];
  historicalMetrics: HistoricalMetrics[];
  isStreaming: boolean;
  totalCost: number;
  totalTokens: number;
  totalRequests: number;
  onModelToggle?: (modelId: string) => void;
}

export function ResponseMetricsPanel({
  realTimeMetrics,
  historicalMetrics,
  isStreaming,
  totalCost,
  totalTokens,
  totalRequests,
  onModelToggle
}: ResponseMetricsPanelProps) {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const formatDuration = (startTime: string, endTime?: string): string => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : currentTime;
    const duration = Math.floor((end.getTime() - start.getTime()) / 1000);
    
    if (duration < 60) {
      return `${duration}s`;
    }
    
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    return `${minutes}m ${seconds}s`;
  };

  const getStatusIcon = (status: RealTimeMetrics['status']) => {
    switch (status) {
      case 'idle':
        return <Activity className="w-4 h-4 text-neutral-shadow" />;
      case 'streaming':
        return <Activity className="w-4 h-4 text-ai-accent animate-pulse" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-semantic-success" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-semantic-error" />;
    }
  };

  const getStatusBadge = (status: RealTimeMetrics['status']) => {
    switch (status) {
      case 'idle':
        return <Badge variant="outline" className="text-neutral-shadow">Idle</Badge>;
      case 'streaming':
        return <Badge className="bg-ai-accent text-white animate-pulse">Streaming</Badge>;
      case 'completed':
        return <Badge className="bg-semantic-success text-white">Completed</Badge>;
      case 'error':
        return <Badge className="bg-semantic-error text-white">Error</Badge>;
    }
  };

  const getTrendIcon = (trend: HistoricalMetrics['trend']) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-semantic-success" />;
      case 'down':
        return <TrendingDown className="w-4 h-4 text-semantic-error" />;
      case 'stable':
        return <div className="w-4 h-4 border-t-2 border-neutral-shadow"></div>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Overall Metrics */}
      <Card className="bg-neutral-white">
        <CardHeader>
          <CardTitle className="text-h3 text-neutral-charcoal flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Live Response Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-neutral-paper rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-caption text-neutral-shadow">Total Cost</p>
                  <p className="text-h2 font-bold text-neutral-charcoal">
                    ${totalCost.toFixed(4)}
                  </p>
                </div>
                <div className="p-2 bg-semantic-warning/10 rounded-lg">
                  <DollarSign className="w-5 h-5 text-semantic-warning" />
                </div>
              </div>
            </div>

            <div className="p-4 bg-neutral-paper rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-caption text-neutral-shadow">Total Tokens</p>
                  <p className="text-h2 font-bold text-neutral-charcoal">
                    {totalTokens.toLocaleString()}
                  </p>
                </div>
                <div className="p-2 bg-ai-primary/10 rounded-lg">
                  <Zap className="w-5 h-5 text-ai-primary" />
                </div>
              </div>
            </div>

            <div className="p-4 bg-neutral-paper rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-caption text-neutral-shadow">Total Requests</p>
                  <p className="text-h2 font-bold text-neutral-charcoal">
                    {totalRequests.toLocaleString()}
                  </p>
                </div>
                <div className="p-2 bg-ai-secondary/10 rounded-lg">
                  <Activity className="w-5 h-5 text-ai-secondary" />
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Real-Time Model Status */}
      {realTimeMetrics.length > 0 && (
        <Card className="bg-neutral-white">
          <CardHeader>
            <CardTitle className="text-h3 text-neutral-charcoal">
              Real-Time Model Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {realTimeMetrics.map((metric) => (
                <div 
                  key={metric.modelId}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    metric.status === 'streaming' 
                      ? 'border-ai-accent bg-ai-accent/5' 
                      : 'border-neutral-fog bg-neutral-paper'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div 
                        className={`w-4 h-4 rounded-full bg-${metric.color}`}
                        style={{ backgroundColor: `hsl(var(--${metric.color}))` }}
                      />
                      <div>
                        <p className="text-body-sm font-medium text-neutral-charcoal">
                          {metric.modelName}
                        </p>
                        <p className="text-caption text-neutral-shadow">
                          {formatDuration(metric.startTime, metric.endTime)}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      {metric.status === 'completed' && (
                        <div className="flex items-center gap-4 text-body-sm text-neutral-charcoal">
                          <div className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            <span>{metric.responseTime?.toFixed(1)}s</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Zap className="w-4 h-4" />
                            <span>{metric.tokenCount}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <DollarSign className="w-4 h-4" />
                            <span>${metric.cost?.toFixed(4)}</span>
                          </div>
                        </div>
                      )}
                      
                      {metric.status === 'error' && (
                        <div className="flex items-center gap-2 text-semantic-error">
                          <AlertCircle className="w-4 h-4" />
                          <span className="text-body-sm">
                            {metric.error || 'Unknown error'}
                          </span>
                        </div>
                      )}
                      
                      <div className="flex items-center gap-2">
                        {getStatusIcon(metric.status)}
                        {getStatusBadge(metric.status)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Historical Performance */}
      <Card className="bg-neutral-white">
        <CardHeader>
          <CardTitle className="text-h3 text-neutral-charcoal">
            Historical Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {historicalMetrics.map((metric) => (
              <div 
                key={metric.modelId}
                className="p-4 bg-neutral-paper rounded-lg hover:bg-neutral-fog transition-colors cursor-pointer"
                onClick={() => onModelToggle?.(metric.modelId)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div 
                      className={`w-4 h-4 rounded-full bg-${metric.color}`}
                      style={{ backgroundColor: `hsl(var(--${metric.color}))` }}
                    />
                    <div>
                      <p className="text-body-sm font-medium text-neutral-charcoal">
                        {metric.modelName}
                      </p>
                      <p className="text-caption text-neutral-shadow">
                        {metric.totalRequests} requests • {metric.successRate.toFixed(1)}% success
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-6">
                    <div className="text-center">
                      <p className="text-body-sm font-semibold text-neutral-charcoal">
                        {metric.averageResponseTime.toFixed(1)}s
                      </p>
                      <p className="text-caption text-neutral-shadow">Avg Time</p>
                    </div>
                    
                    <div className="text-center">
                      <p className="text-body-sm font-semibold text-neutral-charcoal">
                        {metric.averageTokenCount.toLocaleString()}
                      </p>
                      <p className="text-caption text-neutral-shadow">Avg Tokens</p>
                    </div>
                    
                    <div className="text-center">
                      <p className="text-body-sm font-semibold text-neutral-charcoal">
                        ${metric.averageCost.toFixed(4)}
                      </p>
                      <p className="text-caption text-neutral-shadow">Avg Cost</p>
                    </div>
                    
                    <div className="flex items-center gap-1">
                      {getTrendIcon(metric.trend)}
                      <span className={`text-body-sm font-medium ${
                        metric.trend === 'up' ? 'text-semantic-success' :
                        metric.trend === 'down' ? 'text-semantic-error' :
                        'text-neutral-shadow'
                      }`}>
                        {metric.trendPercentage.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default ResponseMetricsPanel;