'use client';

import { Badge } from '@/components/ui/badge';
import type { AuditStatus, AuditLevel } from '@/types/audit';

interface StatusBadgeProps {
  status: AuditStatus;
  className?: string;
}

const statusConfig: Record<AuditStatus, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'warning' | 'success' | 'info' }> = {
  PENDING: { label: 'Pending', variant: 'warning' },
  IN_REVIEW: { label: 'In Review', variant: 'info' },
  APPROVED: { label: 'Approved', variant: 'success' },
  REJECTED: { label: 'Rejected', variant: 'destructive' },
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status];
  return (
    <Badge variant={config.variant} className={className}>
      {config.label}
    </Badge>
  );
}

interface LevelBadgeProps {
  level: AuditLevel;
  className?: string;
}

const levelConfig: Record<AuditLevel, { label: string; className: string }> = {
  HIGH: { label: 'HIGH', className: 'bg-red-500 hover:bg-red-500/80 text-white' },
  MEDIUM: { label: 'MEDIUM', className: 'bg-yellow-500 hover:bg-yellow-500/80 text-white' },
  LOW: { label: 'LOW', className: 'bg-green-500 hover:bg-green-500/80 text-white' },
};

export function LevelBadge({ level, className }: LevelBadgeProps) {
  const config = levelConfig[level];
  return (
    <Badge className={`${config.className} ${className || ''}`}>
      {config.label}
    </Badge>
  );
}
