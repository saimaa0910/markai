import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * P2-11: Route-guard proxy.
 *
 * Guards protected application routes by verifying an authenticated session
 * marker cookie that is set/cleared on login/logout (see store/auth.ts).
 * Note: token values remain in localStorage (sent via Authorization header);
 * this proxy provides a server-side route-level guard and consistent
 * redirects for unauthenticated navigation.
 */

const PUBLIC_PREFIXES = [
  '/auth',
  '/_next',
  '/favicon.ico',
  '/assets',
];

const PROTECTED_PREFIXES = ['/dashboard'];

function isPublic(pathname: string): boolean {
  return PUBLIC_PREFIXES.some((p) => pathname.startsWith(p)) || pathname === '/';
}

function isProtected(pathname: string): boolean {
  return PROTECTED_PREFIXES.some((p) => pathname.startsWith(p));
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasSessionCookie = Boolean(request.cookies.get('eaimos.session')?.value);

  if (isProtected(pathname) && !hasSessionCookie) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = '/auth/login';
    loginUrl.searchParams.set('next', pathname);
    loginUrl.searchParams.set('expired', 'true');
    return NextResponse.redirect(loginUrl);
  }

  if (isPublic(pathname) && hasSessionCookie && pathname.startsWith('/auth')) {
    const dashUrl = request.nextUrl.clone();
    dashUrl.pathname = '/dashboard';
    return NextResponse.redirect(dashUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|assets).*)'],
};
