'use client';

import * as React from 'react';
import { useState, useCallback, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import {
  ManualGenerateForm,
  ScenarioCard,
  PREDEFINED_SCENARIOS,
  ActiveScenariosList,
  LiveEventStream,
  useLiveEvents,
} from '@/components/mock';
import {
  useStartScenario,
  useStopScenario,
  useScenarios,
} from '@/lib/hooks/use-mock';
import type { ScenarioType, ScenarioInfo, EventType } from '@/types/event';

// Generate a random event ID
const generateEventId = () => `evt_${Math.random().toString(36).substr(2, 9)}`;

// Generate a mock live event
const generateMockLiveEvent = (scenario?: ScenarioType) => {
  const eventTypes: EventType[] = ['VIEW', 'CLICK', 'SEARCH', 'PURCHASE', 'COMMENT', 'LOGIN', 'LOGOUT'];

  // Weight event types based on scenario
  let weights: Record<EventType, number>;
  switch (scenario) {
    case 'flash_sale':
      weights = { VIEW: 40, CLICK: 30, PURCHASE: 20, SEARCH: 5, COMMENT: 2, LOGIN: 2, LOGOUT: 1 };
      break;
    case 'abnormal_spike':
      weights = { LOGIN: 30, LOGOUT: 25, VIEW: 15, CLICK: 10, SEARCH: 10, PURCHASE: 5, COMMENT: 5 };
      break;
    default:
      weights = { VIEW: 35, CLICK: 25, SEARCH: 15, PURCHASE: 10, COMMENT: 8, LOGIN: 4, LOGOUT: 3 };
  }

  // Weighted random selection
  const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0);
  let random = Math.random() * totalWeight;
  let selectedType: EventType = 'VIEW';
  for (const [type, weight] of Object.entries(weights)) {
    random -= weight;
    if (random <= 0) {
      selectedType = type as EventType;
      break;
    }
  }

  return {
    id: generateEventId(),
    timestamp: new Date().toISOString(),
    eventType: selectedType,
    userId: `user_${Math.floor(Math.random() * 1000).toString().padStart(3, '0')}`,
    data: {
      page: ['/', '/products', '/cart', '/checkout', '/profile'][Math.floor(Math.random() * 5)],
      amount: selectedType === 'PURCHASE' ? Math.floor(Math.random() * 1000) + 10 : undefined,
    },
  };
};

export default function MockPage() {
  const { toast } = useToast();
  const { events, addEvent, clearEvents } = useLiveEvents();
  const [eventRate, setEventRate] = useState(0);
  const [runningScenarios, setRunningScenarios] = useState<Map<string, { info: ScenarioInfo; intervalId: NodeJS.Timeout }>>(new Map());

  // Fetch running scenarios from API
  const { data: apiScenarios, refetch: refetchScenarios } = useScenarios();

  // Mutations
  const startScenarioMutation = useStartScenario();
  const stopScenarioMutation = useStopScenario();

  // Handle manual generate success
  const handleGenerateSuccess = useCallback((count: number) => {
    toast({
      title: 'Events Generated',
      description: `Successfully generated ${count.toLocaleString()} events`,
      variant: 'success',
    });

    // Add some mock events to the live stream
    for (let i = 0; i < Math.min(count, 50); i++) {
      setTimeout(() => {
        addEvent(generateMockLiveEvent());
      }, i * 50);
    }
  }, [toast, addEvent]);

  // Handle start scenario
  const handleStartScenario = useCallback(async (scenario: ScenarioType) => {
    const predefined = PREDEFINED_SCENARIOS.find((s) => s.id === scenario);
    if (!predefined) return;

    try {
      const result = await startScenarioMutation.mutateAsync({
        scenario,
        durationSeconds: predefined.defaultDuration,
        usersPerSecond: predefined.defaultUsersPerSecond,
      });

      toast({
        title: 'Scenario Started',
        description: `${predefined.name} scenario is now running`,
        variant: 'success',
      });

      // Simulate live events for demo
      const scenarioInfo: ScenarioInfo = {
        scenarioId: result.scenarioId,
        scenario,
        status: 'RUNNING',
        startTime: new Date().toISOString(),
        durationSeconds: predefined.defaultDuration,
        usersPerSecond: predefined.defaultUsersPerSecond,
        generatedCount: 0,
      };

      // Start generating mock events
      const intervalMs = 1000 / predefined.eventsPerSecond;
      let count = 0;
      const intervalId = setInterval(() => {
        addEvent(generateMockLiveEvent(scenario));
        count++;
        setEventRate((prev) => prev * 0.9 + (1000 / intervalMs) * 0.1);
      }, Math.max(intervalMs, 10));

      setRunningScenarios((prev) => new Map(prev).set(result.scenarioId, { info: scenarioInfo, intervalId }));
      refetchScenarios();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to start scenario',
        variant: 'destructive',
      });
    }
  }, [startScenarioMutation, toast, addEvent, refetchScenarios]);

  // Handle stop scenario
  const handleStopScenario = useCallback(async (scenarioId: string) => {
    const running = runningScenarios.get(scenarioId);

    try {
      const result = await stopScenarioMutation.mutateAsync(scenarioId);

      // Clear the interval
      if (running) {
        clearInterval(running.intervalId);
      }

      setRunningScenarios((prev) => {
        const next = new Map(prev);
        next.delete(scenarioId);
        return next;
      });

      toast({
        title: 'Scenario Stopped',
        description: `Generated ${result.totalGenerated.toLocaleString()} events`,
      });

      refetchScenarios();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to stop scenario',
        variant: 'destructive',
      });
    }
  }, [stopScenarioMutation, runningScenarios, toast, refetchScenarios]);

  // Cleanup intervals on unmount
  useEffect(() => {
    return () => {
      runningScenarios.forEach(({ intervalId }) => clearInterval(intervalId));
    };
  }, []);

  // Get all running scenarios (from local state + API)
  const allRunningScenarios = React.useMemo(() => {
    const localScenarios = Array.from(runningScenarios.values()).map(({ info }) => ({
      ...info,
      generatedCount: events.length,
    }));

    // Merge with API scenarios if available
    if (apiScenarios && apiScenarios.length > 0) {
      const apiRunning = apiScenarios.filter((s) => s.status === 'RUNNING');
      return [...localScenarios, ...apiRunning];
    }

    return localScenarios;
  }, [runningScenarios, events, apiScenarios]);

  // Get scenario status
  const getScenarioStatus = useCallback((scenarioId: ScenarioType): 'idle' | 'running' | 'completed' => {
    if (allRunningScenarios.some((s) => s.scenario === scenarioId)) {
      return 'running';
    }
    return 'idle';
  }, [allRunningScenarios]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Event Simulation</h1>
        <p className="text-muted-foreground">
          Generate mock events and simulate user scenarios
        </p>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="manual" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="manual">Manual Generate</TabsTrigger>
          <TabsTrigger value="scenario">Scenario Simulation</TabsTrigger>
        </TabsList>

        {/* Manual Generate Tab */}
        <TabsContent value="manual" className="mt-6">
          <ManualGenerateForm onGenerateSuccess={handleGenerateSuccess} />
        </TabsContent>

        {/* Scenario Simulation Tab */}
        <TabsContent value="scenario" className="mt-6 space-y-6">
          {/* Scenario Cards */}
          <div>
            <h2 className="text-lg font-semibold mb-4">Scenarios</h2>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {PREDEFINED_SCENARIOS.map((scenario) => {
                const status = getScenarioStatus(scenario.id);
                const runningInfo = allRunningScenarios.find((s) => s.scenario === scenario.id);

                return (
                  <ScenarioCard
                    key={scenario.id}
                    id={scenario.id}
                    name={scenario.name}
                    description={scenario.description}
                    icon={scenario.icon}
                    eventsPerSecond={scenario.eventsPerSecond}
                    status={status}
                    stats={
                      runningInfo
                        ? {
                            eventsGenerated: runningInfo.generatedCount,
                            duration: Math.floor(
                              (Date.now() - new Date(runningInfo.startTime).getTime()) / 1000
                            ),
                          }
                        : undefined
                    }
                    onStart={() => handleStartScenario(scenario.id)}
                    onStop={() => {
                      const running = allRunningScenarios.find((s) => s.scenario === scenario.id);
                      if (running) {
                        handleStopScenario(running.scenarioId);
                      }
                    }}
                  />
                );
              })}
            </div>
          </div>

          {/* Active Scenarios */}
          <ActiveScenariosList
            scenarios={allRunningScenarios}
            onStop={handleStopScenario}
          />

          {/* Live Event Stream */}
          <LiveEventStream
            events={events}
            eventRate={eventRate}
            onClear={clearEvents}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
