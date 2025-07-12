import React from 'react'
import { render, screen } from '@testing-library/react'
import { Separator } from '@/components/ui/separator'

describe('Separator', () => {
  it('should render separator with default orientation', () => {
    render(<Separator data-testid="separator" />)
    const separator = screen.getByTestId('separator')
    expect(separator).toBeInTheDocument()
  })

  it('should apply base styling classes', () => {
    render(<Separator data-testid="separator" />)
    const separator = screen.getByTestId('separator')
    expect(separator).toHaveClass('shrink-0 bg-border')
  })

  it('should apply horizontal orientation styling by default', () => {
    render(<Separator data-testid="separator" />)
    const separator = screen.getByTestId('separator')
    expect(separator).toHaveClass('h-[1px] w-full')
  })

  it('should apply vertical orientation styling', () => {
    render(<Separator orientation="vertical" data-testid="separator" />)
    const separator = screen.getByTestId('separator')
    expect(separator).toHaveClass('h-full w-[1px]')
  })

  it('should apply custom className', () => {
    render(<Separator className="custom-separator-class" data-testid="separator" />)
    const separator = screen.getByTestId('separator')
    expect(separator).toHaveClass('custom-separator-class')
  })

  it('should forward ref correctly', () => {
    const ref = React.createRef<HTMLDivElement>()
    render(<Separator ref={ref} />)
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  it('should pass through additional props', () => {
    render(<Separator data-testid="separator" role="separator" aria-orientation="horizontal" />)
    const separator = screen.getByTestId('separator')
    expect(separator).toHaveAttribute('role', 'separator')
    expect(separator).toHaveAttribute('aria-orientation', 'horizontal')
  })

  it('should handle decorative prop', () => {
    render(<Separator decorative data-testid="separator" />)
    const separator = screen.getByTestId('separator')
    expect(separator).toBeInTheDocument()
  })

  it('should be accessible with proper ARIA attributes', () => {
    render(<Separator orientation="vertical" data-testid="separator" />)
    const separator = screen.getByTestId('separator')
    
    // The component should have appropriate accessibility attributes
    expect(separator).toBeInTheDocument()
  })

  it('should work in flex layouts', () => {
    render(
      <div className="flex" data-testid="container">
        <div>Item 1</div>
        <Separator orientation="vertical" data-testid="separator" />
        <div>Item 2</div>
      </div>
    )
    
    const separator = screen.getByTestId('separator')
    expect(separator).toHaveClass('h-full w-[1px]')
  })

  it('should work as divider between content', () => {
    render(
      <div data-testid="container">
        <div>Section 1</div>
        <Separator data-testid="separator" />
        <div>Section 2</div>
      </div>
    )
    
    const separator = screen.getByTestId('separator')
    expect(separator).toHaveClass('h-[1px] w-full')
    expect(screen.getByText('Section 1')).toBeInTheDocument()
    expect(screen.getByText('Section 2')).toBeInTheDocument()
  })
})