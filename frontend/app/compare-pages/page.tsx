"use client"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TokenSystemComparison } from "@/components/token-system-comparison"
import Home from "@/app/page"
import HomeOriginal from "@/app/page-original"
import { 
  getBodyClasses, 
  getHeadingClasses, 
  commonTypographyCombinations, 
  componentTokens,
  getPaddingSpacing,
  getGapSpacing,
  getMarginSpacing
} from "@/lib/design-tokens"

export default function ComparePages() {
  return (
    <div className={componentTokens.ui.layout.page}>
      <div className={componentTokens.ui.layout.container}>
        <div className={getMarginSpacing('lg')}>
          <h1 className={`${commonTypographyCombinations.pageTitle} text-center ${getMarginSpacing('lg')}`}>
            Design Token System Comparison
          </h1>
          
          <div className={`${getGapSpacing('lg')} space-y-8`}>
            {/* Token System Validation */}
            <Card className={componentTokens.ui.card.primary}>
              <CardHeader>
                <CardTitle className={commonTypographyCombinations.sectionHeader}>
                  Token System Validation
                </CardTitle>
              </CardHeader>
              <CardContent>
                <TokenSystemComparison />
              </CardContent>
            </Card>

            {/* Page Comparison */}
            <Card className={componentTokens.ui.card.primary}>
              <CardHeader>
                <CardTitle className={commonTypographyCombinations.sectionHeader}>
                  Page Comparison
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="side-by-side" className="w-full">
                  <TabsList className={`grid w-full grid-cols-3 ${getMarginSpacing('md')}`}>
                    <TabsTrigger value="side-by-side">Side by Side</TabsTrigger>
                    <TabsTrigger value="original">Original (Hardcoded)</TabsTrigger>
                    <TabsTrigger value="tokens">Token System</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="side-by-side">
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                      <div>
                        <div className={`${getMarginSpacing('md')} flex items-center ${getGapSpacing('sm')}`}>
                          <h3 className={`${getHeadingClasses('h3')} ${getBodyClasses('primary')}`}>
                            Original (Hardcoded)
                          </h3>
                          <Badge variant="outline" className="text-xs">
                            Hardcoded CSS
                          </Badge>
                        </div>
                        <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                          <div className="scale-50 origin-top-left w-[200%] h-[200%] overflow-hidden">
                            <HomeOriginal />
                          </div>
                        </div>
                      </div>
                      
                      <div>
                        <div className={`${getMarginSpacing('md')} flex items-center ${getGapSpacing('sm')}`}>
                          <h3 className={`${getHeadingClasses('h3')} ${getBodyClasses('primary')}`}>
                            Token System
                          </h3>
                          <Badge variant="outline" className="text-xs">
                            Design Tokens
                          </Badge>
                        </div>
                        <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                          <div className="scale-50 origin-top-left w-[200%] h-[200%] overflow-hidden">
                            <Home />
                          </div>
                        </div>
                      </div>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="original">
                    <div className={getMarginSpacing('md')}>
                      <div className={`${getMarginSpacing('md')} flex items-center ${getGapSpacing('sm')}`}>
                        <h3 className={`${getHeadingClasses('h3')} ${getBodyClasses('primary')}`}>
                          Original Implementation (Hardcoded CSS)
                        </h3>
                        <Badge variant="outline" className="text-xs">
                          No Design Tokens
                        </Badge>
                      </div>
                      <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                        <HomeOriginal />
                      </div>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="tokens">
                    <div className={getMarginSpacing('md')}>
                      <div className={`${getMarginSpacing('md')} flex items-center ${getGapSpacing('sm')}`}>
                        <h3 className={`${getHeadingClasses('h3')} ${getBodyClasses('primary')}`}>
                          Token System Implementation
                        </h3>
                        <Badge variant="outline" className="text-xs">
                          Centralized Design Tokens
                        </Badge>
                      </div>
                      <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                        <Home />
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>

            {/* Benefits Summary */}
            <Card className={componentTokens.ui.card.secondary}>
              <CardHeader>
                <CardTitle className={commonTypographyCombinations.cardTitle}>
                  Design Token System Benefits
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`grid grid-cols-1 md:grid-cols-2 ${getGapSpacing('lg')}`}>
                  <div>
                    <h4 className={`${getBodyClasses('primary')} font-medium ${getMarginSpacing('sm')}`}>
                      Consistency
                    </h4>
                    <ul className={`${getBodyClasses('secondary')} text-sm space-y-1`}>
                      <li>• Centralized color definitions</li>
                      <li>• Consistent spacing across components</li>
                      <li>• Unified typography system</li>
                      <li>• Standardized component variants</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className={`${getBodyClasses('primary')} font-medium ${getMarginSpacing('sm')}`}>
                      Maintainability
                    </h4>
                    <ul className={`${getBodyClasses('secondary')} text-sm space-y-1`}>
                      <li>• Single source of truth for design values</li>
                      <li>• Easy theme updates</li>
                      <li>• Reduced code duplication</li>
                      <li>• Type-safe design system</li>
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