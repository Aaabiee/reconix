import React from 'react';
import { Activity, AlertCircle, CheckCircle2, Smartphone } from 'lucide-react';
import { StatsCard } from '@/components/stats-card/stats-card.component';
import { DashboardStats } from '@/types/models.types';
import './stats-overview.component.scss';

interface StatsOverviewProps {
  stats: DashboardStats;
}

export const StatsOverview: React.FC<StatsOverviewProps> = ({ stats }) => {
  return (
    <div className="stats-overview grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatsCard
        icon={Smartphone}
        title="Total Recycled SIMs"
        value={stats.totalRecycledSims}
        color="primary"
      />
      <StatsCard
        icon={Activity}
        title="Total Delink Requests"
        value={stats.totalDelinkRequests}
        color="secondary"
      />
      <StatsCard
        icon={AlertCircle}
        title="Pending Requests"
        value={stats.pendingDelinkRequests}
        color="warning"
      />
      <StatsCard
        icon={CheckCircle2}
        title="Completed Requests"
        value={stats.completedDelinkRequests}
        color="success"
      />
    </div>
  );
};
