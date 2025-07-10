'use client';

import React, { useState } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Users, 
  Heart, 
  Activity, 
  Settings,
  RefreshCw,
  Download,
  Filter
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ModelComparisonChart } from '@/components/analytics/ModelComparisonChart';
import { SessionAnalytics } from '@/components/analytics/SessionAnalytics';
import { ResponseMetricsPanel } from '@/components/analytics/ResponseMetricsPanel';
import { UserPreferenceDashboard } from '@/components/analytics/UserPreferenceDashboard';
import { useAnalytics } from '@/hooks/useAnalytics';

export default function AnalyticsPage() {
  const analytics = useAnalytics();
  const [activeTab, setActiveTab] = useState('overview');

  const timeRanges = [
    { value: 'day', label: 'Today' },
    { value: 'week', label: 'This Week' },
    { value: 'month', label: 'This Month' },
    { value: 'quarter', label: 'This Quarter' },
    { value: 'year', label: 'This Year' },
    { value: 'all', label: 'All Time' },
  ];

  const formatLastUpdated = (timestamp: string | null) => {
    if (!timestamp) return 'Never';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / (1000 * 60));
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes} min ago`;
    
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString();
  };

  const handleExportData = () => {
    // TODO: Implement data export functionality
    console.log('Export analytics data');
  };

  return (
    <div className="min-h-screen bg-neutral-white">
      <div className="container mx-auto px-lg py-xl max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-display font-bold text-neutral-charcoal mb-2">
                Analytics Dashboard
              </h1>
              <p className="text-body-lg text-neutral-shadow">
                Track your model preferences, performance metrics, and usage patterns
              </p>
            </div>
            
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 text-body-sm text-neutral-shadow">
                <Activity className="w-4 h-4" />
                <span>Last updated: {formatLastUpdated(analytics.lastUpdated)}</span>
              </div>
              
              <Button
                onClick={analytics.refreshAnalytics}
                disabled={analytics.isLoading}
                variant="outline"
                size="sm"
                className="flex items-center gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${analytics.isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              
              <Button
                onClick={handleExportData}
                variant="outline"
                size="sm"
                className="flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Export
              </Button>
            </div>
          </div>

          {/* Time Range Filter */}
          <div className="flex items-center gap-4">
            <div className="flex bg-neutral-fog rounded-lg p-1">
              {timeRanges.map((range) => (
                <button
                  key={range.value}
                  onClick={() => analytics.updateTimeRange(range.value as any)}
                  className={`px-4 py-2 rounded-md text-body-sm font-medium transition-colors ${
                    analytics.filters.timeRange === range.value
                      ? 'bg-ai-primary text-white'
                      : 'text-neutral-shadow hover:text-neutral-charcoal'
                  }`}
                >
                  {range.label}
                </button>
              ))}
            </div>
            
            <Badge variant="outline" className="text-neutral-shadow">
              {analytics.filters.timeRange === 'all' ? 'All Time' : 
               analytics.filters.timeRange === 'day' ? 'Today' :
               analytics.filters.timeRange === 'week' ? 'This Week' :
               analytics.filters.timeRange === 'month' ? 'This Month' :
               analytics.filters.timeRange === 'quarter' ? 'This Quarter' :
               'This Year'}
            </Badge>
          </div>
        </div>

        {/* Error Display */}
        {analytics.error && (
          <Card className="mb-6 bg-semantic-error/10 border-semantic-error/20">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-semantic-error">
                  <Activity className="w-5 h-5" />
                  <span className="font-medium">Error loading analytics: {analytics.error}</span>
                </div>
                <Button
                  onClick={analytics.clearError}
                  variant="ghost"
                  size="sm"
                  className="text-semantic-error hover:text-semantic-error/80"
                >
                  Dismiss
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Main Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="models" className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Models
            </TabsTrigger>
            <TabsTrigger value="sessions" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              Sessions
            </TabsTrigger>
            <TabsTrigger value="preferences" className="flex items-center gap-2">
              <Heart className="w-4 h-4" />
              Preferences
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <ModelComparisonChart
                data={analytics.modelPerformance}
                isLoading={analytics.isLoading}
                timeRange={analytics.filters.timeRange}
                onTimeRangeChange={analytics.updateTimeRange}
              />
              
              <div className="space-y-6">
                <Card className="bg-neutral-white">
                  <CardHeader>
                    <CardTitle className="text-h3 text-neutral-charcoal">
                      Quick Stats
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between p-3 bg-neutral-paper rounded-lg">
                        <span className="text-body-sm text-neutral-shadow">Total Sessions</span>
                        <span className="text-body font-semibold text-neutral-charcoal">
                          {analytics.sessionMetrics.totalSessions}
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-neutral-paper rounded-lg">
                        <span className="text-body-sm text-neutral-shadow">Total Preferences</span>
                        <span className="text-body font-semibold text-neutral-charcoal">
                          {analytics.userPreferences.totalPreferences}
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-neutral-paper rounded-lg">
                        <span className="text-body-sm text-neutral-shadow">Favorite Model</span>
                        <span className="text-body font-semibold text-neutral-charcoal">
                          {analytics.userPreferences.favoriteModel.modelName}
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-neutral-paper rounded-lg">
                        <span className="text-body-sm text-neutral-shadow">Total Cost</span>
                        <span className="text-body font-semibold text-neutral-charcoal">
                          ${analytics.totalCost.toFixed(4)}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                
                <ResponseMetricsPanel
                  realTimeMetrics={analytics.realTimeMetrics}
                  historicalMetrics={analytics.historicalMetrics}
                  isStreaming={analytics.isStreaming}
                  totalCost={analytics.totalCost}
                  totalTokens={analytics.totalTokens}
                  totalRequests={analytics.totalRequests}
                  onModelToggle={(modelId) => console.log('Toggle model:', modelId)}
                />
              </div>
            </div>
          </TabsContent>

          {/* Models Tab */}
          <TabsContent value="models" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ModelComparisonChart
                data={analytics.modelPerformance}
                isLoading={analytics.isLoading}
                timeRange={analytics.filters.timeRange}
                onTimeRangeChange={analytics.updateTimeRange}
              />
              
              <ResponseMetricsPanel
                realTimeMetrics={analytics.realTimeMetrics}
                historicalMetrics={analytics.historicalMetrics}
                isStreaming={analytics.isStreaming}
                totalCost={analytics.totalCost}
                totalTokens={analytics.totalTokens}
                totalRequests={analytics.totalRequests}
                onModelToggle={(modelId) => console.log('Toggle model:', modelId)}
              />
            </div>
          </TabsContent>

          {/* Sessions Tab */}
          <TabsContent value="sessions" className="space-y-6">
            <SessionAnalytics
              metrics={analytics.sessionMetrics}
              isLoading={analytics.isLoading}
              timeRange={analytics.filters.timeRange}
            />
          </TabsContent>

          {/* Preferences Tab */}
          <TabsContent value="preferences" className="space-y-6">
            <UserPreferenceDashboard
              data={analytics.userPreferences}
              isLoading={analytics.isLoading}
              timeRange={analytics.filters.timeRange}
              onTimeRangeChange={analytics.updateTimeRange}
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}