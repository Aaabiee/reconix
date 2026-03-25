'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { PageLayout } from '@/components/layout/PageLayout';
import { DataTable, Column } from '@/components/ui/DataTable';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { SearchFilterForm } from '@/components/forms/SearchFilterForm';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { usePagination } from '@/hooks/usePagination';
import { useDebounce } from '@/hooks/useDebounce';
import { useApiQuery } from '@/hooks/useApiQuery';
import { delinkService } from '@/services/delink.service';
import { DelinkRequest } from '@/types/models.types';
import { format } from 'date-fns';

export default function DelinkRequestsPage(): JSX.Element {
  const router = useRouter();
  const { page, pageSize, goToPage } = usePagination();
  const [search, setSearch] = React.useState('');
  const [status, setStatus] = React.useState('');
  const debouncedSearch = useDebounce(search, 500);

  const { data: result, isLoading, error } = useApiQuery(
    () =>
      delinkService.getDelinkRequests({
        page,
        pageSize,
        search: debouncedSearch,
        status,
      }),
    [page, pageSize, debouncedSearch, status]
  );

  const columns: Column<DelinkRequest>[] = [
    {
      key: 'phoneNumber',
      header: 'Phone Number',
      sortable: true,
    },
    {
      key: 'nin',
      header: 'NIN',
    },
    {
      key: 'status',
      header: 'Status',
      render: (status) => <StatusBadge status={status as any} />,
    },
    {
      key: 'requestedAt',
      header: 'Requested Date',
      render: (date) => format(new Date(date as string), 'MMM dd, yyyy'),
    },
    {
      key: 'requestedBy',
      header: 'Requested By',
    },
  ];

  return (
    <PageLayout
      title="Delink Requests"
      description="Manage delink requests to remove old NIN/BVN associations from recycled SIMs"
      breadcrumbs={[{ label: 'Delink Requests' }]}
    >
      <ErrorBoundary>
        <SearchFilterForm
          onSearch={setSearch}
          onFilterChange={(name, value) => {
            if (name === 'status') setStatus(value);
          }}
          filters={[
            {
              name: 'status',
              label: 'Status',
              options: [
                { label: 'Pending', value: 'pending' },
                { label: 'Approved', value: 'approved' },
                { label: 'Completed', value: 'completed' },
                { label: 'Rejected', value: 'rejected' },
                { label: 'Cancelled', value: 'cancelled' },
              ],
            },
          ]}
        />
      </ErrorBoundary>

      {error && (
        <div className="p-4 bg-error-50 border border-error-200 rounded-lg text-error-800">
          Failed to load delink requests. Please try again.
        </div>
      )}

      {!error && (
        <ErrorBoundary>
          <DataTable
            columns={columns}
            data={result?.items || []}
            isLoading={isLoading}
            onRowClick={(row) => router.push(`/delink-requests/${row.id}`)}
            pagination={
              result
                ? {
                    currentPage: result.page,
                    totalPages: result.totalPages,
                    onPageChange: goToPage,
                  }
                : undefined
            }
            emptyMessage="No delink requests found."
          />
        </ErrorBoundary>
      )}
    </PageLayout>
  );
}
