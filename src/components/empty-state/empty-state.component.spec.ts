import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { EmptyState } from './empty-state.component';

jest.mock('lucide-react', () => ({
  InboxIcon: (props: any) => React.createElement('svg', { 'data-testid': 'inbox-icon', ...props }),
}));

describe('EmptyState', () => {
  it('renders title and description', () => {
    render(React.createElement(EmptyState, { title: 'No Data', description: 'Nothing to show' }));
    expect(screen.getByText('No Data')).toBeInTheDocument();
    expect(screen.getByText('Nothing to show')).toBeInTheDocument();
  });

  it('renders default icon', () => {
    render(React.createElement(EmptyState, { title: 'Empty', description: 'desc' }));
    expect(screen.getByTestId('inbox-icon')).toBeInTheDocument();
  });

  it('renders custom icon', () => {
    const CustomIcon = (props: any) => React.createElement('div', { 'data-testid': 'custom-icon', ...props });
    render(React.createElement(EmptyState, { title: 'Empty', description: 'desc', icon: CustomIcon }));
    expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
  });

  it('renders action button when provided', () => {
    const onClick = jest.fn();
    render(React.createElement(EmptyState, {
      title: 'Empty',
      description: 'desc',
      action: { label: 'Add Item', onClick },
    }));
    expect(screen.getByText('Add Item')).toBeInTheDocument();
  });

  it('calls action onClick when button is clicked', () => {
    const onClick = jest.fn();
    render(React.createElement(EmptyState, {
      title: 'Empty',
      description: 'desc',
      action: { label: 'Add Item', onClick },
    }));
    fireEvent.click(screen.getByText('Add Item'));
    expect(onClick).toHaveBeenCalled();
  });

  it('does not render action button when not provided', () => {
    const { container } = render(React.createElement(EmptyState, { title: 'Empty', description: 'desc' }));
    expect(container.querySelector('button')).toBeNull();
  });
});
