import '@testing-library/jest-dom'

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    prefetch: jest.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({}),
  usePathname: () => '/',
  redirect: jest.fn(),
}))

// Mock WebSocket
const mockWebSocket = {
  close: jest.fn(),
  send: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  onmessage: null,
  onerror: null,
  readyState: 1, // OPEN
}

global.WebSocket = jest.fn().mockImplementation(() => mockWebSocket)
// Add static constants
Object.assign(global.WebSocket, {
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3,
})

// Mock fetch
global.fetch = jest.fn()

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock Element.hasPointerCapture for Radix UI components
if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = jest.fn()
}

// Mock Element.releasePointerCapture for Radix UI components
if (!Element.prototype.releasePointerCapture) {
  Element.prototype.releasePointerCapture = jest.fn()
}

// Mock Element.setPointerCapture for Radix UI components
if (!Element.prototype.setPointerCapture) {
  Element.prototype.setPointerCapture = jest.fn()
}

// Mock Element.scrollIntoView for Radix UI components
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = jest.fn()
}

// Mock window.alert
global.alert = jest.fn()

// Mock window.confirm
global.confirm = jest.fn(() => true)