import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Twin from '../components/twin';

function mockFetchSuccess(responseText = 'Mocked assistant response') {
  const fetchMock = jest.fn((input: RequestInfo | URL, init?: RequestInit) => {
    if (init?.method === 'HEAD') {
      return Promise.resolve({ ok: false } as Response);
    }

    return Promise.resolve({
      ok: true,
      json: async () => ({
        response: responseText,
        session_id: 'test-session-123',
      }),
    } as Response);
  });

  global.fetch = fetchMock as jest.Mock;
  return fetchMock;
}

function mockFetchFailure() {
  const fetchMock = jest.fn((input: RequestInfo | URL, init?: RequestInit) => {
    if (init?.method === 'HEAD') {
      return Promise.resolve({ ok: false } as Response);
    }

    return Promise.resolve({
      ok: false,
      json: async () => ({ detail: 'Server error' }),
    } as Response);
  });

  global.fetch = fetchMock as jest.Mock;
  return fetchMock;
}

describe('Twin chat component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    process.env.NEXT_PUBLIC_API_URL = 'https://api.example.test';
  });

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_API_URL;
  });

  it('renders the default empty chat state', async () => {
    mockFetchSuccess();

    render(<Twin />);

    expect(screen.getByText("Brian's AI Digital Twin")).toBeInTheDocument();
    expect(screen.getByText("Hello! I'm your Digital Twin.")).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Type your message...')).toBeInTheDocument();

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/avatar.png', { method: 'HEAD' });
    });
  });

  it('keeps the send button disabled until text is entered', () => {
    mockFetchSuccess();

    render(<Twin />);

    const sendButton = screen.getByRole('button');
    expect(sendButton).toBeDisabled();
  });

  it('sends a chat request and renders the assistant response', async () => {
    const fetchMock = mockFetchSuccess('Brian has built cloud-deployed AI portfolio projects.');
    const user = userEvent.setup();

    render(<Twin />);

    const input = screen.getByPlaceholderText('Type your message...');
    await user.type(input, 'What has Brian built?');
    await user.click(screen.getByRole('button'));

    expect(screen.getByText('What has Brian built?')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Brian has built cloud-deployed AI portfolio projects.')).toBeInTheDocument();
    });

    expect(fetchMock).toHaveBeenCalledWith(
      'https://api.example.test/chat',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: 'What has Brian built?',
          session_id: undefined,
        }),
      }),
    );
  });

  it('submits with Enter and shows an error message when the API fails', async () => {
    mockFetchFailure();
    const user = userEvent.setup();

    render(<Twin />);

    const input = screen.getByPlaceholderText('Type your message...');
    await user.type(input, 'Will this fail?{enter}');

    await waitFor(() => {
      expect(screen.getByText('Sorry, I encountered an error. Please try again.')).toBeInTheDocument();
    });
  });
});
