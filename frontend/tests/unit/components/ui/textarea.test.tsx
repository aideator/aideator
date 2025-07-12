import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { Textarea } from '@/components/ui/textarea'

describe('Textarea', () => {
  it('should render textarea element', () => {
    render(<Textarea />)
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('should handle value changes', () => {
    const handleChange = jest.fn()
    render(<Textarea onChange={handleChange} />)
    
    const textarea = screen.getByRole('textbox')
    fireEvent.change(textarea, { target: { value: 'multiline\ntext content' } })
    
    expect(handleChange).toHaveBeenCalled()
  })

  it('should apply default styling classes', () => {
    render(<Textarea data-testid="textarea" />)
    const textarea = screen.getByTestId('textarea')
    
    expect(textarea).toHaveClass(
      'flex',
      'min-h-[80px]',
      'w-full',
      'rounded-md',
      'border',
      'border-input',
      'bg-background',
      'px-3',
      'py-2'
    )
  })

  it('should apply focus styling classes', () => {
    render(<Textarea data-testid="textarea" />)
    const textarea = screen.getByTestId('textarea')
    
    expect(textarea).toHaveClass(
      'focus-visible:outline-none',
      'focus-visible:ring-2',
      'focus-visible:ring-ring',
      'focus-visible:ring-offset-2'
    )
  })

  it('should apply disabled styling when disabled', () => {
    render(<Textarea disabled data-testid="textarea" />)
    const textarea = screen.getByTestId('textarea')
    
    expect(textarea).toBeDisabled()
    expect(textarea).toHaveClass('disabled:cursor-not-allowed', 'disabled:opacity-50')
  })

  it('should apply custom className', () => {
    render(<Textarea className="custom-textarea-class" data-testid="textarea" />)
    const textarea = screen.getByTestId('textarea')
    
    expect(textarea).toHaveClass('custom-textarea-class')
  })

  it('should forward ref correctly', () => {
    const ref = React.createRef<HTMLTextAreaElement>()
    render(<Textarea ref={ref} />)
    
    expect(ref.current).toBeInstanceOf(HTMLTextAreaElement)
  })

  it('should pass through additional props', () => {
    render(<Textarea data-testid="textarea" rows={10} cols={50} />)
    const textarea = screen.getByTestId('textarea')
    
    expect(textarea).toHaveAttribute('rows', '10')
    expect(textarea).toHaveAttribute('cols', '50')
  })

  it('should handle controlled textarea', () => {
    const { rerender } = render(<Textarea value="initial content" onChange={() => {}} />)
    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
    
    expect(textarea.value).toBe('initial content')
    
    rerender(<Textarea value="updated content" onChange={() => {}} />)
    expect(textarea.value).toBe('updated content')
  })

  it('should handle uncontrolled textarea with defaultValue', () => {
    render(<Textarea defaultValue="default multiline content" />)
    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
    
    expect(textarea.value).toBe('default multiline content')
  })

  it('should handle multiline text input', () => {
    render(<Textarea />)
    const textarea = screen.getByRole('textbox')
    
    fireEvent.change(textarea, { 
      target: { value: 'Line 1\nLine 2\nLine 3' } 
    })
    
    expect((textarea as HTMLTextAreaElement).value).toBe('Line 1\nLine 2\nLine 3')
  })

  it('should be resizable by default', () => {
    render(<Textarea data-testid="textarea" />)
    const textarea = screen.getByTestId('textarea')
    
    // Should not have resize-none class by default
    expect(textarea).not.toHaveClass('resize-none')
  })
})