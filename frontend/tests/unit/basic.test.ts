/**
 * Basic smoke test to verify Jest setup
 */
describe('Jest Setup', () => {
  it('should be working', () => {
    expect(true).toBe(true)
  })

  it('should have WebSocket mock', () => {
    expect(global.WebSocket).toBeDefined()
    expect(typeof global.WebSocket).toBe('function')
  })
})