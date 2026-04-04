export type AuditStatus = 'PENDING' | 'IN_REVIEW' | 'APPROVED' | 'REJECTED';
export type AuditLevel = 'HIGH' | 'MEDIUM' | 'LOW';

export interface AuditOrder {
  orderId: string;
  userId: string;
  ruleId: string;
  ruleName?: string;
  triggerData: Record<string, unknown>;
  auditLevel: AuditLevel;
  status: AuditStatus;
  assignee?: string;
  reviewer?: string;
  reviewerNote?: string;
  createTime: string;
  updateTime: string;
  reviewTime?: string;
}

export interface ReviewInput {
  status: 'APPROVED' | 'REJECTED';
  reviewerNote?: string;
}

export interface AuditListParams {
  page?: number;
  size?: number;
  status?: AuditStatus;
  level?: AuditLevel;
  userId?: string;
  assignee?: string;
  sortBy?: 'createTime' | 'updateTime';
  sortOrder?: 'asc' | 'desc';
}

export interface AuditStats {
  total: number;
  pending: number;
  inReview: number;
  approved: number;
  rejected: number;
}

export interface AuditEvent {
  eventId: string;
  time: string;
  eventType: string;
  description: string;
  metadata?: Record<string, unknown>;
}

export interface AuditOrderDetail extends AuditOrder {
  events?: AuditEvent[];
  userTags?: string[];
}
