import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import Main from './main';

const mockPush = jest.fn();
let mockUser: { id: number; email: string; role: string } | null = null;
let mockIsLoading = true;

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({ user: mockUser, isLoading: mockIsLoading }),
}));

jest.mock('@/components/loading-spinner/loading-spinner.component', () => ({
  LoadingSpinner: ({ text }: { text: string }) =>
    React.createElement('div', { 'data-testid': 'spinner' }, text),
}));

jest.mock('../App', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) =>
    React.createElement('div', { 'data-testid': 'app-shell' }, children),
}));

describe('Main', () => {
  beforeEach(() => {
    mockPush.mockClear();
    mockUser = null;
    mockIsLoading = true;
  });

  it('shows loading spinner while auth is initializing', () => {
    render(
      React.createElement(Main, null,
        React.createElement('div', null, 'Dashboard')
      )
    );

    expect(screen.getByTestId('spinner')).toHaveTextContent('Initializing...');
  });

  it('redirects to login when user is not authenticated', async () => {
    mockIsLoading = false;
    mockUser = null;

    render(
      React.createElement(Main, null,
        React.createElement('div', null, 'Dashboard')
      )
    );

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/');
    });
  });

  it('renders App shell with children when authenticated', () => {
    mockIsLoading = false;
    mockUser = { id: 1, email: 'admin@reconix.local', role: 'admin' };

    render(
      React.createElement(Main, null,
        React.createElement('div', { 'data-testid': 'page' }, 'Dashboard')
      )
    );

    expect(screen.getByTestId('app-shell')).toBeInTheDocument();
    expect(screen.getByTestId('page')).toHaveTextContent('Dashboard');
  });

  it('does not redirect when user is still loading', () => {
    mockIsLoading = true;
    mockUser = null;

    render(
      React.createElement(Main, null,
        React.createElement('div', null, 'Content')
      )
    );

    expect(mockPush).not.toHaveBeenCalled();
  });
});
