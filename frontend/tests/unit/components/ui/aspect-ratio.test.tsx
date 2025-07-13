import React from 'react'
import { render, screen } from '@testing-library/react'
import { AspectRatio } from '@/components/ui/aspect-ratio'

describe('AspectRatio', () => {
  it('should render with default ratio', () => {
    render(
      <AspectRatio data-testid="aspect-ratio">
        <div>Content</div>
      </AspectRatio>
    )
    
    const aspectRatio = screen.getByTestId('aspect-ratio')
    expect(aspectRatio).toBeInTheDocument()
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('should apply custom ratio', () => {
    render(
      <AspectRatio ratio={16 / 9} data-testid="aspect-ratio">
        <div>Video content</div>
      </AspectRatio>
    )
    
    const aspectRatio = screen.getByTestId('aspect-ratio')
    expect(aspectRatio).toBeInTheDocument()
    expect(screen.getByText('Video content')).toBeInTheDocument()
  })

  it('should apply custom className', () => {
    render(
      <AspectRatio className="custom-aspect-class" data-testid="aspect-ratio">
        <div>Content</div>
      </AspectRatio>
    )
    
    const aspectRatio = screen.getByTestId('aspect-ratio')
    expect(aspectRatio).toHaveClass('custom-aspect-class')
  })

  it('should forward ref correctly', () => {
    const ref = React.createRef<HTMLDivElement>()
    render(
      <AspectRatio ref={ref}>
        <div>Content</div>
      </AspectRatio>
    )
    
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })

  it('should pass through additional props', () => {
    render(
      <AspectRatio data-testid="aspect-ratio" role="img" aria-label="Image container">
        <img src="/test.jpg" alt="Test" />
      </AspectRatio>
    )
    
    const aspectRatio = screen.getByTestId('aspect-ratio')
    expect(aspectRatio).toHaveAttribute('role', 'img')
    expect(aspectRatio).toHaveAttribute('aria-label', 'Image container')
  })

  it('should handle different content types', () => {
    render(
      <AspectRatio data-testid="aspect-ratio">
        <video controls>
          <source src="/test.mp4" type="video/mp4" />
        </video>
      </AspectRatio>
    )
    
    const aspectRatio = screen.getByTestId('aspect-ratio')
    expect(aspectRatio).toBeInTheDocument()
    expect(aspectRatio.querySelector('video')).toBeInTheDocument()
  })

  it('should maintain aspect ratio for images', () => {
    render(
      <AspectRatio ratio={1} data-testid="square-aspect">
        <img src="/square.jpg" alt="Square image" className="object-cover" />
      </AspectRatio>
    )
    
    const aspectRatio = screen.getByTestId('square-aspect')
    expect(aspectRatio).toBeInTheDocument()
    expect(aspectRatio.querySelector('img')).toHaveClass('object-cover')
  })
})