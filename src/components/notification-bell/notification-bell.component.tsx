'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Bell, X, CheckCircle, AlertTriangle, Info } from 'lucide-react';
import { useWebSocket } from '@/hooks/useWebSocket';
import './notification-bell.component.scss';

interface NotificationItem {
  type: string;
  data: Record<string, unknown>;
  timestamp?: string;
}

const ICON_MAP: Record<string, React.ReactNode> = {
  success: React.createElement(CheckCircle, { size: 16, className: 'text-green-500' }),
  warning: React.createElement(AlertTriangle, { size: 16, className: 'text-amber-500' }),
  error: React.createElement(AlertTriangle, { size: 16, className: 'text-red-500' }),
};

export const NotificationBell: React.FC = () => {
  const { messages, status, clearMessages } = useWebSocket('notifications', {
    autoConnect: true,
    maxMessages: 20,
  });
  const [showPanel, setShowPanel] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  const closePanel = useCallback(() => {
    setShowPanel(false);
  }, []);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        closePanel();
      }
    };

    if (showPanel) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showPanel, closePanel]);

  const unreadCount = messages.length;

  const formatTime = (timestamp?: string): string => {
    if (!timestamp) return '';
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  return (
    <div ref={panelRef} className="notification-bell relative">
      <button
        onClick={() => setShowPanel(!showPanel)}
        className="relative p-2.5 text-gray-500 hover:text-primary-600
                   hover:bg-primary-50 rounded-material transition-all duration-200"
        aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
        aria-expanded={showPanel}
        aria-haspopup="true"
      >
        <Bell size={20} strokeWidth={1.8} />
        {unreadCount > 0 && (
          <span
            className="absolute top-1.5 right-1.5 min-w-[18px] h-[18px] px-1
                       bg-accent-500 rounded-full text-white text-[10px] font-bold
                       flex items-center justify-center ring-2 ring-white"
            aria-hidden="true"
          >
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {showPanel && (
        <div
          className="absolute right-0 mt-2 w-80 bg-white border border-surface-200
                     rounded-material-md shadow-elevation-4 z-50 overflow-hidden"
          role="region"
          aria-label="Notifications panel"
        >
          <div className="flex items-center justify-between px-4 py-3 border-b border-surface-100">
            <h3 className="text-sm font-semibold text-default">Notifications</h3>
            <div className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${
                  status === 'connected' ? 'bg-green-500' : 'bg-gray-300'
                }`}
                title={`WebSocket: ${status}`}
              />
              {unreadCount > 0 && (
                <button
                  onClick={clearMessages}
                  className="text-xs text-primary-600 hover:text-primary-700"
                >
                  Clear all
                </button>
              )}
            </div>
          </div>

          <div className="max-h-80 overflow-y-auto">
            {messages.length === 0 ? (
              <div className="px-4 py-8 text-center text-sm text-gray-400">
                No notifications
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div
                  key={idx}
                  className="px-4 py-3 border-b border-surface-50 hover:bg-surface-50
                             transition-colors duration-150"
                >
                  <div className="flex items-start gap-2.5">
                    <div className="mt-0.5">
                      {ICON_MAP[msg.type] || React.createElement(Info, { size: 16, className: 'text-blue-500' })}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-default truncate">
                        {String(msg.data?.message || msg.type)}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {formatTime(msg.timestamp)}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};
