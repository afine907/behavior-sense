// Event types for mock module

export type EventType = 'VIEW' | 'CLICK' | 'SEARCH' | 'PURCHASE' | 'COMMENT' | 'LOGIN' | 'LOGOUT';

export interface GenerateEventsInput {
  count: number;
  eventTypes?: EventType[];
  userCount?: number;
}

export interface GenerateEventsResult {
  generatedCount: number;
  durationMs: number;
}

// Scenario types
export type ScenarioType = 'flash_sale' | 'normal_traffic' | 'abnormal_spike' | 'bot_attack';

export interface StartScenarioInput {
  scenario: ScenarioType;
  durationSeconds: number;
  usersPerSecond: number;
}

export interface StartScenarioResult {
  scenarioId: string;
}

export interface StopScenarioResult {
  totalGenerated: number;
}

// Scenario status
export type ScenarioStatus = 'RUNNING' | 'STOPPED' | 'ERROR';

export interface ScenarioInfo {
  scenarioId: string;
  scenario: ScenarioType;
  status: ScenarioStatus;
  startTime: string;
  durationSeconds: number;
  usersPerSecond: number;
  generatedCount: number;
}
