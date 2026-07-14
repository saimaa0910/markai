'use client';

import * as React from 'react';
import { DocumentDetailsPage } from '@/features/knowledge/pages/documents/details';

interface RouteProps {
  params: Promise<{ id: string }>;
}

export default function DocumentDetailsRoute({ params }: RouteProps) {
  const resolvedParams = React.use(params);
  return <DocumentDetailsPage id={resolvedParams.id} />;
}
