'use client'

import React, { useState } from 'react'
import { ChevronRight } from 'lucide-react'
import sampleDiffData from '@/lib/sample-diff-data.json'

interface DiffFile {
  name: string
  diff: string
  changes: string
}

interface DiffAnalysis {
  files: DiffFile[]
}

interface DiffViewerProps {
  xmlData?: string
  className?: string
}

const DEFAULT_DIFF_DATA: DiffAnalysis = sampleDiffData

function parseXmlData(xmlString: string): DiffAnalysis {
  const parser = new DOMParser()
  const xmlDoc = parser.parseFromString(xmlString, 'text/xml')
  const fileElements = xmlDoc.getElementsByTagName('file')
  
  const files: DiffFile[] = Array.from(fileElements).map(file => ({
    name: file.getElementsByTagName('name')[0]?.textContent || '',
    diff: file.getElementsByTagName('diff')[0]?.textContent || '',
    changes: file.getElementsByTagName('changes')[0]?.textContent || ''
  }))
  
  return { files }
}

function formatDiff(diff: string): React.ReactElement[] {
  const lines = diff.split('\n')
  return lines.map((line, index) => {
    let className = 'text-gray-400'
    
    if (line.startsWith('+')) {
      className = 'bg-green-900/20 text-green-400'
    } else if (line.startsWith('-')) {
      className = 'bg-red-900/20 text-red-400'
    } else if (line.startsWith('@@')) {
      className = 'text-blue-400'
    }
    
    return (
      <div key={index} className={`px-2 py-0.5 rounded ${className} font-mono text-sm leading-relaxed`}>
        {line}
      </div>
    )
  })
}

function formatChanges(changes: string): React.ReactElement {
  const items = changes.split('\n').filter(item => item.trim().startsWith('-'))
  
  if (items.length > 0) {
    return (
      <ul className="list-disc list-inside space-y-2 text-gray-300">
        {items.map((item, index) => (
          <li key={index} className="text-cyan-300">
            {item.substring(1).trim()}
          </li>
        ))}
      </ul>
    )
  }
  
  return <p className="text-gray-300">{changes}</p>
}

function getFileType(fileName: string): string {
  if (fileName.endsWith('.pyc')) return 'Binary'
  if (fileName.endsWith('.py')) return 'Python'
  if (fileName.endsWith('.js') || fileName.endsWith('.ts')) return 'JavaScript'
  if (fileName.endsWith('.tsx') || fileName.endsWith('.jsx')) return 'React'
  return 'Source'
}

export default function DiffViewer({ xmlData, className = '' }: DiffViewerProps) {
  const [expandedFiles, setExpandedFiles] = useState<Set<number>>(new Set([0]))
  
  // Use JSON data by default, XML parsing when xmlData is provided
  const data = xmlData ? parseXmlData(xmlData) : DEFAULT_DIFF_DATA
  
  const toggleFile = (index: number) => {
    const newExpanded = new Set(expandedFiles)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedFiles(newExpanded)
  }
  
  return (
    <div className={`w-full space-y-4 ${className}`}>
      <div className="space-y-4">
        {data.files.map((file, index) => {
          const isExpanded = expandedFiles.has(index)
          const isBinary = file.diff.includes('Binary files')
          const fileType = getFileType(file.name)
          
          return (
            <div
              key={index}
              className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden transition-all duration-300 hover:border-blue-500"
            >
              <div
                className="px-4 py-3 bg-gray-800 cursor-pointer flex items-center justify-between"
                onClick={() => toggleFile(index)}
              >
                <div className="flex items-center gap-3">
                  <span className="font-medium text-gray-200 text-sm">
                    {file.name}
                  </span>
                  <span className="text-xs px-2 py-1 rounded bg-gray-700 text-blue-300">
                    {fileType}
                  </span>
                </div>
                <ChevronRight
                  className={`h-4 w-4 text-blue-400 transition-transform duration-300 ${
                    isExpanded ? 'rotate-90' : ''
                  }`}
                />
              </div>
              
              {isExpanded && (
                <div className="border-t border-gray-800">
                  <div className="p-4 border-b border-gray-800">
                    <div className="text-blue-400 font-medium mb-2 text-xs uppercase tracking-wide">
                      Diff
                    </div>
                    
                    {isBinary ? (
                      <div className="bg-gray-800 p-3 rounded text-blue-300 italic text-sm">
                        {file.diff}
                      </div>
                    ) : (
                      <div className="bg-black p-3 rounded overflow-x-auto">
                        {formatDiff(file.diff)}
                      </div>
                    )}
                  </div>
                  
                  <div className="p-4">
                    <div className="text-blue-400 font-medium mb-2 text-xs uppercase tracking-wide">
                      Summary of Changes
                    </div>
                    <div className="leading-relaxed text-sm">
                      {formatChanges(file.changes)}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}