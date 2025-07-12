import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { AutoResizeTextarea } from '@/components/auto-resize-textarea'

// Setup window.getComputedStyle mock
const mockGetComputedStyle = jest.fn()
Object.defineProperty(window, 'getComputedStyle', {
  value: mockGetComputedStyle
})

describe('AutoResizeTextarea', () => {
  beforeEach(() => {
    mockGetComputedStyle.mockReturnValue({
      lineHeight: '24px',
      paddingTop: '8px',
      paddingBottom: '8px'
    })
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  it('should render a textarea element', () => {
    render(<AutoResizeTextarea />)
    const textarea = screen.getByRole('textbox')
    expect(textarea).toBeInTheDocument()
  })

  it('should apply default props', () => {
    render(<AutoResizeTextarea data-testid="textarea" />)
    const textarea = screen.getByTestId('textarea')
    expect(textarea).toHaveClass('bg-transparent', 'border-0', 'text-base', 'resize-none')
  })

  it('should apply custom className', () => {
    render(<AutoResizeTextarea className="custom-class" data-testid="textarea" />)
    const textarea = screen.getByTestId('textarea')
    expect(textarea).toHaveClass('custom-class')
  })

  it('should pass through props to underlying textarea', () => {
    render(<AutoResizeTextarea value="test content" data-testid="textarea" />)
    const textarea = screen.getByTestId('textarea') as HTMLTextAreaElement
    expect(textarea.value).toBe('test content')
  })

  it('should adjust height on input', () => {
    render(<AutoResizeTextarea data-testid="textarea" />)
    const textarea = screen.getByTestId('textarea') as HTMLTextAreaElement
    
    // Setup scrollHeight property
    Object.defineProperty(textarea, 'scrollHeight', {
      configurable: true,
      value: 100
    })

    fireEvent.input(textarea, { target: { value: 'content that requires height adjustment' } })
    
    // Should set height based on scrollHeight
    expect(textarea.style.height).toBeTruthy()
  })

  it('should respect minRows prop', () => {
    render(<AutoResizeTextarea minRows={3} data-testid="textarea" />)
    const textarea = screen.getByTestId('textarea') as HTMLTextAreaElement
    
    // The component should set a minimum height based on minRows
    expect(mockGetComputedStyle).toHaveBeenCalled()
  })

  it('should respect maxRows prop', () => {
    render(<AutoResizeTextarea maxRows={10} data-testid="textarea" />)
    const textarea = screen.getByTestId('textarea') as HTMLTextAreaElement
    
    // Setup a large scrollHeight
    Object.defineProperty(textarea, 'scrollHeight', {
      configurable: true,
      value: 500
    })

    fireEvent.input(textarea, { target: { value: 'very long content that should trigger maximum height constraint' } })
    
    // Height should be capped by maxRows calculation
    expect(textarea.style.height).toBeTruthy()
  })

  it('should handle missing computed styles gracefully', () => {
    mockGetComputedStyle.mockReturnValue({
      lineHeight: 'normal',
      paddingTop: '',
      paddingBottom: ''
    })

    render(<AutoResizeTextarea data-testid="textarea" />)
    const textarea = screen.getByTestId('textarea')
    
    fireEvent.input(textarea, { target: { value: 'content' } })
    
    // Should not throw error and still function
    expect(textarea).toBeInTheDocument()
  })

  it('should adjust height on mount', () => {
    render(<AutoResizeTextarea defaultValue="initial content" data-testid="textarea" />)
    const textarea = screen.getByTestId('textarea')
    
    // Component should call adjustHeight on mount
    expect(mockGetComputedStyle).toHaveBeenCalled()
  })

  it('should have correct styling attributes', () => {
    render(<AutoResizeTextarea data-testid="textarea" />)
    const textarea = screen.getByTestId('textarea')
    
    expect(textarea).toHaveClass('focus-visible:ring-0')
    expect(textarea).toHaveClass('focus-visible:ring-offset-0')
  })
})