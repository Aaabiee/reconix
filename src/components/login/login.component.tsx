'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '@/hooks/useAuth';
import { Mail, Lock, AlertCircle } from 'lucide-react';
import './login.component.scss';

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(12, 'Password must be at least 12 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

interface LoginFormProps {
  onSuccess?: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSuccess }) => {
  const { login, isLoading, error } = useAuth();
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData): Promise<void> => {
    setSubmitError(null);

    try {
      await login(data);
      onSuccess?.();
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Login failed. Please try again.';
      setSubmitError(errorMessage);
    }
  };

  const displayError = submitError || error;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="login-form space-y-5" noValidate>
      {displayError && (
        <div className="flex items-start gap-3 p-4 bg-error-50 border border-error-200
                        rounded-material text-error-700 text-sm animate-slide-down"
             role="alert">
          <AlertCircle size={18} className="flex-shrink-0 mt-0.5" />
          <span>{displayError}</span>
        </div>
      )}

      <div className="space-y-1.5">
        <label htmlFor="email" className="input-label">
          Email Address
        </label>
        <div className="relative">
          <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
            <Mail size={18} />
          </div>
          <input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@organization.gov.ng"
            className={`input-field pl-11 ${
              errors.email
                ? 'border-error-400 focus:border-error-500 bg-error-50/30'
                : ''
            }`}
            {...register('email')}
            aria-invalid={errors.email ? 'true' : 'false'}
            aria-describedby={errors.email ? 'email-error' : undefined}
          />
        </div>
        {errors.email && (
          <p id="email-error" className="text-error-600 text-xs font-medium mt-1 animate-slide-down">
            {errors.email.message}
          </p>
        )}
      </div>

      <div className="space-y-1.5">
        <label htmlFor="password" className="input-label">
          Password
        </label>
        <div className="relative">
          <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
            <Lock size={18} />
          </div>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            placeholder="Enter your password"
            className={`input-field pl-11 ${
              errors.password
                ? 'border-error-400 focus:border-error-500 bg-error-50/30'
                : ''
            }`}
            {...register('password')}
            aria-invalid={errors.password ? 'true' : 'false'}
            aria-describedby={errors.password ? 'password-error' : undefined}
          />
        </div>
        {errors.password && (
          <p id="password-error" className="text-error-600 text-xs font-medium mt-1 animate-slide-down">
            {errors.password.message}
          </p>
        )}
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="btn-primary w-full py-3 text-base mt-2"
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            Signing in...
          </span>
        ) : (
          'Sign In'
        )}
      </button>
    </form>
  );
};
