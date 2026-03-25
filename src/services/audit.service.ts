import api from './api';
import { AuditLog } from '@/types/models.types';
import { ApiResponse, PaginatedResponse, PaginationParams } from '@/types/api.types';

export const auditService = {
  async getAuditLogs(
    params: PaginationParams & {
      search?: string;
      action?: string;
      entityType?: string;
      userEmail?: string;
      dateFrom?: string;
      dateTo?: string;
    } = { page: 1, pageSize: 20 }
  ): Promise<PaginatedResponse<AuditLog>> {
    const response = await api.get<ApiResponse<PaginatedResponse<AuditLog>>>(
      '/audit-logs',
      { params }
    );

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async getAuditLogById(id: string): Promise<AuditLog> {
    const response = await api.get<ApiResponse<AuditLog>>(`/audit-logs/${id}`);

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async getEntityAuditHistory(entityType: string, entityId: string): Promise<AuditLog[]> {
    const response = await api.get<ApiResponse<AuditLog[]>>(
      `/audit-logs/entity/${entityType}/${entityId}`
    );

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async getUserAuditHistory(userId: string, params: PaginationParams = { page: 1, pageSize: 20 }): Promise<PaginatedResponse<AuditLog>> {
    const response = await api.get<ApiResponse<PaginatedResponse<AuditLog>>>(
      `/audit-logs/user/${userId}`,
      { params }
    );

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async exportAuditLogs(filters: Record<string, string | undefined>): Promise<Blob> {
    const response = await api.get('/audit-logs/export', {
      params: filters,
      responseType: 'blob',
    });

    return response.data;
  },
};
