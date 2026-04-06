import { auditApi } from './client';
import { toSearchParams } from './utils';
import type { ApiResponse, PaginatedResponse } from '@/types/api';
import type {
  AuditOrder,
  AuditOrderDetail,
  ReviewInput,
  AuditListParams,
  AuditStats,
  AuditLevel,
  AuditEvent,
} from '@/types/audit';

export interface CreateAuditOrderInput {
  userId: string;
  ruleId: string;
  triggerData: Record<string, unknown>;
  auditLevel: AuditLevel;
}

export const auditService = {
  list: (params: AuditListParams) =>
    auditApi
      .get('orders', {
        searchParams: toSearchParams(params),
      })
      .json<ApiResponse<PaginatedResponse<AuditOrder>>>(),

  todo: (params: { page?: number; size?: number }) =>
    auditApi
      .get('orders/todo', {
        searchParams: toSearchParams(params),
      })
      .json<ApiResponse<{ total: number; list: AuditOrder[] }>>(),

  get: (id: string) =>
    auditApi.get(`order/${id}`).json<ApiResponse<AuditOrderDetail>>(),

  create: (data: CreateAuditOrderInput) =>
    auditApi
      .post('order', { json: data })
      .json<ApiResponse<{ orderId: string }>>(),

  review: (id: string, data: ReviewInput) =>
    auditApi
      .put(`order/${id}/review`, { json: data })
      .json<ApiResponse<null>>(),

  stats: () =>
    auditApi.get('stats').json<ApiResponse<AuditStats>>(),

  getEvents: (id: string, params?: { page?: number; size?: number }) =>
    auditApi
      .get(`order/${id}/events`, {
        searchParams: params ? toSearchParams(params) : undefined,
      })
      .json<ApiResponse<PaginatedResponse<AuditEvent>>>(),
};
