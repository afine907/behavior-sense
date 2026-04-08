'use client';

import { useQuery } from '@tanstack/react-query';
import { logsService } from '@/lib/api/logs';
import type { EventLogListParams } from '@/types/logs';

// Query keys
export const logsKeys = {
  all: ['logs'] as const,
  lists: () => [...logsKeys.all, 'list'] as const,
  list: (params: EventLogListParams) => [...logsKeys.lists(), params] as const,
  details: () => [...logsKeys.all, 'detail'] as const,
  detail: (id: string) => [...logsKeys.details(), id] as const,
  stats: () => [...logsKeys.all, 'stats'] as const,
};

// List events with pagination and filters
export function useEventLogs(params: EventLogListParams) {
  return useQuery({
    queryKey: logsKeys.list(params),
    queryFn: async () => {
      const response = await logsService.list(params);
      return response.data;
    },
    staleTime: 30_000, // 30 seconds
  });
}

// Get single event by ID
export function useEventLog(eventId: string) {
  return useQuery({
    queryKey: logsKeys.detail(eventId),
    queryFn: async () => {
      const response = await logsService.get(eventId);
      return response.data;
    },
    enabled: !!eventId,
    staleTime: 60_000, // 1 minute
  });
}

// Get event statistics
export function useEventStats(params?: {
  startTime?: string;
  endTime?: string;
}) {
  return useQuery({
    queryKey: logsKeys.stats(),
    queryFn: async () => {
      const response = await logsService.stats(params);
      return response.data;
    },
    staleTime: 60_000, // 1 minute
  });
}
