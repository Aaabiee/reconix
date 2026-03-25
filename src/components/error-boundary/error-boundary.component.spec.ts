import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { ErrorBoundary } from './error-boundary.component';

jest.mock('lucide-react', () => ({
  AlertCircle: (props: any) => React.createElement('svg', { 'data-testid': 'alert-icon', ...props }),
}));

const ThrowingComponent = () => {
  throw new Error('Test error');
};

const GoodComponent = () => React.createElement('div', null, 'Working fine');

describe('ErrorBoundary', () => {
  beforeEach(() => {
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    (console.error as jest.Mock).mockRestore();
  });

  it('renders children when no error', () => {
    render(React.createElement(ErrorBoundary, null, React.createElement(GoodComponent)));
    expect(screen.getByText('Working fine')).toBeInTheDocument();
  });

  it('renders error message when child throws', () => {
    render(React.createElement(ErrorBoundary, null, React.createElement(ThrowingComponent)));
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('Test error')).toBeInTheDocument();
  });

  it('renders custom fallback when provided', () => {
    const fallback = React.createElement('div', null, 'Custom fallback');
    render(React.createElement(ErrorBoundary, { fallback }, React.createElement(ThrowingComponent)));
    expect(screen.getByText('Custom fallback')).toBeInTheDocument();
  });

  it('renders alert icon in default error UI', () => {
    render(React.createElement(ErrorBoundary, null, React.createElement(ThrowingComponent)));
    expect(screen.getByTestId('alert-icon')).toBeInTheDocument();
  });

  it('calls console.error when error is caught', () => {
    render(React.createElement(ErrorBoundary, null, React.createElement(ThrowingComponent)));
    expect(console.error).toHaveBeenCalled();
  });
});
