import api from './api';
import { RecycledSim } from '@/types/models.types';
import { ApiResponse, PaginatedResponse, PaginationParams } from '@/types/api.types';

export const recycledSimsService = {
  async getRecycledSims(
    params: PaginationParams & {
      search?: string;
      status?: string;
      operatorCode?: string;
    } = { page: 1, pageSize: 10 }
  ): Promise<PaginatedResponse<RecycledSim>> {
    const response = await api.get<ApiResponse<PaginatedResponse<RecycledSim>>>(
      '/recycled-sims',
      { params }
    );

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async getRecycledSimById(id: string): Promise<RecycledSim> {
    const response = await api.get<ApiResponse<RecycledSim>>(`/recycled-sims/${id}`);

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async createRecycledSim(data: Omit<RecycledSim, 'id' | 'createdAt' | 'updatedAt'>): Promise<RecycledSim> {
    const response = await api.post<ApiResponse<RecycledSim>>('/recycled-sims', data);

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async updateRecycledSim(id: string, data: Partial<RecycledSim>): Promise<RecycledSim> {
    const response = await api.put<ApiResponse<RecycledSim>>(`/recycled-sims/${id}`, data);

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async deleteRecycledSim(id: string): Promise<void> {
    await api.delete(`/recycled-sims/${id}`);
  },

  async bulkUploadRecycledSims(file: File): Promise<{ uploadId: string; message: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<ApiResponse<{ uploadId: string; message: string }>>(
      '/recycled-sims/bulk-upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async getUploadStatus(uploadId: string): Promise<{
    status: string;
    totalRows: number;
    successCount: number;
    failureCount: number;
    errors?: Array<{ row: number; error: string }>;
  }> {
    const response = await api.get<
      ApiResponse<{
        status: string;
        totalRows: number;
        successCount: number;
        failureCount: number;
        errors?: Array<{ row: number; error: string }>;
      }>
    >(`/recycled-sims/upload-status/${uploadId}`);

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },
};
