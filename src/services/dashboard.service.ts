import api from './api';
import { DashboardStats, TrendData, RecycledSimsByOperator } from '@/types/models.types';
import { ApiResponse } from '@/types/api.types';

export const dashboardService = {
  async getStats(): Promise<DashboardStats> {
    const response = await api.get<ApiResponse<DashboardStats>>('/dashboard/stats');

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async getTrends(days: number = 30): Promise<TrendData[]> {
    const response = await api.get<ApiResponse<TrendData[]>>('/dashboard/trends', {
      params: { days },
    });

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async getRecycledSimsByOperator(): Promise<RecycledSimsByOperator[]> {
    const response = await api.get<ApiResponse<RecycledSimsByOperator[]>>(
      '/dashboard/recycled-sims-by-operator'
    );

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async getRecentActivity(limit: number = 10): Promise<{
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
  }> {
    const response = await api.get<
      ApiResponse<{
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
      }>
    >('/dashboard/recent-activity', {
      params: { limit },
    });

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },
};
