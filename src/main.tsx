'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { LoadingSpinner } from '@/components/loading-spinner/loading-spinner.component';
import App from '../App';

interface MainProps {
  children: React.ReactNode;
}

export default function Main({ children }: MainProps): JSX.Element {
  const router = useRouter();
  const { user, isLoading } = useAuth();

  React.useEffect(() => {
    if (!isLoading && !user) {
      router.push('/');
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-page">
        <LoadingSpinner text="Initializing..." />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-page">
        <LoadingSpinner text="Redirecting..." />
      </div>
    );
  }

  return <App>{children}</App>;
}
