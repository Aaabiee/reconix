'use client';

import React from 'react';
import { PageLayout } from '@/components/page-layout/page-layout.component';
import { DataTable, Column } from '@/components/data-table/data-table.component';
import { SearchFilterForm } from '@/components/search-filter/search-filter.component';
import { ErrorBoundary } from '@/components/error-boundary/error-boundary.component';
import { usePagination } from '@/hooks/usePagination';
import { useDebounce } from '@/hooks/useDebounce';
import { useApiQuery } from '@/hooks/useApiQuery';
import { auditService } from '@/services/audit.service';
import { AuditLog } from '@/types/models.types';
import { format } from 'date-fns';
import { StatusBadge } from '@/components/status-badge/status-badge.component';

export default function AuditLogsPage(): JSX.Element {
  const { page, pageSize, goToPage } = usePagination();
  const [search, setSearch] = React.useState('');
  const debouncedSearch = useDebounce(search, 500);

  const { data: result, isLoading, error } = useApiQuery(
    () =>
      auditService.getAuditLogs({
        page,
        pageSize,
        search: debouncedSearch,
      }),
    [page, pageSize, debouncedSearch]
  );

  const columns: Column<AuditLog>[] = [
    {
      key: 'userEmail',
      header: 'User',
      sortable: true,
    },
    {
      key: 'action',
      header: 'Action',
      sortable: true,
    },
    {
      key: 'entityType',
      header: 'Entity Type',
    },
    {
      key: 'status',
      header: 'Status',
      render: (status) => (
        <StatusBadge
          status={(status === 'success' ? 'completed' : 'failed') as any}
          label={status as string}
        />
      ),
    },
    {
      key: 'createdAt',
      header: 'Timestamp',
      render: (date) => format(new Date(date as string), 'MMM dd, yyyy HH:mm'),
    },
  ];

  return (
    <PageLayout
      title="Audit Logs"
      description="View system activity and changes made by users"
      breadcrumbs={[{ label: 'Audit Logs' }]}
    >
      <ErrorBoundary>
        <SearchFilterForm onSearch={setSearch} />
      </ErrorBoundary>

      {error && (
        <div className="p-4 bg-error-50 border border-error-200 rounded-lg text-error-800">
          Failed to load audit logs. Please try again.
        </div>
      )}

      {!error && (
        <ErrorBoundary>
          <DataTable
            columns={columns}
            data={result?.items || []}
            isLoading={isLoading}
            pagination={
              result
                ? {
                    currentPage: result.page,
                    totalPages: result.totalPages,
                    onPageChange: goToPage,
                  }
                : undefined
            }
            emptyMessage="No audit logs found."
          />
        </ErrorBoundary>
      )}
    </PageLayout>
  );
}
