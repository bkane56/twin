import '@testing-library/jest-dom'

// Mock scrollIntoView
window.HTMLElement.prototype.scrollIntoView = jest.fn()

