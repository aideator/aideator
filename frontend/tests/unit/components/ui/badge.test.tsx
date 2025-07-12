import React from 'react'
import { render, screen } from '@testing-library/react'
import { Badge } from '@/components/ui/badge'

describe('Badge', () => {
  it('should render badge with text', () => {
    render(<Badge>Test Badge</Badge>)
    expect(screen.getByText('Test Badge')).toBeInTheDocument()
  })

  it('should apply default variant styling', () => {
    render(<Badge data-testid="badge">Default Badge</Badge>)
    const badge = screen.getByTestId('badge')
    expect(badge).toHaveClass('bg-primary text-primary-foreground')
  })

  it('should apply secondary variant styling', () => {
    render(<Badge variant="secondary" data-testid="badge">Secondary Badge</Badge>)
    const badge = screen.getByTestId('badge')
    expect(badge).toHaveClass('bg-secondary text-secondary-foreground')
  })

  it('should apply destructive variant styling', () => {
    render(<Badge variant="destructive" data-testid="badge">Destructive Badge</Badge>)
    const badge = screen.getByTestId('badge')
    expect(badge).toHaveClass('bg-destructive text-destructive-foreground')
  })

  it('should apply outline variant styling', () => {
    render(<Badge variant="outline" data-testid="badge">Outline Badge</Badge>)
    const badge = screen.getByTestId('badge')
    expect(badge).toHaveClass('text-foreground')
  })

  it('should apply base styling classes', () => {
    render(<Badge data-testid="badge">Badge</Badge>)
    const badge = screen.getByTestId('badge')
    expect(badge).toHaveClass('inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors')
  })

  it('should apply custom className', () => {
    render(<Badge className="custom-badge-class" data-testid="badge">Custom Badge</Badge>)
    const badge = screen.getByTestId('badge')
    expect(badge).toHaveClass('custom-badge-class')
  })

  it('should forward ref correctly', () => {
    const ref = React.createRef<HTMLDivElement>()
    render(<Badge ref={ref}>Ref Badge</Badge>)
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  it('should pass through additional props', () => {
    render(<Badge data-testid="badge" role="status" aria-label="Status badge">Status</Badge>)
    const badge = screen.getByTestId('badge')
    expect(badge).toHaveAttribute('role', 'status')
    expect(badge).toHaveAttribute('aria-label', 'Status badge')
  })

  it('should handle focus and hover states', () => {
    render(<Badge data-testid="badge">Focusable Badge</Badge>)
    const badge = screen.getByTestId('badge')
    expect(badge).toHaveClass('focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2')
  })

  it('should render with different content types', () => {
    render(
      <Badge data-testid="badge">
        <span>Icon</span>
        Badge with icon
      </Badge>
    )
    const badge = screen.getByTestId('badge')
    expect(badge).toHaveTextContent('IconBadge with icon')
  })

  it('should handle empty content', () => {
    render(<Badge data-testid="badge" />)
    const badge = screen.getByTestId('badge')
    expect(badge).toBeInTheDocument()
    expect(badge).toBeEmptyDOMElement()
  })
})