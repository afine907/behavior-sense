'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { auditService, type CreateAuditOrderInput } from '@/lib/api';
import type { ReviewInput, AuditListParams } from '@/types/audit';

// Query keys
export const auditKeys = {
  all: ['audit'] as const,
  lists: () => [...auditKeys.all, 'list'] as const,
  list: (params: AuditListParams) => [...auditKeys.lists(), params] as const,
  todos: () => [...auditKeys.all, 'todo'] as const,
  todo: (params: { page?: number; size?: number }) =>
    [...auditKeys.todos(), params] as const,
  details: () => [...auditKeys.all, 'detail'] as const,
  detail: (id: string) => [...auditKeys.details(), id] as const,
  stats: () => [...auditKeys.all, 'stats'] as const,
};

// List audit orders with pagination and filters
export function useAuditOrders(params: AuditListParams) {
  return useQuery({
    queryKey: auditKeys.list(params),
    queryFn: async () => {
      const response = await auditService.list(params);
      return response.data;
    },
  });
}

// Get my todo audit orders
export function useAuditTodo(params: { page?: number; size?: number }) {
  return useQuery({
    queryKey: auditKeys.todo(params),
    queryFn: async () => {
      const response = await auditService.todo(params);
      return response.data;
    },
  });
}

// Get single audit order by ID
export function useAuditOrder(id: string) {
  return useQuery({
    queryKey: auditKeys.detail(id),
    queryFn: async () => {
      const response = await auditService.get(id);
      return response.data;
    },
    enabled: !!id,
  });
}

// Get audit statistics
export function useAuditStats() {
  return useQuery({
    queryKey: auditKeys.stats(),
    queryFn: async () => {
      const response = await auditService.stats();
      return response.data;
    },
  });
}

// Create audit order mutation
export function useCreateAuditOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateAuditOrderInput) => {
      const response = await auditService.create(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.lists() });
      queryClient.invalidateQueries({ queryKey: auditKeys.todos() });
      queryClient.invalidateQueries({ queryKey: auditKeys.stats() });
    },
  });
}

// Submit audit review mutation
export function useReviewAuditOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: ReviewInput;
    }) => {
      const response = await auditService.review(id, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: auditKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: auditKeys.lists() });
      queryClient.invalidateQueries({ queryKey: auditKeys.todos() });
      queryClient.invalidateQueries({ queryKey: auditKeys.stats() });
    },
  });
}

// Approve audit order helper
export function useApproveAuditOrder() {
  const reviewMutation = useReviewAuditOrder();

  return {
    ...reviewMutation,
    mutate: (id: string, reviewerNote?: string) =>
      reviewMutation.mutate({
        id,
        data: { status: 'APPROVED', reviewerNote },
      }),
  };
}

// Reject audit order helper
export function useRejectAuditOrder() {
  const reviewMutation = useReviewAuditOrder();

  return {
    ...reviewMutation,
    mutate: (id: string, reviewerNote?: string) =>
      reviewMutation.mutate({
        id,
        data: { status: 'REJECTED', reviewerNote },
      }),
  };
}
