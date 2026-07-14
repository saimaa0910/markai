'use client';

import * as React from 'react';
import { PromptDetailsPage } from '@/features/prompts/pages/details';

interface RouteProps {
  params: Promise<{ id: string }>;
}

export default function PromptDetailsRoute({ params }: RouteProps) {
  const resolvedParams = React.use(params);
  return <PromptDetailsPage id={resolvedParams.id} />;
}
