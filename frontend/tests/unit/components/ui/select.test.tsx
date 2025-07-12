import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

describe('Select Components', () => {
  const BasicSelect = () => (
    <Select>
      <SelectTrigger>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="option1">Option 1</SelectItem>
        <SelectItem value="option2">Option 2</SelectItem>
        <SelectItem value="option3">Option 3</SelectItem>
      </SelectContent>
    </Select>
  )

  it('should render select trigger', () => {
    render(<BasicSelect />)
    expect(screen.getByRole('combobox')).toBeInTheDocument()
  })

  it('should apply trigger styling classes', () => {
    render(
      <Select>
        <SelectTrigger data-testid="select-trigger">
          <SelectValue />
        </SelectTrigger>
      </Select>
    )
    
    const trigger = screen.getByTestId('select-trigger')
    expect(trigger).toHaveClass(
      'flex',
      'h-10',
      'w-full',
      'items-center',
      'justify-between',
      'rounded-md',
      'border',
      'border-input',
      'bg-background',
      'px-3',
      'py-2',
      'text-sm'
    )
  })

  it('should be disabled when disabled prop is true', () => {
    render(
      <Select disabled>
        <SelectTrigger data-testid="select-trigger">
          <SelectValue />
        </SelectTrigger>
      </Select>
    )
    
    const trigger = screen.getByTestId('select-trigger')
    expect(trigger).toHaveClass('disabled:cursor-not-allowed', 'disabled:opacity-50')
  })

  it('should handle controlled value', () => {
    const handleValueChange = jest.fn()
    
    render(
      <Select value="option2" onValueChange={handleValueChange}>
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="option1">Option 1</SelectItem>
          <SelectItem value="option2">Option 2</SelectItem>
          <SelectItem value="option3">Option 3</SelectItem>
        </SelectContent>
      </Select>
    )
    
    expect(screen.getByRole('combobox')).toHaveAttribute('data-state', 'closed')
  })

  it('should apply custom className to trigger', () => {
    render(
      <Select>
        <SelectTrigger className="custom-trigger-class" data-testid="select-trigger">
          <SelectValue />
        </SelectTrigger>
      </Select>
    )
    
    const trigger = screen.getByTestId('select-trigger')
    expect(trigger).toHaveClass('custom-trigger-class')
  })

  it('should render SelectValue component', () => {
    render(
      <Select>
        <SelectTrigger>
          <SelectValue data-testid="select-value" />
        </SelectTrigger>
      </Select>
    )
    
    expect(screen.getByTestId('select-value')).toBeInTheDocument()
  })

  it('should render SelectContent with proper styling', () => {
    render(
      <Select defaultOpen>
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent data-testid="select-content">
          <SelectItem value="option1">Option 1</SelectItem>
        </SelectContent>
      </Select>
    )
    
    const content = screen.getByTestId('select-content')
    expect(content).toHaveClass(
      'relative',
      'z-50',
      'max-h-96',
      'min-w-[8rem]',
      'overflow-hidden',
      'rounded-md',
      'border',
      'bg-popover',
      'text-popover-foreground',
      'shadow-md'
    )
  })

  it('should render SelectItem with proper styling', () => {
    render(
      <Select defaultOpen>
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="option1" data-testid="select-item">Option 1</SelectItem>
        </SelectContent>
      </Select>
    )
    
    const item = screen.getByTestId('select-item')
    expect(item).toHaveClass(
      'relative',
      'flex',
      'w-full',
      'cursor-default',
      'select-none',
      'items-center',
      'rounded-sm',
      'py-1.5',
      'pl-8',
      'pr-2',
      'text-sm',
      'outline-none'
    )
  })

  it('should handle item selection', () => {
    const handleValueChange = jest.fn()
    
    render(
      <Select onValueChange={handleValueChange} defaultOpen>
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="option1">Option 1</SelectItem>
          <SelectItem value="option2">Option 2</SelectItem>
        </SelectContent>
      </Select>
    )
    
    fireEvent.click(screen.getByText('Option 2'))
    expect(handleValueChange).toHaveBeenCalledWith('option2')
  })

  it('should forward refs correctly', () => {
    const triggerRef = React.createRef<HTMLButtonElement>()
    const contentRef = React.createRef<HTMLDivElement>()
    
    render(
      <Select>
        <SelectTrigger ref={triggerRef}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent ref={contentRef}>
          <SelectItem value="option1">Option 1</SelectItem>
        </SelectContent>
      </Select>
    )
    
    expect(triggerRef.current).toBeInstanceOf(HTMLButtonElement)
  })
})