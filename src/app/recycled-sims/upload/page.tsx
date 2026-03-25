'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { PageLayout } from '@/components/layout/PageLayout';
import { BulkUploadForm } from '@/components/forms/BulkUploadForm';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';

export default function BulkUploadPage(): JSX.Element {
  const router = useRouter();

  return (
    <PageLayout
      title="Bulk Upload Recycled SIMs"
      description="Upload a CSV file containing recycled SIM data"
      breadcrumbs={[
        { label: 'Recycled SIMs', href: '/recycled-sims' },
        { label: 'Bulk Upload' },
      ]}
    >
      <ErrorBoundary>
        <div className="bg-surface rounded-lg shadow-md p-8 border border-secondary-100 max-w-2xl mx-auto">
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-default mb-2">CSV Format Requirements</h3>
            <ul className="list-disc list-inside space-y-1 text-secondary-600 text-sm">
              <li>Column 1: Phone Number (e.g., 2348012345678)</li>
              <li>Column 2: NIN (e.g., 12345678901)</li>
              <li>Column 3: BVN (e.g., 22123456789)</li>
              <li>Column 4: Operator Code (e.g., MTN, GLO, AIRTEL, 9MOBILE)</li>
              <li>Column 5: Status (optional: active, recycled, dormant, blacklisted)</li>
            </ul>
          </div>

          <div className="border-t border-secondary-200 pt-6">
            <BulkUploadForm
              onSuccess={() => {
                setTimeout(() => {
                  router.push('/recycled-sims');
                }, 2000);
              }}
            />
          </div>
        </div>
      </ErrorBoundary>
    </PageLayout>
  );
}
