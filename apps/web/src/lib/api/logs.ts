/**
 * Logs API Service
 */
import { logsApi } from './client';
import { toSearchParams } from './utils';
import type { ApiResponse, PaginatedResponse } from '@/types/api';
import type { EventLog, EventLogListParams, EventStats } from '@/types/logs';

export const logsService = {
  list: (params: EventLogListParams) =>
    logsApi
      .get('events', {
        searchParams: toSearchParams(params),
      })
      .json<ApiResponse<PaginatedResponse<EventLog>>>(),

  get: (eventId: string) =>
    logsApi.get(`events/${eventId}`).json<ApiResponse<EventLog>>(),

  stats: (params?: { startTime?: string; endTime?: string }) =>
    logsApi
      .get('stats', {
        searchParams: params ? toSearchParams(params) : undefined,
      })
      .json<ApiResponse<EventStats>>(),
};
