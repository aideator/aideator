'use client';

import React, { useState, useEffect, useRef, memo } from 'react';
import { motion } from 'framer-motion';

interface SimpleMarkdownProps {
  content: string;
  isStreaming?: boolean;
  className?: string;
}

export const SimpleMarkdown = memo(({ content, isStreaming = false, className = '' }: SimpleMarkdownProps) => {
  const [displayedContent, setDisplayedContent] = useState('');
  const previousContentRef = useRef('');
  const streamingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Handle streaming animation
  useEffect(() => {
    if (isStreaming && content && content !== previousContentRef.current) {
      // Clear any existing timeout
      if (streamingTimeoutRef.current) {
        clearTimeout(streamingTimeoutRef.current);
      }
      
      // Add new content with a brief delay to show animation
      streamingTimeoutRef.current = setTimeout(() => {
        setDisplayedContent(content);
        previousContentRef.current = content;
      }, 50); // Very brief delay for smooth appearance
    } else if (!isStreaming && content) {
      // Not streaming, show content immediately
      setDisplayedContent(content);
      previousContentRef.current = content;
    }
  }, [content, isStreaming]);

  // Clean up timeout on unmount
  useEffect(() => {
    return () => {
      if (streamingTimeoutRef.current) {
        clearTimeout(streamingTimeoutRef.current);
      }
    };
  }, []);

  // Simple formatting function
  const formatContent = (text: string) => {
    return text
      .split('\n')
      .map((line, index) => {
        // Basic markdown-like formatting
        if (line.startsWith('# ')) {
          return (
            <h1 key={index} className="text-lg font-bold mt-4 mb-2 text-gray-900">
              {line.substring(2)}
            </h1>
          );
        }
        if (line.startsWith('## ')) {
          return (
            <h2 key={index} className="text-base font-bold mt-3 mb-2 text-gray-800">
              {line.substring(3)}
            </h2>
          );
        }
        if (line.startsWith('- ') || line.startsWith('* ')) {
          return (
            <li key={index} className="text-sm text-gray-700 ml-4 list-disc">
              {line.substring(2)}
            </li>
          );
        }
        if (line.trim() === '') {
          return <br key={index} />;
        }
        return (
          <p key={index} className="text-sm text-gray-700 mb-2 leading-relaxed">
            {line}
          </p>
        );
      });
  };

  return (
    <div className={`prose prose-xs max-w-none markdown-content ${isStreaming ? 'streaming' : ''} ${className}`} style={{ fontSize: '0.75rem' }}>
      <motion.div
        key={displayedContent.length} // Re-animate when content changes
        initial={isStreaming ? { opacity: 0.7, y: 2 } : { opacity: 1, y: 0 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
      >
        <div className="space-y-1">
          {formatContent(displayedContent)}
        </div>
      </motion.div>
      {/* Add blinking cursor for active streaming */}
      {isStreaming && (
        <motion.span 
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          transition={{ duration: 0.2 }}
          className="streaming-cursor"
        />
      )}
    </div>
  );
});

SimpleMarkdown.displayName = 'SimpleMarkdown';

export default SimpleMarkdown;