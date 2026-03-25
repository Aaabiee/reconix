import { getAuthTokens } from '@/services/api';

export type WebSocketMessage = {
  type: string;
  data: Record<string, unknown>;
  timestamp?: string;
};

type MessageHandler = (message: WebSocketMessage) => void;
type StatusHandler = (status: 'connecting' | 'connected' | 'disconnected' | 'error') => void;

const WS_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || '')
  .replace(/^http/, 'ws')
  .replace(/\/api\/v1$/, '');

const RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 16000, 30000];

export class WebSocketService {
  private ws: WebSocket | null = null;
  private channel: string;
  private messageHandlers: Set<MessageHandler> = new Set();
  private statusHandlers: Set<StatusHandler> = new Set();
  private reconnectAttempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingInterval: ReturnType<typeof setInterval> | null = null;
  private intentionallyClosed = false;

  constructor(channel: string) {
    this.channel = channel;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    const { accessToken } = getAuthTokens();
    if (!accessToken) {
      this.notifyStatus('error');
      return;
    }

    this.intentionallyClosed = false;
    this.notifyStatus('connecting');

    const encodedToken = encodeURIComponent(accessToken);
    const url = `${WS_BASE_URL}/ws/${this.channel}?token=${encodedToken}`;

    try {
      this.ws = new WebSocket(url);
    } catch {
      this.notifyStatus('error');
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this.reconnectAttempt = 0;
      this.notifyStatus('connected');
      this.startPing();
    };

    this.ws.onmessage = (event: MessageEvent) => {
      if (event.data === 'pong') return;

      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.messageHandlers.forEach((handler) => handler(message));
      } catch {
        // ignore malformed messages
      }
    };

    this.ws.onclose = () => {
      this.stopPing();
      this.notifyStatus('disconnected');
      if (!this.intentionallyClosed) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = () => {
      this.notifyStatus('error');
    };
  }

  disconnect(): void {
    this.intentionallyClosed = true;
    this.stopPing();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.notifyStatus('disconnected');
  }

  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  onStatus(handler: StatusHandler): () => void {
    this.statusHandlers.add(handler);
    return () => this.statusHandlers.delete(handler);
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private notifyStatus(status: 'connecting' | 'connected' | 'disconnected' | 'error'): void {
    this.statusHandlers.forEach((handler) => handler(status));
  }

  private scheduleReconnect(): void {
    if (this.intentionallyClosed) return;

    const delay = RECONNECT_DELAYS[
      Math.min(this.reconnectAttempt, RECONNECT_DELAYS.length - 1)
    ];
    this.reconnectAttempt++;

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private startPing(): void {
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send('ping');
      }
    }, 30000);
  }

  private stopPing(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }
}

export const notificationWs = new WebSocketService('notifications');
export const delinkUpdatesWs = new WebSocketService('delink_updates');
