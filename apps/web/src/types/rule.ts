export interface Rule {
  ruleId: string;
  name: string;
  description?: string;
  condition: string;
  priority: number;
  enabled: boolean;
  actions: RuleAction[];
  createTime: string;
  updateTime: string;
}

export interface RuleAction {
  type: 'TAG_USER' | 'TRIGGER_AUDIT';
  params: Record<string, unknown>;
}

export interface CreateRuleInput {
  name: string;
  description?: string;
  condition: string;
  priority: number;
  enabled: boolean;
  actions: RuleAction[];
}

export interface UpdateRuleInput {
  name?: string;
  description?: string;
  condition?: string;
  priority?: number;
  enabled?: boolean;
  actions?: RuleAction[];
}

export interface RuleTestResult {
  matched: boolean;
  details?: Record<string, unknown> | null;
}
