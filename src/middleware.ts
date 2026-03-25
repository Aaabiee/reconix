import { NextRequest, NextResponse } from 'next/server';

const protectedRoutes = [
  '/dashboard',
  '/recycled-sims',
  '/delink-requests',
  '/notifications',
  '/audit-logs',
  '/settings',
];

export function middleware(request: NextRequest): NextResponse {
  const accessToken = request.cookies.get('accessToken');
  const pathname = request.nextUrl.pathname;

  if (protectedRoutes.some((route) => pathname.startsWith(route))) {
    if (!accessToken) {
      return NextResponse.redirect(new URL('/', request.url));
    }
  }

  if (pathname === '/' && accessToken) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/',
    '/dashboard',
    '/dashboard/:path*',
    '/recycled-sims/:path*',
    '/delink-requests/:path*',
    '/notifications/:path*',
    '/audit-logs/:path*',
    '/settings/:path*',
  ],
};
