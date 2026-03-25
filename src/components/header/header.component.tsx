'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Bell, LogOut, Settings, ChevronDown } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import Link from 'next/link';
import './header.component.scss';

interface HeaderProps {
  onNotificationClick?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onNotificationClick }) => {
  const { user, logout } = useAuth();
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const closeMenu = useCallback(() => {
    setShowMenu(false);
  }, []);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        closeMenu();
      }
    };

    if (showMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showMenu, closeMenu]);

  const handleLogout = async (): Promise<void> => {
    try {
      closeMenu();
      await logout();
      window.location.href = '/';
    } catch {
      // logout failure is handled by the auth hook
    }
  };

  const initials = user?.fullName
    ? user.fullName
        .split(' ')
        .map((n) => n.charAt(0))
        .slice(0, 2)
        .join('')
        .toUpperCase()
    : 'U';

  return (
    <header className="app-header bg-white border-b border-surface-200 shadow-elevation-1 sticky top-0 z-20">
      <div className="flex items-center justify-between px-6 py-3">
        <div className="flex-1" />

        <div className="flex items-center gap-2">
          <button
            onClick={onNotificationClick}
            className="relative p-2.5 text-gray-500 hover:text-primary-600
                       hover:bg-primary-50 rounded-material transition-all duration-200"
            aria-label="Notifications"
          >
            <Bell size={20} strokeWidth={1.8} />
            <span className="absolute top-2 right-2 w-2.5 h-2.5 bg-accent-500 rounded-full
                             ring-2 ring-white animate-pulse-glow" />
          </button>

          <div className="w-px h-8 bg-surface-200 mx-1" />

          <div ref={menuRef} className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="flex items-center gap-3 p-2 hover:bg-surface-100
                         rounded-material transition-all duration-200"
              aria-label="User menu"
              aria-expanded={showMenu}
              aria-haspopup="true"
            >
              <div className="w-9 h-9 gradient-primary rounded-full flex items-center justify-center
                              text-white text-sm font-bold shadow-elevation-1">
                {initials}
              </div>
              <div className="hidden sm:block text-left">
                <p className="text-sm font-semibold text-default leading-tight">
                  {user?.fullName}
                </p>
                <p className="text-xs text-gray-400 capitalize">{user?.role}</p>
              </div>
              <ChevronDown
                size={16}
                className={`hidden sm:block text-gray-400 transition-transform duration-200 ${
                  showMenu ? 'rotate-180' : ''
                }`}
              />
            </button>

            {showMenu && (
              <div className="absolute right-0 mt-2 w-52 bg-white border border-surface-200
                              rounded-material-md shadow-elevation-4 z-50 animate-slide-down overflow-hidden"
                   role="menu">
                <div className="p-3 border-b border-surface-100 sm:hidden">
                  <p className="text-sm font-semibold text-default">{user?.fullName}</p>
                  <p className="text-xs text-gray-400 capitalize">{user?.role}</p>
                </div>
                <Link
                  href="/settings"
                  className="flex items-center gap-3 px-4 py-3 text-sm text-gray-700
                             hover:bg-surface-50 transition-colors duration-150"
                  onClick={closeMenu}
                  role="menuitem"
                >
                  <Settings size={16} strokeWidth={1.8} className="text-gray-400" />
                  Settings
                </Link>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-3 px-4 py-3 text-sm text-error-600
                             hover:bg-error-50 w-full text-left
                             border-t border-surface-100 transition-colors duration-150"
                  role="menuitem"
                >
                  <LogOut size={16} strokeWidth={1.8} />
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
