'use client';

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { TrendData } from '@/types/models.types';
import './trends-chart.component.scss';

interface TrendsChartProps {
  data: TrendData[];
}

const CHART_COLORS = {
  recycledSims: '#065A82',
  delinkRequests: '#1C7293',
  completed: '#059669',
};

export const TrendsChart: React.FC<TrendsChartProps> = ({ data }) => {
  return (
    <div className="trends-chart bg-surface rounded-lg shadow-md p-6 border border-secondary-100">
      <h2 className="text-lg font-semibold text-default mb-6">Trends (Last 30 Days)</h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            stroke="#6b7280"
            style={{ fontSize: '0.875rem' }}
          />
          <YAxis stroke="#6b7280" style={{ fontSize: '0.875rem' }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #e5e7eb',
              borderRadius: '0.5rem',
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="recycledSims"
            stroke={CHART_COLORS.recycledSims}
            strokeWidth={2}
            dot={false}
            name="Recycled SIMs"
          />
          <Line
            type="monotone"
            dataKey="delinkRequests"
            stroke={CHART_COLORS.delinkRequests}
            strokeWidth={2}
            dot={false}
            name="Delink Requests"
          />
          <Line
            type="monotone"
            dataKey="completedDelinkRequests"
            stroke={CHART_COLORS.completed}
            strokeWidth={2}
            dot={false}
            name="Completed"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
