'use client';

import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LevelBadge, StatusBadge } from './status-badge';
import { formatRelative } from '@/lib/utils/date';
import type { AuditStatus, AuditLevel } from '@/types/audit';

export interface AuditCardProps {
  orderId: string;
  userId: string;
  level: AuditLevel;
  ruleName: string;
  triggerSummary: string;
  createdAt: string;
  status: AuditStatus;
  onViewDetails?: () => void;
  onQuickApprove?: () => void;
  onQuickReject?: () => void;
  showActions?: boolean;
}

export function AuditCard({
  orderId,
  userId,
  level,
  ruleName,
  triggerSummary,
  createdAt,
  status,
  onViewDetails,
  onQuickApprove,
  onQuickReject,
  showActions = true,
}: AuditCardProps) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="p-0">
        {/* Header with level badge */}
        <div className="flex items-center gap-3 border-b bg-muted/30 px-4 py-3">
          <LevelBadge level={level} />
          <span className="text-sm font-medium text-muted-foreground">
            User: {userId}
          </span>
          <StatusBadge status={status} className="ml-auto" />
        </div>

        {/* Content */}
        <div className="space-y-2 p-4">
          <div>
            <span className="text-xs text-muted-foreground">Rule:</span>
            <p className="text-sm font-medium">{ruleName}</p>
          </div>
          <div>
            <span className="text-xs text-muted-foreground">Trigger:</span>
            <p className="text-sm text-muted-foreground line-clamp-2">
              {triggerSummary}
            </p>
          </div>
          <div className="text-xs text-muted-foreground">
            {formatRelative(createdAt)}
          </div>
        </div>

        {/* Actions */}
        {showActions && (
          <div className="flex items-center gap-2 border-t bg-muted/20 px-4 py-3">
            <Link href={`/audit/order/${orderId}`}>
              <Button variant="outline" size="sm" onClick={onViewDetails}>
                View Details
              </Button>
            </Link>
            {status === 'PENDING' && (
              <>
                <Button
                  variant="default"
                  size="sm"
                  className="bg-green-600 hover:bg-green-700"
                  onClick={onQuickApprove}
                >
                  Approve
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={onQuickReject}
                >
                  Reject
                </Button>
              </>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
