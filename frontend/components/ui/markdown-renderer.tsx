'use client'

import React from 'react'
import ReactMarkdown from 'react-markdown'
import { cn } from '@/lib/utils'

interface MarkdownRendererProps {
  content: string
  className?: string
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <div className={cn("prose prose-invert prose-sm max-w-none", className)}>
      <ReactMarkdown
        components={{
          // Customize heading styles to match app design
          h1: ({ children }) => (
            <h1 className="text-lg font-semibold text-white mb-2 mt-3 first:mt-0">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-base font-semibold text-white mb-2 mt-3 first:mt-0">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-sm font-semibold text-white mb-1 mt-2 first:mt-0">
              {children}
            </h3>
          ),
          // Customize paragraph styles
          p: ({ children }) => (
            <p className="text-gray-300 text-sm leading-relaxed mb-2 last:mb-0">
              {children}
            </p>
          ),
          // Customize list styles
          ul: ({ children }) => (
            <ul className="text-gray-300 text-sm space-y-1 mb-2 pl-4">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="text-gray-300 text-sm space-y-1 mb-2 pl-4">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="text-gray-300 text-sm leading-relaxed">
              {children}
            </li>
          ),
          // Customize code styles
          code: ({ children, className }) => {
            const isInline = !className
            if (isInline) {
              return (
                <code className="bg-gray-800 text-cyan-400 px-1 py-0.5 rounded text-xs font-mono">
                  {children}
                </code>
              )
            }
            // Block code
            return (
              <code className="block bg-gray-800 text-cyan-400 p-2 rounded text-xs font-mono overflow-x-auto">
                {children}
              </code>
            )
          },
          // Customize blockquote styles
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-gray-600 pl-3 text-gray-400 italic mb-2">
              {children}
            </blockquote>
          ),
          // Customize link styles
          a: ({ children, href }) => (
            <a
              href={href}
              className="text-cyan-400 hover:text-cyan-300 underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              {children}
            </a>
          ),
          // Customize strong/bold styles
          strong: ({ children }) => (
            <strong className="text-white font-semibold">{children}</strong>
          ),
          // Customize emphasis/italic styles
          em: ({ children }) => (
            <em className="text-gray-300 italic">{children}</em>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}