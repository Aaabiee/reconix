import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { SearchFilterForm } from './search-filter.component';

jest.mock('@/components/search-bar/search-bar.component', () => ({
  SearchBar: ({ onSearch, placeholder }: { onSearch: (q: string) => void; placeholder: string }) =>
    React.createElement('input', {
      'data-testid': 'search-bar',
      placeholder,
      onChange: (e: React.ChangeEvent<HTMLInputElement>) => onSearch(e.target.value),
    }),
}));

describe('SearchFilterForm', () => {
  const filters = [
    {
      name: 'status',
      label: 'Status',
      options: [
        { label: 'Active', value: 'active' },
        { label: 'Inactive', value: 'inactive' },
      ],
    },
    {
      name: 'operator',
      label: 'Operator',
      options: [
        { label: 'MTN', value: 'mtn' },
        { label: 'Airtel', value: 'airtel' },
      ],
    },
  ];

  it('renders search bar', () => {
    render(React.createElement(SearchFilterForm, { onSearch: jest.fn() }));
    expect(screen.getByTestId('search-bar')).toBeInTheDocument();
  });

  it('renders filter dropdowns', () => {
    render(React.createElement(SearchFilterForm, { onSearch: jest.fn(), filters }));
    expect(screen.getByLabelText('Status')).toBeInTheDocument();
    expect(screen.getByLabelText('Operator')).toBeInTheDocument();
  });

  it('renders filter options', () => {
    render(React.createElement(SearchFilterForm, { onSearch: jest.fn(), filters }));
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('MTN')).toBeInTheDocument();
  });

  it('calls onFilterChange when filter value changes', () => {
    const onFilterChange = jest.fn();
    render(React.createElement(SearchFilterForm, { onSearch: jest.fn(), onFilterChange, filters }));
    fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'active' } });
    expect(onFilterChange).toHaveBeenCalledWith('status', 'active');
  });

  it('renders "All" default option for each filter', () => {
    render(React.createElement(SearchFilterForm, { onSearch: jest.fn(), filters }));
    expect(screen.getByText('All Status')).toBeInTheDocument();
    expect(screen.getByText('All Operator')).toBeInTheDocument();
  });

  it('does not render filter section when no filters provided', () => {
    const { container } = render(React.createElement(SearchFilterForm, { onSearch: jest.fn() }));
    expect(container.querySelectorAll('select').length).toBe(0);
  });
});
