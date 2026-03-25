import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { Sidebar } from './sidebar.component';

const mockUser = { fullName: 'John Doe', role: 'admin', email: 'john@example.com' };

jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({ user: mockUser }),
}));

jest.mock('next/navigation', () => ({
  usePathname: () => '/dashboard',
}));

jest.mock('next/link', () => {
  return ({ children, href, ...props }: any) =>
    React.createElement('a', { href, ...props }, children);
});

jest.mock('next/image', () => {
  return (props: any) => React.createElement('img', props);
});

jest.mock('lucide-react', () => ({
  LayoutDashboard: () => React.createElement('span', null, 'dashboard'),
  Smartphone: () => React.createElement('span', null, 'phone'),
  LinkIcon: () => React.createElement('span', null, 'link'),
  Bell: () => React.createElement('span', null, 'bell'),
  FileText: () => React.createElement('span', null, 'file'),
  Settings: () => React.createElement('span', null, 'settings'),
  Menu: () => React.createElement('span', null, 'menu'),
  X: () => React.createElement('span', null, 'x'),
  ChevronRight: () => React.createElement('span', null, '>'),
}));

describe('Sidebar', () => {
  it('renders navigation', () => {
    render(React.createElement(Sidebar));
    expect(screen.getByRole('navigation', { name: 'Main navigation' })).toBeInTheDocument();
  });

  it('renders menu items based on user role', () => {
    render(React.createElement(Sidebar));
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('Audit Logs')).toBeInTheDocument();
  });

  it('renders user info', () => {
    render(React.createElement(Sidebar));
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('admin')).toBeInTheDocument();
  });

  it('renders user initial avatar', () => {
    render(React.createElement(Sidebar));
    expect(screen.getByText('J')).toBeInTheDocument();
  });

  it('renders logo', () => {
    render(React.createElement(Sidebar));
    expect(screen.getByAltText('Reconix')).toBeInTheDocument();
  });

  it('has toggle menu button', () => {
    render(React.createElement(Sidebar));
    expect(screen.getByLabelText('Toggle menu')).toBeInTheDocument();
  });

  it('marks active page with aria-current', () => {
    render(React.createElement(Sidebar));
    const dashboardLink = screen.getByText('Dashboard').closest('a');
    expect(dashboardLink).toHaveAttribute('aria-current', 'page');
  });
});
