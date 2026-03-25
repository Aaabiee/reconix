'use client';

import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { RecycledSimsByOperator as RecycledSimsByOperatorType } from '@/types/models.types';
import './recycled-sims-operator.component.scss';

interface RecycledSimsByOperatorProps {
  data: RecycledSimsByOperatorType[];
}

const COLORS = ['#065A82', '#1C7293', '#21295C', '#D97706', '#059669'];

export const RecycledSimsByOperator: React.FC<RecycledSimsByOperatorProps> = ({ data }) => {
  const chartData = data.map((item) => ({
    name: item.operatorName,
    value: item.count,
  }));

  return (
    <div className="recycled-sims-operator bg-surface rounded-lg shadow-md p-6 border border-secondary-100">
      <h2 className="text-lg font-semibold text-default mb-6">Recycled SIMs by Operator</h2>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
