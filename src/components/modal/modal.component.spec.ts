import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { Modal } from './modal.component';

jest.mock('lucide-react', () => ({
  X: () => React.createElement('span', { 'data-testid': 'x-icon' }, 'X'),
}));

describe('Modal', () => {
  const defaultProps = {
    isOpen: true,
    title: 'Test Modal',
    onClose: jest.fn(),
    children: React.createElement('p', null, 'Modal content'),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders when isOpen is true', () => {
    render(React.createElement(Modal, defaultProps));
    expect(screen.getByText('Test Modal')).toBeInTheDocument();
    expect(screen.getByText('Modal content')).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    render(React.createElement(Modal, { ...defaultProps, isOpen: false }));
    expect(screen.queryByText('Test Modal')).not.toBeInTheDocument();
  });

  it('has proper aria attributes', () => {
    render(React.createElement(Modal, defaultProps));
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby', 'modal-title');
  });

  it('calls onClose when close button is clicked', () => {
    render(React.createElement(Modal, defaultProps));
    fireEvent.click(screen.getByLabelText('Close modal'));
    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it('calls onClose on Escape key', () => {
    render(React.createElement(Modal, defaultProps));
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it('does not call onClose on Escape when isLoading', () => {
    const onClose = jest.fn();
    render(React.createElement(Modal, { ...defaultProps, onClose, isLoading: true }));
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).not.toHaveBeenCalled();
  });

  it('renders confirm and cancel buttons', () => {
    const onConfirm = jest.fn();
    render(React.createElement(Modal, { ...defaultProps, onConfirm, confirmText: 'OK', cancelText: 'No' }));
    expect(screen.getByText('OK')).toBeInTheDocument();
    expect(screen.getByText('No')).toBeInTheDocument();
  });

  it('calls onConfirm when confirm button is clicked', () => {
    const onConfirm = jest.fn();
    render(React.createElement(Modal, { ...defaultProps, onConfirm }));
    fireEvent.click(screen.getByText('Confirm'));
    expect(onConfirm).toHaveBeenCalled();
  });

  it('disables buttons when isLoading', () => {
    const onConfirm = jest.fn();
    render(React.createElement(Modal, { ...defaultProps, onConfirm, isLoading: true }));
    expect(screen.getByLabelText('Close modal')).toBeDisabled();
  });
});
