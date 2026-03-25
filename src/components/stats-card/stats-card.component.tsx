import React from 'react';
import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';
import './stats-card.component.scss';

interface StatsCardProps {
  icon: LucideIcon;
  title: string;
  value: number | string;
  change?: number;
  changeLabel?: string;
  color?: 'primary' | 'secondary' | 'accent' | 'success' | 'warning' | 'error';
}

const borderColors: Record<string, string> = {
  primary: 'border-l-primary-500',
  secondary: 'border-l-secondary-500',
  accent: 'border-l-accent-500',
  success: 'border-l-success-500',
  warning: 'border-l-warning-500',
  error: 'border-l-error-500',
};

const iconBgColors: Record<string, string> = {
  primary: 'bg-primary-50 text-primary-600',
  secondary: 'bg-secondary-50 text-secondary-600',
  accent: 'bg-accent-50 text-accent-600',
  success: 'bg-success-50 text-success-600',
  warning: 'bg-warning-50 text-warning-600',
  error: 'bg-error-50 text-error-600',
};

export const StatsCard: React.FC<StatsCardProps> = ({
  icon: Icon,
  title,
  value,
  change,
  changeLabel,
  color = 'primary',
}) => {
  const isPositive = change !== undefined && change >= 0;

  return (
    <div
      className={`
        stats-card bg-white rounded-material-md shadow-elevation-1 p-6
        border-l-4 ${borderColors[color]}
        transition-all duration-300 ease-out
        hover:shadow-elevation-3 hover:-translate-y-0.5
      `}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-500 uppercase tracking-wider">
            {title}
          </p>
          <p className="text-3xl font-bold text-default mt-2 tabular-nums">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
          {change !== undefined && (
            <div className={`flex items-center gap-1.5 mt-3 text-sm font-semibold ${
              isPositive ? 'text-success-600' : 'text-error-600'
            }`}>
              {isPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
              <span>
                {isPositive ? '+' : ''}{change}%
              </span>
              <span className="text-gray-400 font-normal text-xs">
                {changeLabel || 'vs last month'}
              </span>
            </div>
          )}
        </div>
        <div className={`${iconBgColors[color]} rounded-material-md p-3 ml-4 flex-shrink-0`}>
          <Icon size={24} strokeWidth={1.8} />
        </div>
      </div>
    </div>
  );
};
