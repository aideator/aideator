'use client';

import React, { useState } from 'react';
import { 
  Heart, 
  TrendingUp, 
  Calendar, 
  Filter, 
  Star, 
  MessageSquare,
  Clock,
  Target,
  Award,
  BarChart3
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

export interface UserPreferenceData {
  totalPreferences: number;
  favoriteModel: {
    modelId: string;
    modelName: string;
    winRate: number;
    totalWins: number;
    color: string;
  };
  modelPreferences: Array<{
    modelId: string;
    modelName: string;
    winRate: number;
    totalComparisons: number;
    totalWins: number;
    averageRating: number;
    color: string;
  }>;
  preferencesByPromptType: Array<{
    category: string;
    favoriteModel: string;
    totalComparisons: number;
    distribution: Array<{
      modelId: string;
      modelName: string;
      percentage: number;
    }>;
  }>;
  preferenceEvolution: Array<{
    date: string;
    modelId: string;
    modelName: string;
    winRate: number;
  }>;
  recentPreferences: Array<{
    id: string;
    modelId: string;
    modelName: string;
    prompt: string;
    timestamp: string;
    rating?: number;
    feedback?: string;
  }>;
}

interface UserPreferenceDashboardProps {
  data: UserPreferenceData;
  isLoading?: boolean;
  timeRange?: 'day' | 'week' | 'month' | 'quarter' | 'year' | 'all';
  onTimeRangeChange?: (range: 'day' | 'week' | 'month' | 'quarter' | 'year' | 'all') => void;
}

export function UserPreferenceDashboard({ 
  data, 
  isLoading = false, 
  timeRange = 'month',
  onTimeRangeChange 
}: UserPreferenceDashboardProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [showOnlyFavorites, setShowOnlyFavorites] = useState(false);

  const timeRanges = [
    { value: 'day', label: 'Today' },
    { value: 'week', label: 'Last Week' },
    { value: 'month', label: 'Last Month' },
    { value: 'quarter', label: 'Last Quarter' },
    { value: 'year', label: 'Last Year' },
    { value: 'all', label: 'All Time' },
  ];

  const promptCategories = ['all', ...data.preferencesByPromptType.map(p => p.category)];

  const filteredModelPreferences = data.modelPreferences.filter(model => {
    if (showOnlyFavorites && model.winRate < 30) return false;
    return true;
  });

  const getRatingStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`w-3 h-3 ${
          i < rating ? 'text-semantic-warning fill-current' : 'text-neutral-fog'
        }`}
      />
    ));
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="bg-neutral-white">
            <CardContent className="p-6">
              <div className="animate-pulse space-y-4">
                <div className="h-6 bg-neutral-fog rounded w-1/4"></div>
                <div className="space-y-2">
                  <div className="h-4 bg-neutral-fog rounded"></div>
                  <div className="h-4 bg-neutral-fog rounded w-3/4"></div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <Card className="bg-neutral-white">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-h3 text-neutral-charcoal flex items-center gap-2">
              <Heart className="w-5 h-5" />
              Your Preference Dashboard
            </CardTitle>
            <div className="flex items-center gap-3">
              <div className="flex bg-neutral-fog rounded-lg p-1">
                {timeRanges.map((range) => (
                  <button
                    key={range.value}
                    onClick={() => onTimeRangeChange?.(range.value as any)}
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
              <Button
                variant={showOnlyFavorites ? 'default' : 'outline'}
                size="sm"
                onClick={() => setShowOnlyFavorites(!showOnlyFavorites)}
                className="flex items-center gap-2"
              >
                <Filter className="w-4 h-4" />
                Favorites Only
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-neutral-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-caption text-neutral-shadow">Total Preferences</p>
                <p className="text-h2 font-bold text-neutral-charcoal">
                  {data.totalPreferences}
                </p>
              </div>
              <div className="p-2 bg-ai-primary/10 rounded-lg">
                <Target className="w-5 h-5 text-ai-primary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-caption text-neutral-shadow">Favorite Model</p>
                <p className="text-body font-bold text-neutral-charcoal">
                  {data.favoriteModel.modelName}
                </p>
                <p className="text-caption text-neutral-shadow">
                  {data.favoriteModel.winRate.toFixed(1)}% win rate
                </p>
              </div>
              <div className="p-2 bg-semantic-warning/10 rounded-lg">
                <Award className="w-5 h-5 text-semantic-warning" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-caption text-neutral-shadow">Avg Rating</p>
                <p className="text-h2 font-bold text-neutral-charcoal">
                  {(data.modelPreferences.reduce((sum, m) => sum + m.averageRating, 0) / data.modelPreferences.length).toFixed(1)}
                </p>
              </div>
              <div className="p-2 bg-semantic-success/10 rounded-lg">
                <Star className="w-5 h-5 text-semantic-success" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-caption text-neutral-shadow">Categories</p>
                <p className="text-h2 font-bold text-neutral-charcoal">
                  {data.preferencesByPromptType.length}
                </p>
              </div>
              <div className="p-2 bg-ai-accent/10 rounded-lg">
                <BarChart3 className="w-5 h-5 text-ai-accent" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Model Preferences */}
      <Card className="bg-neutral-white">
        <CardHeader>
          <CardTitle className="text-h3 text-neutral-charcoal">
            Your Model Preferences
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredModelPreferences.map((model) => (
              <div 
                key={model.modelId}
                className="p-4 bg-neutral-paper rounded-lg hover:bg-neutral-fog transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div 
                      className={`w-4 h-4 rounded-full bg-${model.color}`}
                      style={{ backgroundColor: `hsl(var(--${model.color}))` }}
                    />
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-body-sm font-medium text-neutral-charcoal">
                          {model.modelName}
                        </p>
                        {model.modelId === data.favoriteModel.modelId && (
                          <Badge className="bg-semantic-warning text-white">
                            <Heart className="w-3 h-3 mr-1" />
                            Favorite
                          </Badge>
                        )}
                      </div>
                      <p className="text-caption text-neutral-shadow">
                        {model.totalWins} wins out of {model.totalComparisons} comparisons
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-6">
                    <div className="text-center">
                      <p className="text-body-sm font-semibold text-neutral-charcoal">
                        {model.winRate.toFixed(1)}%
                      </p>
                      <p className="text-caption text-neutral-shadow">Win Rate</p>
                    </div>
                    
                    <div className="text-center">
                      <div className="flex items-center gap-1">
                        {getRatingStars(Math.round(model.averageRating))}
                      </div>
                      <p className="text-caption text-neutral-shadow">
                        {model.averageRating.toFixed(1)} avg
                      </p>
                    </div>
                    
                    <div className="w-24">
                      <div className="w-full bg-neutral-fog rounded-full h-2">
                        <div
                          className={`h-full bg-${model.color} rounded-full transition-all duration-500`}
                          style={{ 
                            width: `${model.winRate}%`,
                            backgroundColor: `hsl(var(--${model.color}))`
                          }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Preferences by Category */}
      <Card className="bg-neutral-white">
        <CardHeader>
          <CardTitle className="text-h3 text-neutral-charcoal">
            Preferences by Prompt Type
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {data.preferencesByPromptType.map((category) => (
              <div key={category.category} className="p-4 bg-neutral-paper rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <p className="text-body-sm font-medium text-neutral-charcoal capitalize">
                      {category.category}
                    </p>
                    <p className="text-caption text-neutral-shadow">
                      {category.totalComparisons} comparisons
                    </p>
                  </div>
                  <Badge variant="outline">
                    Favorite: {category.favoriteModel}
                  </Badge>
                </div>
                
                <div className="space-y-2">
                  {category.distribution.map((model) => (
                    <div key={model.modelId} className="flex items-center justify-between">
                      <span className="text-body-sm text-neutral-charcoal">
                        {model.modelName}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="text-body-sm font-medium text-neutral-charcoal">
                          {model.percentage.toFixed(1)}%
                        </span>
                        <div className="w-16 bg-neutral-fog rounded-full h-1">
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
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Preferences */}
      <Card className="bg-neutral-white">
        <CardHeader>
          <CardTitle className="text-h3 text-neutral-charcoal">
            Recent Preferences
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {data.recentPreferences.map((pref) => (
              <div 
                key={pref.id}
                className="p-3 bg-neutral-paper rounded-lg hover:bg-neutral-fog transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="text-body-sm font-medium text-neutral-charcoal">
                        {pref.modelName}
                      </p>
                      {pref.rating && (
                        <div className="flex items-center gap-1">
                          {getRatingStars(pref.rating)}
                        </div>
                      )}
                    </div>
                    <p className="text-body-sm text-neutral-shadow line-clamp-2">
                      {pref.prompt}
                    </p>
                    {pref.feedback && (
                      <p className="text-caption text-neutral-shadow mt-1 italic">
                        "{pref.feedback}"
                      </p>
                    )}
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-1 text-caption text-neutral-shadow">
                      <Clock className="w-3 h-3" />
                      {formatDate(pref.timestamp)}
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

