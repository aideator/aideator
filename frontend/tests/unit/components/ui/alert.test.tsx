import React from 'react'
import { render, screen } from '@testing-library/react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

describe('Alert Components', () => {
  it('should render Alert component', () => {
    render(<Alert data-testid="alert">Alert content</Alert>)
    const alert = screen.getByTestId('alert')
    expect(alert).toBeInTheDocument()
    expect(alert).toHaveTextContent('Alert content')
  })

  it('should apply default variant styling', () => {
    render(<Alert data-testid="alert">Default Alert</Alert>)
    const alert = screen.getByTestId('alert')
    expect(alert).toHaveClass('border', 'text-foreground')
  })

  it('should apply destructive variant styling', () => {
    render(<Alert variant="destructive" data-testid="alert">Destructive Alert</Alert>)
    const alert = screen.getByTestId('alert')
    expect(alert).toHaveClass('border-destructive/50', 'text-destructive')
  })

  it('should apply base styling classes', () => {
    render(<Alert data-testid="alert">Alert</Alert>)
    const alert = screen.getByTestId('alert')
    expect(alert).toHaveClass(
      'relative',
      'w-full',
      'rounded-lg',
      'border',
      'p-4'
    )
  })

  it('should render AlertTitle component', () => {
    render(
      <Alert>
        <AlertTitle data-testid="alert-title">Alert Title</AlertTitle>
      </Alert>
    )
    const title = screen.getByTestId('alert-title')
    expect(title).toBeInTheDocument()
    expect(title).toHaveClass('mb-1', 'font-medium', 'leading-none', 'tracking-tight')
    expect(title).toHaveTextContent('Alert Title')
  })

  it('should render AlertDescription component', () => {
    render(
      <Alert>
        <AlertDescription data-testid="alert-description">
          Alert description text
        </AlertDescription>
      </Alert>
    )
    const description = screen.getByTestId('alert-description')
    expect(description).toBeInTheDocument()
    expect(description).toHaveClass('text-sm')
    expect(description).toHaveTextContent('Alert description text')
  })

  it('should render complete alert with title and description', () => {
    render(
      <Alert data-testid="complete-alert">
        <AlertTitle>Error Occurred</AlertTitle>
        <AlertDescription>
          There was an error processing your request. Please try again.
        </AlertDescription>
      </Alert>
    )
    
    expect(screen.getByTestId('complete-alert')).toBeInTheDocument()
    expect(screen.getByText('Error Occurred')).toBeInTheDocument()
    expect(screen.getByText('There was an error processing your request. Please try again.')).toBeInTheDocument()
  })

  it('should apply custom className to Alert', () => {
    render(<Alert className="custom-alert-class" data-testid="alert">Custom Alert</Alert>)
    const alert = screen.getByTestId('alert')
    expect(alert).toHaveClass('custom-alert-class')
  })

  it('should apply custom className to AlertTitle', () => {
    render(
      <Alert>
        <AlertTitle className="custom-title-class" data-testid="title">Title</AlertTitle>
      </Alert>
    )
    const title = screen.getByTestId('title')
    expect(title).toHaveClass('custom-title-class')
  })

  it('should apply custom className to AlertDescription', () => {
    render(
      <Alert>
        <AlertDescription className="custom-description-class" data-testid="description">
          Description
        </AlertDescription>
      </Alert>
    )
    const description = screen.getByTestId('description')
    expect(description).toHaveClass('custom-description-class')
  })

  it('should forward refs correctly', () => {
    const alertRef = React.createRef<HTMLDivElement>()
    const titleRef = React.createRef<HTMLParagraphElement>()
    const descriptionRef = React.createRef<HTMLDivElement>()
    
    render(
      <Alert ref={alertRef}>
        <AlertTitle ref={titleRef}>Title</AlertTitle>
        <AlertDescription ref={descriptionRef}>Description</AlertDescription>
      </Alert>
    )
    
    expect(alertRef.current).toBeInstanceOf(HTMLDivElement)
    expect(titleRef.current).toBeInstanceOf(HTMLHeadingElement)
    expect(descriptionRef.current).toBeInstanceOf(HTMLDivElement)
  })

  it('should pass through additional props', () => {
    render(
      <Alert data-testid="alert" role="alert" aria-live="polite">
        Alert content
      </Alert>
    )
    const alert = screen.getByTestId('alert')
    expect(alert).toHaveAttribute('role', 'alert')
    expect(alert).toHaveAttribute('aria-live', 'polite')
  })

  it('should handle different content types', () => {
    render(
      <Alert data-testid="alert">
        <AlertTitle>
          <span>Icon</span> Title with icon
        </AlertTitle>
        <AlertDescription>
          Description with <strong>emphasis</strong>
        </AlertDescription>
      </Alert>
    )
    
    const alert = screen.getByTestId('alert')
    expect(alert).toHaveTextContent('Icon Title with icon')
    expect(screen.getByText('emphasis')).toBeInTheDocument()
  })

  it('should support accessibility attributes', () => {
    render(
      <Alert 
        data-testid="alert" 
        role="alert" 
        aria-labelledby="alert-title"
        aria-describedby="alert-description"
      >
        <AlertTitle id="alert-title">Error</AlertTitle>
        <AlertDescription id="alert-description">Something went wrong</AlertDescription>
      </Alert>
    )
    
    const alert = screen.getByTestId('alert')
    expect(alert).toHaveAttribute('aria-labelledby', 'alert-title')
    expect(alert).toHaveAttribute('aria-describedby', 'alert-description')
  })
})