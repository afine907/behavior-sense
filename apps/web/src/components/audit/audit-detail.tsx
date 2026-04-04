'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { StatusBadge, LevelBadge } from './status-badge';
import { EventTimeline } from './event-timeline';
import { ReviewForm } from './review-form';
import { formatDate } from '@/lib/utils/date';
import { ExternalLink } from 'lucide-react';
import type { AuditOrder } from '@/types/audit';

interface AuditDetailProps {
  order: AuditOrder;
  events?: Array<{
    time: string;
    eventType: string;
    description: string;
    metadata?: Record<string, unknown>;
  }>;
  onReview: (data: { status: 'APPROVED' | 'REJECTED'; reviewerNote?: string }) => void;
  isReviewing?: boolean;
  hasMoreEvents?: boolean;
  onLoadMoreEvents?: () => void;
  isLoadingEvents?: boolean;
}

export function AuditDetail({
  order,
  events = [],
  onReview,
  isReviewing = false,
  hasMoreEvents = false,
  onLoadMoreEvents,
  isLoadingEvents = false,
}: AuditDetailProps) {
  // Extract rule name from triggerData if available
  const ruleName = (order.triggerData?.ruleName as string) || `Rule ${order.ruleId}`;

  // Generate trigger summary from triggerData
  const triggerSummary = Object.entries(order.triggerData || {})
    .filter(([key]) => key !== 'ruleName' && key !== 'ruleId')
    .map(([key, value]) => `${key}: ${String(value)}`)
    .join(', ') || 'No trigger data available';

  // Check if order can be reviewed
  const canReview = order.status === 'PENDING' || order.status === 'IN_REVIEW';

  return (
    <div className="space-y-6">
      {/* Status Header */}
      <Card>
        <CardContent className="flex items-center justify-between p-6">
          <div className="flex items-center gap-4">
            <div>
              <h2 className="text-lg font-semibold">Audit Order</h2>
              <p className="text-sm text-muted-foreground">{order.orderId}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={order.status} />
            <LevelBadge level={order.auditLevel} />
          </div>
        </CardContent>
      </Card>

      {/* Info Cards */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Trigger Information */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Trigger Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <span className="text-xs text-muted-foreground">Rule Name</span>
              <p className="text-sm font-medium">{ruleName}</p>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">Rule ID</span>
              <p className="text-sm text-muted-foreground">{order.ruleId}</p>
            </div>
            <Separator />
            <div>
              <span className="text-xs text-muted-foreground">Condition Matched</span>
              <p className="text-sm">{triggerSummary}</p>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">Triggered At</span>
              <p className="text-sm">{formatDate(order.createTime)}</p>
            </div>
            {order.assignee && (
              <div>
                <span className="text-xs text-muted-foreground">Assignee</span>
                <p className="text-sm">{order.assignee}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* User Profile Summary */}
        <Card>
          <CardHeader className="flex flex-row items-start justify-between">
            <div>
              <CardTitle className="text-base">User Profile</CardTitle>
              <CardDescription>User involved in this audit</CardDescription>
            </div>
            <Link href={`/insight/${order.userId}`}>
              <Button variant="ghost" size="sm">
                <ExternalLink className="mr-1 h-4 w-4" />
                View Full Profile
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <span className="text-xs text-muted-foreground">User ID</span>
              <p className="text-sm font-medium">{order.userId}</p>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">Tags</span>
              <div className="mt-1 flex flex-wrap gap-1">
                {(order.triggerData?.userTags as string[])?.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs"
                  >
                    {tag}
                  </span>
                )) || <span className="text-sm text-muted-foreground">No tags</span>}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Event Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Event Timeline</CardTitle>
          <CardDescription>Events leading to this audit</CardDescription>
        </CardHeader>
        <CardContent>
          <EventTimeline
            events={events}
            loadMore={onLoadMoreEvents}
            hasMore={hasMoreEvents}
            isLoading={isLoadingEvents}
          />
        </CardContent>
      </Card>

      {/* Review Form */}
      {canReview && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Review Decision</CardTitle>
            <CardDescription>Submit your review for this audit order</CardDescription>
          </CardHeader>
          <CardContent>
            <ReviewForm onSubmit={onReview} isSubmitting={isReviewing} />
          </CardContent>
        </Card>
      )}

      {/* Already reviewed message */}
      {!canReview && (
        <Card className="bg-muted/50">
          <CardContent className="flex items-center justify-center p-6">
            <p className="text-sm text-muted-foreground">
              This audit order has already been{' '}
              <StatusBadge status={order.status} className="mx-1" />
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
