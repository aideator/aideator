"use client"

import { 
  getAgentColorClasses,
  getOutputTypeColorClasses,
  getStatusColorClasses,
  getBodyClasses,
  getHeadingClasses,
  commonTypographyCombinations,
  componentTokens,
  getPaddingSpacing,
  getGapSpacing,
  getMarginSpacing
} from "@/lib/design-tokens"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, X, AlertTriangle } from "lucide-react"

// Original hardcoded values from agent-output-viewer.tsx for comparison
const originalAgentColors = {
  1: 'border-cyan-500/40 bg-cyan-50 dark:bg-cyan-950/20',
  2: 'border-violet-500/40 bg-violet-50 dark:bg-violet-950/20',
  3: 'border-orange-500/40 bg-orange-50 dark:bg-orange-950/20',
  4: 'border-rose-500/40 bg-rose-50 dark:bg-rose-950/20',
  5: 'border-emerald-500/40 bg-emerald-50 dark:bg-emerald-950/20',
  6: 'border-blue-500/40 bg-blue-50 dark:bg-blue-950/20',
}

const originalOutputTypeColors = {
  'assistant_response': 'border-green-500/40 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
  'system_status': 'border-blue-500/40 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
  'debug_info': 'border-purple-500/40 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400',
  'error': 'border-red-500/40 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
  'diffs': 'border-yellow-500/40 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
  'default': 'border-gray-500/40 bg-gray-100 dark:bg-gray-800/50 text-gray-700 dark:text-gray-400',
}

interface ComparisonRowProps {
  label: string
  original: string
  token: string
  isValid: boolean
}

function ComparisonRow({ label, original, token, isValid }: ComparisonRowProps) {
  return (
    <div className={`grid grid-cols-4 ${getGapSpacing('sm')} items-center py-2 border-b border-gray-200 dark:border-gray-700`}>
      <div className={`text-sm ${getBodyClasses('primary')}`}>{label}</div>
      <div className={`text-xs ${commonTypographyCombinations.codeInline} break-all`}>
        {original}
      </div>
      <div className={`text-xs ${commonTypographyCombinations.codeInline} break-all`}>
        {token}
      </div>
      <div className="flex items-center justify-center">
        {isValid ? (
          <CheckCircle className={`w-4 h-4 ${getStatusColorClasses('success')}`} />
        ) : (
          <X className={`w-4 h-4 ${getStatusColorClasses('failed')}`} />
        )}
      </div>
    </div>
  )
}

function AgentColorComparison() {
  const agentIds = [1, 2, 3, 4, 5, 6]
  
  return (
    <Card className={componentTokens.ui.card.secondary}>
      <CardHeader>
        <CardTitle className={commonTypographyCombinations.cardTitle}>
          Agent Color System Validation
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`grid grid-cols-4 ${getGapSpacing('sm')} ${getMarginSpacing('sm')} font-medium text-sm`}>
          <div>Agent</div>
          <div>Original (Hardcoded)</div>
          <div>Token System</div>
          <div>Match</div>
        </div>
        
        {agentIds.map(agentId => {
          const originalColor = originalAgentColors[agentId as keyof typeof originalAgentColors] || 'border-gray-500/20 bg-gray-50 dark:bg-gray-950/20'
          const tokenColor = getAgentColorClasses(agentId)
          const isValid = originalColor === tokenColor
          
          return (
            <ComparisonRow
              key={agentId}
              label={`Agent ${agentId}`}
              original={originalColor}
              token={tokenColor}
              isValid={isValid}
            />
          )
        })}
      </CardContent>
    </Card>
  )
}

function OutputTypeColorComparison() {
  const outputTypes = ['assistant_response', 'system_status', 'debug_info', 'error', 'diffs', 'unknown_type']
  
  return (
    <Card className={componentTokens.ui.card.secondary}>
      <CardHeader>
        <CardTitle className={commonTypographyCombinations.cardTitle}>
          Output Type Color System Validation
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`grid grid-cols-4 ${getGapSpacing('sm')} ${getMarginSpacing('sm')} font-medium text-sm`}>
          <div>Output Type</div>
          <div>Original (Hardcoded)</div>
          <div>Token System</div>
          <div>Match</div>
        </div>
        
        {outputTypes.map(outputType => {
          const originalColor = originalOutputTypeColors[outputType as keyof typeof originalOutputTypeColors] || originalOutputTypeColors.default
          const tokenColor = getOutputTypeColorClasses(outputType)
          const isValid = originalColor === tokenColor
          
          return (
            <ComparisonRow
              key={outputType}
              label={outputType}
              original={originalColor}
              token={tokenColor}
              isValid={isValid}
            />
          )
        })}
      </CardContent>
    </Card>
  )
}

function VisualColorComparison() {
  return (
    <Card className={componentTokens.ui.card.secondary}>
      <CardHeader>
        <CardTitle className={commonTypographyCombinations.cardTitle}>
          Visual Color Comparison
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`${getGapSpacing('lg')} space-y-6`}>
          {/* Agent Colors Visual */}
          <div>
            <h4 className={`${getBodyClasses('primary')} font-medium ${getMarginSpacing('sm')}`}>
              Agent Colors
            </h4>
            <div className={`grid grid-cols-1 md:grid-cols-2 ${getGapSpacing('md')}`}>
              <div>
                <h5 className={`${getBodyClasses('secondary')} text-sm ${getMarginSpacing('xs')}`}>
                  Original (Hardcoded)
                </h5>
                <div className={`grid grid-cols-3 ${getGapSpacing('xs')}`}>
                  {[1, 2, 3, 4, 5, 6].map(agentId => {
                    const originalColor = originalAgentColors[agentId as keyof typeof originalAgentColors]
                    return (
                      <div 
                        key={`orig-${agentId}`} 
                        className={`${originalColor} ${getPaddingSpacing('sm')} rounded text-center border`}
                      >
                        <div className="text-xs font-medium">Agent {agentId}</div>
                      </div>
                    )
                  })}
                </div>
              </div>
              <div>
                <h5 className={`${getBodyClasses('secondary')} text-sm ${getMarginSpacing('xs')}`}>
                  Token System
                </h5>
                <div className={`grid grid-cols-3 ${getGapSpacing('xs')}`}>
                  {[1, 2, 3, 4, 5, 6].map(agentId => (
                    <div 
                      key={`token-${agentId}`} 
                      className={`${getAgentColorClasses(agentId)} ${getPaddingSpacing('sm')} rounded text-center border`}
                    >
                      <div className="text-xs font-medium">Agent {agentId}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Output Type Colors Visual */}
          <div>
            <h4 className={`${getBodyClasses('primary')} font-medium ${getMarginSpacing('sm')}`}>
              Output Type Colors
            </h4>
            <div className={`grid grid-cols-1 md:grid-cols-2 ${getGapSpacing('md')}`}>
              <div>
                <h5 className={`${getBodyClasses('secondary')} text-sm ${getMarginSpacing('xs')}`}>
                  Original (Hardcoded)
                </h5>
                <div className={`${getGapSpacing('xs')} space-y-1`}>
                  {['assistant_response', 'system_status', 'debug_info', 'error', 'diffs'].map(outputType => {
                    const originalColor = originalOutputTypeColors[outputType as keyof typeof originalOutputTypeColors]
                    return (
                      <Badge 
                        key={`orig-${outputType}`} 
                        variant="outline" 
                        className={`${originalColor} text-xs`}
                      >
                        {outputType}
                      </Badge>
                    )
                  })}
                </div>
              </div>
              <div>
                <h5 className={`${getBodyClasses('secondary')} text-sm ${getMarginSpacing('xs')}`}>
                  Token System
                </h5>
                <div className={`${getGapSpacing('xs')} space-y-1`}>
                  {['assistant_response', 'system_status', 'debug_info', 'error', 'diffs'].map(outputType => (
                    <Badge 
                      key={`token-${outputType}`} 
                      variant="outline" 
                      className={`${getOutputTypeColorClasses(outputType)} text-xs`}
                    >
                      {outputType}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function TokenSystemComparison() {
  const agentColorMatches = [1, 2, 3, 4, 5, 6].every(agentId => {
    const originalColor = originalAgentColors[agentId as keyof typeof originalAgentColors]
    const tokenColor = getAgentColorClasses(agentId)
    return originalColor === tokenColor
  })

  const outputTypeMatches = ['assistant_response', 'system_status', 'debug_info', 'error', 'diffs'].every(outputType => {
    const originalColor = originalOutputTypeColors[outputType as keyof typeof originalOutputTypeColors]
    const tokenColor = getOutputTypeColorClasses(outputType)
    return originalColor === tokenColor
  })

  const overallValid = agentColorMatches && outputTypeMatches

  return (
    <div className="space-y-6">
      {/* Validation Summary */}
      <Card className={componentTokens.ui.card.primary}>
        <CardHeader>
          <CardTitle className={`${commonTypographyCombinations.sectionHeader} flex items-center ${getGapSpacing('sm')}`}>
            Token System Validation Summary
            {overallValid ? (
              <CheckCircle className={`w-5 h-5 ${getStatusColorClasses('success')}`} />
            ) : (
              <AlertTriangle className={`w-5 h-5 ${getStatusColorClasses('failed')}`} />
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className={`${getGapSpacing('md')} space-y-2`}>
            <div className={`flex items-center justify-between ${getPaddingSpacing('sm')} rounded ${agentColorMatches ? 'bg-green-50 dark:bg-green-950/20' : 'bg-red-50 dark:bg-red-950/20'}`}>
              <span className={getBodyClasses('primary')}>Agent Colors</span>
              {agentColorMatches ? (
                <span className={`${getStatusColorClasses('success')} text-sm`}>✓ All colors match</span>
              ) : (
                <span className={`${getStatusColorClasses('failed')} text-sm`}>✗ Some colors don't match</span>
              )}
            </div>
            <div className={`flex items-center justify-between ${getPaddingSpacing('sm')} rounded ${outputTypeMatches ? 'bg-green-50 dark:bg-green-950/20' : 'bg-red-50 dark:bg-red-950/20'}`}>
              <span className={getBodyClasses('primary')}>Output Type Colors</span>
              {outputTypeMatches ? (
                <span className={`${getStatusColorClasses('success')} text-sm`}>✓ All colors match</span>
              ) : (
                <span className={`${getStatusColorClasses('failed')} text-sm`}>✗ Some colors don't match</span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Visual Comparison */}
      <VisualColorComparison />

      {/* Detailed Validation Tables */}
      <AgentColorComparison />
      <OutputTypeColorComparison />
    </div>
  )
}