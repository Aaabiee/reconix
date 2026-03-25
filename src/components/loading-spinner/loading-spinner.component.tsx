import React from 'react';
import './loading-spinner.component.scss';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 'md', text }) => {
  const sizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
  };

  const textSizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
  };

  return (
    <div className="loading-spinner flex flex-col items-center justify-center gap-4">
      <div
        className={`${sizeClasses[size]} border-4 border-primary-200 border-t-primary-500 rounded-full animate-spin`}
        role="status"
        aria-label="Loading"
      />
      {text && <p className={`${textSizeClasses[size]} text-secondary-600`}>{text}</p>}
    </div>
  );
};
