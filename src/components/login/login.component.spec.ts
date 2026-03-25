import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { LoginForm } from './login.component';

const mockLogin = jest.fn();

jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    login: mockLogin,
    isLoading: false,
    error: null,
  }),
}));

jest.mock('react-hook-form', () => {
  const actual = jest.requireActual('react-hook-form');
  return { ...actual };
});

jest.mock('lucide-react', () => ({
  Mail: () => React.createElement('span', null, 'mail'),
  Lock: () => React.createElement('span', null, 'lock'),
  AlertCircle: () => React.createElement('span', null, 'alert'),
}));

describe('LoginForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders email and password fields', () => {
    render(React.createElement(LoginForm));
    expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
  });

  it('renders submit button', () => {
    render(React.createElement(LoginForm));
    expect(screen.getByText('Sign In')).toBeInTheDocument();
  });

  it('email field has correct type', () => {
    render(React.createElement(LoginForm));
    const emailInput = screen.getByLabelText('Email Address');
    expect(emailInput).toHaveAttribute('type', 'email');
  });

  it('password field has correct type', () => {
    render(React.createElement(LoginForm));
    const passwordInput = screen.getByLabelText('Password');
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  it('has autocomplete attributes for security', () => {
    render(React.createElement(LoginForm));
    expect(screen.getByLabelText('Email Address')).toHaveAttribute('autoComplete', 'email');
    expect(screen.getByLabelText('Password')).toHaveAttribute('autoComplete', 'current-password');
  });

  it('form has noValidate to use custom validation', () => {
    const { container } = render(React.createElement(LoginForm));
    expect(container.querySelector('form')).toHaveAttribute('noValidate');
  });

  it('has aria-invalid attribute on fields', () => {
    render(React.createElement(LoginForm));
    expect(screen.getByLabelText('Email Address')).toHaveAttribute('aria-invalid', 'false');
    expect(screen.getByLabelText('Password')).toHaveAttribute('aria-invalid', 'false');
  });

  it('enforces minimum 12 character password matching backend policy', async () => {
    render(React.createElement(LoginForm));
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByText('Sign In');

    fireEvent.change(passwordInput, { target: { value: 'short123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/at least 12 characters/i)).toBeInTheDocument();
    });
  });
});
