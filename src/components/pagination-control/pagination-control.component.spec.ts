import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { PaginationControl } from './pagination-control.component';

jest.mock('lucide-react', () => ({
  ChevronLeft: () => React.createElement('span', null, '<'),
  ChevronRight: () => React.createElement('span', null, '>'),
}));

describe('PaginationControl', () => {
  const defaultProps = {
    currentPage: 3,
    totalPages: 10,
    onPageChange: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders pagination navigation', () => {
    render(React.createElement(PaginationControl, defaultProps));
    expect(screen.getByRole('navigation', { name: 'Pagination' })).toBeInTheDocument();
  });

  it('renders previous and next buttons', () => {
    render(React.createElement(PaginationControl, defaultProps));
    expect(screen.getByLabelText('Previous page')).toBeInTheDocument();
    expect(screen.getByLabelText('Next page')).toBeInTheDocument();
  });

  it('disables previous button on first page', () => {
    render(React.createElement(PaginationControl, { ...defaultProps, currentPage: 1 }));
    expect(screen.getByLabelText('Previous page')).toBeDisabled();
  });

  it('disables next button on last page', () => {
    render(React.createElement(PaginationControl, { ...defaultProps, currentPage: 10 }));
    expect(screen.getByLabelText('Next page')).toBeDisabled();
  });

  it('calls onPageChange when a page button is clicked', () => {
    render(React.createElement(PaginationControl, defaultProps));
    fireEvent.click(screen.getByLabelText('Go to page 4'));
    expect(defaultProps.onPageChange).toHaveBeenCalledWith(4);
  });

  it('calls onPageChange with previous page on prev click', () => {
    render(React.createElement(PaginationControl, defaultProps));
    fireEvent.click(screen.getByLabelText('Previous page'));
    expect(defaultProps.onPageChange).toHaveBeenCalledWith(2);
  });

  it('calls onPageChange with next page on next click', () => {
    render(React.createElement(PaginationControl, defaultProps));
    fireEvent.click(screen.getByLabelText('Next page'));
    expect(defaultProps.onPageChange).toHaveBeenCalledWith(4);
  });

  it('marks current page with aria-current', () => {
    render(React.createElement(PaginationControl, defaultProps));
    expect(screen.getByLabelText('Go to page 3')).toHaveAttribute('aria-current', 'page');
  });

  it('disables all buttons when isLoading', () => {
    render(React.createElement(PaginationControl, { ...defaultProps, isLoading: true }));
    expect(screen.getByLabelText('Previous page')).toBeDisabled();
    expect(screen.getByLabelText('Next page')).toBeDisabled();
  });
});
