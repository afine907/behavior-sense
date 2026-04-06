import { mockApi } from './client';
import type { ApiResponse } from '@/types/api';
import type {
  GenerateEventsInput,
  GenerateEventsResult,
  StartScenarioInput,
  StartScenarioResult,
  StopScenarioResult,
  ScenarioInfo,
} from '@/types/event';

export const mockService = {
  // Generate mock events
  generate: (data: GenerateEventsInput) =>
    mockApi
      .post('generate', { json: data })
      .json<ApiResponse<GenerateEventsResult>>(),

  // Start scenario simulation
  startScenario: (data: StartScenarioInput) =>
    mockApi
      .post('scenario/start', { json: data })
      .json<ApiResponse<StartScenarioResult>>(),

  // Stop scenario simulation
  stopScenario: (scenarioId: string) =>
    mockApi
      .post(`scenario/${scenarioId}/stop`)
      .json<ApiResponse<StopScenarioResult>>(),

  // Get scenario info
  getScenario: (scenarioId: string) =>
    mockApi
      .get(`scenario/${scenarioId}`)
      .json<ApiResponse<ScenarioInfo>>(),

  // List running scenarios
  listScenarios: () =>
    mockApi.get('scenarios').json<ApiResponse<ScenarioInfo[]>>(),
};
