import React, { ReactNode, useState } from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { EmptyState } from '@/components/empty-state/empty-state.component';
import { PaginationControl } from '@/components/pagination-control/pagination-control.component';
import './data-table.component.scss';

export interface Column<T> {
  key: keyof T;
  header: string;
  render?: (value: T[keyof T], row: T) => ReactNode;
  sortable?: boolean;
  width?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  isLoading?: boolean;
  isSortable?: boolean;
  onSort?: (key: string, order: 'asc' | 'desc') => void;
  pagination?: {
    currentPage: number;
    totalPages: number;
    onPageChange: (page: number) => void;
  };
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
}

type SortConfig = {
  key: string;
  order: 'asc' | 'desc';
} | null;

export const DataTable = React.forwardRef<HTMLDivElement, DataTableProps<any>>(
  (
    {
      columns,
      data,
      isLoading = false,
      isSortable = true,
      onSort,
      pagination,
      onRowClick,
      emptyMessage = 'No data found',
    },
    ref
  ) => {
    const [sortConfig, setSortConfig] = useState<SortConfig>(null);

    const handleSort = (key: string): void => {
      if (!isSortable) return;

      let order: 'asc' | 'desc' = 'asc';
      if (sortConfig?.key === key && sortConfig.order === 'asc') {
        order = 'desc';
      }

      setSortConfig({ key, order });
      if (onSort) {
        onSort(key, order);
      }
    };

    const getSortIcon = (key: string): ReactNode => {
      if (!isSortable) return null;

      if (sortConfig?.key === key) {
        return sortConfig.order === 'asc' ? (
          <ArrowUp size={14} className="text-primary-500" />
        ) : (
          <ArrowDown size={14} className="text-primary-500" />
        );
      }

      return <ArrowUpDown size={14} className="text-gray-300" />;
    };

    if (isLoading) {
      return (
        <div className="data-table data-table--loading bg-white rounded-material-md shadow-elevation-1 overflow-hidden">
          <div className="p-0">
            <div className="border-b border-surface-200 bg-surface-50 px-6 py-3 flex gap-6">
              {columns.map((_col, i) => (
                <div key={i} className="skeleton-shimmer h-4 flex-1" />
              ))}
            </div>
            {Array.from({ length: 5 }).map((_, rowIdx) => (
              <div key={rowIdx} className="px-6 py-4 flex gap-6 border-b border-surface-100">
                {columns.map((_, colIdx) => (
                  <div key={colIdx} className="skeleton-shimmer h-4 flex-1" />
                ))}
              </div>
            ))}
          </div>
        </div>
      );
    }

    if (!data || data.length === 0) {
      return (
        <div className="data-table data-table--empty bg-white rounded-material-md shadow-elevation-1 p-8">
          <EmptyState title="No Results" description={emptyMessage} />
        </div>
      );
    }

    return (
      <div ref={ref} className="data-table space-y-4">
        <div className="bg-white rounded-material-md shadow-elevation-1 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-surface-50 border-b-2 border-surface-200">
                  {columns.map((column) => (
                    <th
                      key={String(column.key)}
                      className={`px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider ${
                        column.sortable ? 'cursor-pointer select-none hover:bg-surface-100 transition-colors' : ''
                      } ${column.width || ''}`}
                      onClick={() => {
                        if (column.sortable) {
                          handleSort(String(column.key));
                        }
                      }}
                    >
                      <div className="flex items-center gap-2">
                        {column.header}
                        {column.sortable && getSortIcon(String(column.key))}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100">
                {data.map((row, idx) => (
                  <tr
                    key={idx}
                    className={`
                      transition-colors duration-150
                      ${idx % 2 === 0 ? 'bg-white' : 'bg-surface-50/50'}
                      hover:bg-primary-50/40
                      ${onRowClick ? 'cursor-pointer' : ''}
                    `}
                    onClick={() => onRowClick?.(row)}
                  >
                    {columns.map((column) => (
                      <td
                        key={String(column.key)}
                        className="px-6 py-4 text-sm text-default whitespace-nowrap"
                      >
                        {column.render
                          ? column.render(row[column.key], row)
                          : String(row[column.key] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {pagination && (
          <div className="flex justify-center pt-2">
            <PaginationControl
              currentPage={pagination.currentPage}
              totalPages={pagination.totalPages}
              onPageChange={pagination.onPageChange}
              isLoading={isLoading}
            />
          </div>
        )}
      </div>
    );
  }
);

DataTable.displayName = 'DataTable';
