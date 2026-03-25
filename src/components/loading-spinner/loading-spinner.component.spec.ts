import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { LoadingSpinner } from './loading-spinner.component';

describe('LoadingSpinner', () => {
  it('renders spinner with status role', () => {
    render(React.createElement(LoadingSpinner));
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('has accessible label', () => {
    render(React.createElement(LoadingSpinner));
    expect(screen.getByLabelText('Loading')).toBeInTheDocument();
  });

  it('renders text when provided', () => {
    render(React.createElement(LoadingSpinner, { text: 'Please wait...' }));
    expect(screen.getByText('Please wait...')).toBeInTheDocument();
  });

  it('does not render text when not provided', () => {
    const { container } = render(React.createElement(LoadingSpinner));
    expect(container.querySelector('p')).toBeNull();
  });

  it('applies small size classes', () => {
    render(React.createElement(LoadingSpinner, { size: 'sm' }));
    const spinner = screen.getByRole('status');
    expect(spinner).toHaveClass('w-6', 'h-6');
  });

  it('applies large size classes', () => {
    render(React.createElement(LoadingSpinner, { size: 'lg' }));
    const spinner = screen.getByRole('status');
    expect(spinner).toHaveClass('w-16', 'h-16');
  });

  it('defaults to medium size', () => {
    render(React.createElement(LoadingSpinner));
    const spinner = screen.getByRole('status');
    expect(spinner).toHaveClass('w-12', 'h-12');
  });
});
