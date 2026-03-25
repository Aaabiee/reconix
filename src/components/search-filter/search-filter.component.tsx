'use client';

import React from 'react';
import { SearchBar } from '@/components/search-bar/search-bar.component';
import './search-filter.component.scss';

interface FilterOption {
  label: string;
  value: string;
}

interface SearchFilterFormProps {
  onSearch: (query: string) => void;
  onFilterChange?: (filterName: string, value: string) => void;
  filters?: Array<{
    name: string;
    label: string;
    options: FilterOption[];
  }>;
}

export const SearchFilterForm: React.FC<SearchFilterFormProps> = ({
  onSearch,
  onFilterChange,
  filters = [],
}) => {
  return (
    <div className="search-filter space-y-4 bg-surface p-6 rounded-lg border border-secondary-100">
      <SearchBar placeholder="Search..." onSearch={onSearch} />

      {filters.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {filters.map((filter) => (
            <div key={filter.name}>
              <label htmlFor={filter.name} className="block text-sm font-medium text-default mb-2">
                {filter.label}
              </label>
              <select
                id={filter.name}
                onChange={(e) => onFilterChange?.(filter.name, e.target.value)}
                className="w-full px-4 py-2 border border-secondary-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">All {filter.label}</option>
                {filter.options.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
