'use client';

import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { UserProfile } from '@/components/insight';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { formatTime } from '@/lib/utils/date';
import {
  ArrowLeft,
  Clock,
  Eye,
  MousePointerClick,
  Search,
  ShoppingCart,
  LogIn,
  LogOut,
  MessageSquare,
} from 'lucide-react';

// Event type to icon mapping
const eventIcons: Record<string, typeof Eye> = {
  VIEW: Eye,
  CLICK: MousePointerClick,
  SEARCH: Search,
  PURCHASE: ShoppingCart,
  LOGIN: LogIn,
  LOGOUT: LogOut,
  COMMENT: MessageSquare,
};

// Event types
interface BaseEvent {
  id: string;
  eventType: string;
  timestamp: string;
  properties: Record<string, unknown>;
}

// Mock recent events (would come from API in real implementation)
const mockEvents: BaseEvent[] = [
  {
    id: '1',
    eventType: 'VIEW',
    timestamp: '2024-01-15T14:30:00Z',
    properties: { page: '/product/123' },
  },
  {
    id: '2',
    eventType: 'CLICK',
    timestamp: '2024-01-15T14:28:00Z',
    properties: { element: 'add_to_cart' },
  },
  {
    id: '3',
    eventType: 'SEARCH',
    timestamp: '2024-01-15T14:25:00Z',
    properties: { query: '手机壳' },
  },
  {
    id: '4',
    eventType: 'VIEW',
    timestamp: '2024-01-15T14:20:00Z',
    properties: { page: '/category/electronics' },
  },
  {
    id: '5',
    eventType: 'LOGIN',
    timestamp: '2024-01-15T14:15:00Z',
    properties: { device: 'mobile', ip: '192.168.1.1' },
  },
];

function getEventDescription(event: BaseEvent): string {
  const { eventType, properties } = event;
  switch (eventType) {
    case 'VIEW':
      return `Page: ${properties.page ?? 'unknown'}`;
    case 'CLICK':
      return `Element: ${properties.element ?? 'unknown'}`;
    case 'SEARCH':
      return `Query: "${properties.query ?? ''}"`;
    case 'PURCHASE':
      return `Amount: ¥${properties.amount ?? 0}`;
    case 'LOGIN':
      return `Device: ${properties.device ?? 'unknown'}`;
    case 'LOGOUT':
      return 'Logged out';
    case 'COMMENT':
      return `Content: ${properties.content ?? ''}`;
    default:
      return JSON.stringify(properties);
  }
}

interface EventItemProps {
  event: BaseEvent;
}

function EventItem({ event }: EventItemProps) {
  const Icon = eventIcons[event.eventType] || Eye;

  return (
    <div className="flex items-start gap-3 rounded-lg bg-muted/30 p-3 transition-colors hover:bg-muted/50">
      <div className="rounded-md bg-background p-2">
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium">{event.eventType}</span>
          <span className="text-xs text-muted-foreground">
            {formatTime(event.timestamp)}
          </span>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          {getEventDescription(event)}
        </p>
      </div>
    </div>
  );
}

export default function UserProfilePage() {
  const params = useParams();
  const router = useRouter();
  const userId = params.id as string;

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <div>
        <Button variant="ghost" size="sm" asChild>
          <Link href="/insight">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Search
          </Link>
        </Button>
      </div>

      {/* User Profile Component */}
      <UserProfile userId={userId} />

      {/* Recent Events Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Recent Events
              </CardTitle>
              <CardDescription>Latest user activity</CardDescription>
            </div>
            <Button variant="outline" size="sm">
              View All
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {mockEvents.map((event) => (
              <EventItem key={event.id} event={event} />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
