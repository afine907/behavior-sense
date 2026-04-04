'use client';

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Square, Clock, Activity, Inbox } from 'lucide-react';
import type { ScenarioInfo } from '@/types/event';

interface ActiveScenariosListProps {
  scenarios: ScenarioInfo[];
  onStop: (scenarioId: string) => void;
}

export function ActiveScenariosList({ scenarios, onStop }: ActiveScenariosListProps) {
  const formatDuration = (startTime: string) => {
    const start = new Date(startTime).getTime();
    const now = Date.now();
    const diffSeconds = Math.floor((now - start) / 1000);

    const hours = Math.floor(diffSeconds / 3600);
    const minutes = Math.floor((diffSeconds % 3600) / 60);
    const seconds = diffSeconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m ${seconds}s`;
    }
    if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  };

  if (scenarios.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Active Scenarios
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Inbox className="h-12 w-12 text-muted-foreground/50 mb-3" />
            <p className="text-muted-foreground">No active scenarios</p>
            <p className="text-sm text-muted-foreground/70">
              Start a scenario to see it here
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Active Scenarios
          <Badge variant="default" className="ml-auto">
            {scenarios.length} running
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {scenarios.map((scenario) => (
            <div
              key={scenario.scenarioId}
              className="flex items-center justify-between p-3 rounded-lg border bg-muted/50"
            >
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                  <span className="font-medium capitalize">
                    {scenario.scenario.replace('_', ' ')}
                  </span>
                </div>

                <Badge variant="secondary" className="text-xs">
                  {scenario.usersPerSecond} users/sec
                </Badge>
              </div>

              <div className="flex items-center gap-4">
                <div className="flex items-center gap-1 text-sm text-muted-foreground">
                  <Activity className="h-4 w-4" />
                  <span className="font-mono">
                    {scenario.generatedCount.toLocaleString()} events
                  </span>
                </div>

                <div className="flex items-center gap-1 text-sm text-muted-foreground">
                  <Clock className="h-4 w-4" />
                  <span className="font-mono">
                    <DurationTimer startTime={scenario.startTime} />
                  </span>
                </div>

                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => onStop(scenario.scenarioId)}
                >
                  <Square className="h-4 w-4 mr-1" />
                  Stop
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// Timer component that updates every second
function DurationTimer({ startTime }: { startTime: string }) {
  const [duration, setDuration] = React.useState(() => {
    const start = new Date(startTime).getTime();
    const now = Date.now();
    return Math.floor((now - start) / 1000);
  });

  React.useEffect(() => {
    const interval = setInterval(() => {
      const start = new Date(startTime).getTime();
      const now = Date.now();
      setDuration(Math.floor((now - start) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  const hours = Math.floor(duration / 3600);
  const minutes = Math.floor((duration % 3600) / 60);
  const seconds = duration % 60;

  if (hours > 0) {
    return <>{hours}h {minutes}m {seconds}s</>;
  }
  if (minutes > 0) {
    return <>{minutes}m {seconds}s</>;
  }
  return <>{seconds}s</>;
}
