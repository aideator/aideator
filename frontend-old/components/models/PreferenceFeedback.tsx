'use client';

import React, { useState } from 'react';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle, 
  DialogFooter 
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Star, 
  StarOff, 
  ThumbsUp, 
  ThumbsDown, 
  MessageCircle, 
  Send,
  CheckCircle2,
  X 
} from 'lucide-react';

interface PreferenceFeedbackProps {
  isOpen: boolean;
  onClose: () => void;
  selectedModelId: string;
  selectedModelName: string;
  allModels: {
    id: string;
    name: string;
    response: string;
  }[];
  onSubmitFeedback: (feedback: PreferenceFeedbackData) => void;
  mode?: 'modal' | 'inline';
  className?: string;
}

export interface PreferenceFeedbackData {
  selectedModelId: string;
  rating?: number;
  reasons: string[];
  customFeedback?: string;
  comparisonNotes?: string;
}

const FEEDBACK_REASONS = [
  'More accurate information',
  'Better writing style',
  'More comprehensive coverage',
  'Clearer explanations',
  'Better structured response',
  'More helpful examples',
  'Faster response time',
  'More relevant to my needs',
  'Better formatting',
  'More creative approach',
];

export function PreferenceFeedback({
  isOpen,
  onClose,
  selectedModelId,
  selectedModelName,
  allModels,
  onSubmitFeedback,
  mode = 'modal',
  className,
}: PreferenceFeedbackProps) {
  const [rating, setRating] = useState<number | undefined>();
  const [selectedReasons, setSelectedReasons] = useState<string[]>([]);
  const [customFeedback, setCustomFeedback] = useState('');
  const [comparisonNotes, setComparisonNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleReasonToggle = (reason: string) => {
    setSelectedReasons(prev => 
      prev.includes(reason) 
        ? prev.filter(r => r !== reason)
        : [...prev, reason]
    );
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    
    try {
      const feedbackData: PreferenceFeedbackData = {
        selectedModelId,
        rating,
        reasons: selectedReasons,
        customFeedback: customFeedback.trim() || undefined,
        comparisonNotes: comparisonNotes.trim() || undefined,
      };

      await onSubmitFeedback(feedbackData);
      
      // Reset form
      setRating(undefined);
      setSelectedReasons([]);
      setCustomFeedback('');
      setComparisonNotes('');
      
      onClose();
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    // Reset form when closing
    setRating(undefined);
    setSelectedReasons([]);
    setCustomFeedback('');
    setComparisonNotes('');
    onClose();
  };

  const renderStarRating = () => (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          onClick={() => setRating(star)}
          className="text-2xl hover:scale-110 transition-transform"
        >
          {rating && star <= rating ? (
            <Star className="w-6 h-6 fill-amber-600 text-amber-600" />
          ) : (
            <StarOff className="w-6 h-6 text-neutral-fog hover:text-amber-600" />
          )}
        </button>
      ))}
      {rating && (
        <span className="ml-2 text-body-sm text-neutral-shadow">
          {rating} out of 5 stars
        </span>
      )}
    </div>
  );

  const renderReasonSelection = () => (
    <div className="space-y-3">
      <label className="block text-label font-medium text-neutral-charcoal">
        Why did you prefer this response? (Select all that apply)
      </label>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {FEEDBACK_REASONS.map((reason) => (
          <div
            key={reason}
            className={`p-sm rounded-md border cursor-pointer transition-all ${
              selectedReasons.includes(reason)
                ? 'border-ai-primary bg-ai-primary/10 text-ai-primary'
                : 'border-neutral-fog bg-neutral-white hover:border-neutral-shadow'
            }`}
            onClick={() => handleReasonToggle(reason)}
          >
            <div className="flex items-center gap-2">
              <div className={`w-4 h-4 rounded border flex items-center justify-center ${
                selectedReasons.includes(reason)
                  ? 'border-ai-primary bg-ai-primary'
                  : 'border-neutral-fog'
              }`}>
                {selectedReasons.includes(reason) && (
                  <CheckCircle2 className="w-3 h-3 text-white" />
                )}
              </div>
              <span className="text-body-sm">{reason}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderCustomFeedback = () => (
    <div className="space-y-2">
      <label className="block text-label font-medium text-neutral-charcoal">
        Additional feedback (optional)
      </label>
      <Textarea
        value={customFeedback}
        onChange={(e) => setCustomFeedback(e.target.value)}
        placeholder="Share any specific thoughts about why you preferred this response..."
        rows={3}
        className="w-full bg-neutral-white border border-neutral-fog rounded-md px-md py-sm text-body placeholder:text-neutral-shadow focus:border-ai-primary focus:ring-2 focus:ring-ai-primary/20 transition-colors resize-none"
      />
    </div>
  );

  const renderComparisonNotes = () => (
    <div className="space-y-2">
      <label className="block text-label font-medium text-neutral-charcoal">
        Comparison notes (optional)
      </label>
      <Textarea
        value={comparisonNotes}
        onChange={(e) => setComparisonNotes(e.target.value)}
        placeholder="How did this response compare to the others? What made it stand out?"
        rows={3}
        className="w-full bg-neutral-white border border-neutral-fog rounded-md px-md py-sm text-body placeholder:text-neutral-shadow focus:border-ai-primary focus:ring-2 focus:ring-ai-primary/20 transition-colors resize-none"
      />
    </div>
  );

  const content = (
    <div className={`space-y-lg ${className}`}>
      {/* Selected Model Info */}
      <Card className="bg-ai-primary/5 border-ai-primary/20">
        <CardContent className="p-md">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle2 className="w-5 h-5 text-ai-primary" />
            <span className="font-medium text-neutral-charcoal">
              You selected: {selectedModelName}
            </span>
          </div>
          <p className="text-body-sm text-neutral-shadow">
            Help us understand what made this response better than the others
          </p>
        </CardContent>
      </Card>

      {/* Star Rating */}
      <div className="space-y-2">
        <label className="block text-label font-medium text-neutral-charcoal">
          How would you rate this response?
        </label>
        {renderStarRating()}
      </div>

      {/* Reason Selection */}
      {renderReasonSelection()}

      {/* Custom Feedback */}
      {renderCustomFeedback()}

      {/* Comparison Notes */}
      {renderComparisonNotes()}

      {/* Action Buttons */}
      <div className="flex items-center gap-3 justify-end">
        <Button
          onClick={handleClose}
          variant="outline"
          disabled={isSubmitting}
        >
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          disabled={isSubmitting || selectedReasons.length === 0}
          className="bg-ai-primary text-white hover:bg-ai-primary/90"
        >
          {isSubmitting ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
              Submitting...
            </>
          ) : (
            <>
              <Send className="w-4 h-4 mr-2" />
              Submit Feedback
            </>
          )}
        </Button>
      </div>
    </div>
  );

  if (mode === 'inline') {
    return (
      <Card className={`bg-neutral-paper border border-neutral-fog ${className}`}>
        <CardContent className="p-lg">
          {content}
        </CardContent>
      </Card>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MessageCircle className="w-5 h-5 text-ai-primary" />
            Preference Feedback
          </DialogTitle>
          <DialogDescription>
            Your feedback helps us understand which models work best for different types of tasks
          </DialogDescription>
        </DialogHeader>
        
        {content}
      </DialogContent>
    </Dialog>
  );
}

