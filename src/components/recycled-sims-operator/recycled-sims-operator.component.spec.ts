import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { RecycledSimsByOperator } from './recycled-sims-operator.component';

jest.mock('recharts', () => ({
  PieChart: ({ children }: { children: React.ReactNode }) =>
    React.createElement('div', { 'data-testid': 'pie-chart' }, children),
  Pie: ({ children }: { children: React.ReactNode }) =>
    React.createElement('div', { 'data-testid': 'pie' }, children),
  Cell: () => React.createElement('div', { 'data-testid': 'cell' }),
  Tooltip: () => React.createElement('div'),
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) =>
    React.createElement('div', { 'data-testid': 'responsive-container' }, children),
}));

const mockData = [
  { operatorName: 'MTN', count: 500 },
  { operatorName: 'Airtel', count: 300 },
  { operatorName: 'Glo', count: 200 },
];

describe('RecycledSimsByOperator', () => {
  it('renders chart title', () => {
    render(React.createElement(RecycledSimsByOperator, { data: mockData }));
    expect(screen.getByText('Recycled SIMs by Operator')).toBeInTheDocument();
  });

  it('renders chart container', () => {
    render(React.createElement(RecycledSimsByOperator, { data: mockData }));
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
  });

  it('renders pie chart', () => {
    render(React.createElement(RecycledSimsByOperator, { data: mockData }));
    expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
  });

  it('renders cells for each operator', () => {
    render(React.createElement(RecycledSimsByOperator, { data: mockData }));
    const cells = screen.getAllByTestId('cell');
    expect(cells).toHaveLength(3);
  });

  it('has the component class', () => {
    const { container } = render(React.createElement(RecycledSimsByOperator, { data: mockData }));
    expect(container.querySelector('.recycled-sims-operator')).toBeInTheDocument();
  });
});
