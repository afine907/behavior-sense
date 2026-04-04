'use client';

import * as React from 'react';
import { useState } from 'react';
import { ChevronDown, ChevronUp, Clock } from 'lucide-react';
import { cn } from '@/lib/utils/cn';
import { formatTime } from '@/lib/utils/date';
import { Button } from '@/components/ui/button';

interface EventItem {
  time: string;
  eventType: string;
  description: string;
  metadata?: Record<string, unknown>;
}

export interface EventTimelineProps {
  events: EventItem[];
  loadMore?: () => void;
  hasMore?: boolean;
  isLoading?: boolean;
}

const eventTypeColors: Record<string, string> = {
  VIEW: 'bg-blue-500',
  CLICK: 'bg-green-500',
  SEARCH: 'bg-purple-500',
  PURCHASE: 'bg-yellow-500',
  LOGIN: 'bg-cyan-500',
  LOGOUT: 'bg-gray-500',
  LOGIN_FAIL: 'bg-red-500',
  COMMENT: 'bg-pink-500',
  DEFAULT: 'bg-gray-400',
};

function getEventColor(eventType: string): string {
  return eventTypeColors[eventType.toUpperCase()] || eventTypeColors.DEFAULT;
}

function EventItemRow({ event }: { event: EventItem }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="relative flex gap-4 pb-6 last:pb-0">
      {/* Timeline connector */}
      <div className="flex flex-col items-center">
        <div
          className={cn(
            'h-3 w-3 rounded-full ring-4 ring-background',
            getEventColor(event.eventType)
          )}
        />
        <div className="flex-1 w-px bg-border" />
      </div>

      {/* Content */}
      <div className="flex-1 space-y-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{event.eventType}</span>
          <span className="text-xs text-muted-foreground">
            {formatTime(event.time)}
          </span>
        </div>
        <p className="text-sm text-muted-foreground">{event.description}</p>

        {/* Expandable metadata */}
        {event.metadata && Object.keys(event.metadata).length > 0 && (
          <div className="mt-2">
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-xs"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? (
                <>
                  <ChevronUp className="mr-1 h-3 w-3" />
                  Hide Details
                </>
              ) : (
                <>
                  <ChevronDown className="mr-1 h-3 w-3" />
                  Show Details
                </>
              )}
            </Button>
            {expanded && (
              <pre className="mt-2 overflow-x-auto rounded-md bg-muted p-2 text-xs">
                {JSON.stringify(event.metadata, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export function EventTimeline({
  events,
  loadMore,
  hasMore = false,
  isLoading = false,
}: EventTimelineProps) {
  if (events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <Clock className="h-10 w-10 text-muted-foreground/50" />
        <p className="mt-2 text-sm text-muted-foreground">No events found</p>
      </div>
    );
  }

  return (
    <div className="space-y-0">
      {events.map((event, index) => (
        <EventItemRow key={`${event.time}-${index}`} event={event} />
      ))}

      {hasMore && (
        <div className="pt-4">
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={loadMore}
            disabled={isLoading}
          >
            {isLoading ? 'Loading...' : 'Load More'}
          </Button>
        </div>
      )}
    </div>
  );
}
