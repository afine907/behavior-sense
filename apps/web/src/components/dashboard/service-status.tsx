'use client';

import * as React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils/cn';
import { Activity, Server, Clock } from 'lucide-react';

export type ServiceHealthStatus = 'healthy' | 'unhealthy' | 'unknown';

export interface ServiceInfo {
  name: string;
  port: number;
  status: ServiceHealthStatus;
  latency?: number;
  lastCheck?: string;
}

export interface ServiceStatusProps {
  services: ServiceInfo[];
  loading?: boolean;
  className?: string;
}

function ServiceStatusSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="h-5 w-32 animate-pulse rounded bg-muted" />
        <div className="h-4 w-48 animate-pulse rounded bg-muted" />
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex items-center gap-3 rounded-lg border p-3">
              <div className="h-3 w-3 animate-pulse rounded-full bg-muted" />
              <div className="flex-1">
                <div className="h-4 w-16 animate-pulse rounded bg-muted" />
                <div className="mt-1 h-3 w-12 animate-pulse rounded bg-muted" />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function StatusDot({ status }: { status: ServiceHealthStatus }) {
  const colorClass = {
    healthy: 'bg-green-500',
    unhealthy: 'bg-red-500',
    unknown: 'bg-gray-400',
  }[status];

  const pulseClass = status === 'healthy' ? 'animate-pulse' : '';

  return (
    <div className="relative flex h-3 w-3">
      <span className={cn('absolute inline-flex h-full w-full rounded-full opacity-75', colorClass, pulseClass)} />
      <span className={cn('relative inline-flex h-3 w-3 rounded-full', colorClass)} />
    </div>
  );
}

function ServiceCard({ service }: { service: ServiceInfo }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border bg-card p-3 transition-colors hover:bg-accent/50">
      <StatusDot status={service.status} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">{service.name}</span>
          <span className="text-xs text-muted-foreground">:{service.port}</span>
        </div>
        {service.latency !== undefined && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            <span>{service.latency}ms</span>
          </div>
        )}
      </div>
      {service.status === 'healthy' && (
        <Activity className="h-4 w-4 text-green-500" />
      )}
    </div>
  );
}

export function ServiceStatus({ services, loading = false, className }: ServiceStatusProps) {
  if (loading) {
    return <ServiceStatusSkeleton />;
  }

  const healthyCount = services.filter((s) => s.status === 'healthy').length;
  const allHealthy = healthyCount === services.length;

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Server className="h-4 w-4" />
          Service Status
        </CardTitle>
        <CardDescription>
          {allHealthy
            ? 'All services operational'
            : `${healthyCount}/${services.length} services healthy`}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3">
          {services.map((service) => (
            <ServiceCard key={service.name} service={service} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
