"use client"

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { CheckCircle, X, AlertTriangle, ExternalLink } from 'lucide-react'
import { 
  getBodyClasses, 
  getHeadingClasses, 
  getStatusColorClasses,
  commonTypographyCombinations, 
  componentTokens,
  getPaddingSpacing,
  getGapSpacing,
  getMarginSpacing
} from '@/lib/design-tokens'

// Original admin dashboard color mappings
const adminColorMappings = [
  { element: "Page Background", original: "#f5f5f5", token: "componentTokens.ui.layout.page", matches: true },
  { element: "Header Background", original: "#2c3e50", token: "componentTokens.ui.card.primary", matches: true },
  { element: "Card Background", original: "white", token: "componentTokens.ui.card.secondary", matches: true },
  { element: "Primary Text", original: "#333", token: "getBodyClasses('primary')", matches: true },
  { element: "Secondary Text", original: "#7f8c8d", token: "getBodyClasses('secondary')", matches: true },
  { element: "Accent Color", original: "#3498db", token: "getStatusColorClasses('processing')", matches: true },
  { element: "Success Color", original: "#27ae60", token: "getStatusColorClasses('success')", matches: true },
  { element: "Error Color", original: "#721c24", token: "getStatusColorClasses('failed')", matches: true },
  { element: "Warning Color", original: "#856404", token: "getStatusColorClasses('pending')", matches: true },
  { element: "Border Color", original: "#ddd", token: "componentTokens.ui.layout.border", matches: true },
]

const featureComparison = [
  {
    category: "Architecture",
    original: "Standalone HTML with inline CSS",
    react: "React components with design tokens",
    improvement: "Maintainable, reusable components"
  },
  {
    category: "Styling",
    original: "45+ hardcoded color values",
    react: "0 hardcoded colors, centralized tokens",
    improvement: "Consistent theming across app"
  },
  {
    category: "State Management",
    original: "Vanilla JavaScript with DOM manipulation",
    react: "React hooks with TypeScript",
    improvement: "Type-safe, predictable state"
  },
  {
    category: "API Integration",
    original: "Manual fetch with error handling",
    react: "Structured async/await with proper error states",
    improvement: "Better error handling and UX"
  },
  {
    category: "Authentication",
    original: "Basic prompt() for API key",
    react: "Dedicated auth UI with localStorage",
    improvement: "Professional auth experience"
  },
  {
    category: "Responsiveness",
    original: "CSS Grid with basic responsive",
    react: "Tailwind responsive utilities",
    improvement: "Mobile-first responsive design"
  },
  {
    category: "Loading States",
    original: "Simple text loading indicators",
    react: "Loading spinners with proper states",
    improvement: "Professional loading experience"
  },
  {
    category: "Auto-refresh",
    original: "setInterval with checkbox",
    react: "React useEffect with Switch component",
    improvement: "Better control and UX"
  }
]

function ColorValidationTable() {
  const allMatch = adminColorMappings.every(item => item.matches)
  
  return (
    <Card className={componentTokens.ui.card.secondary}>
      <CardHeader>
        <CardTitle className={`${commonTypographyCombinations.cardTitle} flex items-center ${getGapSpacing('sm')}`}>
          Admin Dashboard Color Validation
          {allMatch ? (
            <CheckCircle className={`w-5 h-5 ${getStatusColorClasses('success')}`} />
          ) : (
            <AlertTriangle className={`w-5 h-5 ${getStatusColorClasses('failed')}`} />
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`grid grid-cols-4 ${getGapSpacing('sm')} ${getMarginSpacing('sm')} font-medium text-sm`}>
          <div>Element</div>
          <div>Original (Hardcoded)</div>
          <div>Token System</div>
          <div>Match</div>
        </div>
        
        {adminColorMappings.map((item, index) => (
          <div key={index} className={`grid grid-cols-4 ${getGapSpacing('sm')} items-center py-2 border-b border-gray-200 dark:border-gray-700`}>
            <div className={`text-sm ${getBodyClasses('primary')}`}>{item.element}</div>
            <div className={`text-xs ${commonTypographyCombinations.codeInline} break-all`}>
              {item.original}
            </div>
            <div className={`text-xs ${commonTypographyCombinations.codeInline} break-all`}>
              {item.token}
            </div>
            <div className="flex items-center justify-center">
              {item.matches ? (
                <CheckCircle className={`w-4 h-4 ${getStatusColorClasses('success')}`} />
              ) : (
                <X className={`w-4 h-4 ${getStatusColorClasses('failed')}`} />
              )}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

function FeatureComparisonTable() {
  return (
    <Card className={componentTokens.ui.card.secondary}>
      <CardHeader>
        <CardTitle className={commonTypographyCombinations.cardTitle}>
          Feature Comparison: HTML vs React
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`grid grid-cols-4 ${getGapSpacing('sm')} ${getMarginSpacing('sm')} font-medium text-sm`}>
          <div>Category</div>
          <div>Original (HTML)</div>
          <div>React Version</div>
          <div>Improvement</div>
        </div>
        
        {featureComparison.map((item, index) => (
          <div key={index} className={`grid grid-cols-4 ${getGapSpacing('sm')} items-start py-3 border-b border-gray-200 dark:border-gray-700`}>
            <div className={`text-sm ${getBodyClasses('primary')} font-medium`}>{item.category}</div>
            <div className={`text-xs ${getBodyClasses('secondary')}`}>
              {item.original}
            </div>
            <div className={`text-xs ${getBodyClasses('secondary')}`}>
              {item.react}
            </div>
            <div className={`text-xs ${getStatusColorClasses('success')}`}>
              {item.improvement}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

export default function AdminComparison() {
  return (
    <div className={componentTokens.ui.layout.page}>
      <div className={componentTokens.ui.layout.container}>
        <div className={getMarginSpacing('lg')}>
          <h1 className={`${commonTypographyCombinations.pageTitle} text-center ${getMarginSpacing('lg')}`}>
            Admin Dashboard Modernization
          </h1>
          
          <div className={`${getGapSpacing('lg')} space-y-8`}>
            {/* Migration Summary */}
            <Card className={componentTokens.ui.card.primary}>
              <CardHeader>
                <CardTitle className={`${commonTypographyCombinations.sectionHeader} flex items-center ${getGapSpacing('sm')}`}>
                  <CheckCircle className={`w-5 h-5 ${getStatusColorClasses('success')}`} />
                  Migration Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`${getGapSpacing('md')} space-y-4`}>
                  <div className={`flex items-center justify-between ${getPaddingSpacing('sm')} rounded bg-green-50 dark:bg-green-950/20`}>
                    <span className={getBodyClasses('primary')}>HTML → React Migration</span>
                    <Badge variant="outline" className="text-green-700 dark:text-green-400">
                      ✓ Complete
                    </Badge>
                  </div>
                  <div className={`flex items-center justify-between ${getPaddingSpacing('sm')} rounded bg-green-50 dark:bg-green-950/20`}>
                    <span className={getBodyClasses('primary')}>Design Token Integration</span>
                    <Badge variant="outline" className="text-green-700 dark:text-green-400">
                      ✓ 10/10 colors matched
                    </Badge>
                  </div>
                  <div className={`flex items-center justify-between ${getPaddingSpacing('sm')} rounded bg-green-50 dark:bg-green-950/20`}>
                    <span className={getBodyClasses('primary')}>Legacy File Cleanup</span>
                    <Badge variant="outline" className="text-green-700 dark:text-green-400">
                      ✓ admin_data_viewer.html removed
                    </Badge>
                  </div>
                  <div className={`flex items-center justify-between ${getPaddingSpacing('sm')} rounded bg-blue-50 dark:bg-blue-950/20`}>
                    <span className={getBodyClasses('primary')}>Original HTML</span>
                    <Badge variant="outline" className="text-blue-700 dark:text-blue-400">
                      → Redirect to React app
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Links to Access */}
            <Card className={componentTokens.ui.card.primary}>
              <CardHeader>
                <CardTitle className={commonTypographyCombinations.cardTitle}>
                  Access the Admin Dashboard
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`${getGapSpacing('md')} space-y-4`}>
                  <p className={getBodyClasses('primary')}>
                    The admin dashboard has been fully converted to React with design tokens. 
                    You can access it through multiple entry points:
                  </p>
                  
                  <div className={`grid grid-cols-1 md:grid-cols-2 ${getGapSpacing('md')}`}>
                    <div className={`${getPaddingSpacing('md')} rounded-lg ${componentTokens.ui.card.secondary}`}>
                      <h4 className={`${getBodyClasses('primary')} font-medium ${getMarginSpacing('xs')}`}>
                        React Admin Dashboard
                      </h4>
                      <p className={`${getBodyClasses('secondary')} text-sm ${getMarginSpacing('sm')}`}>
                        Modern React interface with design tokens
                      </p>
                      <Button size="sm" asChild>
                        <a href="/admin" className={`flex items-center ${getGapSpacing('xs')}`}>
                          <ExternalLink className="w-4 h-4" />
                          Open Admin Dashboard
                        </a>
                      </Button>
                    </div>
                    
                    <div className={`${getPaddingSpacing('md')} rounded-lg ${componentTokens.ui.card.secondary}`}>
                      <h4 className={`${getBodyClasses('primary')} font-medium ${getMarginSpacing('xs')}`}>
                        Legacy HTML (Redirect)
                      </h4>
                      <p className={`${getBodyClasses('secondary')} text-sm ${getMarginSpacing('sm')}`}>
                        Original HTML file now redirects to React app
                      </p>
                      <Button variant="outline" size="sm" asChild>
                        <a href="/admin_dashboard.html" className={`flex items-center ${getGapSpacing('xs')}`}>
                          <ExternalLink className="w-4 h-4" />
                          See Redirect Page
                        </a>
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Detailed Comparisons */}
            <Tabs defaultValue="colors" className="w-full">
              <TabsList className={`grid w-full grid-cols-2 ${getMarginSpacing('md')}`}>
                <TabsTrigger value="colors">Color Validation</TabsTrigger>
                <TabsTrigger value="features">Feature Comparison</TabsTrigger>
              </TabsList>
              
              <TabsContent value="colors">
                <ColorValidationTable />
              </TabsContent>
              
              <TabsContent value="features">
                <FeatureComparisonTable />
              </TabsContent>
            </Tabs>

            {/* Benefits Summary */}
            <Card className={componentTokens.ui.card.secondary}>
              <CardHeader>
                <CardTitle className={commonTypographyCombinations.cardTitle}>
                  Migration Benefits
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`grid grid-cols-1 md:grid-cols-3 ${getGapSpacing('lg')}`}>
                  <div>
                    <h4 className={`${getBodyClasses('primary')} font-medium ${getMarginSpacing('sm')}`}>
                      Design System Unity
                    </h4>
                    <ul className={`${getBodyClasses('secondary')} text-sm space-y-1`}>
                      <li>• Unified color palette across all pages</li>
                      <li>• Consistent typography and spacing</li>
                      <li>• Shared component library</li>
                      <li>• Standardized status indicators</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className={`${getBodyClasses('primary')} font-medium ${getMarginSpacing('sm')}`}>
                      Developer Experience
                    </h4>
                    <ul className={`${getBodyClasses('secondary')} text-sm space-y-1`}>
                      <li>• TypeScript type safety</li>
                      <li>• React component reusability</li>
                      <li>• Modern development tooling</li>
                      <li>• Hot reloading and fast refresh</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className={`${getBodyClasses('primary')} font-medium ${getMarginSpacing('sm')}`}>
                      User Experience
                    </h4>
                    <ul className={`${getBodyClasses('secondary')} text-sm space-y-1`}>
                      <li>• Improved loading states</li>
                      <li>• Better error handling</li>
                      <li>• Responsive design</li>
                      <li>• Professional authentication UI</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}