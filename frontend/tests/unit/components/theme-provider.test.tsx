import React from 'react'
import { render, screen } from '@testing-library/react'
import { ThemeProvider } from '@/components/theme-provider'

// Mock window.matchMedia for next-themes
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

describe('ThemeProvider', () => {
  it('should render children correctly', () => {
    render(
      <ThemeProvider>
        <div>Child Component</div>
      </ThemeProvider>
    )
    
    expect(screen.getByText('Child Component')).toBeInTheDocument()
  })

  it('should apply theme provider wrapper', () => {
    const { container } = render(
      <ThemeProvider>
        <div>Content</div>
      </ThemeProvider>
    )
    
    // ThemeProvider should render its children
    expect(container.firstChild).toBeInTheDocument()
  })

  it('should handle multiple children', () => {
    render(
      <ThemeProvider>
        <div>First Child</div>
        <div>Second Child</div>
      </ThemeProvider>
    )
    
    expect(screen.getByText('First Child')).toBeInTheDocument()
    expect(screen.getByText('Second Child')).toBeInTheDocument()
  })

  it('should work without children', () => {
    const { container } = render(<ThemeProvider />)
    
    expect(container.firstChild).toBeInTheDocument()
  })
})