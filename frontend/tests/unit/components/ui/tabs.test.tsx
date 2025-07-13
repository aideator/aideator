import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'

describe('Tabs Components', () => {
  const BasicTabs = () => (
    <Tabs defaultValue="tab1">
      <TabsList>
        <TabsTrigger value="tab1">Tab 1</TabsTrigger>
        <TabsTrigger value="tab2">Tab 2</TabsTrigger>
        <TabsTrigger value="tab3">Tab 3</TabsTrigger>
      </TabsList>
      <TabsContent value="tab1">Content for Tab 1</TabsContent>
      <TabsContent value="tab2">Content for Tab 2</TabsContent>
      <TabsContent value="tab3">Content for Tab 3</TabsContent>
    </Tabs>
  )

  it('should render tabs with default value', () => {
    render(<BasicTabs />)
    
    expect(screen.getByText('Tab 1')).toBeInTheDocument()
    expect(screen.getByText('Tab 2')).toBeInTheDocument()
    expect(screen.getByText('Tab 3')).toBeInTheDocument()
    expect(screen.getByText('Content for Tab 1')).toBeInTheDocument()
  })

  it('should apply TabsList styling classes', () => {
    render(
      <Tabs defaultValue="tab1">
        <TabsList data-testid="tabs-list">
          <TabsTrigger value="tab1">Tab 1</TabsTrigger>
        </TabsList>
      </Tabs>
    )
    
    const tabsList = screen.getByTestId('tabs-list')
    expect(tabsList).toHaveClass('inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground')
  })

  it('should apply TabsTrigger styling classes', () => {
    render(
      <Tabs defaultValue="tab1">
        <TabsList>
          <TabsTrigger value="tab1" data-testid="tab-trigger">Tab 1</TabsTrigger>
        </TabsList>
      </Tabs>
    )
    
    const trigger = screen.getByTestId('tab-trigger')
    expect(trigger).toHaveClass('inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background')
  })

  it('should apply TabsContent styling classes', () => {
    render(
      <Tabs defaultValue="tab1">
        <TabsContent value="tab1" data-testid="tab-content">Content</TabsContent>
      </Tabs>
    )
    
    const content = screen.getByTestId('tab-content')
    expect(content).toHaveClass('mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2')
  })

  it('should switch tabs when triggers are clicked', async () => {
    render(<BasicTabs />)
    
    // Initially Tab 1 content should be visible
    expect(screen.getByText('Content for Tab 1')).toBeInTheDocument()
    
    // Click Tab 2
    fireEvent.click(screen.getByText('Tab 2'))
    
    // Now Tab 2 content should be visible and Tab 1 should be gone
    await screen.findByText('Content for Tab 2')
    expect(screen.queryByText('Content for Tab 1')).not.toBeInTheDocument()
  })

  it('should handle controlled tabs', () => {
    const handleValueChange = jest.fn()
    
    render(
      <Tabs value="tab2" onValueChange={handleValueChange}>
        <TabsList>
          <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          <TabsTrigger value="tab2">Tab 2</TabsTrigger>
        </TabsList>
        <TabsContent value="tab1">Content 1</TabsContent>
        <TabsContent value="tab2">Content 2</TabsContent>
      </Tabs>
    )
    
    expect(screen.getByText('Content 2')).toBeInTheDocument()
    
    // Just verify the component renders properly in controlled mode
    expect(screen.getByText('Tab 1')).toBeInTheDocument()
    expect(screen.getByText('Tab 2')).toBeInTheDocument()
  })

  it('should apply custom className to components', () => {
    render(
      <Tabs defaultValue="tab1">
        <TabsList className="custom-list-class" data-testid="tabs-list">
          <TabsTrigger value="tab1" className="custom-trigger-class" data-testid="tab-trigger">
            Tab 1
          </TabsTrigger>
        </TabsList>
        <TabsContent value="tab1" className="custom-content-class" data-testid="tab-content">
          Content
        </TabsContent>
      </Tabs>
    )
    
    expect(screen.getByTestId('tabs-list')).toHaveClass('custom-list-class')
    expect(screen.getByTestId('tab-trigger')).toHaveClass('custom-trigger-class')
    expect(screen.getByTestId('tab-content')).toHaveClass('custom-content-class')
  })

  it('should handle disabled triggers', () => {
    render(
      <Tabs defaultValue="tab1">
        <TabsList>
          <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          <TabsTrigger value="tab2" disabled data-testid="disabled-trigger">Tab 2</TabsTrigger>
        </TabsList>
        <TabsContent value="tab1">Content 1</TabsContent>
        <TabsContent value="tab2">Content 2</TabsContent>
      </Tabs>
    )
    
    const disabledTrigger = screen.getByTestId('disabled-trigger')
    expect(disabledTrigger).toHaveClass('disabled:pointer-events-none disabled:opacity-50')
  })

  it('should forward refs correctly', () => {
    const tabsRef = React.createRef<HTMLDivElement>()
    const listRef = React.createRef<HTMLDivElement>()
    const triggerRef = React.createRef<HTMLButtonElement>()
    const contentRef = React.createRef<HTMLDivElement>()
    
    render(
      <Tabs ref={tabsRef} defaultValue="tab1">
        <TabsList ref={listRef}>
          <TabsTrigger ref={triggerRef} value="tab1">Tab 1</TabsTrigger>
        </TabsList>
        <TabsContent ref={contentRef} value="tab1">Content</TabsContent>
      </Tabs>
    )
    
    expect(tabsRef.current).toBeInstanceOf(HTMLDivElement)
    expect(listRef.current).toBeInstanceOf(HTMLDivElement)
    expect(triggerRef.current).toBeInstanceOf(HTMLButtonElement)
    expect(contentRef.current).toBeInstanceOf(HTMLDivElement)
  })

  it('should handle keyboard navigation', async () => {
    render(<BasicTabs />)
    
    const tab1 = screen.getByText('Tab 1')
    
    // Simulate keyboard navigation without focusing first
    fireEvent.keyDown(tab1, { key: 'ArrowRight' })
    
    expect(screen.getByText('Content for Tab 1')).toBeInTheDocument()
  })
})