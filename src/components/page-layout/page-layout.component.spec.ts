import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { PageLayout } from './page-layout.component';

jest.mock('next/link', () => {
  return ({ children, href, ...props }: any) =>
    React.createElement('a', { href, ...props }, children);
});

jest.mock('lucide-react', () => ({
  ChevronRight: () => React.createElement('span', null, '>'),
}));

describe('PageLayout', () => {
  it('renders title', () => {
    render(React.createElement(PageLayout, { title: 'Test Page' }, 'Content'));
    expect(screen.getByText('Test Page')).toBeInTheDocument();
  });

  it('renders description when provided', () => {
    render(React.createElement(PageLayout, { title: 'Page', description: 'A description' }, 'Content'));
    expect(screen.getByText('A description')).toBeInTheDocument();
  });

  it('renders children', () => {
    render(React.createElement(PageLayout, { title: 'Page' }, 'Child content'));
    expect(screen.getByText('Child content')).toBeInTheDocument();
  });

  it('renders breadcrumbs when provided', () => {
    const breadcrumbs = [
      { label: 'Section', href: '/section' },
      { label: 'Current' },
    ];
    render(React.createElement(PageLayout, { title: 'Page', breadcrumbs }, 'Content'));
    expect(screen.getByRole('navigation', { name: 'Breadcrumb' })).toBeInTheDocument();
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Section')).toBeInTheDocument();
    expect(screen.getByText('Current')).toBeInTheDocument();
  });

  it('renders breadcrumb links for items with href', () => {
    const breadcrumbs = [{ label: 'Section', href: '/section' }];
    render(React.createElement(PageLayout, { title: 'Page', breadcrumbs }, 'Content'));
    const link = screen.getByText('Section');
    expect(link.tagName).toBe('A');
    expect(link).toHaveAttribute('href', '/section');
  });

  it('renders current page breadcrumb as span with aria-current', () => {
    const breadcrumbs = [{ label: 'Current Page' }];
    render(React.createElement(PageLayout, { title: 'Page', breadcrumbs }, 'Content'));
    const current = screen.getByText('Current Page');
    expect(current.tagName).toBe('SPAN');
    expect(current).toHaveAttribute('aria-current', 'page');
  });

  it('renders header section when provided', () => {
    const header = React.createElement('div', null, 'Header content');
    render(React.createElement(PageLayout, { title: 'Page', header }, 'Content'));
    expect(screen.getByText('Header content')).toBeInTheDocument();
  });

  it('has a main element', () => {
    render(React.createElement(PageLayout, { title: 'Page' }, 'Content'));
    expect(screen.getByRole('main')).toBeInTheDocument();
  });
});
