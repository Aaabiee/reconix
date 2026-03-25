import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';

const mockPush = jest.fn();
const mockLogin = jest.fn();
const mockLogout = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => '/',
}));

jest.mock('next/image', () => {
  return (props: any) => React.createElement('img', props);
});

jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: null,
    login: mockLogin,
    logout: mockLogout,
    isLoading: false,
    error: null,
  }),
}));

jest.mock('@/hooks/useDebounce', () => ({
  useDebounce: (val: string) => val,
}));

describe('Authentication Flow Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the login page when user is not authenticated', async () => {
    const { LoginForm } = await import('@/components/login/login.component');
    render(React.createElement(LoginForm));

    expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByText('Sign In')).toBeInTheDocument();
  });

  it('displays email and password input fields with correct types', async () => {
    const { LoginForm } = await import('@/components/login/login.component');
    render(React.createElement(LoginForm));

    const emailInput = screen.getByLabelText('Email Address');
    const passwordInput = screen.getByLabelText('Password');

    expect(emailInput).toHaveAttribute('type', 'email');
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  it('has autocomplete attributes for credential management', async () => {
    const { LoginForm } = await import('@/components/login/login.component');
    render(React.createElement(LoginForm));

    expect(screen.getByLabelText('Email Address')).toHaveAttribute('autoComplete', 'email');
    expect(screen.getByLabelText('Password')).toHaveAttribute('autoComplete', 'current-password');
  });

  it('form uses noValidate to rely on custom validation', async () => {
    const { LoginForm } = await import('@/components/login/login.component');
    const { container } = render(React.createElement(LoginForm));

    expect(container.querySelector('form')).toHaveAttribute('noValidate');
  });

  it('has proper aria-invalid attributes on initial render', async () => {
    const { LoginForm } = await import('@/components/login/login.component');
    render(React.createElement(LoginForm));

    expect(screen.getByLabelText('Email Address')).toHaveAttribute('aria-invalid', 'false');
    expect(screen.getByLabelText('Password')).toHaveAttribute('aria-invalid', 'false');
  });

  it('submit button is not disabled initially', async () => {
    const { LoginForm } = await import('@/components/login/login.component');
    render(React.createElement(LoginForm));

    expect(screen.getByText('Sign In')).not.toBeDisabled();
  });

  it('user can type into email and password fields', async () => {
    const { LoginForm } = await import('@/components/login/login.component');
    render(React.createElement(LoginForm));

    const emailInput = screen.getByLabelText('Email Address');
    const passwordInput = screen.getByLabelText('Password');

    fireEvent.change(emailInput, { target: { value: 'admin@reconix.gov.ng' } });
    fireEvent.change(passwordInput, { target: { value: 'SecurePass123' } });

    expect(emailInput).toHaveValue('admin@reconix.gov.ng');
    expect(passwordInput).toHaveValue('SecurePass123');
  });
});
