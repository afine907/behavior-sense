'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { insightService, type UpdateTagInput, type BatchTagsRequest } from '@/lib/api';

// Query keys
export const insightKeys = {
  all: ['insight'] as const,
  users: () => [...insightKeys.all, 'user'] as const,
  userTags: (userId: string) => [...insightKeys.users(), userId, 'tags'] as const,
  userProfile: (userId: string) =>
    [...insightKeys.users(), userId, 'profile'] as const,
  tagStatistics: (tagName: string) =>
    [...insightKeys.all, 'statistics', tagName] as const,
};

// Get user tags
export function useUserTags(userId: string) {
  return useQuery({
    queryKey: insightKeys.userTags(userId),
    queryFn: async () => {
      const response = await insightService.getUserTags(userId);
      return response.data;
    },
    enabled: !!userId,
  });
}

// Get user profile
export function useUserProfile(userId: string) {
  return useQuery({
    queryKey: insightKeys.userProfile(userId),
    queryFn: async () => {
      const response = await insightService.getUserProfile(userId);
      return response.data;
    },
    enabled: !!userId,
  });
}

// Get tag statistics
export function useTagStatistics(tagName: string) {
  return useQuery({
    queryKey: insightKeys.tagStatistics(tagName),
    queryFn: async () => {
      const response = await insightService.getTagStatistics(tagName);
      return response.data;
    },
    enabled: !!tagName,
  });
}

// Batch get user tags
export function useBatchUserTags() {
  return useMutation({
    mutationFn: async (data: BatchTagsRequest) => {
      const response = await insightService.batchGetUserTags(data);
      return response.data;
    },
  });
}

// Update user tag mutation
export function useUpdateUserTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      userId,
      data,
    }: {
      userId: string;
      data: UpdateTagInput;
    }) => {
      const response = await insightService.updateUserTag(userId, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: insightKeys.userTags(variables.userId),
      });
      queryClient.invalidateQueries({
        queryKey: insightKeys.userProfile(variables.userId),
      });
      queryClient.invalidateQueries({
        queryKey: insightKeys.tagStatistics(variables.data.tagName),
      });
    },
  });
}
