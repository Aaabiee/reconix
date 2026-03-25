import api from './api';
import { DelinkRequest } from '@/types/models.types';
import { ApiResponse, PaginatedResponse, PaginationParams } from '@/types/api.types';

export const delinkService = {
  async getDelinkRequests(
    params: PaginationParams & {
      search?: string;
      status?: string;
    } = { page: 1, pageSize: 10 }
  ): Promise<PaginatedResponse<DelinkRequest>> {
    const response = await api.get<ApiResponse<PaginatedResponse<DelinkRequest>>>(
      '/delink-requests',
      { params }
    );

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async getDelinkRequestById(id: string): Promise<DelinkRequest> {
    const response = await api.get<ApiResponse<DelinkRequest>>(`/delink-requests/${id}`);

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async createDelinkRequest(recycledSimId: string, delinkReason: string): Promise<DelinkRequest> {
    const response = await api.post<ApiResponse<DelinkRequest>>('/delink-requests', {
      recycledSimId,
      delinkReason,
    });

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async approveDelinkRequest(id: string, notes?: string): Promise<DelinkRequest> {
    const response = await api.post<ApiResponse<DelinkRequest>>(
      `/delink-requests/${id}/approve`,
      { notes }
    );

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async rejectDelinkRequest(id: string, reason: string): Promise<DelinkRequest> {
    const response = await api.post<ApiResponse<DelinkRequest>>(
      `/delink-requests/${id}/reject`,
      { reason }
    );

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async cancelDelinkRequest(id: string, reason?: string): Promise<DelinkRequest> {
    const response = await api.post<ApiResponse<DelinkRequest>>(
      `/delink-requests/${id}/cancel`,
      { reason }
    );

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async completeDelinkRequest(id: string): Promise<DelinkRequest> {
    const response = await api.post<ApiResponse<DelinkRequest>>(
      `/delink-requests/${id}/complete`
    );

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async getDelinkStatistics(): Promise<{
    totalRequests: number;
    pendingRequests: number;
    approvedRequests: number;
    completedRequests: number;
    rejectedRequests: number;
    successRate: number;
  }> {
    const response = await api.get<
      ApiResponse<{
        totalRequests: number;
        pendingRequests: number;
        approvedRequests: number;
        completedRequests: number;
        rejectedRequests: number;
        successRate: number;
      }>
    >('/delink-requests/statistics');

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },
};
