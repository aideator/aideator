'use client';

import React from 'react';
import { MessageSquare, Clock, Users, BarChart3, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export interface SessionMetrics {
  totalSessions: number;
  averageSessionDuration: number;
  averageTurnsPerSession: number;
  totalTurns: number;
  activeSessionsLast24h: number;
  topModelsUsed: Array<{
    modelId: string;
    modelName: string;
    usageCount: number;
    percentage: number;
  }>;
  sessionDurationDistribution: Array<{
    range: string;
    count: number;
    percentage: number;
  }>;
  turnsPerSessionDistribution: Array<{
    range: string;
    count: number;
    percentage: number;
  }>;
}

interface SessionAnalyticsProps {
  metrics: SessionMetrics;
  isLoading?: boolean;
  timeRange?: 'day' | 'week' | 'month' | 'all';
}

export function SessionAnalytics({ 
  metrics, 
  isLoading = false, 
  timeRange = 'week' 
}: SessionAnalyticsProps) {
  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes === 0) {
      return `${remainingSeconds.toFixed(0)}s`;
    }
    
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  };

  const getTimeRangeLabel = (range: string): string => {
    switch (range) {
      case 'day': return 'Today';
      case 'week': return 'This Week';
      case 'month': return 'This Month';
      case 'all': return 'All Time';
      default: return 'This Week';
    }
  };

  if (isLoading) {
    return (
      <Card className="bg-neutral-white">
        <CardHeader>
          <CardTitle className="text-h3 text-neutral-charcoal">Session Analytics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="animate-pulse">
                <div className="h-16 bg-neutral-fog rounded"></div>
              </div>
            ))}
          </div>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse">
                <div className="h-6 bg-neutral-fog rounded mb-2"></div>
                <div className="h-4 bg-neutral-fog rounded w-3/4"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-neutral-white">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-h3 text-neutral-charcoal">Session Analytics</CardTitle>
          <Badge variant="outline" className="text-neutral-shadow">
            {getTimeRangeLabel(timeRange)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="p-4 bg-neutral-paper rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-caption text-neutral-shadow">Total Sessions</p>
                <p className="text-h2 font-bold text-neutral-charcoal">
                  {metrics.totalSessions.toLocaleString()}
                </p>
              </div>
              <div className="p-2 bg-ai-primary/10 rounded-lg">
                <MessageSquare className="w-5 h-5 text-ai-primary" />
              </div>
            </div>
          </div>

          <div className="p-4 bg-neutral-paper rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-caption text-neutral-shadow">Avg Duration</p>
                <p className="text-h2 font-bold text-neutral-charcoal">
                  {formatDuration(metrics.averageSessionDuration)}
                </p>
              </div>
              <div className="p-2 bg-ai-secondary/10 rounded-lg">
                <Clock className="w-5 h-5 text-ai-secondary" />
              </div>
            </div>
          </div>

          <div className="p-4 bg-neutral-paper rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-caption text-neutral-shadow">Avg Turns</p>
                <p className="text-h2 font-bold text-neutral-charcoal">
                  {metrics.averageTurnsPerSession.toFixed(1)}
                </p>
              </div>
              <div className="p-2 bg-ai-accent/10 rounded-lg">
                <BarChart3 className="w-5 h-5 text-ai-accent" />
              </div>
            </div>
          </div>

          <div className="p-4 bg-neutral-paper rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-caption text-neutral-shadow">Active (24h)</p>
                <p className="text-h2 font-bold text-neutral-charcoal">
                  {metrics.activeSessionsLast24h}
                </p>
              </div>
              <div className="p-2 bg-semantic-success/10 rounded-lg">
                <TrendingUp className="w-5 h-5 text-semantic-success" />
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Models Used */}
          <div>
            <h4 className="text-body font-semibold text-neutral-charcoal mb-3 flex items-center gap-2">
              <Users className="w-4 h-4" />
              Most Used Models
            </h4>
            <div className="space-y-3">
              {metrics.topModelsUsed.map((model, index) => (
                <div key={model.modelId} className="flex items-center justify-between p-3 bg-neutral-paper rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-6 h-6 bg-ai-primary/10 rounded-full text-ai-primary text-body-sm font-bold">
                      {index + 1}
                    </div>
                    <div>
                      <p className="text-body-sm font-medium text-neutral-charcoal">
                        {model.modelName}
                      </p>
                      <p className="text-caption text-neutral-shadow">
                        {model.usageCount} uses
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-body-sm font-semibold text-neutral-charcoal">
                      {model.percentage.toFixed(1)}%
                    </p>
                    <div className="w-12 bg-neutral-fog rounded-full h-1 mt-1">
                      <div
                        className="h-full bg-ai-primary rounded-full transition-all duration-500"
                        style={{ width: `${model.percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Session Duration Distribution */}
          <div>
            <h4 className="text-body font-semibold text-neutral-charcoal mb-3 flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Session Duration Distribution
            </h4>
            <div className="space-y-3">
              {metrics.sessionDurationDistribution.map((duration, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-neutral-paper rounded-lg">
                  <div>
                    <p className="text-body-sm font-medium text-neutral-charcoal">
                      {duration.range}
                    </p>
                    <p className="text-caption text-neutral-shadow">
                      {duration.count} sessions
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-body-sm font-semibold text-neutral-charcoal">
                      {duration.percentage.toFixed(1)}%
                    </p>
                    <div className="w-12 bg-neutral-fog rounded-full h-1 mt-1">
                      <div
                        className="h-full bg-ai-secondary rounded-full transition-all duration-500"
                        style={{ width: `${duration.percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Turns Per Session Distribution */}
        <div className="mt-6">
          <h4 className="text-body font-semibold text-neutral-charcoal mb-3 flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Turns Per Session Distribution
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {metrics.turnsPerSessionDistribution.map((turns, index) => (
              <div key={index} className="p-3 bg-neutral-paper rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-body-sm font-medium text-neutral-charcoal">
                    {turns.range}
                  </span>
                  <span className="text-body-sm font-semibold text-neutral-charcoal">
                    {turns.percentage.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-neutral-fog rounded-full h-2">
                  <div
                    className="h-full bg-ai-accent rounded-full transition-all duration-500"
                    style={{ width: `${turns.percentage}%` }}
                  />
                </div>
                <p className="text-caption text-neutral-shadow mt-1">
                  {turns.count} sessions
                </p>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default SessionAnalytics;