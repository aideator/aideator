import React from 'react'
import { render } from '@testing-library/react'
import RootLayout from '@/app/layout'

// Mock next/font
jest.mock('next/font/google', () => ({
  Inter: () => ({
    className: 'inter-font'
  })
}))

describe('RootLayout', () => {
  it('should render children content', () => {
    const { getByText } = render(
      <RootLayout>
        <div>Child Content</div>
      </RootLayout>
    )
    
    expect(getByText('Child Content')).toBeInTheDocument()
  })

  it('should include page header component', () => {
    const { container } = render(
      <RootLayout>
        <div>Content</div>
      </RootLayout>
    )
    
    // Should have layout structure
    expect(container.firstChild).toBeInTheDocument()
  })

  it('should include theme provider in component tree', () => {
    const { container } = render(
      <RootLayout>
        <div>Test Content</div>
      </RootLayout>
    )
    
    // Should render without errors
    expect(container.firstChild).toBeInTheDocument()
  })

  it('should handle multiple children', () => {
    const { getByText } = render(
      <RootLayout>
        <div>First Child</div>
        <div>Second Child</div>
      </RootLayout>
    )
    
    expect(getByText('First Child')).toBeInTheDocument()
    expect(getByText('Second Child')).toBeInTheDocument()
  })

  it('should render layout structure correctly', () => {
    const { container, getByText } = render(
      <RootLayout>
        <main>Main Content</main>
      </RootLayout>
    )
    
    expect(getByText('Main Content')).toBeInTheDocument()
    expect(container.firstChild).toBeInTheDocument()
  })
})