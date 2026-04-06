'use client';

import { useQuery, type UseQueryResult } from '@tanstack/react-query';
import { mockApi, rulesApi, insightApi, auditApi } from '@/lib/api';
import type { ApiResponse, PaginatedResponse } from '@/types/api';
import type { AuditOrder } from '@/types/audit';
import type { Rule } from '@/types/rule';
import type { TimeRange } from '@/components/dashboard';

// Query keys
export const dashboardKeys = {
  all: ['dashboard'] as const,
  metrics: () => [...dashboardKeys.all, 'metrics'] as const,
  services: () => [...dashboardKeys.all, 'services'] as const,
  eventTrend: (range: TimeRange) => [...dashboardKeys.all, 'eventTrend', range] as const,
  recentActivity: () => [...dashboardKeys.all, 'recentActivity'] as const,
};

// Dashboard metrics interface
export interface DashboardMetrics {
  totalEvents: number;
  activeRules: number;
  tagsUpdated: number;
  pendingAudits: number;
  eventsChange: number;
  rulesChange: number;
  tagsChange: number;
  auditsChange: number;
}

// Service health interface
export interface ServiceHealth {
  name: string;
  port: number;
  status: 'healthy' | 'unhealthy' | 'unknown';
  latency?: number;
}

// Event trend data point
export interface EventTrendPoint {
  time: string;
  value: number;
  [key: string]: string | number;
}

// Recent activity item
export interface RecentActivityItem {
  id: string;
  type: 'rule_trigger' | 'tag_update' | 'audit_complete' | 'event_batch';
  title: string;
  description: string;
  timestamp: string;
}

// Fetch dashboard metrics
export function useDashboardMetrics(): UseQueryResult<DashboardMetrics, Error> {
  return useQuery({
    queryKey: dashboardKeys.metrics(),
    queryFn: async (): Promise<DashboardMetrics> => {
      // Fetch data from multiple services in parallel
      const [rulesRes, auditsRes] = await Promise.all([
        rulesApi.get('rules', { searchParams: { size: '1' } }).json<ApiResponse<PaginatedResponse<Rule>>>(),
        auditApi.get('audit/stats').json<ApiResponse<{ pending: number }>>(),
      ]);

      // Calculate metrics
      const activeRules = rulesRes.data?.total || 0;
      const pendingAudits = auditsRes.data?.pending || 0;

      return {
        totalEvents: Math.floor(Math.random() * 50000) + 10000, // Mock for now
        activeRules,
        tagsUpdated: Math.floor(Math.random() * 500) + 100, // Mock for now
        pendingAudits,
        eventsChange: Math.random() * 20 - 5,
        rulesChange: Math.random() * 10 - 2,
        tagsChange: Math.random() * 15 - 3,
        auditsChange: Math.random() * 10 - 5,
      };
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}

// Fetch service health status
export function useServiceHealth(): UseQueryResult<ServiceHealth[], Error> {
  return useQuery({
    queryKey: dashboardKeys.services(),
    queryFn: async (): Promise<ServiceHealth[]> => {
      const services = [
        { name: 'mock', port: 8001, url: mockApi },
        { name: 'rules', port: 8002, url: rulesApi },
        { name: 'insight', port: 8003, url: insightApi },
        { name: 'audit', port: 8004, url: auditApi },
      ];

      const results = await Promise.allSettled(
        services.map(async (service) => {
          const start = Date.now();
          try {
            await service.url.get('health').json();
            const latency = Date.now() - start;
            return {
              name: service.name,
              port: service.port,
              status: 'healthy' as const,
              latency,
            };
          } catch (error) {
            console.error(`Health check failed for ${service.name}:`, error);
            return {
              name: service.name,
              port: service.port,
              status: 'unhealthy' as const,
              latency: undefined,
            };
          }
        })
      );

      return results.map((result, index) => {
        if (result.status === 'fulfilled') {
          return result.value;
        }
        return {
          name: services[index].name,
          port: services[index].port,
          status: 'unknown' as const,
        };
      });
    },
    refetchInterval: 60000, // Refresh every minute
  });
}

// Fetch event trend data
export function useEventTrend(timeRange: TimeRange): UseQueryResult<EventTrendPoint[], Error> {
  return useQuery({
    queryKey: dashboardKeys.eventTrend(timeRange),
    queryFn: async (): Promise<EventTrendPoint[]> => {
      // Generate mock trend data based on time range
      const now = Date.now();
      const points: EventTrendPoint[] = [];

      const config = {
        '1h': { count: 12, interval: 5 * 60 * 1000 }, // 5 min intervals
        '6h': { count: 12, interval: 30 * 60 * 1000 }, // 30 min intervals
        '24h': { count: 24, interval: 60 * 60 * 1000 }, // 1 hour intervals
        '7d': { count: 7, interval: 24 * 60 * 60 * 1000 }, // 1 day intervals
      }[timeRange];

      for (let i = config.count - 1; i >= 0; i--) {
        const timestamp = new Date(now - i * config.interval);
        const value = Math.floor(Math.random() * 1000) + 500;

        points.push({
          time: timeRange === '7d'
            ? timestamp.toLocaleDateString('en-US', { weekday: 'short' })
            : timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
          value,
        });
      }

      return points;
    },
    refetchInterval: 60000, // Refresh every minute
  });
}

// Fetch recent activity
export function useRecentActivity(): UseQueryResult<RecentActivityItem[], Error> {
  return useQuery({
    queryKey: dashboardKeys.recentActivity(),
    queryFn: async (): Promise<RecentActivityItem[]> => {
      // Fetch recent audit orders as activity
      try {
        const auditsRes = await auditApi
          .get('audit/orders', { searchParams: { size: '5' } })
          .json<ApiResponse<PaginatedResponse<AuditOrder>>>();

        const activities: RecentActivityItem[] = (auditsRes.data?.list || []).map((audit) => ({
          id: audit.orderId,
          type: 'audit_complete' as const,
          title: `Audit ${audit.status.toLowerCase()}`,
          description: `Order for ${audit.userId} - ${audit.auditLevel}`,
          timestamp: audit.createTime,
        }));

        // Add some mock rule triggers
        const now = Date.now();
        const mockActivities: RecentActivityItem[] = [
          {
            id: '1',
            type: 'rule_trigger',
            title: 'Rule triggered',
            description: 'high_risk_user for user_045',
            timestamp: new Date(now - 2 * 60 * 1000).toISOString(),
          },
          {
            id: '2',
            type: 'tag_update',
            title: 'Tag updated',
            description: 'VIP tag added to user_123',
            timestamp: new Date(now - 5 * 60 * 1000).toISOString(),
          },
          {
            id: '3',
            type: 'event_batch',
            title: 'Events generated',
            description: '1,000 mock events created',
            timestamp: new Date(now - 15 * 60 * 1000).toISOString(),
          },
        ];

        return [...mockActivities, ...activities].slice(0, 8);
      } catch {
        // Return mock data on error
        const now = Date.now();
        return [
          {
            id: '1',
            type: 'rule_trigger' as const,
            title: 'Rule triggered',
            description: 'high_risk_user for user_045',
            timestamp: new Date(now - 2 * 60 * 1000).toISOString(),
          },
          {
            id: '2',
            type: 'tag_update' as const,
            title: 'Tag updated',
            description: 'VIP tag added to user_123',
            timestamp: new Date(now - 5 * 60 * 1000).toISOString(),
          },
          {
            id: '3',
            type: 'audit_complete' as const,
            title: 'Audit completed',
            description: 'Order #1024 approved',
            timestamp: new Date(now - 12 * 60 * 1000).toISOString(),
          },
          {
            id: '4',
            type: 'event_batch' as const,
            title: 'Events generated',
            description: '1,000 mock events created',
            timestamp: new Date(now - 25 * 60 * 1000).toISOString(),
          },
        ];
      }
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}
