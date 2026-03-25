import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { StatusBadge } from './status-badge.component';

describe('StatusBadge', () => {
  it('renders with default label from status', () => {
    render(React.createElement(StatusBadge, { status: 'pending' }));
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('renders with custom label', () => {
    render(React.createElement(StatusBadge, { status: 'active', label: 'Online' }));
    expect(screen.getByText('Online')).toBeInTheDocument();
  });

  it('applies correct CSS classes for completed status', () => {
    const { container } = render(React.createElement(StatusBadge, { status: 'completed' }));
    const badge = container.querySelector('.status-badge');
    expect(badge).toHaveClass('bg-success-50');
    expect(badge).toHaveClass('text-success-800');
    expect(badge).toHaveClass('border-success-200');
  });

  it('applies correct CSS classes for error status', () => {
    const { container } = render(React.createElement(StatusBadge, { status: 'error' }));
    const badge = container.querySelector('.status-badge');
    expect(badge).toHaveClass('bg-error-50');
    expect(badge).toHaveClass('text-error-800');
  });

  it('capitalizes status name correctly', () => {
    render(React.createElement(StatusBadge, { status: 'approved' }));
    expect(screen.getByText('Approved')).toBeInTheDocument();
  });

  it('renders as a span element', () => {
    const { container } = render(React.createElement(StatusBadge, { status: 'active' }));
    expect(container.querySelector('span.status-badge')).toBeInTheDocument();
  });
});
