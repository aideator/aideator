'use client';

import React, { useMemo, memo } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
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
  // Parse content into blocks for efficient rendering
  const blocks = useMemo(() => {
    // Split content by double newlines to create blocks
    const parts = content.split(/\n\n+/);
    return parts.map((part, index) => ({
      id: `block-${index}`,
      content: part,
      isLast: index === parts.length - 1
    }));
  }, [content]);

  const components = useMemo(() => ({
    code: CodeBlock,
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
    blockquote: ({ children }: { children: React.ReactNode }) => (
      <blockquote className="border-l-4 border-gray-300 pl-3 italic my-2 text-gray-600" style={{ fontSize: '0.75rem' }}>
        {children}
      </blockquote>
    ),
    a: ({ children, href }: { children: React.ReactNode; href?: string }) => (
      <a 
        href={href} 
        className="text-blue-600 hover:text-blue-800 underline transition-colors" 
        target="_blank" 
        rel="noopener noreferrer"
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
      {blocks.map((block, index) => (
        <motion.div
          key={block.id}
          initial={isStreaming && block.isLast ? { opacity: 0.7 } : { opacity: 1 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.15 }}
          className={isStreaming && block.isLast ? 'streaming-text' : ''}
        >
          <ReactMarkdown
            remarkPlugins={[remarkGfm, remarkBreaks]}
            components={components}
          >
            {block.content}
          </ReactMarkdown>
        </motion.div>
      ))}
    </div>
  );
});

MemoizedMarkdown.displayName = 'MemoizedMarkdown';

export default MemoizedMarkdown;