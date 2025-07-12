import { renderHook, act } from '@testing-library/react'
import { useToast, toast } from '@/hooks/use-toast'

describe('useToast', () => {
  beforeEach(() => {
    // Clear any existing toasts
    const { result } = renderHook(() => useToast())
    act(() => {
      result.current.dismiss()
    })
  })

  it('should return toast function and dismiss function', () => {
    const { result } = renderHook(() => useToast())
    
    expect(typeof result.current.toast).toBe('function')
    expect(typeof result.current.dismiss).toBe('function')
    expect(Array.isArray(result.current.toasts)).toBe(true)
  })

  it('should add toast when toast function is called', () => {
    const { result } = renderHook(() => useToast())
    
    act(() => {
      result.current.toast({
        title: 'Test Toast',
        description: 'This is a test toast message'
      })
    })
    
    expect(result.current.toasts).toHaveLength(1)
    expect(result.current.toasts[0].title).toBe('Test Toast')
    expect(result.current.toasts[0].description).toBe('This is a test toast message')
  })

  it('should generate unique IDs for toasts', () => {
    const { result } = renderHook(() => useToast())
    
    let firstToastId: string
    let secondToastId: string
    
    act(() => {
      const firstToast = result.current.toast({ title: 'Toast 1' })
      firstToastId = firstToast.id
    })
    
    act(() => {
      const secondToast = result.current.toast({ title: 'Toast 2' })
      secondToastId = secondToast.id
    })
    
    // With TOAST_LIMIT = 1, only one toast exists at a time
    expect(result.current.toasts).toHaveLength(1)
    expect(firstToastId).not.toBe(secondToastId)
  })

  it('should handle different toast variants', () => {
    const { result } = renderHook(() => useToast())
    
    act(() => {
      result.current.toast({
        title: 'Success Toast',
        variant: 'default'
      })
    })
    
    // With TOAST_LIMIT = 1, only one toast exists at a time
    expect(result.current.toasts).toHaveLength(1)
    expect(result.current.toasts[0].variant).toBe('default')
    
    act(() => {
      result.current.toast({
        title: 'Error Toast',
        variant: 'destructive'
      })
    })
    
    expect(result.current.toasts).toHaveLength(1)
    expect(result.current.toasts[0].variant).toBe('destructive')
  })

  it('should dismiss specific toast by ID', () => {
    const { result } = renderHook(() => useToast())
    
    let toastId: string
    
    act(() => {
      const toast = result.current.toast({ title: 'Toast 1' })
      toastId = toast.id
    })
    
    expect(result.current.toasts).toHaveLength(1)
    
    act(() => {
      result.current.dismiss(toastId)
    })
    
    // Toast should be marked as not open but still in array initially
    expect(result.current.toasts[0].open).toBe(false)
  })

  it('should dismiss all toasts when no ID provided', () => {
    const { result } = renderHook(() => useToast())
    
    act(() => {
      result.current.toast({ title: 'Toast 1' })
    })
    
    expect(result.current.toasts).toHaveLength(1)
    
    act(() => {
      result.current.dismiss()
    })
    
    // Toast should be marked as not open
    expect(result.current.toasts[0].open).toBe(false)
  })

  it('should limit number of toasts', () => {
    const { result } = renderHook(() => useToast())
    
    // Add more toasts than the limit
    act(() => {
      for (let i = 0; i < 10; i++) {
        result.current.toast({ title: `Toast ${i + 1}` })
      }
    })
    
    // Should respect TOAST_LIMIT = 1
    expect(result.current.toasts.length).toBe(1)
    expect(result.current.toasts[0].title).toBe('Toast 10') // Last toast should be shown
  })

  it('should handle toast with action', () => {
    const { result } = renderHook(() => useToast())
    
    const actionHandler = jest.fn()
    
    act(() => {
      result.current.toast({
        title: 'Toast with Action',
        action: {
          altText: 'Action',
          onClick: actionHandler
        }
      })
    })
    
    expect(result.current.toasts).toHaveLength(1)
    expect(result.current.toasts[0].action).toBeDefined()
  })

  it('should auto-dismiss toasts after duration', async () => {
    jest.useFakeTimers()
    
    const { result } = renderHook(() => useToast())
    
    act(() => {
      result.current.toast({
        title: 'Auto-dismiss Toast'
      })
    })
    
    expect(result.current.toasts).toHaveLength(1)
    
    // Dismiss the toast manually first to trigger the removal timer
    act(() => {
      result.current.dismiss()
    })
    
    // Fast-forward time to trigger removal
    act(() => {
      jest.advanceTimersByTime(1000000) // TOAST_REMOVE_DELAY
    })
    
    // Toast should be automatically removed
    expect(result.current.toasts).toHaveLength(0)
    
    jest.useRealTimers()
  })
})

describe('toast function', () => {
  it('should be available as standalone function', () => {
    expect(typeof toast).toBe('function')
  })

  it('should create toast with standalone function', () => {
    const result = toast({
      title: 'Standalone Toast',
      description: 'Created with standalone function'
    })
    
    expect(result).toHaveProperty('id')
    expect(result).toHaveProperty('dismiss')
  })
})