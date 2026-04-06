import { rulesApi } from './client';
import { toSearchParams } from './utils';
import type { ApiResponse, PaginatedResponse } from '@/types/api';
import type {
  Rule,
  CreateRuleInput,
  UpdateRuleInput,
  RuleTestResult,
} from '@/types/rule';

export const rulesService = {
  list: (params: { page?: number; size?: number; enabled?: boolean }) =>
    rulesApi
      .get('', {
        searchParams: toSearchParams(params),
      })
      .json<ApiResponse<PaginatedResponse<Rule>>>(),

  get: (id: string) =>
    rulesApi.get(id).json<ApiResponse<Rule>>(),

  create: (data: CreateRuleInput) =>
    rulesApi
      .post('', { json: data })
      .json<ApiResponse<{ ruleId: string }>>(),

  update: (id: string, data: UpdateRuleInput) =>
    rulesApi.put(id, { json: data }).json<ApiResponse<null>>(),

  delete: (id: string) =>
    rulesApi.delete(id).json<ApiResponse<null>>(),

  test: (id: string, testData: Record<string, unknown>) =>
    rulesApi
      .post(`${id}/test`, { json: testData })
      .json<ApiResponse<RuleTestResult>>(),
};
