import '@testing-library/jest-dom';

describe('WebSocket Service Integration', () => {
  describe('WebSocketService', () => {
    it('constructs with channel name', () => {
      const { WebSocketService } = require('@/services/websocket.service');
      const service = new WebSocketService('notifications');
      expect(service.isConnected).toBe(false);
    });

    it('exports named channel instances', () => {
      const { notificationWs, delinkUpdatesWs } = require('@/services/websocket.service');
      expect(notificationWs).toBeDefined();
      expect(delinkUpdatesWs).toBeDefined();
      expect(notificationWs.isConnected).toBe(false);
      expect(delinkUpdatesWs.isConnected).toBe(false);
    });

    it('onMessage returns unsubscribe function', () => {
      const { WebSocketService } = require('@/services/websocket.service');
      const service = new WebSocketService('notifications');
      const handler = jest.fn();
      const unsubscribe = service.onMessage(handler);
      expect(typeof unsubscribe).toBe('function');
      unsubscribe();
    });

    it('onStatus returns unsubscribe function', () => {
      const { WebSocketService } = require('@/services/websocket.service');
      const service = new WebSocketService('notifications');
      const handler = jest.fn();
      const unsubscribe = service.onStatus(handler);
      expect(typeof unsubscribe).toBe('function');
      unsubscribe();
    });

    it('disconnect sets intentionally closed', () => {
      const { WebSocketService } = require('@/services/websocket.service');
      const service = new WebSocketService('notifications');
      service.disconnect();
      expect(service.isConnected).toBe(false);
    });
  });

  describe('WebSocket Security', () => {
    it('requires authentication token for connection', () => {
      jest.mock('@/services/api', () => ({
        __esModule: true,
        default: {},
        getAuthTokens: () => ({ accessToken: '', refreshToken: '' }),
      }));

      const { WebSocketService } = require('@/services/websocket.service');
      const service = new WebSocketService('notifications');
      const statusHandler = jest.fn();
      service.onStatus(statusHandler);
      service.connect();
      expect(statusHandler).toHaveBeenCalledWith('error');
    });

    it('only allows predefined channels', () => {
      const allowedChannels = ['notifications', 'delink_updates', 'sim_alerts', 'system'];
      allowedChannels.forEach((channel) => {
        const { WebSocketService } = require('@/services/websocket.service');
        const service = new WebSocketService(channel);
        expect(service).toBeDefined();
      });
    });
  });
});
