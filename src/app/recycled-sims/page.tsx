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
import { recycledSimsService } from '@/services/recycled-sims.service';
import { RecycledSim } from '@/types/models.types';
import Link from 'next/link';
import { Upload } from 'lucide-react';

export default function RecycledSimsPage(): JSX.Element {
  const router = useRouter();
  const { page, pageSize, goToPage } = usePagination();
  const [search, setSearch] = React.useState('');
  const [status, setStatus] = React.useState('');
  const debouncedSearch = useDebounce(search, 500);

  const { data: result, isLoading, error, refetch } = useApiQuery(
    () =>
      recycledSimsService.getRecycledSims({
        page,
        pageSize,
        search: debouncedSearch,
        status,
      }),
    [page, pageSize, debouncedSearch, status]
  );

  const columns: Column<RecycledSim>[] = [
    {
      key: 'phoneNumber',
      header: 'Phone Number',
      sortable: true,
    },
    {
      key: 'nin',
      header: 'NIN',
      sortable: true,
    },
    {
      key: 'bvn',
      header: 'BVN',
    },
    {
      key: 'operatorName',
      header: 'Operator',
      sortable: true,
    },
    {
      key: 'simStatus',
      header: 'Status',
      render: (status) => <StatusBadge status={status as any} />,
    },
    {
      key: 'recycledDate',
      header: 'Recycled Date',
    },
  ];

  return (
    <PageLayout
      title="Recycled SIMs"
      description="View and manage recycled SIM cards linked to old NIN/BVN records"
      breadcrumbs={[{ label: 'Recycled SIMs' }]}
      header={
        <div className="flex gap-4">
          <Link
            href="/recycled-sims/upload"
            className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-surface rounded-lg hover:bg-primary-600 font-medium transition-colors"
          >
            <Upload size={18} />
            Bulk Upload
          </Link>
        </div>
      }
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
                { label: 'Active', value: 'active' },
                { label: 'Recycled', value: 'recycled' },
                { label: 'Dormant', value: 'dormant' },
                { label: 'Blacklisted', value: 'blacklisted' },
              ],
            },
          ]}
        />
      </ErrorBoundary>

      {error && (
        <div className="p-4 bg-error-50 border border-error-200 rounded-lg text-error-800">
          Failed to load recycled SIMs. Please try again.
        </div>
      )}

      {!error && (
        <ErrorBoundary>
          <DataTable
            columns={columns}
            data={result?.items || []}
            isLoading={isLoading}
            onRowClick={(row) => router.push(`/recycled-sims/${row.id}`)}
            pagination={
              result ? {
                currentPage: result.page,
                totalPages: result.totalPages,
                onPageChange: goToPage,
              } : undefined
            }
            emptyMessage="No recycled SIMs found. Try adjusting your search filters."
          />
        </ErrorBoundary>
      )}
    </PageLayout>
  );
}
