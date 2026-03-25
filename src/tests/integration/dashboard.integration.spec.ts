import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => '/dashboard',
}));

jest.mock('next/link', () => {
  return ({ children, href, ...props }: any) =>
    React.createElement('a', { href, ...props }, children);
});

jest.mock('next/image', () => {
  return (props: any) => React.createElement('img', props);
});

jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { fullName: 'Admin User', role: 'admin', email: 'admin@reconix.gov.ng' },
    isLoading: false,
    error: null,
  }),
}));

jest.mock('recharts', () => ({
  LineChart: ({ children }: any) => React.createElement('div', { 'data-testid': 'line-chart' }, children),
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
  ResponsiveContainer: ({ children }: any) => React.createElement('div', null, children),
  PieChart: ({ children }: any) => React.createElement('div', { 'data-testid': 'pie-chart' }, children),
  Pie: ({ children }: any) => React.createElement('div', null, children),
  Cell: () => null,
}));

jest.mock('date-fns', () => ({
  format: () => 'Jan 15, 10:30',
}));

jest.mock('lucide-react', () => ({
  Activity: () => React.createElement('span'),
  AlertCircle: () => React.createElement('span'),
  CheckCircle2: () => React.createElement('span'),
  Smartphone: () => React.createElement('span'),
  TrendingUp: () => React.createElement('span'),
  TrendingDown: () => React.createElement('span'),
  ChevronRight: () => React.createElement('span'),
  Bell: () => React.createElement('span'),
  LinkIcon: () => React.createElement('span'),
  Clock: () => React.createElement('span'),
  InboxIcon: () => React.createElement('span'),
}));

describe('Dashboard Integration', () => {
  it('renders StatsOverview with all stat cards', async () => {
    const { StatsOverview } = await import('@/components/stats-overview/stats-overview.component');

    const mockStats = {
      totalRecycledSims: 5000,
      totalDelinkRequests: 1200,
      pendingDelinkRequests: 150,
      completedDelinkRequests: 1050,
    };

    render(React.createElement(StatsOverview, { stats: mockStats }));

    expect(screen.getByText('Total Recycled SIMs')).toBeInTheDocument();
    expect(screen.getByText('Total Delink Requests')).toBeInTheDocument();
    expect(screen.getByText('Pending Requests')).toBeInTheDocument();
    expect(screen.getByText('Completed Requests')).toBeInTheDocument();
  });

  it('renders TrendsChart with correct title', async () => {
    const { TrendsChart } = await import('@/components/trends-chart/trends-chart.component');

    const mockTrends = [
      { date: '2024-01-01', recycledSims: 100, delinkRequests: 50, completedDelinkRequests: 40 },
    ];

    render(React.createElement(TrendsChart, { data: mockTrends }));
    expect(screen.getByText('Trends (Last 30 Days)')).toBeInTheDocument();
  });

  it('renders RecycledSimsByOperator with correct title', async () => {
    const { RecycledSimsByOperator } = await import('@/components/recycled-sims-operator/recycled-sims-operator.component');

    const mockData = [
      { operatorName: 'MTN', count: 2000 },
      { operatorName: 'Airtel', count: 1500 },
    ];

    render(React.createElement(RecycledSimsByOperator, { data: mockData }));
    expect(screen.getByText('Recycled SIMs by Operator')).toBeInTheDocument();
  });

  it('renders RecentActivity with both sections', async () => {
    const { RecentActivity } = await import('@/components/recent-activity/recent-activity.component');

    render(React.createElement(RecentActivity, {
      recentDelinkRequests: [
        { id: '1', phoneNumber: '08012345678', status: 'pending', createdAt: '2024-01-15T10:30:00Z' },
      ],
      recentNotifications: [
        { id: 'n1', title: 'System Update', message: 'Maintenance scheduled', createdAt: '2024-01-15T11:00:00Z' },
      ],
    }));

    expect(screen.getByText('Recent Delink Requests')).toBeInTheDocument();
    expect(screen.getByText('Recent Notifications')).toBeInTheDocument();
    expect(screen.getByText('08012345678')).toBeInTheDocument();
    expect(screen.getByText('System Update')).toBeInTheDocument();
  });

  it('ErrorBoundary renders children when no error', async () => {
    const { ErrorBoundary } = await import('@/components/error-boundary/error-boundary.component');

    render(
      React.createElement(ErrorBoundary, null,
        React.createElement('div', null, 'Dashboard Content')
      )
    );

    expect(screen.getByText('Dashboard Content')).toBeInTheDocument();
  });

  it('PageLayout renders with title and description', async () => {
    const { PageLayout } = await import('@/components/page-layout/page-layout.component');

    render(
      React.createElement(PageLayout, {
        title: 'Dashboard',
        description: 'Overview of recycled SIMs',
      }, React.createElement('div', null, 'Content'))
    );

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Overview of recycled SIMs')).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
  });
});
