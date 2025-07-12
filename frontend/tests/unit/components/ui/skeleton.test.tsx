import React from 'react'
import { render, screen } from '@testing-library/react'
import { Skeleton } from '@/components/ui/skeleton'

describe('Skeleton', () => {
  it('should render skeleton component', () => {
    render(<Skeleton data-testid="skeleton" />)
    const skeleton = screen.getByTestId('skeleton')
    expect(skeleton).toBeInTheDocument()
  })

  it('should apply base styling classes', () => {
    render(<Skeleton data-testid="skeleton" />)
    const skeleton = screen.getByTestId('skeleton')
    expect(skeleton).toHaveClass('animate-pulse rounded-md bg-muted')
  })

  it('should apply custom className', () => {
    render(<Skeleton className="custom-skeleton-class" data-testid="skeleton" />)
    const skeleton = screen.getByTestId('skeleton')
    expect(skeleton).toHaveClass('custom-skeleton-class')
  })

  it('should render with custom dimensions', () => {
    render(<Skeleton className="h-4 w-full" data-testid="skeleton" />)
    const skeleton = screen.getByTestId('skeleton')
    expect(skeleton).toHaveClass('h-4 w-full')
  })

  it('should forward ref correctly', () => {
    const ref = React.createRef<HTMLDivElement>()
    render(<Skeleton ref={ref} />)
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  it('should pass through additional props', () => {
    render(<Skeleton data-testid="skeleton" role="progressbar" aria-label="Loading content" />)
    const skeleton = screen.getByTestId('skeleton')
    expect(skeleton).toHaveAttribute('role', 'progressbar')
    expect(skeleton).toHaveAttribute('aria-label', 'Loading content')
  })

  it('should render multiple skeleton components', () => {
    render(
      <div>
        <Skeleton data-testid="skeleton-1" className="h-4 w-full mb-2" />
        <Skeleton data-testid="skeleton-2" className="h-4 w-3/4 mb-2" />
        <Skeleton data-testid="skeleton-3" className="h-4 w-1/2" />
      </div>
    )
    
    expect(screen.getByTestId('skeleton-1')).toBeInTheDocument()
    expect(screen.getByTestId('skeleton-2')).toBeInTheDocument()
    expect(screen.getByTestId('skeleton-3')).toBeInTheDocument()
  })

  it('should be accessible', () => {
    render(<Skeleton data-testid="skeleton" />)
    const skeleton = screen.getByTestId('skeleton')
    
    // Should be a div element by default
    expect(skeleton.tagName).toBe('DIV')
  })

  it('should support different shapes', () => {
    render(
      <div>
        <Skeleton data-testid="circle" className="rounded-full h-12 w-12" />
        <Skeleton data-testid="rectangle" className="rounded-none h-4 w-full" />
        <Skeleton data-testid="rounded" className="rounded-lg h-20 w-full" />
      </div>
    )
    
    expect(screen.getByTestId('circle')).toHaveClass('rounded-full')
    expect(screen.getByTestId('rectangle')).toHaveClass('rounded-none')
    expect(screen.getByTestId('rounded')).toHaveClass('rounded-lg')
  })

  it('should handle inline styles', () => {
    render(<Skeleton data-testid="skeleton" style={{ height: '20px', width: '100px' }} />)
    const skeleton = screen.getByTestId('skeleton')
    expect(skeleton).toHaveStyle({ height: '20px', width: '100px' })
  })
})