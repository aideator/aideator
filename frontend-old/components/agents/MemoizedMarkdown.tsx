'use client';

import React, { useMemo, memo, useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { motion } from 'framer-motion';

interface CodeProps {
  node?: React.ReactNode;
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
}

interface MemoizedMarkdownProps {
  content: string;
  isStreaming?: boolean;
  className?: string;
}

// Memoized code component for better performance
const CodeBlock = memo(({ inline, className, children, ...props }: CodeProps) => {
  const match = /language-(\w+)/.exec(className || '');
  const language = match ? match[1] : '';
  
  if (!inline && language) {
    return (
      <div className="relative group my-4">
        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={() => {
              const code = String(children).replace(/\n$/, '');
              navigator.clipboard.writeText(code);
            }}
            className="text-xs bg-gray-700 hover:bg-gray-600 text-white px-2 py-1 rounded transition-colors"
          >
            Copy
          </button>
        </div>
        <SyntaxHighlighter
          style={oneDark}
          language={language}
          PreTag="div"
          className="rounded-lg !bg-gray-900"
          customStyle={{ fontSize: '0.7rem', lineHeight: '1.2' }}
          {...props}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      </div>
    );
  }
  
  return (
    <code className="bg-gray-100 px-1 py-0.5 rounded font-mono" style={{ fontSize: '0.7rem' }} {...props}>
      {children}
    </code>
  );
});

CodeBlock.displayName = 'CodeBlock';

// Main markdown component with memoization
export const MemoizedMarkdown = memo(({ content, isStreaming = false, className = '' }: MemoizedMarkdownProps) => {
  const [displayedContent, setDisplayedContent] = useState('');
  const [isCurrentlyStreaming, setIsCurrentlyStreaming] = useState(false);
  const [markdownError, setMarkdownError] = useState(false);
  const previousContentRef = useRef('');
  const streamingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Handle streaming animation
  useEffect(() => {
    if (isStreaming && content && content !== previousContentRef.current) {
      setIsCurrentlyStreaming(true);
      
      // Clear any existing timeout
      if (streamingTimeoutRef.current) {
        clearTimeout(streamingTimeoutRef.current);
      }
      
      // Get the new content that was added
      const newContent = content.slice(previousContentRef.current.length);
      
      if (newContent) {
        // Add new content with a brief delay to show animation
        streamingTimeoutRef.current = setTimeout(() => {
          setDisplayedContent(content);
          previousContentRef.current = content;
        }, 50); // Very brief delay for smooth appearance
      }
    } else if (!isStreaming && content) {
      // Not streaming, show content immediately
      setDisplayedContent(content);
      setIsCurrentlyStreaming(false);
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

  const components = useMemo(() => ({
    code: CodeBlock as any,
    h1: ({ children }: { children: React.ReactNode }) => (
      <h1 className="font-bold mt-3 mb-2 text-gray-900" style={{ fontSize: '1rem' }}>{children}</h1>
    ),
    h2: ({ children }: { children: React.ReactNode }) => (
      <h2 className="font-bold mt-2.5 mb-1.5 text-gray-800" style={{ fontSize: '0.875rem' }}>{children}</h2>
    ),
    h3: ({ children }: { children: React.ReactNode }) => (
      <h3 className="font-semibold mt-2 mb-1 text-gray-800" style={{ fontSize: '0.8rem' }}>{children}</h3>
    ),
    p: ({ children }: { children: React.ReactNode }) => (
      <p className="mb-2 leading-normal text-gray-700" style={{ fontSize: '0.75rem', lineHeight: '1.5' }}>{children}</p>
    ),
    ul: ({ children }: { children: React.ReactNode }) => (
      <ul className="list-disc list-inside mb-2 space-y-0.5" style={{ fontSize: '0.75rem' }}>{children}</ul>
    ),
    ol: ({ children }: { children: React.ReactNode }) => (
      <ol className="list-decimal list-inside mb-2 space-y-0.5" style={{ fontSize: '0.75rem' }}>{children}</ol>
    ),
    li: ({ children }: { children: React.ReactNode }) => (
      <li className="text-gray-700" style={{ fontSize: '0.75rem' }}>{children}</li>
    ),
    blockquote: ({ children, ...props }: React.ComponentPropsWithoutRef<'blockquote'>) => (
      <blockquote className="border-l-4 border-gray-300 pl-3 italic my-2 text-gray-600" style={{ fontSize: '0.75rem' }} {...props}>
        {children}
      </blockquote>
    ),
    a: ({ children, href, ...props }: React.ComponentPropsWithoutRef<'a'>) => (
      <a 
        href={href} 
        className="text-blue-600 hover:text-blue-800 underline transition-colors" 
        target="_blank" 
        rel="noopener noreferrer"
        {...props}
      >
        {children}
      </a>
    ),
    table: ({ children }: { children: React.ReactNode }) => (
      <div className="overflow-x-auto my-4">
        <table className="min-w-full border-collapse border border-gray-300">
          {children}
        </table>
      </div>
    ),
    th: ({ children }: { children: React.ReactNode }) => (
      <th className="border border-gray-300 px-2 py-1 bg-gray-100 font-semibold text-left" style={{ fontSize: '0.7rem' }}>
        {children}
      </th>
    ),
    td: ({ children }: { children: React.ReactNode }) => (
      <td className="border border-gray-300 px-2 py-1" style={{ fontSize: '0.7rem' }}>{children}</td>
    ),
    pre: ({ children }: { children: React.ReactNode }) => (
      <pre className="whitespace-pre-wrap font-mono text-xs bg-gray-100 p-2 rounded my-2 overflow-x-auto">{children}</pre>
    ),
  }), []);

  return (
    <div className={`prose prose-xs max-w-none markdown-content ${isStreaming ? 'streaming' : ''} ${className}`} style={{ fontSize: '0.75rem' }}>
      <motion.div
        key={displayedContent.length} // Re-animate when content changes
        initial={isStreaming ? { opacity: 0.7, y: 2 } : { opacity: 1, y: 0 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
      >
        {markdownError ? (
          // Fallback to simple pre-formatted text if markdown fails
          <pre className="whitespace-pre-wrap text-sm font-mono leading-relaxed text-gray-700">
            {displayedContent}
          </pre>
        ) : (
          <ReactMarkdown
            components={components as any}
          >
            {displayedContent}
          </ReactMarkdown>
        )}
      </motion.div>
      {/* Add blinking cursor for active streaming */}
      {isStreaming && displayedContent.length > 0 && (
        <motion.span 
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          transition={{ duration: 0.2 }}
          className="streaming-cursor inline-block align-middle"
          style={{ marginLeft: '2px' }}
        />
      )}
    </div>
  );
});

MemoizedMarkdown.displayName = 'MemoizedMarkdown';

