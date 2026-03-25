import { useState, useEffect, useCallback, useRef } from 'react';
import { WebSocketService, WebSocketMessage } from '@/services/websocket.service';

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface UseWebSocketReturn {
  status: ConnectionStatus;
  messages: WebSocketMessage[];
  lastMessage: WebSocketMessage | null;
  connect: () => void;
  disconnect: () => void;
  clearMessages: () => void;
}

export const useWebSocket = (
  channel: string,
  options: { autoConnect?: boolean; maxMessages?: number } = {},
): UseWebSocketReturn => {
  const { autoConnect = true, maxMessages = 50 } = options;
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const serviceRef = useRef<WebSocketService | null>(null);

  useEffect(() => {
    serviceRef.current = new WebSocketService(channel);
    const service = serviceRef.current;

    const unsubStatus = service.onStatus((newStatus) => {
      setStatus(newStatus);
    });

    const unsubMessage = service.onMessage((message) => {
      setLastMessage(message);
      setMessages((prev) => {
        const next = [message, ...prev];
        return next.slice(0, maxMessages);
      });
    });

    if (autoConnect) {
      service.connect();
    }

    return () => {
      unsubStatus();
      unsubMessage();
      service.disconnect();
    };
  }, [channel, autoConnect, maxMessages]);

  const connect = useCallback(() => {
    serviceRef.current?.connect();
  }, []);

  const disconnect = useCallback(() => {
    serviceRef.current?.disconnect();
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setLastMessage(null);
  }, []);

  return {
    status,
    messages,
    lastMessage,
    connect,
    disconnect,
    clearMessages,
  };
};
