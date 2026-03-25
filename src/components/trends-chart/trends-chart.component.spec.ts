import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { TrendsChart } from './trends-chart.component';

jest.mock('recharts', () => ({
  LineChart: ({ children }: { children: React.ReactNode }) =>
    React.createElement('div', { 'data-testid': 'line-chart' }, children),
  Line: () => React.createElement('div', { 'data-testid': 'line' }),
  XAxis: () => React.createElement('div'),
  YAxis: () => React.createElement('div'),
  CartesianGrid: () => React.createElement('div'),
  Tooltip: () => React.createElement('div'),
  Legend: () => React.createElement('div'),
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) =>
    React.createElement('div', { 'data-testid': 'responsive-container' }, children),
}));

const mockData = [
  { date: '2024-01-01', recycledSims: 10, delinkRequests: 5, completedDelinkRequests: 3 },
  { date: '2024-01-02', recycledSims: 15, delinkRequests: 8, completedDelinkRequests: 6 },
];

describe('TrendsChart', () => {
  it('renders chart title', () => {
    render(React.createElement(TrendsChart, { data: mockData }));
    expect(screen.getByText('Trends (Last 30 Days)')).toBeInTheDocument();
  });

  it('renders the chart container', () => {
    render(React.createElement(TrendsChart, { data: mockData }));
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
  });

  it('renders the line chart', () => {
    render(React.createElement(TrendsChart, { data: mockData }));
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });

  it('has the trends-chart class', () => {
    const { container } = render(React.createElement(TrendsChart, { data: mockData }));
    expect(container.querySelector('.trends-chart')).toBeInTheDocument();
  });
});
