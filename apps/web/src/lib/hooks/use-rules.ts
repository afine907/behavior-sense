'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { rulesService } from '@/lib/api';
import type {
  Rule,
  CreateRuleInput,
  UpdateRuleInput,
} from '@/types/rule';

// Query keys
export const rulesKeys = {
  all: ['rules'] as const,
  lists: () => [...rulesKeys.all, 'list'] as const,
  list: (params: { page?: number; size?: number; enabled?: boolean }) =>
    [...rulesKeys.lists(), params] as const,
  details: () => [...rulesKeys.all, 'detail'] as const,
  detail: (id: string) => [...rulesKeys.details(), id] as const,
};

// List rules with pagination
export function useRules(params: {
  page?: number;
  size?: number;
  enabled?: boolean;
}) {
  return useQuery({
    queryKey: rulesKeys.list(params),
    queryFn: async () => {
      const response = await rulesService.list(params);
      return response.data;
    },
  });
}

// Get single rule by ID
export function useRule(id: string) {
  return useQuery({
    queryKey: rulesKeys.detail(id),
    queryFn: async () => {
      const response = await rulesService.get(id);
      return response.data;
    },
    enabled: !!id,
  });
}

// Create rule mutation
export function useCreateRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateRuleInput) => {
      const response = await rulesService.create(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rulesKeys.lists() });
    },
    onError: (error) => {
      console.error('Failed to create rule:', error);
    },
  });
}

// Update rule mutation
export function useUpdateRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: UpdateRuleInput }) => {
      const response = await rulesService.update(id, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: rulesKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: rulesKeys.lists() });
    },
    onError: (error) => {
      console.error('Failed to update rule:', error);
    },
  });
}

// Delete rule mutation
export function useDeleteRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await rulesService.delete(id);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rulesKeys.lists() });
    },
    onError: (error) => {
      console.error('Failed to delete rule:', error);
    },
  });
}

// Toggle rule enabled status
export function useToggleRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, enabled }: { id: string; enabled: boolean }) => {
      const response = await rulesService.update(id, { enabled });
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: rulesKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: rulesKeys.lists() });
    },
    onError: (error) => {
      console.error('Failed to toggle rule:', error);
    },
  });
}

// Test rule with sample data
export function useTestRule() {
  return useMutation({
    mutationFn: async ({
      id,
      testData,
    }: {
      id: string;
      testData: Record<string, unknown>;
    }) => {
      const response = await rulesService.test(id, testData);
      return response.data;
    },
    onError: (error) => {
      console.error('Failed to test rule:', error);
    },
  });
}
