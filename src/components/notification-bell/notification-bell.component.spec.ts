import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { NotificationBell } from './notification-bell.component';

const mockMessages: Array<{ type: string; data: Record<string, unknown>; timestamp?: string }> = [];
const mockClearMessages = jest.fn();

jest.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    messages: mockMessages,
    status: 'connected',
    lastMessage: null,
    connect: jest.fn(),
    disconnect: jest.fn(),
    clearMessages: mockClearMessages,
  }),
}));

jest.mock('lucide-react', () => ({
  Bell: () => React.createElement('span', { 'data-testid': 'bell-icon' }, 'bell'),
  X: () => React.createElement('span', null, 'x'),
  CheckCircle: () => React.createElement('span', null, 'check'),
  AlertTriangle: () => React.createElement('span', null, 'alert'),
  Info: () => React.createElement('span', null, 'info'),
}));

describe('NotificationBell', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockMessages.length = 0;
  });

  it('renders bell icon', () => {
    render(React.createElement(NotificationBell));
    expect(screen.getByTestId('bell-icon')).toBeInTheDocument();
  });

  it('has accessible label', () => {
    render(React.createElement(NotificationBell));
    expect(screen.getByLabelText('Notifications')).toBeInTheDocument();
  });

  it('shows notification panel on click', () => {
    render(React.createElement(NotificationBell));
    fireEvent.click(screen.getByLabelText('Notifications'));
    expect(screen.getByText('Notifications')).toBeInTheDocument();
    expect(screen.getByText('No notifications')).toBeInTheDocument();
  });

  it('shows unread count badge when messages exist', () => {
    mockMessages.push(
      { type: 'info', data: { message: 'Test notification 1' } },
      { type: 'success', data: { message: 'Test notification 2' } },
    );

    render(React.createElement(NotificationBell));
    expect(screen.getByLabelText(/2 unread/)).toBeInTheDocument();
  });

  it('displays message content in panel', () => {
    mockMessages.push(
      { type: 'info', data: { message: 'SIM recycled successfully' } },
    );

    render(React.createElement(NotificationBell));
    fireEvent.click(screen.getByLabelText(/1 unread/));
    expect(screen.getByText('SIM recycled successfully')).toBeInTheDocument();
  });

  it('caps badge at 9+', () => {
    for (let i = 0; i < 12; i++) {
      mockMessages.push({ type: 'info', data: { message: `msg ${i}` } });
    }

    render(React.createElement(NotificationBell));
    expect(screen.getByText('9+')).toBeInTheDocument();
  });

  it('has aria-expanded attribute', () => {
    render(React.createElement(NotificationBell));
    const button = screen.getByLabelText('Notifications');
    expect(button).toHaveAttribute('aria-expanded', 'false');
    fireEvent.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'true');
  });

  it('shows connection status indicator', () => {
    render(React.createElement(NotificationBell));
    fireEvent.click(screen.getByLabelText('Notifications'));
    expect(screen.getByTitle('WebSocket: connected')).toBeInTheDocument();
  });
});
