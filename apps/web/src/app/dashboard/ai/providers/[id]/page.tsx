'use client';

import * as React from 'react';
import { ProviderDetailsPage } from '@/features/ai-platform/pages/provider-details';

interface RouteProps {
  params: Promise<{ id: string }>;
}

export default function ProviderDetailsRoute({ params }: RouteProps) {
  const resolvedParams = React.use(params);
  return <ProviderDetailsPage id={resolvedParams.id} />;
}
