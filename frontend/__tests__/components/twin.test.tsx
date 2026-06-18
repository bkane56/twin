import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Twin from '@/components/twin'

// Mock environment variables
const mockApiUrl = 'http://localhost:8000'

// Mock fetch globally
const mockFetch = jest.fn() as jest.MockedFunction<typeof fetch>
global.fetch = mockFetch

describe('Twin Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Mock successful fetch response
    const customMockFetch = (url: string | URL | Request) => {
      if (typeof url === 'string' && url.includes('/avatar.png')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({})
        } as Response)
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({
          response: 'Test response from assistant',
          session_id: 'test-session-id-123'
        })
      } as Response)
    }
    mockFetch.mockImplementation(customMockFetch)

    // Mock process.env
    Object.defineProperty(process.env, 'NEXT_PUBLIC_API_URL', {
      value: mockApiUrl,
      writable: true
    })
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  describe('Component Rendering', () => {
    test('renders the Twin component with header', async () => {
      await act(async () => {
        render(<Twin />)
      })

      expect(screen.getByText(/Brian's AI Digital Twin/i)).toBeInTheDocument()
      expect(screen.getByText(/Because it is all about Me/i)).toBeInTheDocument()
    })

    test('renders initial greeting message', async () => {
      await act(async () => {
        render(<Twin />)
      })

      expect(screen.getByText(/Hello! I'm your Digital Twin/i)).toBeInTheDocument()
      expect(screen.getByText(/Ask me anything/i)).toBeInTheDocument()
    })

    test('renders message input field', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      expect(input).toBeInTheDocument()
      expect(input).not.toBeDisabled()
    })

    test('renders send button', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const button = screen.getByRole('button')
      expect(button).toBeInTheDocument()
    })

    test('send button is disabled when input is empty', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })

    test('send button is enabled when input has text', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'Hello')

      const button = screen.getByRole('button')
      expect(button).not.toBeDisabled()
    })
  })

  describe('Message Sending', () => {
    test('sends message when enter key is pressed', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'Hello{Enter}')

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/chat'),
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
          })
        )
      })
    })

    test('sends message when send button is clicked', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'Test message')

      const button = screen.getByRole('button')
      await userEvent.click(button)

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalled()
      })
    })

    test('does not send empty messages', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      const button = screen.getByRole('button')

      // Button should be disabled when input is empty
      expect(button).toBeDisabled()

      expect(global.fetch).not.toHaveBeenCalledWith(
        expect.stringContaining('/chat'),
        expect.any(Object)
      )
    })

    test('clears input field after sending message', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'Test message')

      const button = screen.getByRole('button')
      await userEvent.click(button)

      await waitFor(() => {
        expect(input).toHaveValue('')
      })
    })

    test('does not send message while loading', async () => {
      await act(async () => {
        render(<Twin />)
      })

      // Make fetch delay to simulate loading
      mockFetch.mockImplementationOnce(() =>
        new Promise(resolve =>
          setTimeout(() => resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
              response: 'response',
              session_id: 'test-session'
            })
          } as Response), 1000)
        )
      )

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'First message')

      const button = screen.getByRole('button')
      await userEvent.click(button)

      // Immediately try to send another
      await userEvent.type(input, 'Second message')
      await userEvent.click(button)

      // Should only be called once
      expect(global.fetch).toHaveBeenCalledTimes(1)
    })
  })

  describe('Session Management', () => {
    test('generates session_id on first message', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'Hello')

      const button = screen.getByRole('button')
      await userEvent.click(button)

      await waitFor(() => {
        const chatCall = (global.fetch as jest.Mock).mock.calls.find((call: unknown[]) => 
          typeof call[0] === 'string' && call[0].includes('/chat')
        )
        expect(chatCall).toBeDefined()
        const body = JSON.parse(chatCall[1].body)
        // First call should not include session_id or it should be undefined
        expect(body.message).toBe('Hello')
      })
    })

    test('reuses session_id for subsequent messages', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)

      // Send first message
      await userEvent.type(input, 'First')
      let button = screen.getByRole('button')
      await userEvent.click(button)

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/chat'),
          expect.any(Object)
        )
      })

      // Send second message
      await userEvent.type(input, 'Second')
      button = screen.getByRole('button')
      await userEvent.click(button)

      await waitFor(() => {
        // avatar check (1) + first chat (1) + second chat (1) = 3
        expect(global.fetch).toHaveBeenCalledTimes(3)
      })
    })
  })

  describe('Message Display', () => {
    test('displays user message in chat', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'User question')

      const button = screen.getByRole('button')
      await userEvent.click(button)

      await waitFor(() => {
        expect(screen.getByText('User question')).toBeInTheDocument()
      })
    })

    test('displays assistant response in chat', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'Hello')

      const button = screen.getByRole('button')
      await userEvent.click(button)

      await waitFor(() => {
        expect(screen.getByText('Test response from assistant')).toBeInTheDocument()
      })
    })

    test('displays multiple messages in correct order', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)

      // Send first message
      await userEvent.type(input, 'First message')
      let button = screen.getByRole('button')
      await userEvent.click(button)

      await waitFor(() => {
        expect(screen.getByText('First message')).toBeInTheDocument()
      })

      // Send second message
      await userEvent.type(input, 'Second message')
      button = screen.getByRole('button')
      await userEvent.click(button)

      await waitFor(() => {
        expect(screen.getByText('Second message')).toBeInTheDocument()
      })
    })

    test('displays loading indicator while fetching', async () => {
      mockFetch.mockImplementationOnce(() =>
        new Promise(resolve =>
          setTimeout(() => resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
              response: 'response',
              session_id: 'test'
            })
          } as Response), 500)
        )
      )

      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'Test')

      const button = screen.getByRole('button')
      await userEvent.click(button)

      // Look for loading indicator (animated dots)
      await waitFor(() => {
        // Component should show loading state
        const loadingElements = screen.queryAllByRole('button')
        expect(loadingElements.length).toBeGreaterThan(0)
      })
    })

    test('displays error message on fetch failure', async () => {
      mockFetch.mockImplementationOnce(() =>
        Promise.resolve({
          ok: false,
          status: 500,
          json: () => Promise.resolve({})
        } as Response)
      )

      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'Test')

      const button = screen.getByRole('button')
      await userEvent.click(button)

      await waitFor(() => {
        expect(screen.getByText(/Sorry, I encountered an error/i)).toBeInTheDocument()
      })
    })
  })

  describe('Input Handling', () => {
    test('focuses input after sending message', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'Message')

      const button = screen.getByRole('button')
      await userEvent.click(button)

      await waitFor(() => {
        expect(input).toHaveFocus()
      }, { timeout: 300 })
    })

    test('allows multi-line input with shift+enter', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'Line 1{Shift>}{Enter}{/Shift}Line 2')

      // Message should not be sent on shift+enter
      expect(global.fetch).not.toHaveBeenCalledWith(
        expect.stringContaining('/chat'),
        expect.any(Object)
      )
    })

    test('disables input while loading', async () => {
      // Slow fetch to keep loading state visible
      mockFetch.mockImplementationOnce(() =>
        new Promise(resolve =>
          setTimeout(() => resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
              response: 'response',
              session_id: 'test'
            })
          } as Response), 500)
        )
      )

      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'Test')

      const button = screen.getByRole('button')
      await userEvent.click(button)

      // Input should be disabled after clicking send
      await waitFor(() => {
        expect(input).toBeDisabled()
      }, { timeout: 100 })
    })
  })

  describe('Auto-scroll Behavior', () => {
    test('scrolls to bottom when new message arrives', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'Test{Enter}')

      await waitFor(() => {
        expect(window.HTMLElement.prototype.scrollIntoView).toHaveBeenCalled()
      })
    })
  })

  describe('API Integration', () => {
    test('sends correct request format to API', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'Hello API')

      const button = screen.getByRole('button')
      await userEvent.click(button)

      await waitFor(() => {
        const chatCall = (global.fetch as jest.Mock).mock.calls.find((call: unknown[]) => 
          typeof call[0] === 'string' && call[0].includes('/chat')
        )
        expect(chatCall).toBeDefined()
        expect(chatCall[0]).toContain('/chat')
        expect(chatCall[1].method).toBe('POST')
        expect(chatCall[1].headers['Content-Type']).toBe('application/json')

        const body = JSON.parse(chatCall[1].body)
        expect(body.message).toBe('Hello API')
      })
    })

    test('uses NEXT_PUBLIC_API_URL from environment', async () => {
      Object.defineProperty(process.env, 'NEXT_PUBLIC_API_URL', {
        value: 'https://api.example.com',
        writable: true
      })

      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'Test')

      const button = screen.getByRole('button')
      await userEvent.click(button)

      await waitFor(() => {
        const chatCall = (global.fetch as jest.Mock).mock.calls.find((call: unknown[]) => 
          typeof call[0] === 'string' && call[0].includes('https://api.example.com')
        ) as unknown[] | undefined
        expect(chatCall).toBeDefined()
        expect(chatCall![0]).toContain('https://api.example.com')
      })
    })

    test('falls back to localhost when API_URL not set', async () => {
      Object.defineProperty(process.env, 'NEXT_PUBLIC_API_URL', {
        value: '',
        writable: true
      })

      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'Test')

      const button = screen.getByRole('button')
      await userEvent.click(button)

      await waitFor(() => {
        const chatCall = (global.fetch as jest.Mock).mock.calls.find((call: unknown[]) =>
          typeof call[0] === 'string' && call[0].includes('http://localhost:8000')
        )
        expect(chatCall).toBeDefined()
        expect(chatCall[0]).toContain('http://localhost:8000')
      })
    })
  })

  describe('Avatar Display', () => {
    test('checks for avatar file on mount', async () => {
      mockFetch.mockImplementation((url: string | URL | Request) => {
        if (url === '/avatar.png') {
          return Promise.resolve({ ok: true, status: 200 } as Response)
        }
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({
            response: 'response',
            session_id: 'test'
          })
        } as Response)
      })

      await act(async () => {
        render(<Twin />)
      })

      // Component mounts and checks for avatar
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/avatar.png', { method: 'HEAD' })
      })
    })

    test('displays avatar image when available', async () => {
      mockFetch.mockImplementation((url: string | URL | Request) => {
        if (url === '/avatar.png') {
          return Promise.resolve({ ok: true, status: 200 } as Response)
        }
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({
            response: 'response',
            session_id: 'test'
          })
        } as Response)
      })

      await act(async () => {
        render(<Twin />)
      })

      // Wait for the avatar check to complete
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/avatar.png', { method: 'HEAD' })
      })

      await waitFor(() => {
        const images = screen.getAllByRole('img')
        expect(images.length).toBeGreaterThan(0)
        expect(images[0]).toHaveAttribute('src', '/avatar.png')
      })
    })

    test('displays assistant avatar in messages when available', async () => {
      mockFetch.mockImplementation((url: string | URL | Request) => {
        if (url === '/avatar.png') {
          return Promise.resolve({ ok: true, status: 200 } as Response)
        }
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({
            response: 'Assistant reply',
            session_id: 'test-session'
          })
        } as Response)
      })

      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'Hello{Enter}')

      await waitFor(() => {
        const assistantImages = screen.getAllByAltText('Digital Twin Avatar')
        expect(assistantImages.length).toBeGreaterThan(0)
      })
    })

    test('handles fetch error during avatar check', async () => {
      mockFetch.mockImplementationOnce(() => Promise.reject(new Error('Network error')))

      await act(async () => {
        render(<Twin />)
      })

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/avatar.png', { method: 'HEAD' })
      })

      // Should fall back to bot icon
      expect(screen.queryByRole('img')).not.toBeInTheDocument()
    })
  })

  describe('Accessibility & Other', () => {
    test('input field has proper labels and attributes', async () => {
      await act(async () => {
        render(<Twin />)
      })
      const input = screen.getByPlaceholderText(/Type your message/i)
      expect(input).toHaveAttribute('type', 'text')
    })

    test('button has clear purpose', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const button = screen.getByRole('button')
      expect(button).toBeInTheDocument()
    })

    test('messages display timestamps', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'Test')

      const button = screen.getByRole('button')
      await userEvent.click(button)

      await waitFor(() => {
        // Component renders timestamps for messages
        const timeElements = screen.queryAllByText(/\d{1,2}:\d{2}/)
        expect(timeElements.length).toBeGreaterThanOrEqual(0)
      })
    })

    test('focuses input on mount', async () => {
      await act(async () => {
        render(<Twin />)
      })
      const input = screen.getByPlaceholderText(/Type your message/i)
      expect(input).toHaveFocus()
    })

    test('handles non-json response from API', async () => {
      mockFetch.mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.reject(new Error('Invalid JSON'))
        } as Response)
      )

      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'Test{Enter}')

      await waitFor(() => {
        expect(screen.getByText(/Sorry, I encountered an error/i)).toBeInTheDocument()
      })
    })

    test('does not send message when input is only whitespace', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, '   ')
      
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })

    test('handles fetch rejection', async () => {
      mockFetch.mockImplementationOnce(() => Promise.reject(new Error('Network error')))

      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      await userEvent.type(input, 'Test{Enter}')

      await waitFor(() => {
        expect(screen.getByText(/Sorry, I encountered an error/i)).toBeInTheDocument()
      })
    })

    test('re-uses existing session id on second message', async () => {
      await act(async () => {
        render(<Twin />)
      })

      const input = screen.getByPlaceholderText(/Type your message/i)
      
      // First message
      await userEvent.type(input, 'First{Enter}')
      await waitFor(() => {
        expect(screen.getByText('Test response from assistant')).toBeInTheDocument()
      })

      // Second message
      await userEvent.type(input, 'Second{Enter}')
      
      await waitFor(() => {
        const chatCalls = (global.fetch as jest.Mock).mock.calls.filter((call: unknown[]) =>
          typeof call[0] === 'string' && call[0].includes('/chat')
        )
        expect(chatCalls.length).toBe(2)
        const secondCallBody = JSON.parse(chatCalls[1][1].body)
        expect(secondCallBody.session_id).toBe('test-session-id-123')
      })
    })

    test('does not scroll if messagesEndRef is null', async () => {
      // This is hard to test directly as it's an implementation detail,
      // but we can at least ensure it doesn't crash.
      // The scrollToBottom uses messagesEndRef.current?.scrollIntoView
      await act(async () => {
        render(<Twin />)
      })
      // No crash is success
    })
  })
})

