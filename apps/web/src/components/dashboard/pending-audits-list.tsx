'use client';

import * as React from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils/cn';
import { ArrowRight, AlertTriangle, Clock, User } from 'lucide-react';
import type { AuditLevel } from '@/types/audit';

export interface PendingAuditItem {
  orderId: string;
  userId: string;
  ruleName: string;
  level: AuditLevel;
  createdAt: string;
  triggerSummary?: string;
}

export interface PendingAuditsListProps {
  items: PendingAuditItem[];
  loading?: boolean;
  className?: string;
  viewAllHref?: string;
}

const LEVEL_COLORS: Record<AuditLevel, string> = {
  HIGH: 'bg-red-100 text-red-700 border-red-200',
  MEDIUM: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  LOW: 'bg-green-100 text-green-700 border-green-200',
};

const LEVEL_ICONS: Record<AuditLevel, React.ComponentType<{ className?: string }>> = {
  HIGH: AlertTriangle,
  MEDIUM: Clock,
  LOW: User,
};

function PendingAuditsSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 rounded-lg border p-3">
          <div className="h-6 w-14 animate-pulse rounded bg-muted" />
          <div className="flex-1">
            <div className="h-4 w-24 animate-pulse rounded bg-muted" />
            <div className="mt-1 h-3 w-32 animate-pulse rounded bg-muted" />
          </div>
        </div>
      ))}
    </div>
  );
}

function LevelBadge({ level }: { level: AuditLevel }) {
  const Icon = LEVEL_ICONS[level];
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded border px-2 py-0.5 text-xs font-medium',
        LEVEL_COLORS[level]
      )}
    >
      <Icon className="h-3 w-3" />
      {level}
    </span>
  );
}

function PendingAuditRow({ item }: { item: PendingAuditItem }) {
  return (
    <Link
      href={`/audit/${item.orderId}`}
      className="flex items-center gap-3 rounded-lg border bg-card p-3 transition-colors hover:bg-accent/50"
    >
      <LevelBadge level={item.level} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">{item.userId}</span>
        </div>
        <p className="text-xs text-muted-foreground truncate">
          {item.ruleName}
          {item.triggerSummary && ` - ${item.triggerSummary}`}
        </p>
      </div>
      <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />
    </Link>
  );
}

export function PendingAuditsList({
  items,
  loading = false,
  className,
  viewAllHref = '/audit',
}: PendingAuditsListProps) {
  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base">Pending Audits</CardTitle>
            <CardDescription>
              {loading ? 'Loading...' : `${items.length} pending review`}
            </CardDescription>
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
          <PendingAuditsSkeleton />
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <p className="text-sm text-muted-foreground">No pending audits</p>
          </div>
        ) : (
          <div className="space-y-2">
            {items.slice(0, 4).map((item) => (
              <PendingAuditRow key={item.orderId} item={item} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
