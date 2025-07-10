'use client';

import React from 'react';
import { TrendingUp, Clock, DollarSign } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export interface ModelPerformanceData {
  modelId: string;
  modelName: string;
  winRate: number;
  averageResponseTime: number;
  averageCost: number;
  totalComparisons: number;
  totalWins: number;
  color: string;
}

interface ModelComparisonChartProps {
  data: ModelPerformanceData[];
  isLoading?: boolean;
  timeRange?: 'day' | 'week' | 'month' | 'all';
  onTimeRangeChange?: (range: 'day' | 'week' | 'month' | 'all') => void;
}

export function ModelComparisonChart({ 
  data, 
  isLoading = false, 
  timeRange = 'week',
  onTimeRangeChange 
}: ModelComparisonChartProps) {
  const sortedData = [...data].sort((a, b) => b.winRate - a.winRate);
  const maxWinRate = Math.max(...data.map(d => d.winRate));
  const maxResponseTime = Math.max(...data.map(d => d.averageResponseTime));
  const maxCost = Math.max(...data.map(d => d.averageCost));

  const timeRanges = [
    { value: 'day', label: 'Today' },
    { value: 'week', label: 'This Week' },
    { value: 'month', label: 'This Month' },
    { value: 'all', label: 'All Time' },
  ];

  if (isLoading) {
    return (
      <Card className="bg-neutral-white">
        <CardHeader>
          <CardTitle className="text-h3 text-neutral-charcoal">Model Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
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

  if (data.length === 0) {
    return (
      <Card className="bg-neutral-white">
        <CardHeader>
          <CardTitle className="text-h3 text-neutral-charcoal">Model Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <TrendingUp className="w-12 h-12 mx-auto text-neutral-shadow mb-4" />
            <p className="text-neutral-shadow text-body">No comparison data available yet</p>
            <p className="text-neutral-shadow text-body-sm mt-2">
              Start comparing models to see performance analytics
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-neutral-white">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-h3 text-neutral-charcoal">Model Performance</CardTitle>
          {onTimeRangeChange && (
            <div className="flex bg-neutral-fog rounded-lg p-1">
              {timeRanges.map((range) => (
                <button
                  key={range.value}
                  onClick={() => onTimeRangeChange(range.value as any)}
                  className={`px-3 py-1 rounded-md text-body-sm font-medium transition-colors ${
                    timeRange === range.value
                      ? 'bg-ai-primary text-white'
                      : 'text-neutral-shadow hover:text-neutral-charcoal'
                  }`}
                >
                  {range.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Win Rate Chart */}
          <div>
            <h4 className="text-body font-semibold text-neutral-charcoal mb-3 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Win Rate
            </h4>
            <div className="space-y-3">
              {sortedData.map((model) => (
                <div key={model.modelId} className="group">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <div 
                        className={`w-3 h-3 rounded-full bg-${model.color}`}
                        style={{ backgroundColor: `hsl(var(--${model.color}))` }}
                      />
                      <span className="text-body-sm font-medium text-neutral-charcoal">
                        {model.modelName}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-body-sm font-semibold text-neutral-charcoal">
                        {model.winRate.toFixed(1)}%
                      </span>
                      <span className="text-caption text-neutral-shadow ml-2">
                        ({model.totalWins}/{model.totalComparisons})
                      </span>
                    </div>
                  </div>
                  <div className="w-full bg-neutral-fog rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full bg-${model.color} transition-all duration-500 ease-out`}
                      style={{ 
                        width: `${(model.winRate / maxWinRate) * 100}%`,
                        backgroundColor: `hsl(var(--${model.color}))`
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Response Time Chart */}
          <div>
            <h4 className="text-body font-semibold text-neutral-charcoal mb-3 flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Average Response Time
            </h4>
            <div className="space-y-3">
              {data.map((model) => (
                <div key={model.modelId} className="group">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <div 
                        className={`w-3 h-3 rounded-full bg-${model.color}`}
                        style={{ backgroundColor: `hsl(var(--${model.color}))` }}
                      />
                      <span className="text-body-sm font-medium text-neutral-charcoal">
                        {model.modelName}
                      </span>
                    </div>
                    <span className="text-body-sm font-semibold text-neutral-charcoal">
                      {model.averageResponseTime.toFixed(1)}s
                    </span>
                  </div>
                  <div className="w-full bg-neutral-fog rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full bg-${model.color} transition-all duration-500 ease-out`}
                      style={{ 
                        width: `${(model.averageResponseTime / maxResponseTime) * 100}%`,
                        backgroundColor: `hsl(var(--${model.color}))`
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Cost Chart */}
          <div>
            <h4 className="text-body font-semibold text-neutral-charcoal mb-3 flex items-center gap-2">
              <DollarSign className="w-4 h-4" />
              Average Cost per Response
            </h4>
            <div className="space-y-3">
              {data.map((model) => (
                <div key={model.modelId} className="group">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <div 
                        className={`w-3 h-3 rounded-full bg-${model.color}`}
                        style={{ backgroundColor: `hsl(var(--${model.color}))` }}
                      />
                      <span className="text-body-sm font-medium text-neutral-charcoal">
                        {model.modelName}
                      </span>
                    </div>
                    <span className="text-body-sm font-semibold text-neutral-charcoal">
                      ${model.averageCost.toFixed(4)}
                    </span>
                  </div>
                  <div className="w-full bg-neutral-fog rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full bg-${model.color} transition-all duration-500 ease-out`}
                      style={{ 
                        width: `${(model.averageCost / maxCost) * 100}%`,
                        backgroundColor: `hsl(var(--${model.color}))`
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default ModelComparisonChart;