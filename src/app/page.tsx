'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { LoginForm } from '@/components/login/login.component';
import { useAuth } from '@/hooks/useAuth';
import { LoadingSpinner } from '@/components/loading-spinner/loading-spinner.component';

export default function LoginPage(): JSX.Element {
  const router = useRouter();
  const { user, isLoading } = useAuth();

  React.useEffect(() => {
    if (user) {
      router.push('/dashboard');
    }
  }, [user, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-page">
        <LoadingSpinner text="Loading..." />
      </div>
    );
  }

  if (user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-page">
        <LoadingSpinner text="Redirecting..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex">
      <div className="hidden lg:flex lg:w-[55%] relative overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: "url('/branding/banner.svg')" }}
        />
        <div className="relative z-10 flex flex-col justify-between p-12 w-full">
          <div className="animate-fade-in">
            <Image
              src="/branding/logo-wide.svg"
              alt="Reconix"
              width={200}
              height={48}
              priority
              className="brightness-0 invert opacity-90"
            />
          </div>

          <div className="animate-slide-up max-w-lg">
            <h1 className="text-4xl font-bold text-white mb-4 leading-tight">
              National Identity
              <br />
              Reconciliation Platform
            </h1>
            <p className="text-primary-200 text-lg leading-relaxed">
              Secure management of recycled SIM identities across Nigeria&apos;s
              telecommunications infrastructure.
            </p>
            <div className="flex gap-8 mt-10">
              <div className="text-center">
                <div className="text-3xl font-bold text-accent-400">99.9%</div>
                <div className="text-primary-300 text-sm mt-1">Uptime</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-accent-400">256-bit</div>
                <div className="text-primary-300 text-sm mt-1">Encryption</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-accent-400">SOC 2</div>
                <div className="text-primary-300 text-sm mt-1">Compliant</div>
              </div>
            </div>
          </div>

          <div className="animate-fade-in text-primary-300 text-sm">
            &copy; {new Date().getFullYear()} Reconix. All rights reserved.
          </div>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-6 sm:p-12 bg-page relative">
        <div className="absolute inset-0 opacity-30"
          style={{
            backgroundImage: 'radial-gradient(circle at 20% 80%, rgba(2,195,154,0.08) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(6,90,130,0.06) 0%, transparent 50%)',
          }}
        />

        <div className="w-full max-w-md relative z-10 animate-scale-in">
          <div className="lg:hidden mb-10 text-center">
            <Image
              src="/branding/logo-wide.svg"
              alt="Reconix"
              width={180}
              height={43}
              priority
              className="mx-auto"
            />
          </div>

          <div className="card-glass">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-default">Welcome Back</h2>
              <p className="text-muted mt-2 text-sm">
                Sign in to access the reconciliation platform
              </p>
            </div>

            <LoginForm
              onSuccess={() => {
                router.push('/dashboard');
              }}
            />

            <div className="mt-6 pt-6 border-t border-surface-200 text-center">
              <p className="text-xs text-muted">
                Protected by enterprise-grade security
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
