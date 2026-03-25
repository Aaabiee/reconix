import React from 'react';
import clsx from 'clsx';
import './status-badge.component.scss';

type StatusType = 'pending' | 'approved' | 'completed' | 'rejected' | 'failed' | 'active' | 'inactive' | 'success' | 'warning' | 'error';

interface StatusBadgeProps {
  status: StatusType;
  label?: string;
}

const statusStyles: Record<StatusType, { bg: string; text: string; border: string }> = {
  pending: { bg: 'bg-warning-50', text: 'text-warning-800', border: 'border-warning-200' },
  approved: { bg: 'bg-primary-50', text: 'text-primary-800', border: 'border-primary-200' },
  completed: { bg: 'bg-success-50', text: 'text-success-800', border: 'border-success-200' },
  rejected: { bg: 'bg-error-50', text: 'text-error-800', border: 'border-error-200' },
  failed: { bg: 'bg-error-50', text: 'text-error-800', border: 'border-error-200' },
  active: { bg: 'bg-success-50', text: 'text-success-800', border: 'border-success-200' },
  inactive: { bg: 'bg-secondary-50', text: 'text-secondary-800', border: 'border-secondary-200' },
  success: { bg: 'bg-success-50', text: 'text-success-800', border: 'border-success-200' },
  warning: { bg: 'bg-warning-50', text: 'text-warning-800', border: 'border-warning-200' },
  error: { bg: 'bg-error-50', text: 'text-error-800', border: 'border-error-200' },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label }) => {
  const styles = statusStyles[status];
  const displayLabel = label || status.charAt(0).toUpperCase() + status.slice(1);

  return (
    <span
      className={clsx(
        'status-badge inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border',
        styles.bg,
        styles.text,
        styles.border
      )}
    >
      {displayLabel}
    </span>
  );
};
