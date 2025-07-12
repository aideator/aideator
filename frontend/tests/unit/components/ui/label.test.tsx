import React from 'react'
import { render, screen } from '@testing-library/react'
import { Label } from '@/components/ui/label'

describe('Label', () => {
  it('should render label with text', () => {
    render(<Label>Test Label</Label>)
    expect(screen.getByText('Test Label')).toBeInTheDocument()
  })

  it('should apply base styling classes', () => {
    render(<Label data-testid="label">Label Text</Label>)
    const label = screen.getByTestId('label')
    expect(label).toHaveClass('text-sm font-medium leading-none')
  })

  it('should apply disabled styling when disabled', () => {
    render(<Label data-testid="label" className="disabled:cursor-not-allowed disabled:opacity-70">Disabled Label</Label>)
    const label = screen.getByTestId('label')
    expect(label).toHaveClass('disabled:cursor-not-allowed disabled:opacity-70')
  })

  it('should apply custom className', () => {
    render(<Label className="custom-label-class" data-testid="label">Custom Label</Label>)
    const label = screen.getByTestId('label')
    expect(label).toHaveClass('custom-label-class')
  })

  it('should be associated with input using htmlFor', () => {
    render(
      <div>
        <Label htmlFor="test-input">Test Label</Label>
        <input id="test-input" type="text" />
      </div>
    )
    
    const label = screen.getByText('Test Label')
    const input = screen.getByRole('textbox')
    
    expect(label).toHaveAttribute('for', 'test-input')
    expect(input).toHaveAttribute('id', 'test-input')
  })

  it('should forward ref correctly', () => {
    const ref = React.createRef<HTMLLabelElement>()
    render(<Label ref={ref}>Ref Label</Label>)
    expect(ref.current).toBeInstanceOf(HTMLLabelElement)
  })

  it('should pass through additional props', () => {
    render(<Label data-testid="label" title="Label tooltip">Label with tooltip</Label>)
    const label = screen.getByTestId('label')
    expect(label).toHaveAttribute('title', 'Label tooltip')
  })

  it('should render as label element by default', () => {
    render(<Label data-testid="label">Label Element</Label>)
    const label = screen.getByTestId('label')
    expect(label.tagName).toBe('LABEL')
  })

  it('should handle click events', () => {
    const handleClick = jest.fn()
    render(<Label onClick={handleClick}>Clickable Label</Label>)
    
    const label = screen.getByText('Clickable Label')
    label.click()
    
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('should render with child elements', () => {
    render(
      <Label data-testid="label">
        <span>Required</span>
        Field Label
      </Label>
    )
    
    const label = screen.getByTestId('label')
    expect(label).toHaveTextContent('RequiredField Label')
    expect(screen.getByText('Required')).toBeInTheDocument()
  })
})