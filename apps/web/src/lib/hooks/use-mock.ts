'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { mockService } from '@/lib/api';
import type {
  GenerateEventsInput,
  StartScenarioInput,
} from '@/types/event';

// Query keys
export const mockKeys = {
  all: ['mock'] as const,
  scenarios: () => [...mockKeys.all, 'scenarios'] as const,
  scenario: (id: string) => [...mockKeys.scenarios(), id] as const,
};

// Generate mock events mutation
export function useGenerateEvents() {
  return useMutation({
    mutationFn: async (data: GenerateEventsInput) => {
      const response = await mockService.generate(data);
      return response.data;
    },
  });
}

// Start scenario simulation mutation
export function useStartScenario() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: StartScenarioInput) => {
      const response = await mockService.startScenario(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mockKeys.scenarios() });
    },
  });
}

// Stop scenario simulation mutation
export function useStopScenario() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (scenarioId: string) => {
      const response = await mockService.stopScenario(scenarioId);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: mockKeys.scenarios() });
    },
  });
}

// Get scenario info
export function useScenario(scenarioId: string) {
  return useQuery({
    queryKey: mockKeys.scenario(scenarioId),
    queryFn: async () => {
      const response = await mockService.getScenario(scenarioId);
      return response.data;
    },
    enabled: !!scenarioId,
    refetchInterval: 5000, // Refresh every 5 seconds for running scenarios
  });
}

// List running scenarios
export function useScenarios() {
  return useQuery({
    queryKey: mockKeys.scenarios(),
    queryFn: async () => {
      const response = await mockService.listScenarios();
      return response.data;
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });
}
