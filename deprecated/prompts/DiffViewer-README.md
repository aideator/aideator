# DiffViewer React Component

A React TypeScript component that renders XML-formatted diff analysis data in an interactive, collapsible interface.

## Features

- 📄 Displays file diffs and change summaries from XML data
- 🎨 Dark theme with VS Code-inspired styling using Tailwind CSS
- 🔄 Interactive expand/collapse for each file
- 🏷️ File type detection and labeling
- 📱 Responsive design
- 🎯 TypeScript support with proper interfaces

## Usage

### Basic Usage (Default Demo Data)

```tsx
import DiffViewer from './DiffViewer'

function App() {
  return <DiffViewer />
}
```

### With Custom XML Data

```tsx
import DiffViewer from './DiffViewer'

const xmlData = `<diff_analysis>
  <file>
    <name>src/components/Button.tsx</name>
    <diff>@@ -1,5 +1,5 @@
 import React from 'react'
 
-export function Button({ children }: { children: React.ReactNode }) {
+export function Button({ children, onClick }: { children: React.ReactNode, onClick?: () => void }) {
   return (
-    <button className="bg-blue-500 text-white px-4 py-2 rounded">
+    <button className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded transition-colors" onClick={onClick}>
       {children}
     </button>
   )
 }</diff>
    <changes>- Added optional onClick prop to Button component
- Added hover state styling with transition-colors
- Improved component props interface with onClick handler</changes>
  </file>
</diff_analysis>`

function App() {
  return <DiffViewer xmlData={xmlData} />
}
```

### With Custom Styling

```tsx
import DiffViewer from './DiffViewer'

function App() {
  return (
    <DiffViewer 
      xmlData={customXmlData}
      className="my-8 px-4"
    />
  )
}
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `xmlData` | `string` | Demo data | XML string containing diff analysis data |
| `className` | `string` | `''` | Additional CSS classes to apply to the container |

## XML Data Format

The component expects XML data in the following format:

```xml
<diff_analysis>
  <file>
    <name>path/to/file.ext</name>
    <diff>Git diff content here...</diff>
    <changes>Human-readable summary of changes...</changes>
  </file>
  <!-- More files... -->
</diff_analysis>
```

### XML Structure

- `<diff_analysis>` - Root element containing all files
- `<file>` - Container for each individual file's data
- `<name>` - File path and name
- `<diff>` - Git diff output (raw diff format)
- `<changes>` - Human-readable description of what changed

## File Type Detection

The component automatically detects file types based on file extensions:

- `.py` → Python
- `.js`, `.ts` → JavaScript  
- `.jsx`, `.tsx` → React
- `.pyc` → Binary
- Others → Source

Binary files are handled differently, showing a notice instead of diff syntax highlighting.

## Styling

The component uses Tailwind CSS classes and follows a dark theme. Key styling features:

- **Colors**: Blue accents, gray backgrounds, syntax highlighting
- **Typography**: Monospace fonts for code, system fonts for text
- **Animations**: Smooth expand/collapse transitions
- **Responsive**: Adapts to different screen sizes

## Dependencies

- React 18+
- TypeScript
- Tailwind CSS
- Lucide React (for icons)

## Example Integration

```tsx
// In a Next.js page or component
import { useState } from 'react'
import DiffViewer from '@/components/DiffViewer'

export default function DiffAnalysisPage() {
  const [xmlData, setXmlData] = useState<string>('')
  
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        setXmlData(e.target?.result as string)
      }
      reader.readAsText(file)
    }
  }
  
  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="mb-8">
        <input 
          type="file" 
          accept=".xml"
          onChange={handleFileUpload}
          className="mb-4"
        />
      </div>
      
      <DiffViewer xmlData={xmlData} />
    </div>
  )
}
```

## Browser Support

- Modern browsers with ES2015+ support
- DOMParser API (widely supported)
- CSS Grid and Flexbox support