'use client';

import * as React from 'react';
import { CollectionDetailsPage } from '@/features/knowledge/pages/collections/details';

interface RouteProps {
  params: Promise<{ id: string }>;
}

export default function CollectionDetailsRoute({ params }: RouteProps) {
  const resolvedParams = React.use(params);
  return <CollectionDetailsPage id={resolvedParams.id} />;
}
