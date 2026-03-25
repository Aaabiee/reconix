'use client';

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { PageLayout } from '@/components/page-layout/page-layout.component';
import { StatusBadge } from '@/components/status-badge/status-badge.component';
import { Modal } from '@/components/modal/modal.component';
import { LoadingSpinner } from '@/components/loading-spinner/loading-spinner.component';
import { ErrorBoundary } from '@/components/error-boundary/error-boundary.component';
import { useApiQuery } from '@/hooks/useApiQuery';
import { delinkService } from '@/services/delink.service';
import { format } from 'date-fns';
import { CheckCircle, XCircle, Clock } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';

export default function DelinkRequestDetailPage(): JSX.Element {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const id = params.id as string;
  const [showApproveModal, setShowApproveModal] = React.useState(false);
  const [showRejectModal, setShowRejectModal] = React.useState(false);
  const [rejectReason, setRejectReason] = React.useState('');
  const [isProcessing, setIsProcessing] = React.useState(false);

  const { data: request, isLoading, error, refetch } = useApiQuery(
    () => delinkService.getDelinkRequestById(id),
    [id]
  );

  const handleApprove = async (): Promise<void> => {
    setIsProcessing(true);
    try {
      await delinkService.approveDelinkRequest(id);
      await refetch();
      setShowApproveModal(false);
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Approval failed:', error);
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReject = async (): Promise<void> => {
    if (!rejectReason.trim()) return;

    setIsProcessing(true);
    try {
      await delinkService.rejectDelinkRequest(id, rejectReason);
      await refetch();
      setShowRejectModal(false);
      setRejectReason('');
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Rejection failed:', error);
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const canApprove = request?.status === 'pending' && user?.role === 'admin';
  const canReject = request?.status === 'pending' && user?.role === 'admin';

  if (isLoading) {
    return (
      <PageLayout title="Loading...">
        <LoadingSpinner text="Loading request details..." />
      </PageLayout>
    );
  }

  if (error || !request) {
    return (
      <PageLayout
        title="Error"
        breadcrumbs={[{ label: 'Delink Requests', href: '/delink-requests' }]}
      >
        <div className="p-4 bg-error-50 border border-error-200 rounded-lg text-error-800">
          Failed to load request details. Please try again.
        </div>
      </PageLayout>
    );
  }

  const statusIcons: Record<string, React.ReactNode> = {
    pending: <Clock className="text-warning-600" size={24} />,
    approved: <CheckCircle className="text-primary-600" size={24} />,
    completed: <CheckCircle className="text-success-600" size={24} />,
    rejected: <XCircle className="text-error-600" size={24} />,
  };

  return (
    <PageLayout
      title={`Delink Request: ${request.phoneNumber}`}
      breadcrumbs={[
        { label: 'Delink Requests', href: '/delink-requests' },
        { label: request.phoneNumber },
      ]}
    >
      <ErrorBoundary>
        <div className="space-y-6">
          <div className="bg-surface rounded-lg shadow-md p-8 border border-secondary-100">
            <div className="flex items-start justify-between mb-6">
              <div className="flex items-center gap-4">
                {statusIcons[request.status] || statusIcons.pending}
                <div>
                  <h2 className="text-2xl font-bold text-default">{request.phoneNumber}</h2>
                  <p className="text-secondary-600 mt-1">NIN: {request.nin}</p>
                </div>
              </div>
              <StatusBadge status={request.status as any} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-secondary-600">BVN</label>
                  <p className="font-mono text-lg text-default mt-1">{request.bvn}</p>
                </div>
                <div>
                  <label className="text-sm text-secondary-600">Operator</label>
                  <p className="text-lg text-default mt-1">{request.operatorName}</p>
                </div>
                <div>
                  <label className="text-sm text-secondary-600">Requested By</label>
                  <p className="text-lg text-default mt-1">{request.requestedBy}</p>
                </div>
                <div>
                  <label className="text-sm text-secondary-600">Requested Date</label>
                  <p className="text-lg text-default mt-1">
                    {format(new Date(request.requestedAt), 'PPP p')}
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                {request.approvedBy && (
                  <div>
                    <label className="text-sm text-secondary-600">Approved By</label>
                    <p className="text-lg text-default mt-1">{request.approvedBy}</p>
                  </div>
                )}
                {request.approvedAt && (
                  <div>
                    <label className="text-sm text-secondary-600">Approved Date</label>
                    <p className="text-lg text-default mt-1">
                      {format(new Date(request.approvedAt), 'PPP p')}
                    </p>
                  </div>
                )}
                {request.completedAt && (
                  <div>
                    <label className="text-sm text-secondary-600">Completed Date</label>
                    <p className="text-lg text-default mt-1">
                      {format(new Date(request.completedAt), 'PPP p')}
                    </p>
                  </div>
                )}
                {request.notes && (
                  <div>
                    <label className="text-sm text-secondary-600">Notes</label>
                    <p className="text-lg text-default mt-1">{request.notes}</p>
                  </div>
                )}
              </div>
            </div>

            {request.delinkReason && (
              <div className="mt-6 p-4 bg-page rounded-lg border border-secondary-200">
                <label className="text-sm font-medium text-secondary-600">Delink Reason</label>
                <p className="text-default mt-2">{request.delinkReason}</p>
              </div>
            )}

            {canApprove || canReject ? (
              <div className="flex gap-4 mt-8">
                {canApprove && (
                  <button
                    onClick={() => setShowApproveModal(true)}
                    className="flex items-center gap-2 px-6 py-2 bg-success-500 text-surface rounded-lg hover:bg-success-600 font-medium transition-colors"
                  >
                    <CheckCircle size={18} />
                    Approve Request
                  </button>
                )}
                {canReject && (
                  <button
                    onClick={() => setShowRejectModal(true)}
                    className="flex items-center gap-2 px-6 py-2 bg-error-500 text-surface rounded-lg hover:bg-error-600 font-medium transition-colors"
                  >
                    <XCircle size={18} />
                    Reject Request
                  </button>
                )}
              </div>
            ) : null}
          </div>
        </div>
      </ErrorBoundary>

      <Modal
        isOpen={showApproveModal}
        title="Approve Delink Request"
        onClose={() => setShowApproveModal(false)}
        onConfirm={handleApprove}
        isLoading={isProcessing}
      >
        <p className="text-default">
          Are you sure you want to approve this delink request? This will proceed with delinking
          the SIM from the NIN/BVN record.
        </p>
      </Modal>

      <Modal
        isOpen={showRejectModal}
        title="Reject Delink Request"
        onClose={() => setShowRejectModal(false)}
        size="md"
      >
        <div className="space-y-4">
          <p className="text-default">Please provide a reason for rejecting this request:</p>
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="Enter rejection reason"
            rows={4}
            className="w-full px-4 py-2 border border-secondary-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <button
            onClick={handleReject}
            disabled={!rejectReason.trim() || isProcessing}
            className="w-full px-4 py-2 bg-error-500 text-surface rounded-lg hover:bg-error-600 disabled:opacity-50 font-medium transition-colors"
          >
            {isProcessing ? 'Rejecting...' : 'Reject Request'}
          </button>
        </div>
      </Modal>
    </PageLayout>
  );
}
