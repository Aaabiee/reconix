'use client';

import React from 'react';
import { PageLayout } from '@/components/page-layout/page-layout.component';
import { LoadingSpinner } from '@/components/loading-spinner/loading-spinner.component';
import { EmptyState } from '@/components/empty-state/empty-state.component';
import { ErrorBoundary } from '@/components/error-boundary/error-boundary.component';
import { usePagination } from '@/hooks/usePagination';
import { useApiQuery } from '@/hooks/useApiQuery';
import { notificationsService } from '@/services/notifications.service';
import { format } from 'date-fns';
import { Bell } from 'lucide-react';

export default function NotificationsPage(): JSX.Element {
  const { page, pageSize, goToPage } = usePagination();

  const { data: result, isLoading, error } = useApiQuery(() =>
    notificationsService.getNotifications({ page, pageSize })
  );

  const handleMarkAsRead = async (id: string): Promise<void> => {
    try {
      await notificationsService.markAsRead(id);
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to mark as read:', error);
      }
    }
  };

  return (
    <PageLayout
      title="Notifications"
      description="View and manage your notifications"
      breadcrumbs={[{ label: 'Notifications' }]}
    >
      {error && (
        <div className="p-4 bg-error-50 border border-error-200 rounded-lg text-error-800">
          Failed to load notifications. Please try again.
        </div>
      )}

      {isLoading && (
        <div className="flex justify-center py-12">
          <LoadingSpinner text="Loading notifications..." />
        </div>
      )}

      {!isLoading && !error && result && (
        <ErrorBoundary>
          <div className="space-y-4">
            {result.items.length === 0 ? (
              <EmptyState
                icon={Bell}
                title="No Notifications"
                description="You have no notifications at this time"
              />
            ) : (
              result.items.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                    notification.read
                      ? 'bg-page border-secondary-200'
                      : 'bg-primary-50 border-primary-200'
                  }`}
                  onClick={() => handleMarkAsRead(notification.id)}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="font-semibold text-default">{notification.title}</h3>
                      <p className="text-secondary-600 text-sm mt-1">{notification.message}</p>
                      <p className="text-xs text-secondary-500 mt-2">
                        {format(new Date(notification.createdAt), 'PPP p')}
                      </p>
                    </div>
                    {!notification.read && (
                      <div className="w-3 h-3 bg-primary-500 rounded-full flex-shrink-0 mt-1" />
                    )}
                  </div>
                </div>
              ))
            )}
          </div>

          {result.totalPages > 1 && (
            <div className="flex justify-center mt-8">
              <div className="flex gap-2">
                <button
                  onClick={() => goToPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 border border-secondary-200 rounded-lg hover:bg-page disabled:opacity-50"
                >
                  Previous
                </button>
                <span className="px-4 py-2">
                  Page {page} of {result.totalPages}
                </span>
                <button
                  onClick={() => goToPage(Math.min(result.totalPages, page + 1))}
                  disabled={page === result.totalPages}
                  className="px-4 py-2 border border-secondary-200 rounded-lg hover:bg-page disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </ErrorBoundary>
      )}
    </PageLayout>
  );
}
