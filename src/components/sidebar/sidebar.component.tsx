'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Smartphone,
  LinkIcon,
  Bell,
  FileText,
  Settings,
  Menu,
  X,
  ChevronRight,
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import './sidebar.component.scss';

const menuItems = [
  {
    label: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
    roles: ['admin', 'analyst', 'viewer'],
  },
  {
    label: 'Recycled SIMs',
    href: '/recycled-sims',
    icon: Smartphone,
    roles: ['admin', 'analyst', 'viewer'],
  },
  {
    label: 'Delink Requests',
    href: '/delink-requests',
    icon: LinkIcon,
    roles: ['admin', 'operator', 'analyst'],
  },
  {
    label: 'Notifications',
    href: '/notifications',
    icon: Bell,
    roles: ['admin', 'operator', 'analyst', 'viewer'],
  },
  {
    label: 'Audit Logs',
    href: '/audit-logs',
    icon: FileText,
    roles: ['admin'],
  },
  {
    label: 'Settings',
    href: '/settings',
    icon: Settings,
    roles: ['admin', 'operator', 'analyst', 'viewer'],
  },
];

interface SidebarProps {
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onClose }) => {
  const pathname = usePathname();
  const { user } = useAuth();
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const visibleMenuItems = menuItems.filter(
    (item) => user?.role && item.roles.includes(user.role)
  );

  const toggleMobile = (): void => {
    setIsMobileOpen(!isMobileOpen);
  };

  const closeMobileMenu = (): void => {
    setIsMobileOpen(false);
    onClose?.();
  };

  const NavContent = (
    <nav className="flex-1 px-3 py-4 space-y-1" aria-label="Main navigation">
      {visibleMenuItems.map((item) => {
        const isActive = pathname === item.href;
        const Icon = item.icon;

        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={closeMobileMenu}
            className={`
              group flex items-center gap-3 px-4 py-2.5 rounded-material-md
              font-medium text-sm transition-all duration-200
              ${isActive
                ? 'bg-primary-500 text-white shadow-elevation-1'
                : 'text-gray-600 hover:bg-primary-50 hover:text-primary-700'
              }
            `}
            aria-current={isActive ? 'page' : undefined}
          >
            <Icon
              size={20}
              strokeWidth={isActive ? 2 : 1.8}
              className={isActive ? 'text-white' : 'text-gray-400 group-hover:text-primary-500'}
            />
            <span className="flex-1">{item.label}</span>
            {isActive && (
              <ChevronRight size={16} className="text-white/60" />
            )}
          </Link>
        );
      })}
    </nav>
  );

  return (
    <>
      <button
        onClick={toggleMobile}
        className="md:hidden fixed bottom-6 right-6 z-40 p-3
                   gradient-primary text-white rounded-full shadow-elevation-3
                   transition-transform duration-200 active:scale-95"
        aria-label="Toggle menu"
      >
        {isMobileOpen ? <X size={22} /> : <Menu size={22} />}
      </button>

      <aside
        className={`
          sidebar fixed md:static inset-y-0 left-0 w-64 bg-white
          border-r border-surface-200 shadow-elevation-1
          transform transition-transform duration-300 ease-out z-30
          ${isMobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}
      >
        <div className="sticky top-0 h-screen flex flex-col">
          <div className="px-5 py-5 border-b border-surface-200">
            <Image
              src="/branding/logo-wide.svg"
              alt="Reconix"
              width={150}
              height={36}
              priority
            />
          </div>

          {NavContent}

          {user && (
            <div className="px-4 py-4 border-t border-surface-200 bg-surface-50">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full gradient-primary flex items-center justify-center
                                text-white text-sm font-bold flex-shrink-0">
                  {user.fullName.charAt(0).toUpperCase()}
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-default truncate">
                    {user.fullName}
                  </p>
                  <p className="text-xs text-gray-400 capitalize">{user.role}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </aside>

      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/30 backdrop-blur-sm z-20 md:hidden animate-fade-in"
          onClick={closeMobileMenu}
        />
      )}
    </>
  );
};
