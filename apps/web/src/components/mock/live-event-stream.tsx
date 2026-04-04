'use client';

import * as React from 'react';
import { useRef, useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Pause, Play, Trash2, Activity, Radio } from 'lucide-react';
import type { EventType } from '@/types/event';

interface LiveEvent {
  id: string;
  timestamp: string;
  eventType: EventType;
  userId: string;
  data: Record<string, unknown>;
}

interface LiveEventStreamProps {
  events: LiveEvent[];
  eventRate?: number;
  onClear?: () => void;
}

const EVENT_TYPE_COLORS: Record<EventType, string> = {
  VIEW: 'text-blue-400',
  CLICK: 'text-green-400',
  SEARCH: 'text-yellow-400',
  PURCHASE: 'text-purple-400',
  COMMENT: 'text-pink-400',
  LOGIN: 'text-cyan-400',
  LOGOUT: 'text-orange-400',
};

const MAX_EVENTS = 500;

export function LiveEventStream({ events, eventRate = 0, onClear }: LiveEventStreamProps) {
  const [isPaused, setIsPaused] = useState(false);
  const [filterType, setFilterType] = useState<EventType | 'all'>('all');
  const scrollRef = useRef<HTMLDivElement>(null);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);

  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    if (shouldAutoScroll && !isPaused && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events, isPaused, shouldAutoScroll]);

  // Handle manual scroll to disable auto-scroll
  const handleScroll = useCallback(() => {
    if (scrollRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
      setShouldAutoScroll(isAtBottom);
    }
  }, []);

  const filteredEvents = React.useMemo(() => {
    let result = events;
    if (filterType !== 'all') {
      result = result.filter((e) => e.eventType === filterType);
    }
    // Keep only the last MAX_EVENTS
    return result.slice(-MAX_EVENTS);
  }, [events, filterType]);

  const formatEvent = (event: LiveEvent) => {
    const time = new Date(event.timestamp).toLocaleTimeString();
    const colorClass = EVENT_TYPE_COLORS[event.eventType] || 'text-gray-400';

    return (
      <div
        key={event.id}
        className="font-mono text-xs py-0.5 border-b border-border/30 last:border-0"
      >
        <span className="text-muted-foreground mr-2">[{time}]</span>
        <span className={`${colorClass} font-semibold mr-2`}>
          {event.eventType}
        </span>
        <span className="text-foreground">
          {JSON.stringify({ user: event.userId, ...event.data })}
        </span>
      </div>
    );
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Radio className="h-5 w-5" />
            Live Event Stream
          </CardTitle>
          <div className="flex items-center gap-2">
            {eventRate > 0 && (
              <Badge variant="outline" className="font-mono">
                <Activity className="h-3 w-3 mr-1" />
                {eventRate.toFixed(1)} events/s
              </Badge>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsPaused(!isPaused)}
            >
              {isPaused ? (
                <>
                  <Play className="h-4 w-4 mr-1" />
                  Resume
                </>
              ) : (
                <>
                  <Pause className="h-4 w-4 mr-1" />
                  Pause
                </>
              )}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onClear}
              disabled={events.length === 0}
            >
              <Trash2 className="h-4 w-4 mr-1" />
              Clear
            </Button>
          </div>
        </div>

        <div className="flex items-center gap-2 mt-2">
          <span className="text-sm text-muted-foreground">Filter:</span>
          <Select
            value={filterType}
            onValueChange={(v) => setFilterType(v as EventType | 'all')}
          >
            <SelectTrigger className="w-40 h-8">
              <SelectValue placeholder="All types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              {Object.keys(EVENT_TYPE_COLORS).map((type) => (
                <SelectItem key={type} value={type}>
                  {type}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <span className="text-sm text-muted-foreground ml-4">
            Showing {filteredEvents.length} of {events.length} events
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className="h-64 overflow-y-auto bg-muted/50 rounded-lg p-3 font-mono text-sm"
        >
          {filteredEvents.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
              <Radio className="h-8 w-8 mb-2 opacity-50" />
              <p>No events to display</p>
              <p className="text-xs opacity-70">
                Generate events or start a scenario to see live data
              </p>
            </div>
          ) : (
            filteredEvents.map(formatEvent)
          )}
        </div>

        {isPaused && (
          <div className="mt-2 text-center">
            <Badge variant="secondary">Stream paused - {events.length - filteredEvents.length} new events waiting</Badge>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Hook to manage live events with auto-trim
export function useLiveEvents(maxEvents: number = MAX_EVENTS) {
  const [events, setEvents] = useState<LiveEvent[]>([]);

  const addEvent = useCallback((event: LiveEvent) => {
    setEvents((prev) => {
      const newEvents = [...prev, event];
      // Auto-trim older events
      if (newEvents.length > maxEvents) {
        return newEvents.slice(-maxEvents);
      }
      return newEvents;
    });
  }, [maxEvents]);

  const addEvents = useCallback((newEvents: LiveEvent[]) => {
    setEvents((prev) => {
      const combined = [...prev, ...newEvents];
      if (combined.length > maxEvents) {
        return combined.slice(-maxEvents);
      }
      return combined;
    });
  }, [maxEvents]);

  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  return {
    events,
    addEvent,
    addEvents,
    clearEvents,
  };
}
