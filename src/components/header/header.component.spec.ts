import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { Header } from './header.component';

const mockLogout = jest.fn();

jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { fullName: 'Jane Smith', role: 'analyst', email: 'jane@example.com' },
    logout: mockLogout,
  }),
}));

jest.mock('next/link', () => {
  return ({ children, href, ...props }: any) =>
    React.createElement('a', { href, ...props }, children);
});

jest.mock('lucide-react', () => ({
  Bell: () => React.createElement('span', null, 'bell'),
  LogOut: () => React.createElement('span', null, 'logout'),
  Settings: () => React.createElement('span', null, 'settings'),
  ChevronDown: () => React.createElement('span', null, 'v'),
}));

describe('Header', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders header element', () => {
    render(React.createElement(Header));
    expect(screen.getByRole('banner')).toBeInTheDocument();
  });

  it('renders notification button', () => {
    render(React.createElement(Header));
    expect(screen.getByLabelText('Notifications')).toBeInTheDocument();
  });

  it('renders user menu button', () => {
    render(React.createElement(Header));
    expect(screen.getByLabelText('User menu')).toBeInTheDocument();
  });

  it('user menu button has aria-expanded', () => {
    render(React.createElement(Header));
    const menuButton = screen.getByLabelText('User menu');
    expect(menuButton).toHaveAttribute('aria-expanded', 'false');
  });

  it('user menu button has aria-haspopup', () => {
    render(React.createElement(Header));
    expect(screen.getByLabelText('User menu')).toHaveAttribute('aria-haspopup', 'true');
  });

  it('renders user initials', () => {
    render(React.createElement(Header));
    expect(screen.getByText('JS')).toBeInTheDocument();
  });

  it('shows dropdown menu when user menu is clicked', () => {
    render(React.createElement(Header));
    fireEvent.click(screen.getByLabelText('User menu'));
    expect(screen.getByRole('menu')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('Sign Out')).toBeInTheDocument();
  });

  it('calls onNotificationClick when notification button is clicked', () => {
    const onNotificationClick = jest.fn();
    render(React.createElement(Header, { onNotificationClick }));
    fireEvent.click(screen.getByLabelText('Notifications'));
    expect(onNotificationClick).toHaveBeenCalled();
  });
});
