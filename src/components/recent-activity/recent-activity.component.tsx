import React from 'react';
import { Bell, LinkIcon, Clock } from 'lucide-react';
import { format } from 'date-fns';
import Link from 'next/link';
import './recent-activity.component.scss';

interface RecentActivityProps {
  recentDelinkRequests: Array<{
    id: string;
    phoneNumber: string;
    status: string;
    createdAt: string;
  }>;
  recentNotifications: Array<{
    id: string;
    title: string;
    message: string;
    createdAt: string;
  }>;
}

export const RecentActivity: React.FC<RecentActivityProps> = ({
  recentDelinkRequests,
  recentNotifications,
}) => {
  return (
    <div className="recent-activity grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-surface rounded-lg shadow-md p-6 border border-secondary-100">
        <h3 className="text-lg font-semibold text-default mb-4 flex items-center gap-2">
          <LinkIcon size={20} className="text-primary-600" />
          Recent Delink Requests
        </h3>
        <div className="space-y-3">
          {recentDelinkRequests.length === 0 ? (
            <p className="text-secondary-600 text-sm">No recent requests</p>
          ) : (
            recentDelinkRequests.map((request) => (
              <Link
                key={request.id}
                href={`/delink-requests/${encodeURIComponent(request.id)}`}
                className="flex justify-between items-center p-3 bg-page rounded-lg hover:bg-secondary-50 transition-colors"
              >
                <div>
                  <p className="font-medium text-default">{request.phoneNumber}</p>
                  <p className="text-sm text-secondary-600">{request.status}</p>
                </div>
                <span className="text-xs text-secondary-500">
                  {format(new Date(request.createdAt), 'MMM dd, HH:mm')}
                </span>
              </Link>
            ))
          )}
        </div>
      </div>

      <div className="bg-surface rounded-lg shadow-md p-6 border border-secondary-100">
        <h3 className="text-lg font-semibold text-default mb-4 flex items-center gap-2">
          <Bell size={20} className="text-primary-600" />
          Recent Notifications
        </h3>
        <div className="space-y-3">
          {recentNotifications.length === 0 ? (
            <p className="text-secondary-600 text-sm">No recent notifications</p>
          ) : (
            recentNotifications.map((notification) => (
              <div key={notification.id} className="p-3 bg-page rounded-lg border-l-4 border-primary-500">
                <p className="font-medium text-default">{notification.title}</p>
                <p className="text-sm text-secondary-600 mt-1">{notification.message}</p>
                <div className="flex items-center gap-1 mt-2 text-xs text-secondary-500">
                  <Clock size={14} />
                  {format(new Date(notification.createdAt), 'MMM dd, HH:mm')}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
