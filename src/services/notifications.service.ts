import api from './api';
import { Notification } from '@/types/models.types';
import { ApiResponse, PaginatedResponse, PaginationParams } from '@/types/api.types';

export const notificationsService = {
  async getNotifications(
    params: PaginationParams & {
      read?: boolean;
      type?: string;
    } = { page: 1, pageSize: 20 }
  ): Promise<PaginatedResponse<Notification>> {
    const response = await api.get<ApiResponse<PaginatedResponse<Notification>>>(
      '/notifications',
      { params }
    );

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async getNotificationById(id: string): Promise<Notification> {
    const response = await api.get<ApiResponse<Notification>>(`/notifications/${id}`);

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async markAsRead(id: string): Promise<Notification> {
    const response = await api.put<ApiResponse<Notification>>(`/notifications/${id}/read`);

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data;
  },

  async markAllAsRead(): Promise<void> {
    await api.put('/notifications/read-all');
  },

  async deleteNotification(id: string): Promise<void> {
    await api.delete(`/notifications/${id}`);
  },

  async getUnreadCount(): Promise<number> {
    const response = await api.get<ApiResponse<{ count: number }>>('/notifications/unread-count');

    if (!response.data.data) {
      throw new Error('No data returned');
    }

    return response.data.data.count;
  },

  async subscribeToNotifications(callback: (notification: Notification) => void): Promise<void> {
    if (typeof window === 'undefined') return;

    const eventSource = new EventSource('/api/notifications/stream');

    eventSource.addEventListener('notification', (event) => {
      try {
        const notification = JSON.parse(event.data) as Notification;
        callback(notification);
      } catch (error) {
        if (process.env.NODE_ENV === 'development') {
          console.error('Error parsing notification:', error);
        }
      }
    });

    eventSource.addEventListener('error', () => {
      eventSource.close();
    });
  },
};
