/**
 * Basic smoke test to verify Jest setup
 */
describe('Jest Setup', () => {
  it('should be working', () => {
    expect(true).toBe(true)
  })

  it('should have fetch available', () => {
    expect(global.fetch).toBeDefined()
    expect(typeof global.fetch).toBe('function')
  })
})