'use client';

import React from 'react';
import { PageLayout } from '@/components/layout/PageLayout';
import { useAuth } from '@/hooks/useAuth';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { Copy, Check } from 'lucide-react';
import { format } from 'date-fns';

export default function SettingsPage(): JSX.Element {
  const { user, isLoading } = useAuth();
  const [copiedId, setCopiedId] = React.useState<string | null>(null);

  const handleCopyApiKey = (key: string): void => {
    navigator.clipboard.writeText(key);
    setCopiedId(key);
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (isLoading) {
    return (
      <PageLayout title="Settings">
        <LoadingSpinner text="Loading settings..." />
      </PageLayout>
    );
  }

  return (
    <PageLayout
      title="Settings"
      description="Manage your account settings and preferences"
      breadcrumbs={[{ label: 'Settings' }]}
    >
      <ErrorBoundary>
        <div className="space-y-6">
          <div className="bg-surface rounded-lg shadow-md p-8 border border-secondary-100">
            <h2 className="text-2xl font-bold text-default mb-6">Account Information</h2>

            <div className="space-y-4">
              <div>
                <label className="text-sm text-secondary-600">Full Name</label>
                <p className="text-lg text-default mt-1 font-medium">{user?.fullName}</p>
              </div>

              <div>
                <label className="text-sm text-secondary-600">Email</label>
                <p className="text-lg text-default mt-1 font-medium">{user?.email}</p>
              </div>

              <div>
                <label className="text-sm text-secondary-600">Role</label>
                <p className="text-lg text-default mt-1 font-medium capitalize">{user?.role}</p>
              </div>

              {user?.operatorName && (
                <div>
                  <label className="text-sm text-secondary-600">Operator</label>
                  <p className="text-lg text-default mt-1 font-medium">{user.operatorName}</p>
                </div>
              )}

              <div className="pt-4 border-t border-secondary-200">
                <p className="text-xs text-secondary-500">
                  Account created: {format(new Date(user?.createdAt || ''), 'PPP p')}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-surface rounded-lg shadow-md p-8 border border-secondary-100">
            <h2 className="text-2xl font-bold text-default mb-6">API Keys</h2>

            <p className="text-secondary-600 mb-6">
              API keys are used to authenticate your requests to the Reconix API. Keep them
              secret and never share them publicly.
            </p>

            <div className="space-y-4">
              <div className="p-4 bg-page rounded-lg border border-secondary-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-secondary-600">Production API Key</p>
                    <p className="font-mono text-sm text-default mt-2">reconix_xxxxxxxxxxxxxxxxxxxx</p>
                  </div>
                  <button
                    onClick={() => handleCopyApiKey('reconix_xxxxxxxxxxxxxxxxxxxx')}
                    className="p-2 hover:bg-secondary-100 rounded-lg transition-colors"
                    aria-label="Copy API key"
                  >
                    {copiedId === 'reconix_xxxxxxxxxxxxxxxxxxxx' ? (
                      <Check className="text-success-600" size={20} />
                    ) : (
                      <Copy className="text-secondary-600" size={20} />
                    )}
                  </button>
                </div>
              </div>
            </div>

            <button className="mt-6 px-6 py-2 border border-primary-500 text-primary-600 rounded-lg hover:bg-primary-50 font-medium transition-colors">
              Generate New API Key
            </button>
          </div>

          <div className="bg-surface rounded-lg shadow-md p-8 border border-secondary-100">
            <h2 className="text-2xl font-bold text-default mb-6">Preferences</h2>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-page rounded-lg">
                <div>
                  <p className="font-medium text-default">Email Notifications</p>
                  <p className="text-sm text-secondary-600 mt-1">
                    Receive notifications about important events
                  </p>
                </div>
                <input type="checkbox" defaultChecked className="w-5 h-5" />
              </div>

              <div className="flex items-center justify-between p-4 bg-page rounded-lg">
                <div>
                  <p className="font-medium text-default">System Alerts</p>
                  <p className="text-sm text-secondary-600 mt-1">
                    Get alerts for critical system events
                  </p>
                </div>
                <input type="checkbox" defaultChecked className="w-5 h-5" />
              </div>
            </div>
          </div>
        </div>
      </ErrorBoundary>
    </PageLayout>
  );
}
