import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { SearchBar } from './search-bar.component';

jest.mock('lucide-react', () => ({
  Search: () => React.createElement('span', null, 'search-icon'),
  X: () => React.createElement('span', null, 'x-icon'),
}));

jest.mock('@/hooks/useDebounce', () => ({
  useDebounce: (value: string) => value,
}));

describe('SearchBar', () => {
  it('renders with default placeholder', () => {
    render(React.createElement(SearchBar, { onSearch: jest.fn() }));
    expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument();
  });

  it('renders with custom placeholder', () => {
    render(React.createElement(SearchBar, { onSearch: jest.fn(), placeholder: 'Find users...' }));
    expect(screen.getByPlaceholderText('Find users...')).toBeInTheDocument();
  });

  it('has accessible search label', () => {
    render(React.createElement(SearchBar, { onSearch: jest.fn() }));
    expect(screen.getByLabelText('Search')).toBeInTheDocument();
  });

  it('calls onSearch when value changes', () => {
    const onSearch = jest.fn();
    render(React.createElement(SearchBar, { onSearch }));
    fireEvent.change(screen.getByLabelText('Search'), { target: { value: 'test' } });
    expect(onSearch).toHaveBeenCalledWith('test');
  });

  it('shows clear button when value is not empty', () => {
    render(React.createElement(SearchBar, { onSearch: jest.fn() }));
    fireEvent.change(screen.getByLabelText('Search'), { target: { value: 'query' } });
    expect(screen.getByLabelText('Clear search')).toBeInTheDocument();
  });

  it('clears input when clear button is clicked', () => {
    const onSearch = jest.fn();
    render(React.createElement(SearchBar, { onSearch }));
    const input = screen.getByLabelText('Search');
    fireEvent.change(input, { target: { value: 'query' } });
    fireEvent.click(screen.getByLabelText('Clear search'));
    expect(input).toHaveValue('');
  });

  it('does not show clear button when clearable is false', () => {
    render(React.createElement(SearchBar, { onSearch: jest.fn(), clearable: false }));
    fireEvent.change(screen.getByLabelText('Search'), { target: { value: 'query' } });
    expect(screen.queryByLabelText('Clear search')).not.toBeInTheDocument();
  });
});
