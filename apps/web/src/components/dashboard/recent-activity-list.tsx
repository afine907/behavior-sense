'use client';

import * as React from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils/cn';
import { ArrowRight, ExternalLink } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export interface ActivityItem {
  id: string;
  type: 'rule_trigger' | 'tag_update' | 'audit_complete' | 'event_batch' | 'scenario';
  title: string;
  description: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
  href?: string;
}

export interface RecentActivityListProps {
  title: string;
  description?: string;
  activities: ActivityItem[];
  loading?: boolean;
  className?: string;
  emptyMessage?: string;
  viewAllHref?: string;
  maxItems?: number;
}

function ActivityListSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-start gap-3">
          <div className="mt-1 h-2 w-2 animate-pulse rounded-full bg-muted" />
          <div className="flex-1">
            <div className="h-4 w-32 animate-pulse rounded bg-muted" />
            <div className="mt-1 h-3 w-48 animate-pulse rounded bg-muted" />
          </div>
          <div className="h-3 w-16 animate-pulse rounded bg-muted" />
        </div>
      ))}
    </div>
  );
}

const ACTIVITY_TYPE_COLORS: Record<ActivityItem['type'], string> = {
  rule_trigger: 'bg-blue-500',
  tag_update: 'bg-purple-500',
  audit_complete: 'bg-green-500',
  event_batch: 'bg-orange-500',
  scenario: 'bg-cyan-500',
};

function ActivityTypeDot({ type }: { type: ActivityItem['type'] }) {
  return (
    <div
      className={cn(
        'mt-1.5 h-2 w-2 rounded-full',
        ACTIVITY_TYPE_COLORS[type]
      )}
    />
  );
}

function ActivityItemRow({ activity }: { activity: ActivityItem }) {
  const timeAgo = formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true });

  const content = (
    <div className="flex items-start gap-3 py-2 transition-colors hover:bg-accent/50 rounded-lg px-2 -mx-2">
      <ActivityTypeDot type={activity.type} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{activity.title}</p>
        <p className="text-xs text-muted-foreground truncate">{activity.description}</p>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-xs text-muted-foreground">{timeAgo}</span>
        {activity.href && <ExternalLink className="h-3 w-3 text-muted-foreground" />}
      </div>
    </div>
  );

  if (activity.href) {
    return (
      <Link href={activity.href}>
        {content}
      </Link>
    );
  }

  return content;
}

export function RecentActivityList({
  title,
  description,
  activities,
  loading = false,
  className,
  emptyMessage = 'No recent activity',
  viewAllHref,
  maxItems = 5,
}: RecentActivityListProps) {
  const displayActivities = activities.slice(0, maxItems);

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base">{title}</CardTitle>
            {description && <CardDescription>{description}</CardDescription>}
          </div>
          {viewAllHref && (
            <Button variant="ghost" size="sm" asChild className="shrink-0">
              <Link href={viewAllHref}>
                View All
                <ArrowRight className="ml-1 h-3 w-3" />
              </Link>
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <ActivityListSkeleton count={maxItems} />
        ) : displayActivities.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <p className="text-sm text-muted-foreground">{emptyMessage}</p>
          </div>
        ) : (
          <div className="space-y-1">
            {displayActivities.map((activity) => (
              <ActivityItemRow key={activity.id} activity={activity} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
