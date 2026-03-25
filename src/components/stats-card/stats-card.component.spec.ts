import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { StatsCard } from './stats-card.component';

const MockIcon = (props: any) => React.createElement('svg', { 'data-testid': 'mock-icon', ...props });

jest.mock('lucide-react', () => ({
  TrendingUp: () => React.createElement('span', { 'data-testid': 'trending-up' }, 'up'),
  TrendingDown: () => React.createElement('span', { 'data-testid': 'trending-down' }, 'down'),
}));

describe('StatsCard', () => {
  it('renders title and value', () => {
    render(React.createElement(StatsCard, { icon: MockIcon, title: 'Total Users', value: 1500 }));
    expect(screen.getByText('Total Users')).toBeInTheDocument();
    expect(screen.getByText('1,500')).toBeInTheDocument();
  });

  it('renders string values', () => {
    render(React.createElement(StatsCard, { icon: MockIcon, title: 'Status', value: 'Active' }));
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('renders positive change indicator', () => {
    render(React.createElement(StatsCard, { icon: MockIcon, title: 'Growth', value: 100, change: 15 }));
    expect(screen.getByText('+15%')).toBeInTheDocument();
    expect(screen.getByTestId('trending-up')).toBeInTheDocument();
  });

  it('renders negative change indicator', () => {
    render(React.createElement(StatsCard, { icon: MockIcon, title: 'Decline', value: 50, change: -10 }));
    expect(screen.getByText('-10%')).toBeInTheDocument();
    expect(screen.getByTestId('trending-down')).toBeInTheDocument();
  });

  it('renders custom change label', () => {
    render(React.createElement(StatsCard, { icon: MockIcon, title: 'Test', value: 10, change: 5, changeLabel: 'vs last week' }));
    expect(screen.getByText('vs last week')).toBeInTheDocument();
  });

  it('renders the icon', () => {
    render(React.createElement(StatsCard, { icon: MockIcon, title: 'Test', value: 10 }));
    expect(screen.getByTestId('mock-icon')).toBeInTheDocument();
  });

  it('does not show change when not provided', () => {
    render(React.createElement(StatsCard, { icon: MockIcon, title: 'Test', value: 10 }));
    expect(screen.queryByTestId('trending-up')).not.toBeInTheDocument();
    expect(screen.queryByTestId('trending-down')).not.toBeInTheDocument();
  });
});
