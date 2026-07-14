'use client';

import * as React from 'react';
import { ModelDetailsPage } from '@/features/ai-platform/pages/model-details';

interface RouteProps {
  params: Promise<{ id: string }>;
}

export default function ModelDetailsRoute({ params }: RouteProps) {
  const resolvedParams = React.use(params);
  return <ModelDetailsPage id={resolvedParams.id} />;
}
