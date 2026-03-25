import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { DelinkRequestForm } from './delink-request-form.component';

jest.mock('@/services/delink.service', () => ({
  delinkService: {
    createDelinkRequest: jest.fn(),
  },
}));

describe('DelinkRequestForm', () => {
  it('renders the form fields', () => {
    render(React.createElement(DelinkRequestForm));
    expect(screen.getByLabelText('Recycled SIM')).toBeInTheDocument();
    expect(screen.getByLabelText('Reason for Delinking')).toBeInTheDocument();
  });

  it('renders submit button', () => {
    render(React.createElement(DelinkRequestForm));
    expect(screen.getByText('Create Delink Request')).toBeInTheDocument();
  });

  it('pre-fills recycledSimId when provided', () => {
    render(React.createElement(DelinkRequestForm, { recycledSimId: 'SIM-123' }));
    const input = screen.getByLabelText('Recycled SIM');
    expect(input).toHaveValue('SIM-123');
  });

  it('disables recycledSimId input when pre-filled', () => {
    render(React.createElement(DelinkRequestForm, { recycledSimId: 'SIM-123' }));
    expect(screen.getByLabelText('Recycled SIM')).toBeDisabled();
  });

  it('has aria-invalid on fields', () => {
    render(React.createElement(DelinkRequestForm));
    expect(screen.getByLabelText('Recycled SIM')).toHaveAttribute('aria-invalid', 'false');
    expect(screen.getByLabelText('Reason for Delinking')).toHaveAttribute('aria-invalid', 'false');
  });

  it('has noValidate on the form', () => {
    const { container } = render(React.createElement(DelinkRequestForm));
    expect(container.querySelector('form')).toHaveAttribute('noValidate');
  });

  it('renders textarea with proper rows', () => {
    render(React.createElement(DelinkRequestForm));
    const textarea = screen.getByLabelText('Reason for Delinking');
    expect(textarea).toHaveAttribute('rows', '4');
  });
});
