'use client'

import { useState } from 'react'
import { ChevronRight } from 'lucide-react'

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

const DEFAULT_XML_DATA = `<diff_analysis>
  <file>
    <name>__pycache__/test_hello.cpython-311-pytest-7.4.3.pyc</name>
    <diff>index 2c9f1c0..d41c6b0 100644
Binary files a/__pycache__/test_hello.cpython-311-pytest-7.4.3.pyc and b/__pycache__/test_hello.cpython-311-pytest-7.4.3.pyc differ</diff>
    <changes>Binary file updated - This is a compiled Python test bytecode file that was automatically regenerated, likely when the test suite was run after hello.py was modified. No manual changes were made to this file.</changes>
  </file>
  <file>
    <name>hello.py</name>
    <diff>@@ -3,8 +3,8 @@ import time

def greet(name="World"):
-    """Generate a greeting message."""
-    return f"Hello, {name}!"
+    """Generate an exciting greeting message."""
+    return f"🎉 Woohoo! Hello, awesome {name}! Let's rock this day! 🚀"</diff>
    <changes>- Modified the docstring of the greet() function from "Generate a greeting message." to "Generate an exciting greeting message."
- Changed the greeting message format from a simple "Hello, {name}!" to an enthusiastic "🎉 Woohoo! Hello, awesome {name}! Let's rock this day! 🚀" with emojis and more energetic language
- The function signature remains unchanged, still accepting an optional name parameter with "World" as the default</changes>
  </file>
</diff_analysis>`

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

function formatDiff(diff: string): JSX.Element[] {
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

function formatChanges(changes: string): JSX.Element {
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
  
  const data = parseXmlData(xmlData || DEFAULT_XML_DATA)
  
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
    <div className={`max-w-4xl mx-auto space-y-5 ${className}`}>
      <h1 className="text-2xl font-semibold text-blue-400 mb-8 flex items-center gap-2">
        📄 Diff Analysis Viewer
      </h1>
      
      <div className="space-y-5">
        {data.files.map((file, index) => {
          const isExpanded = expandedFiles.has(index)
          const isBinary = file.diff.includes('Binary files')
          const fileType = getFileType(file.name)
          
          return (
            <div
              key={index}
              className="bg-gray-800 border border-gray-600 rounded-lg overflow-hidden transition-all duration-300 hover:border-blue-500 hover:shadow-lg hover:shadow-blue-500/20"
            >
              <div
                className="px-5 py-4 bg-gray-700 cursor-pointer flex items-center justify-between"
                onClick={() => toggleFile(index)}
              >
                <div className="flex items-center gap-3">
                  <span className="font-semibold text-yellow-300 text-base">
                    {file.name}
                  </span>
                  <span className="text-xs px-2 py-1 rounded bg-gray-600 text-blue-300">
                    {fileType}
                  </span>
                </div>
                <ChevronRight
                  className={`h-5 w-5 text-blue-400 transition-transform duration-300 ${
                    isExpanded ? 'rotate-90' : ''
                  }`}
                />
              </div>
              
              {isExpanded && (
                <div className="border-t border-gray-600">
                  <div className="p-5 border-b border-gray-600">
                    <div className="text-blue-400 font-semibold mb-3 text-sm uppercase tracking-wide">
                      Diff
                    </div>
                    
                    {isBinary ? (
                      <div className="bg-gray-600 p-4 rounded text-blue-300 italic">
                        {file.diff}
                      </div>
                    ) : (
                      <div className="bg-gray-900 p-4 rounded overflow-x-auto">
                        {formatDiff(file.diff)}
                      </div>
                    )}
                  </div>
                  
                  <div className="p-5">
                    <div className="text-blue-400 font-semibold mb-3 text-sm uppercase tracking-wide">
                      Summary of Changes
                    </div>
                    <div className="leading-relaxed">
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