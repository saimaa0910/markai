/**
 * @file index.ts
 * @description Next.js Middleware Handlers & Auth Guards.
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function handleAuthMiddleware(request: NextRequest) {
  // TODO: Validate JWT token from request cookies / headers
  return NextResponse.next();
}
