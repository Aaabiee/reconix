import React from 'react';
import { InboxIcon } from 'lucide-react';
import './empty-state.component.scss';

interface EmptyStateProps {
  icon?: React.ElementType;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon = InboxIcon,
  title,
  description,
  action,
}) => {
  return (
    <div className="empty-state flex flex-col items-center justify-center py-12 px-4">
      <Icon className="text-secondary-400 mb-4" size={48} />
      <h3 className="text-lg font-semibold text-default mb-2">{title}</h3>
      <p className="text-secondary-600 text-center mb-6 max-w-md">{description}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="px-4 py-2 bg-primary-500 text-surface rounded-lg hover:bg-primary-600 transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  );
};
