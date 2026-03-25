import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { StatsOverview } from './stats-overview.component';

jest.mock('@/components/stats-card/stats-card.component', () => ({
  StatsCard: ({ title, value }: { title: string; value: number }) =>
    React.createElement('div', { 'data-testid': `stats-card-${title}` }, `${title}: ${value}`),
}));

jest.mock('lucide-react', () => ({
  Activity: () => React.createElement('span'),
  AlertCircle: () => React.createElement('span'),
  CheckCircle2: () => React.createElement('span'),
  Smartphone: () => React.createElement('span'),
}));

const mockStats = {
  totalRecycledSims: 1500,
  totalDelinkRequests: 320,
  pendingDelinkRequests: 45,
  completedDelinkRequests: 275,
};

describe('StatsOverview', () => {
  it('renders all four stats cards', () => {
    render(React.createElement(StatsOverview, { stats: mockStats }));
    expect(screen.getByTestId('stats-card-Total Recycled SIMs')).toBeInTheDocument();
    expect(screen.getByTestId('stats-card-Total Delink Requests')).toBeInTheDocument();
    expect(screen.getByTestId('stats-card-Pending Requests')).toBeInTheDocument();
    expect(screen.getByTestId('stats-card-Completed Requests')).toBeInTheDocument();
  });

  it('passes correct values to stats cards', () => {
    render(React.createElement(StatsOverview, { stats: mockStats }));
    expect(screen.getByText(/1500/)).toBeInTheDocument();
    expect(screen.getByText(/320/)).toBeInTheDocument();
    expect(screen.getByText(/45/)).toBeInTheDocument();
    expect(screen.getByText(/275/)).toBeInTheDocument();
  });

  it('renders within a grid container', () => {
    const { container } = render(React.createElement(StatsOverview, { stats: mockStats }));
    expect(container.querySelector('.stats-overview')).toBeInTheDocument();
  });
});
