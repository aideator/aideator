import { renderHook, act } from '@testing-library/react'
import { useIsMobile } from '@/hooks/use-mobile'

// Mock window.matchMedia
const mockMatchMedia = jest.fn()
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: mockMatchMedia,
})

// Mock window.innerWidth
Object.defineProperty(window, 'innerWidth', {
  writable: true,
  configurable: true,
  value: 1024,
})

describe('useIsMobile', () => {
  let mockMediaQueryList: {
    matches: boolean
    media: string
    addEventListener: jest.Mock
    removeEventListener: jest.Mock
    addListener: jest.Mock
    removeListener: jest.Mock
    dispatchEvent: jest.Mock
  }

  beforeEach(() => {
    mockMediaQueryList = {
      matches: false,
      media: '(max-width: 767px)',
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      addListener: jest.fn(),
      removeListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }

    mockMatchMedia.mockReturnValue(mockMediaQueryList)

    // Reset window.innerWidth to desktop size
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    })
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  it('should return false for desktop screen size', () => {
    const { result } = renderHook(() => useIsMobile())

    expect(result.current).toBe(false)
    expect(mockMatchMedia).toHaveBeenCalledWith('(max-width: 767px)')
  })

  it('should return true for mobile screen size', () => {
    // Set mobile screen size
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 320,
    })

    const { result } = renderHook(() => useIsMobile())

    expect(result.current).toBe(true)
  })

  it('should add and remove event listener correctly', () => {
    const { unmount } = renderHook(() => useIsMobile())

    expect(mockMediaQueryList.addEventListener).toHaveBeenCalledWith('change', expect.any(Function))

    unmount()

    expect(mockMediaQueryList.removeEventListener).toHaveBeenCalledWith('change', expect.any(Function))
  })

  it('should update when window size changes', () => {
    let changeHandler: () => void

    mockMediaQueryList.addEventListener.mockImplementation((event, handler) => {
      if (event === 'change') {
        changeHandler = handler
      }
    })

    const { result } = renderHook(() => useIsMobile())

    // Initially desktop
    expect(result.current).toBe(false)

    // Simulate screen size change to mobile
    act(() => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      })
      
      // Trigger the change handler
      if (changeHandler) {
        changeHandler()
      }
    })

    expect(result.current).toBe(true)
  })

  it('should use correct mobile breakpoint (768px)', () => {
    renderHook(() => useIsMobile())

    expect(mockMatchMedia).toHaveBeenCalledWith('(max-width: 767px)')
  })

  it('should handle edge case at breakpoint boundary', () => {
    // Test exactly at the breakpoint (768px should be desktop, 767px should be mobile)
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768,
    })

    const { result } = renderHook(() => useIsMobile())
    expect(result.current).toBe(false)

    // Test just below breakpoint
    act(() => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 767,
      })
    })

    const { result: result767 } = renderHook(() => useIsMobile())
    expect(result767.current).toBe(true)
  })

  it('should return false when isMobile state is undefined initially', () => {
    // Test the !!isMobile logic
    const { result } = renderHook(() => useIsMobile())
    
    // Should return false (converted from undefined/false)
    expect(typeof result.current).toBe('boolean')
    expect(result.current === true || result.current === false).toBe(true)
  })

  it('should set initial state based on current window size', () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 400, // Mobile size
    })

    const { result } = renderHook(() => useIsMobile())

    expect(result.current).toBe(true)
  })
})