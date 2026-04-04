'use client';

import * as React from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { cn } from '@/lib/utils/cn';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  trend?: 'up' | 'down' | 'neutral';
  icon?: React.ReactNode;
  href?: string;
  loading?: boolean;
  description?: string;
}

function MetricCardSkeleton() {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="h-4 w-24 animate-pulse rounded bg-muted" />
        <div className="h-4 w-4 animate-pulse rounded bg-muted" />
      </CardHeader>
      <CardContent>
        <div className="h-8 w-20 animate-pulse rounded bg-muted" />
        <div className="mt-2 h-3 w-32 animate-pulse rounded bg-muted" />
      </CardContent>
    </Card>
  );
}

export function MetricCard({
  title,
  value,
  change,
  trend = 'neutral',
  icon,
  href,
  loading = false,
  description,
}: MetricCardProps) {
  if (loading) {
    return <MetricCardSkeleton />;
  }

  const trendIcon = {
    up: TrendingUp,
    down: TrendingDown,
    neutral: Minus,
  }[trend];

  const trendColor = {
    up: 'text-green-500',
    down: 'text-red-500',
    neutral: 'text-muted-foreground',
  }[trend];

  const cardContent = (
    <Card className={cn('transition-all', href && 'hover:shadow-md hover:border-primary/50')}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <span className="text-sm font-medium text-muted-foreground">{title}</span>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {(change !== undefined || description) && (
          <div className="mt-1 flex items-center gap-1 text-xs">
            {change !== undefined && (
              <>
                {React.createElement(trendIcon, {
                  className: cn('h-3 w-3', trendColor),
                })}
                <span className={trendColor}>
                  {change > 0 ? '+' : ''}
                  {change}%
                </span>
              </>
            )}
            {description && (
              <span className="text-muted-foreground">{description}</span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );

  if (href) {
    return (
      <Link href={href} className="block">
        {cardContent}
      </Link>
    );
  }

  return cardContent;
}
