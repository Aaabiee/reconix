import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => '/delink-requests',
}));

jest.mock('next/link', () => {
  return ({ children, href, ...props }: any) =>
    React.createElement('a', { href, ...props }, children);
});

jest.mock('@/services/delink.service', () => ({
  delinkService: {
    createDelinkRequest: jest.fn().mockResolvedValue({ id: 'req-1' }),
  },
}));

jest.mock('@/hooks/useDebounce', () => ({
  useDebounce: (val: string) => val,
}));

jest.mock('lucide-react', () => ({
  Search: () => React.createElement('span'),
  X: () => React.createElement('span'),
  InboxIcon: () => React.createElement('span'),
  ArrowUpDown: () => React.createElement('span'),
  ArrowUp: () => React.createElement('span'),
  ArrowDown: () => React.createElement('span'),
  ChevronLeft: () => React.createElement('span'),
  ChevronRight: () => React.createElement('span'),
}));

describe('Delink Workflow Integration', () => {
  it('renders the delink request form with required fields', async () => {
    const { DelinkRequestForm } = await import('@/components/delink-request-form/delink-request-form.component');

    render(React.createElement(DelinkRequestForm));

    expect(screen.getByLabelText('Recycled SIM')).toBeInTheDocument();
    expect(screen.getByLabelText('Reason for Delinking')).toBeInTheDocument();
    expect(screen.getByText('Create Delink Request')).toBeInTheDocument();
  });

  it('pre-fills and disables SIM ID when provided', async () => {
    const { DelinkRequestForm } = await import('@/components/delink-request-form/delink-request-form.component');

    render(React.createElement(DelinkRequestForm, { recycledSimId: 'SIM-456' }));

    const simInput = screen.getByLabelText('Recycled SIM');
    expect(simInput).toHaveValue('SIM-456');
    expect(simInput).toBeDisabled();
  });

  it('user can fill in the delink reason', async () => {
    const { DelinkRequestForm } = await import('@/components/delink-request-form/delink-request-form.component');

    render(React.createElement(DelinkRequestForm));

    const reasonInput = screen.getByLabelText('Reason for Delinking');
    fireEvent.change(reasonInput, { target: { value: 'SIM was recycled to a new subscriber' } });

    expect(reasonInput).toHaveValue('SIM was recycled to a new subscriber');
  });

  it('form has proper validation attributes', async () => {
    const { DelinkRequestForm } = await import('@/components/delink-request-form/delink-request-form.component');

    const { container } = render(React.createElement(DelinkRequestForm));

    expect(container.querySelector('form')).toHaveAttribute('noValidate');
    expect(screen.getByLabelText('Recycled SIM')).toHaveAttribute('aria-invalid', 'false');
    expect(screen.getByLabelText('Reason for Delinking')).toHaveAttribute('aria-invalid', 'false');
  });

  it('search filter form renders with search bar', async () => {
    const { SearchFilterForm } = await import('@/components/search-filter/search-filter.component');

    render(React.createElement(SearchFilterForm, { onSearch: jest.fn() }));

    expect(screen.getByLabelText('Search')).toBeInTheDocument();
  });

  it('search filter renders operator filter dropdown', async () => {
    const { SearchFilterForm } = await import('@/components/search-filter/search-filter.component');

    const filters = [
      {
        name: 'operator',
        label: 'Operator',
        options: [
          { label: 'MTN', value: 'mtn' },
          { label: 'Airtel', value: 'airtel' },
          { label: 'Glo', value: 'glo' },
        ],
      },
      {
        name: 'status',
        label: 'Status',
        options: [
          { label: 'Pending', value: 'pending' },
          { label: 'Approved', value: 'approved' },
        ],
      },
    ];

    render(React.createElement(SearchFilterForm, { onSearch: jest.fn(), filters }));

    expect(screen.getByLabelText('Operator')).toBeInTheDocument();
    expect(screen.getByLabelText('Status')).toBeInTheDocument();
    expect(screen.getByText('MTN')).toBeInTheDocument();
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('data table renders with columns and data', async () => {
    const { DataTable } = await import('@/components/data-table/data-table.component');

    const columns = [
      { key: 'phone' as const, header: 'Phone Number', sortable: true },
      { key: 'status' as const, header: 'Status' },
    ];

    const data = [
      { phone: '08012345678', status: 'pending' },
      { phone: '08098765432', status: 'approved' },
    ];

    render(React.createElement(DataTable, { columns, data }));

    expect(screen.getByText('Phone Number')).toBeInTheDocument();
    expect(screen.getByText('08012345678')).toBeInTheDocument();
    expect(screen.getByText('08098765432')).toBeInTheDocument();
  });

  it('data table shows empty state when no data', async () => {
    const { DataTable } = await import('@/components/data-table/data-table.component');

    const columns = [
      { key: 'phone' as const, header: 'Phone Number' },
    ];

    render(React.createElement(DataTable, {
      columns,
      data: [],
      emptyMessage: 'No delink requests found',
    }));

    expect(screen.getByText(/No delink requests found/)).toBeInTheDocument();
  });
});
