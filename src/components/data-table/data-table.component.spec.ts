import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { DataTable, Column } from './data-table.component';

jest.mock('@/components/empty-state/empty-state.component', () => ({
  EmptyState: ({ title, description }: { title: string; description: string }) =>
    React.createElement('div', { 'data-testid': 'empty-state' }, `${title}: ${description}`),
}));

jest.mock('@/components/pagination-control/pagination-control.component', () => ({
  PaginationControl: ({ currentPage, totalPages }: { currentPage: number; totalPages: number }) =>
    React.createElement('div', { 'data-testid': 'pagination' }, `Page ${currentPage} of ${totalPages}`),
}));

jest.mock('lucide-react', () => ({
  ArrowUpDown: () => React.createElement('span', null, 'sort'),
  ArrowUp: () => React.createElement('span', null, 'asc'),
  ArrowDown: () => React.createElement('span', null, 'desc'),
}));

interface TestRow {
  id: number;
  name: string;
  status: string;
}

const columns: Column<TestRow>[] = [
  { key: 'id', header: 'ID', sortable: true },
  { key: 'name', header: 'Name', sortable: true },
  { key: 'status', header: 'Status' },
];

const data: TestRow[] = [
  { id: 1, name: 'Alice', status: 'active' },
  { id: 2, name: 'Bob', status: 'inactive' },
];

describe('DataTable', () => {
  it('renders table with data', () => {
    render(React.createElement(DataTable, { columns, data }));
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
  });

  it('renders column headers', () => {
    render(React.createElement(DataTable, { columns, data }));
    expect(screen.getByText('ID')).toBeInTheDocument();
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
  });

  it('shows empty state when data is empty', () => {
    render(React.createElement(DataTable, { columns, data: [], emptyMessage: 'Nothing here' }));
    expect(screen.getByTestId('empty-state')).toBeInTheDocument();
  });

  it('renders loading skeleton when isLoading is true', () => {
    const { container } = render(React.createElement(DataTable, { columns, data: [], isLoading: true }));
    expect(container.querySelectorAll('.skeleton-shimmer').length).toBeGreaterThan(0);
  });

  it('calls onRowClick when a row is clicked', () => {
    const onRowClick = jest.fn();
    render(React.createElement(DataTable, { columns, data, onRowClick }));
    fireEvent.click(screen.getByText('Alice'));
    expect(onRowClick).toHaveBeenCalledWith(data[0]);
  });

  it('calls onSort when a sortable column header is clicked', () => {
    const onSort = jest.fn();
    render(React.createElement(DataTable, { columns, data, onSort }));
    fireEvent.click(screen.getByText('Name'));
    expect(onSort).toHaveBeenCalledWith('name', 'asc');
  });

  it('renders pagination when pagination prop is provided', () => {
    const pagination = { currentPage: 1, totalPages: 5, onPageChange: jest.fn() };
    render(React.createElement(DataTable, { columns, data, pagination }));
    expect(screen.getByTestId('pagination')).toBeInTheDocument();
  });

  it('renders custom cell content via render function', () => {
    const customColumns: Column<TestRow>[] = [
      {
        key: 'name',
        header: 'Name',
        render: (value) => React.createElement('strong', null, String(value)),
      },
    ];
    render(React.createElement(DataTable, { columns: customColumns, data }));
    expect(screen.getByText('Alice').tagName).toBe('STRONG');
  });
});
