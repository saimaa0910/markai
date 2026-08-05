/**
 * @file index.ts
 * @description Campaigns Mutation Hooks.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

export function useCreateCampaignMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (campaignData: Record<string, unknown>) => {
      // TODO: Call API endpoint POST /api/campaigns
      return campaignData;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });
}
