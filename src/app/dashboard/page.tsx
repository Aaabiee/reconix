'use client';

import { PageLayout } from '@/components/page-layout/page-layout.component';
import { StatsOverview } from '@/components/stats-overview/stats-overview.component';
import { TrendsChart } from '@/components/trends-chart/trends-chart.component';
import { RecycledSimsByOperator } from '@/components/recycled-sims-operator/recycled-sims-operator.component';
import { RecentActivity } from '@/components/recent-activity/recent-activity.component';
import { ErrorBoundary } from '@/components/error-boundary/error-boundary.component';
import { useApiQuery } from '@/hooks/useApiQuery';
import { dashboardService } from '@/services/dashboard.service';

export default function DashboardPage(): JSX.Element {
  const { data: stats, isLoading: statsLoading, error: statsError } = useApiQuery(() =>
    dashboardService.getStats()
  );

  const { data: trends, isLoading: trendsLoading, error: trendsError } = useApiQuery(() =>
    dashboardService.getTrends(30)
  );

  const { data: operators, isLoading: operatorsLoading, error: operatorsError } = useApiQuery(
    () => dashboardService.getRecycledSimsByOperator()
  );

  const { data: activity, isLoading: activityLoading, error: activityError } = useApiQuery(() =>
    dashboardService.getRecentActivity(10)
  );

  const isLoading = statsLoading || trendsLoading || operatorsLoading || activityLoading;
  const error = statsError || trendsError || operatorsError || activityError;

  return (
    <PageLayout
      title="Dashboard"
      description="Overview of recycled SIMs and delink requests"
    >
      <div
        className="absolute top-0 left-0 right-0 h-48 -z-10 opacity-50"
        style={{ backgroundImage: "url('/branding/dashboard-pattern.svg')", backgroundSize: 'cover' }}
      />

      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 animate-fade-in">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1 space-y-3">
                  <div className="skeleton-shimmer h-4 w-24" />
                  <div className="skeleton-shimmer h-8 w-16" />
                  <div className="skeleton-shimmer h-3 w-32" />
                </div>
                <div className="skeleton-shimmer h-12 w-12 rounded-material" />
              </div>
            </div>
          ))}
        </div>
      )}

      {error && (
        <div className="card border-l-4 border-l-error-500 p-5 animate-slide-up">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-error-50 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-error-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-default">Unable to load dashboard</h3>
              <p className="text-sm text-muted mt-0.5">Please check your connection and try again.</p>
            </div>
          </div>
        </div>
      )}

      {!isLoading && !error && stats && (
        <div className="space-y-8 animate-slide-up">
          <ErrorBoundary>
            <StatsOverview stats={stats} />
          </ErrorBoundary>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <ErrorBoundary>
                {trends && <TrendsChart data={trends} />}
              </ErrorBoundary>
            </div>
            <div>
              <ErrorBoundary>
                {operators && <RecycledSimsByOperator data={operators} />}
              </ErrorBoundary>
            </div>
          </div>

          <ErrorBoundary>
            {activity && (
              <RecentActivity
                recentDelinkRequests={activity.recentDelinkRequests}
                recentNotifications={activity.recentNotifications}
              />
            )}
          </ErrorBoundary>
        </div>
      )}
    </PageLayout>
  );
}
