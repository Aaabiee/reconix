import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

jest.mock('@/components/sidebar/sidebar.component', () => ({
  Sidebar: () => <nav data-testid="sidebar">Sidebar</nav>,
}));

jest.mock('@/components/header/header.component', () => ({
  Header: () => <header data-testid="header">Header</header>,
}));

describe('App', () => {
  it('renders the application shell with sidebar and header', () => {
    render(
      <App>
        <div data-testid="page-content">Page Content</div>
      </App>
    );

    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('header')).toBeInTheDocument();
    expect(screen.getByTestId('page-content')).toBeInTheDocument();
  });

  it('renders children inside the main content area', () => {
    render(
      <App>
        <h1>Dashboard</h1>
      </App>
    );

    const main = document.querySelector('main');
    expect(main).toBeInTheDocument();
    expect(main).toHaveTextContent('Dashboard');
  });

  it('applies overflow-y-auto on the main element for scrolling', () => {
    render(
      <App>
        <div>Content</div>
      </App>
    );

    const main = document.querySelector('main');
    expect(main?.className).toContain('overflow-y-auto');
  });

  it('wraps content in a flex layout', () => {
    const { container } = render(
      <App>
        <div>Content</div>
      </App>
    );

    const root = container.firstChild as HTMLElement;
    expect(root.className).toContain('flex');
    expect(root.className).toContain('h-screen');
  });
});
