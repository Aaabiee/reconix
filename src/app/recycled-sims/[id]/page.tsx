'use client';

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { PageLayout } from '@/components/page-layout/page-layout.component';
import { StatusBadge } from '@/components/status-badge/status-badge.component';
import { Modal } from '@/components/modal/modal.component';
import { DelinkRequestForm } from '@/components/delink-request-form/delink-request-form.component';
import { LoadingSpinner } from '@/components/loading-spinner/loading-spinner.component';
import { ErrorBoundary } from '@/components/error-boundary/error-boundary.component';
import { useApiQuery } from '@/hooks/useApiQuery';
import { recycledSimsService } from '@/services/recycled-sims.service';
import { format } from 'date-fns';
import { AlertCircle } from 'lucide-react';

export default function RecycledSimDetailPage(): JSX.Element {
  const params = useParams();
  const router = useRouter();
  const [showDelinkModal, setShowDelinkModal] = React.useState(false);
  const id = params.id as string;

  const { data: sim, isLoading, error } = useApiQuery(
    () => recycledSimsService.getRecycledSimById(id),
    [id]
  );

  if (isLoading) {
    return (
      <PageLayout title="Loading...">
        <LoadingSpinner text="Loading SIM details..." />
      </PageLayout>
    );
  }

  if (error || !sim) {
    return (
      <PageLayout
        title="Error"
        breadcrumbs={[{ label: 'Recycled SIMs', href: '/recycled-sims' }]}
      >
        <div className="p-4 bg-error-50 border border-error-200 rounded-lg text-error-800">
          Failed to load SIM details. Please try again.
        </div>
      </PageLayout>
    );
  }

  return (
    <PageLayout
      title={`SIM: ${sim.phoneNumber}`}
      breadcrumbs={[{ label: 'Recycled SIMs', href: '/recycled-sims' }, { label: sim.phoneNumber }]}
    >
      <ErrorBoundary>
        <div className="bg-surface rounded-lg shadow-md p-8 border border-secondary-100">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-6">
              <div>
                <label className="text-sm text-secondary-600">Phone Number</label>
                <p className="text-xl font-semibold text-default mt-1">{sim.phoneNumber}</p>
              </div>

              <div>
                <label className="text-sm text-secondary-600">Status</label>
                <div className="mt-1">
                  <StatusBadge status={sim.simStatus as any} />
                </div>
              </div>

              <div>
                <label className="text-sm text-secondary-600">NIN</label>
                <p className="text-lg font-mono text-default mt-1">{sim.nin}</p>
              </div>

              <div>
                <label className="text-sm text-secondary-600">BVN</label>
                <p className="text-lg font-mono text-default mt-1">{sim.bvn}</p>
              </div>

              <div>
                <label className="text-sm text-secondary-600">Operator</label>
                <p className="text-lg text-default mt-1">{sim.operatorName}</p>
              </div>
            </div>

            <div className="space-y-6">
              <div>
                <label className="text-sm text-secondary-600">Last Used Date</label>
                <p className="text-lg text-default mt-1">
                  {format(new Date(sim.lastUsedDate), 'PPP p')}
                </p>
              </div>

              <div>
                <label className="text-sm text-secondary-600">Recycled Date</label>
                <p className="text-lg text-default mt-1">
                  {format(new Date(sim.recycledDate), 'PPP p')}
                </p>
              </div>

              <div>
                <label className="text-sm text-secondary-600">Detection Method</label>
                <p className="text-lg text-default mt-1">{sim.detectionMethod}</p>
              </div>

              {sim.notes && (
                <div>
                  <label className="text-sm text-secondary-600">Notes</label>
                  <p className="text-lg text-default mt-1">{sim.notes}</p>
                </div>
              )}

              <div className="pt-4 border-t border-secondary-200">
                <p className="text-xs text-secondary-500 mb-2">
                  Created: {format(new Date(sim.createdAt), 'PPP p')}
                </p>
                <p className="text-xs text-secondary-500">
                  Updated: {format(new Date(sim.updatedAt), 'PPP p')}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-8 p-4 bg-warning-50 border border-warning-200 rounded-lg flex gap-3">
            <AlertCircle className="text-warning-600 flex-shrink-0 mt-0.5" size={20} />
            <div>
              <p className="font-medium text-warning-900">Action Required</p>
              <p className="text-warning-800 text-sm mt-1">
                This SIM card has been detected as recycled. Please create a delink request to
                remove the old NIN/BVN associations.
              </p>
            </div>
          </div>

          <button
            onClick={() => setShowDelinkModal(true)}
            className="mt-6 px-6 py-2 bg-primary-500 text-surface rounded-lg hover:bg-primary-600 font-medium transition-colors"
          >
            Create Delink Request
          </button>
        </div>
      </ErrorBoundary>

      <Modal
        isOpen={showDelinkModal}
        title="Create Delink Request"
        onClose={() => setShowDelinkModal(false)}
        size="md"
      >
        <DelinkRequestForm
          recycledSimId={id}
          onSuccess={() => {
            setShowDelinkModal(false);
            router.push('/delink-requests');
          }}
        />
      </Modal>
    </PageLayout>
  );
}
