import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api-client';
import {
  ImageGenerateRequest, ImageEditRequest, ImageVariationRequest,
  ImageUpscaleRequest, ImageBackgroundRemoveRequest, ImageBackgroundReplaceRequest,
  ImageInpaintRequest, ImageOutpaintRequest, ImageResponse,
  ImageHistoryItem, ImageProvider, ImageModel
} from '../types';

export const useImageStudio = () => {
  const queryClient = useQueryClient();

  // Queries
  const useHistory = () => {
    return useQuery<ImageHistoryItem[]>({
      queryKey: ['image-studio', 'history'],
      queryFn: async () => {
        const res = await apiClient.get<ImageHistoryItem[]>('/agents/image/history');
        return res.data;
      },
    });
  };

  const useProviders = () => {
    return useQuery<ImageProvider[]>({
      queryKey: ['image-studio', 'providers'],
      queryFn: async () => {
        const res = await apiClient.get<ImageProvider[]>('/agents/image/providers');
        return res.data;
      },
    });
  };

  const useModels = () => {
    return useQuery<ImageModel[]>({
      queryKey: ['image-studio', 'models'],
      queryFn: async () => {
        const res = await apiClient.get<ImageModel[]>('/agents/image/models');
        return res.data;
      },
    });
  };

  // Mutations
  const generateMutation = useMutation<ImageResponse, Error, ImageGenerateRequest>({
    mutationFn: async (payload) => {
      const res = await apiClient.post<ImageResponse>('/agents/image/generate', payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['image-studio', 'history'] });
    },
  });

  const editMutation = useMutation<ImageResponse, Error, ImageEditRequest>({
    mutationFn: async (payload) => {
      const res = await apiClient.post<ImageResponse>('/agents/image/edit', payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['image-studio', 'history'] });
    },
  });

  const variationMutation = useMutation<ImageResponse, Error, ImageVariationRequest>({
    mutationFn: async (payload) => {
      const res = await apiClient.post<ImageResponse>('/agents/image/variation', payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['image-studio', 'history'] });
    },
  });

  const upscaleMutation = useMutation<ImageResponse, Error, ImageUpscaleRequest>({
    mutationFn: async (payload) => {
      const res = await apiClient.post<ImageResponse>('/agents/image/upscale', payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['image-studio', 'history'] });
    },
  });

  const removeBackgroundMutation = useMutation<ImageResponse, Error, ImageBackgroundRemoveRequest>({
    mutationFn: async (payload) => {
      const res = await apiClient.post<ImageResponse>('/agents/image/background/remove', payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['image-studio', 'history'] });
    },
  });

  const replaceBackgroundMutation = useMutation<ImageResponse, Error, ImageBackgroundReplaceRequest>({
    mutationFn: async (payload) => {
      const res = await apiClient.post<ImageResponse>('/agents/image/background/replace', payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['image-studio', 'history'] });
    },
  });

  const inpaintMutation = useMutation<ImageResponse, Error, ImageInpaintRequest>({
    mutationFn: async (payload) => {
      const res = await apiClient.post<ImageResponse>('/agents/image/inpaint', payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['image-studio', 'history'] });
    },
  });

  const outpaintMutation = useMutation<ImageResponse, Error, ImageOutpaintRequest>({
    mutationFn: async (payload) => {
      const res = await apiClient.post<ImageResponse>('/agents/image/outpaint', payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['image-studio', 'history'] });
    },
  });

  return {
    useHistory,
    useProviders,
    useModels,
    generateMutation,
    editMutation,
    variationMutation,
    upscaleMutation,
    removeBackgroundMutation,
    replaceBackgroundMutation,
    inpaintMutation,
    outpaintMutation,
  };
};
export default useImageStudio;
