import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { Input } from '@/components/ui/input'

describe('Input', () => {
  it('should render input element', () => {
    render(<Input />)
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('should handle value changes', () => {
    const handleChange = jest.fn()
    render(<Input onChange={handleChange} />)
    
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'test value' } })
    
    expect(handleChange).toHaveBeenCalled()
  })

  it('should apply default styling classes', () => {
    render(<Input data-testid="input" />)
    const input = screen.getByTestId('input')
    
    expect(input).toHaveClass(
      'flex',
      'h-10',
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
    render(<Input data-testid="input" />)
    const input = screen.getByTestId('input')
    
    expect(input).toHaveClass(
      'focus-visible:outline-none',
      'focus-visible:ring-2',
      'focus-visible:ring-ring',
      'focus-visible:ring-offset-2'
    )
  })

  it('should apply disabled styling when disabled', () => {
    render(<Input disabled data-testid="input" />)
    const input = screen.getByTestId('input')
    
    expect(input).toBeDisabled()
    expect(input).toHaveClass('disabled:cursor-not-allowed', 'disabled:opacity-50')
  })

  it('should apply custom className', () => {
    render(<Input className="custom-class" data-testid="input" />)
    const input = screen.getByTestId('input')
    
    expect(input).toHaveClass('custom-class')
  })

  it('should accept different input types', () => {
    render(<Input type="email" data-testid="email-input" />)
    const input = screen.getByTestId('email-input')
    
    expect(input).toHaveAttribute('type', 'email')
  })

  it('should forward ref correctly', () => {
    const ref = React.createRef<HTMLInputElement>()
    render(<Input ref={ref} />)
    
    expect(ref.current).toBeInstanceOf(HTMLInputElement)
  })

  it('should pass through additional props', () => {
    render(<Input data-testid="input" maxLength={10} />)
    const input = screen.getByTestId('input')
    
    expect(input).toHaveAttribute('maxLength', '10')
  })

  it('should handle controlled input', () => {
    const { rerender } = render(<Input value="initial" onChange={() => {}} />)
    const input = screen.getByRole('textbox') as HTMLInputElement
    
    expect(input.value).toBe('initial')
    
    rerender(<Input value="updated" onChange={() => {}} />)
    expect(input.value).toBe('updated')
  })

  it('should handle uncontrolled input with defaultValue', () => {
    render(<Input defaultValue="default text" />)
    const input = screen.getByRole('textbox') as HTMLInputElement
    
    expect(input.value).toBe('default text')
  })
})