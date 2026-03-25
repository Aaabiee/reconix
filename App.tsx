'use client';

import React from 'react';
import { Sidebar } from '@/components/sidebar/sidebar.component';
import { Header } from '@/components/header/header.component';

interface AppProps {
  children: React.ReactNode;
}

export default function App({ children }: AppProps): JSX.Element {
  return (
    <div className="flex h-screen bg-page">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
