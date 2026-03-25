import React, { ReactNode } from 'react';
import { ChevronRight } from 'lucide-react';
import Link from 'next/link';
import './page-layout.component.scss';

export interface Breadcrumb {
  label: string;
  href?: string;
}

interface PageLayoutProps {
  title: string;
  description?: string;
  breadcrumbs?: Breadcrumb[];
  children: ReactNode;
  header?: ReactNode;
}

export const PageLayout: React.FC<PageLayoutProps> = ({
  title,
  description,
  breadcrumbs,
  children,
  header,
}) => {
  return (
    <div className="page-layout min-h-screen bg-page">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {breadcrumbs && breadcrumbs.length > 0 && (
          <nav className="flex items-center gap-2 mb-6 text-sm" aria-label="Breadcrumb">
            <Link href="/dashboard" className="text-primary-600 hover:text-primary-700">
              Home
            </Link>
            {breadcrumbs.map((crumb, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <ChevronRight size={16} className="text-secondary-400" aria-hidden="true" />
                {crumb.href ? (
                  <Link href={crumb.href} className="text-primary-600 hover:text-primary-700">
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-secondary-600" aria-current="page">{crumb.label}</span>
                )}
              </div>
            ))}
          </nav>
        )}

        <div className="mb-8">
          <h1 className="text-3xl font-bold text-default">{title}</h1>
          {description && <p className="text-secondary-600 mt-2">{description}</p>}
        </div>

        {header && <div className="mb-6">{header}</div>}

        <main className="space-y-6">{children}</main>
      </div>
    </div>
  );
};
