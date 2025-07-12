import React from 'react'
import { render, screen } from '@testing-library/react'
import { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent } from '@/components/ui/card'

describe('Card Components', () => {
  it('should render Card component', () => {
    render(<Card data-testid="card">Card content</Card>)
    const card = screen.getByTestId('card')
    expect(card).toBeInTheDocument()
    expect(card).toHaveClass('rounded-lg', 'border', 'bg-card', 'text-card-foreground', 'shadow-sm')
  })

  it('should render CardHeader component', () => {
    render(
      <Card>
        <CardHeader data-testid="card-header">Header content</CardHeader>
      </Card>
    )
    const header = screen.getByTestId('card-header')
    expect(header).toBeInTheDocument()
    expect(header).toHaveClass('flex', 'flex-col', 'space-y-1.5', 'p-6')
  })

  it('should render CardTitle component', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle data-testid="card-title">Card Title</CardTitle>
        </CardHeader>
      </Card>
    )
    const title = screen.getByTestId('card-title')
    expect(title).toBeInTheDocument()
    expect(title).toHaveClass('text-2xl', 'font-semibold', 'leading-none', 'tracking-tight')
    expect(title).toHaveTextContent('Card Title')
  })

  it('should render CardDescription component', () => {
    render(
      <Card>
        <CardHeader>
          <CardDescription data-testid="card-description">Card description text</CardDescription>
        </CardHeader>
      </Card>
    )
    const description = screen.getByTestId('card-description')
    expect(description).toBeInTheDocument()
    expect(description).toHaveClass('text-sm', 'text-muted-foreground')
    expect(description).toHaveTextContent('Card description text')
  })

  it('should render CardContent component', () => {
    render(
      <Card>
        <CardContent data-testid="card-content">Content area</CardContent>
      </Card>
    )
    const content = screen.getByTestId('card-content')
    expect(content).toBeInTheDocument()
    expect(content).toHaveClass('p-6', 'pt-0')
    expect(content).toHaveTextContent('Content area')
  })

  it('should render CardFooter component', () => {
    render(
      <Card>
        <CardFooter data-testid="card-footer">Footer content</CardFooter>
      </Card>
    )
    const footer = screen.getByTestId('card-footer')
    expect(footer).toBeInTheDocument()
    expect(footer).toHaveClass('flex', 'items-center', 'p-6', 'pt-0')
    expect(footer).toHaveTextContent('Footer content')
  })

  it('should render complete card with all components', () => {
    render(
      <Card data-testid="complete-card">
        <CardHeader>
          <CardTitle>Complete Card</CardTitle>
          <CardDescription>This is a complete card with all components</CardDescription>
        </CardHeader>
        <CardContent>
          Main content goes here
        </CardContent>
        <CardFooter>
          Footer actions
        </CardFooter>
      </Card>
    )
    
    expect(screen.getByTestId('complete-card')).toBeInTheDocument()
    expect(screen.getByText('Complete Card')).toBeInTheDocument()
    expect(screen.getByText('This is a complete card with all components')).toBeInTheDocument()
    expect(screen.getByText('Main content goes here')).toBeInTheDocument()
    expect(screen.getByText('Footer actions')).toBeInTheDocument()
  })

  it('should apply custom className to Card', () => {
    render(<Card className="custom-card-class" data-testid="card" />)
    const card = screen.getByTestId('card')
    expect(card).toHaveClass('custom-card-class')
  })

  it('should apply custom className to CardHeader', () => {
    render(
      <Card>
        <CardHeader className="custom-header-class" data-testid="header" />
      </Card>
    )
    const header = screen.getByTestId('header')
    expect(header).toHaveClass('custom-header-class')
  })

  it('should forward refs correctly', () => {
    const cardRef = React.createRef<HTMLDivElement>()
    const headerRef = React.createRef<HTMLDivElement>()
    
    render(
      <Card ref={cardRef}>
        <CardHeader ref={headerRef} />
      </Card>
    )
    
    expect(cardRef.current).toBeInstanceOf(HTMLDivElement)
    expect(headerRef.current).toBeInstanceOf(HTMLDivElement)
  })

  it('should pass through additional props', () => {
    render(<Card data-testid="card" role="region" aria-label="Test card" />)
    const card = screen.getByTestId('card')
    expect(card).toHaveAttribute('role', 'region')
    expect(card).toHaveAttribute('aria-label', 'Test card')
  })
})