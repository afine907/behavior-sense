/**
 * 事件日志类型定义
 */

export type EventType =
  | 'view'
  | 'click'
  | 'search'
  | 'purchase'
  | 'comment'
  | 'login'
  | 'logout'
  | 'register'
  | 'favorite'
  | 'share';

export interface EventLog {
  eventId: string;
  userId: string;
  eventType: EventType;
  timestamp: string;
  sessionId: string | null;
  pageUrl: string | null;
  referrer: string | null;
  userAgent: string | null;
  ipAddress: string | null;
  properties: Record<string, unknown>;
  ingestedAt: string | null;
}

export interface EventLogListParams {
  userId?: string;
  eventType?: EventType;
  sessionId?: string;
  startTime?: string;
  endTime?: string;
  pageUrl?: string;
  ipAddress?: string;
  page?: number;
  size?: number;
  sortOrder?: 'asc' | 'desc';
}

export interface EventStats {
  totalEvents: number;
  uniqueUsers: number;
  uniqueSessions: number;
  eventTypeCounts: Record<EventType, number>;
}
