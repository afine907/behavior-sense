'use client';

import * as React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  type TooltipProps,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils/cn';

export type TimeRange = '1h' | '6h' | '24h' | '7d';

export interface TrendDataPoint {
  time: string;
  value: number;
  [key: string]: string | number;
}

export interface TrendChartProps {
  title: string;
  description?: string;
  data: TrendDataPoint[];
  timeRange: TimeRange;
  onTimeRangeChange: (range: TimeRange) => void;
  loading?: boolean;
  className?: string;
  color?: string;
  valueFormatter?: (value: number) => string;
}

const TIME_RANGES: { value: TimeRange; label: string }[] = [
  { value: '1h', label: '1h' },
  { value: '6h', label: '6h' },
  { value: '24h', label: '24h' },
  { value: '7d', label: '7d' },
];

function TrendChartSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <div className="h-5 w-32 animate-pulse rounded bg-muted" />
            <div className="mt-1 h-4 w-48 animate-pulse rounded bg-muted" />
          </div>
          <div className="flex gap-1">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-8 w-10 animate-pulse rounded bg-muted" />
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[200px] animate-pulse rounded bg-muted" />
      </CardContent>
    </Card>
  );
}

function CustomTooltip({
  active,
  payload,
  label,
  valueFormatter,
}: TooltipProps<number, string> & { valueFormatter?: (value: number) => string }) {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-lg border bg-background p-2 shadow-sm">
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className="mt-1 font-medium">
          {valueFormatter ? valueFormatter(payload[0].value as number) : payload[0].value}
        </div>
      </div>
    );
  }
  return null;
}

export function TrendChart({
  title,
  description,
  data,
  timeRange,
  onTimeRangeChange,
  loading = false,
  className,
  color = 'hsl(var(--primary))',
  valueFormatter,
}: TrendChartProps) {
  if (loading) {
    return <TrendChartSkeleton />;
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle className="text-base">{title}</CardTitle>
            {description && <CardDescription>{description}</CardDescription>}
          </div>
          <div className="flex gap-1">
            {TIME_RANGES.map((range) => (
              <button
                key={range.value}
                onClick={() => onTimeRangeChange(range.value)}
                className={cn(
                  'rounded-md px-3 py-1 text-xs font-medium transition-colors',
                  timeRange === range.value
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                )}
              >
                {range.label}
              </button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[200px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={data}
              margin={{
                top: 5,
                right: 10,
                left: 0,
                bottom: 5,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                className="text-muted-foreground"
              />
              <YAxis
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={valueFormatter}
                className="text-muted-foreground"
              />
              <Tooltip content={<CustomTooltip valueFormatter={valueFormatter} />} />
              <Line
                type="monotone"
                dataKey="value"
                stroke={color}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: color }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
