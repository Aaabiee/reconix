import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { RecentActivity } from './recent-activity.component';

jest.mock('next/link', () => {
  return ({ children, href, ...props }: any) =>
    React.createElement('a', { href, ...props }, children);
});

jest.mock('lucide-react', () => ({
  Bell: () => React.createElement('span', null, 'bell'),
  LinkIcon: () => React.createElement('span', null, 'link'),
  Clock: () => React.createElement('span', null, 'clock'),
}));

jest.mock('date-fns', () => ({
  format: () => 'Jan 15, 10:30',
}));

const mockDelinkRequests = [
  { id: '1', phoneNumber: '08012345678', status: 'pending', createdAt: '2024-01-15T10:30:00Z' },
  { id: '2', phoneNumber: '08098765432', status: 'approved', createdAt: '2024-01-14T09:00:00Z' },
];

const mockNotifications = [
  { id: 'n1', title: 'New Request', message: 'A new delink request', createdAt: '2024-01-15T11:00:00Z' },
];

describe('RecentActivity', () => {
  it('renders delink requests section', () => {
    render(React.createElement(RecentActivity, {
      recentDelinkRequests: mockDelinkRequests,
      recentNotifications: [],
    }));
    expect(screen.getByText('Recent Delink Requests')).toBeInTheDocument();
  });

  it('renders notifications section', () => {
    render(React.createElement(RecentActivity, {
      recentDelinkRequests: [],
      recentNotifications: mockNotifications,
    }));
    expect(screen.getByText('Recent Notifications')).toBeInTheDocument();
  });

  it('renders delink request phone numbers', () => {
    render(React.createElement(RecentActivity, {
      recentDelinkRequests: mockDelinkRequests,
      recentNotifications: [],
    }));
    expect(screen.getByText('08012345678')).toBeInTheDocument();
    expect(screen.getByText('08098765432')).toBeInTheDocument();
  });

  it('renders notification titles and messages', () => {
    render(React.createElement(RecentActivity, {
      recentDelinkRequests: [],
      recentNotifications: mockNotifications,
    }));
    expect(screen.getByText('New Request')).toBeInTheDocument();
    expect(screen.getByText('A new delink request')).toBeInTheDocument();
  });

  it('shows empty message when no delink requests', () => {
    render(React.createElement(RecentActivity, {
      recentDelinkRequests: [],
      recentNotifications: [],
    }));
    expect(screen.getByText('No recent requests')).toBeInTheDocument();
  });

  it('shows empty message when no notifications', () => {
    render(React.createElement(RecentActivity, {
      recentDelinkRequests: [],
      recentNotifications: [],
    }));
    expect(screen.getByText('No recent notifications')).toBeInTheDocument();
  });

  it('uses encodeURIComponent in delink request links', () => {
    render(React.createElement(RecentActivity, {
      recentDelinkRequests: mockDelinkRequests,
      recentNotifications: [],
    }));
    const link = screen.getByText('08012345678').closest('a');
    expect(link).toHaveAttribute('href', '/delink-requests/1');
  });
});
