'use client';

import * as React from 'react';
import {
  MetricCard,
  ServiceStatus,
  TrendChart,
  RecentActivityList,
  PendingAuditsList,
  type TimeRange,
  type ActivityItem,
  type PendingAuditItem,
} from '@/components/dashboard';
import {
  useDashboardMetrics,
  useServiceHealth,
  useEventTrend,
  useRecentActivity,
  useAuditTodo,
} from '@/lib/hooks';
import { Sparkles, ScrollText, Users, ClipboardCheck, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { format } from 'date-fns';

export default function DashboardPage() {
  const [timeRange, setTimeRange] = React.useState<TimeRange>('24h');
  const [lastUpdated, setLastUpdated] = React.useState(new Date());

  // Fetch dashboard data
  const { data: metrics, isLoading: metricsLoading, refetch: refetchMetrics } = useDashboardMetrics();
  const { data: services, isLoading: servicesLoading, refetch: refetchServices } = useServiceHealth();
  const { data: trendData, isLoading: trendLoading, refetch: refetchTrend } = useEventTrend(timeRange);
  const { data: activityData, isLoading: activityLoading, refetch: refetchActivity } = useRecentActivity();
  const { data: todoData, isLoading: todoLoading, refetch: refetchTodo } = useAuditTodo({ size: 4 });

  // Handle manual refresh
  const handleRefresh = React.useCallback(() => {
    refetchMetrics();
    refetchServices();
    refetchTrend();
    refetchActivity();
    refetchTodo();
    setLastUpdated(new Date());
  }, [refetchMetrics, refetchServices, refetchTrend, refetchActivity, refetchTodo]);

  // Transform activity data
  const activities: ActivityItem[] = React.useMemo(() => {
    if (!activityData) return [];
    return activityData.map((item) => ({
      id: item.id,
      type: item.type,
      title: item.title,
      description: item.description,
      timestamp: item.timestamp,
    }));
  }, [activityData]);

  // Transform pending audits data
  const pendingAudits: PendingAuditItem[] = React.useMemo(() => {
    if (!todoData?.list) return [];
    return todoData.list.map((audit) => ({
      orderId: audit.orderId,
      userId: audit.userId,
      ruleName: audit.ruleId,
      level: audit.auditLevel,
      createdAt: audit.createTime,
    }));
  }, [todoData]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome to BehaviorSense Admin Console
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm text-muted-foreground">
            Last updated: {format(lastUpdated, 'HH:mm:ss')}
          </div>
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total Events"
          value={metrics?.totalEvents?.toLocaleString() ?? '-'}
          change={metrics?.eventsChange}
          trend={metrics?.eventsChange && metrics.eventsChange > 0 ? 'up' : 'down'}
          icon={<Sparkles className="h-4 w-4" />}
          href="/mock"
          loading={metricsLoading}
        />
        <MetricCard
          title="Active Rules"
          value={metrics?.activeRules ?? '-'}
          change={metrics?.rulesChange}
          trend={metrics?.rulesChange && metrics.rulesChange > 0 ? 'up' : 'down'}
          icon={<ScrollText className="h-4 w-4" />}
          href="/rules"
          loading={metricsLoading}
        />
        <MetricCard
          title="Tags Updated"
          value={metrics?.tagsUpdated?.toLocaleString() ?? '-'}
          change={metrics?.tagsChange}
          trend={metrics?.tagsChange && metrics.tagsChange > 0 ? 'up' : 'down'}
          icon={<Users className="h-4 w-4" />}
          href="/insight"
          loading={metricsLoading}
        />
        <MetricCard
          title="Pending Audits"
          value={metrics?.pendingAudits ?? '-'}
          change={metrics?.auditsChange}
          trend={metrics?.auditsChange && metrics.auditsChange > 0 ? 'up' : 'down'}
          icon={<ClipboardCheck className="h-4 w-4" />}
          href="/audit"
          loading={metricsLoading}
        />
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <TrendChart
            title="Event Trend"
            description="Events processed over time"
            data={trendData ?? []}
            timeRange={timeRange}
            onTimeRangeChange={setTimeRange}
            loading={trendLoading}
            valueFormatter={(value) => value.toLocaleString()}
          />
        </div>
        <ServiceStatus
          services={services ?? []}
          loading={servicesLoading}
        />
      </div>

      {/* Activity Row */}
      <div className="grid gap-4 lg:grid-cols-2">
        <RecentActivityList
          title="Recent Activity"
          description="Latest events and actions"
          activities={activities}
          loading={activityLoading}
          viewAllHref="/monitor"
        />
        <PendingAuditsList
          items={pendingAudits}
          loading={todoLoading}
          viewAllHref="/audit"
        />
      </div>
    </div>
  );
}
