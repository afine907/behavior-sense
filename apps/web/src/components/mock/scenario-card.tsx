'use client';

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Play, Square, Zap, Users, AlertTriangle } from 'lucide-react';
import type { ScenarioType } from '@/types/event';

export interface ScenarioCardProps {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  eventsPerSecond: number;
  status: 'idle' | 'running' | 'completed';
  stats?: {
    eventsGenerated: number;
    duration: number;
  };
  onStart: () => void;
  onStop: () => void;
}

const statusVariants = {
  idle: 'secondary',
  running: 'default',
  completed: 'success',
} as const;

export function ScenarioCard({
  name,
  description,
  icon,
  eventsPerSecond,
  status,
  stats,
  onStart,
  onStop,
}: ScenarioCardProps) {
  const isRunning = status === 'running';

  return (
    <Card className="relative overflow-hidden">
      {isRunning && (
        <div className="absolute inset-0 bg-primary/5 pointer-events-none" />
      )}
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-muted">
              {icon}
            </div>
            <CardTitle className="text-base">{name}</CardTitle>
          </div>
          <Badge variant={statusVariants[status]}>
            {status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">{description}</p>

        <div className="flex items-center gap-2 text-sm">
          <Zap className="h-4 w-4 text-yellow-500" />
          <span>{eventsPerSecond.toLocaleString()} events/sec</span>
        </div>

        {isRunning && stats && (
          <div className="space-y-1 text-sm">
            <div className="flex items-center justify-between text-muted-foreground">
              <span>Generated:</span>
              <span className="font-mono text-foreground">
                {stats.eventsGenerated.toLocaleString()}
              </span>
            </div>
            <div className="flex items-center justify-between text-muted-foreground">
              <span>Duration:</span>
              <span className="font-mono text-foreground">
                {Math.floor(stats.duration / 60)}m {stats.duration % 60}s
              </span>
            </div>
          </div>
        )}

        {status === 'completed' && stats && (
          <div className="p-2 rounded bg-muted text-sm">
            <span className="text-muted-foreground">Total: </span>
            <span className="font-semibold">{stats.eventsGenerated.toLocaleString()} events</span>
          </div>
        )}

        <Button
          onClick={isRunning ? onStop : onStart}
          variant={isRunning ? 'destructive' : 'default'}
          className="w-full"
          size="sm"
        >
          {isRunning ? (
            <>
              <Square className="mr-2 h-4 w-4" />
              Stop
            </>
          ) : (
            <>
              <Play className="mr-2 h-4 w-4" />
              Start
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}

// Predefined scenario configurations
export const PREDEFINED_SCENARIOS: Array<{
  id: ScenarioType;
  name: string;
  description: string;
  icon: React.ReactNode;
  eventsPerSecond: number;
  defaultDuration: number;
  defaultUsersPerSecond: number;
}> = [
  {
    id: 'flash_sale',
    name: 'Flash Sale',
    description: 'High traffic simulation with rapid user activity and purchase events.',
    icon: <Zap className="h-5 w-5 text-yellow-500" />,
    eventsPerSecond: 1000,
    defaultDuration: 60,
    defaultUsersPerSecond: 100,
  },
  {
    id: 'normal_traffic',
    name: 'Normal Traffic',
    description: 'Regular user behavior patterns with moderate activity levels.',
    icon: <Users className="h-5 w-5 text-blue-500" />,
    eventsPerSecond: 100,
    defaultDuration: 300,
    defaultUsersPerSecond: 10,
  },
  {
    id: 'abnormal_spike',
    name: 'Abnormal Behavior',
    description: 'Risky behavior patterns including rapid actions and anomalies.',
    icon: <AlertTriangle className="h-5 w-5 text-red-500" />,
    eventsPerSecond: 50,
    defaultDuration: 120,
    defaultUsersPerSecond: 5,
  },
];
