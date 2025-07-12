import { cn } from '@/lib/utils'

describe('cn utility function', () => {
  it('should merge class names correctly', () => {
    const result = cn('base-class', 'additional-class')
    expect(result).toBe('base-class additional-class')
  })

  it('should handle conditional classes', () => {
    const result = cn('base-class', true && 'conditional-class')
    expect(result).toBe('base-class conditional-class')
  })

  it('should filter out falsy values', () => {
    const result = cn('base-class', false && 'conditional-class', null, undefined)
    expect(result).toBe('base-class')
  })

  it('should handle empty input', () => {
    const result = cn()
    expect(result).toBe('')
  })

  it('should handle arrays of classes', () => {
    const result = cn(['class1', 'class2'], 'class3')
    expect(result).toBe('class1 class2 class3')
  })

  it('should merge conflicting Tailwind classes', () => {
    const result = cn('p-4', 'p-6')
    expect(result).toBe('p-6')
  })
})