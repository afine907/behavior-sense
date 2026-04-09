'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { useEventLogs, useEventStats } from '@/lib/hooks/use-logs';
import type { EventType } from '@/types/logs';
import {
  Search,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Database,
  Users,
  Activity,
  Eye,
  MousePointer,
  ShoppingCart,
  Search as SearchIcon,
  MessageSquare,
  LogIn,
  LogOut,
  Heart,
  Share2,
  UserPlus,
  FileText,
} from 'lucide-react';
import { format } from 'date-fns';

const EVENT_TYPE_OPTIONS = [
  { value: 'ALL', label: 'All Types', icon: <Activity className="h-4 w-4" /> },
  { value: 'view', label: 'View', icon: <Eye className="h-4 w-4" /> },
  { value: 'click', label: 'Click', icon: <MousePointer className="h-4 w-4" /> },
  { value: 'search', label: 'Search', icon: <SearchIcon className="h-4 w-4" /> },
  { value: 'purchase', label: 'Purchase', icon: <ShoppingCart className="h-4 w-4" /> },
  { value: 'comment', label: 'Comment', icon: <MessageSquare className="h-4 w-4" /> },
  { value: 'login', label: 'Login', icon: <LogIn className="h-4 w-4" /> },
  { value: 'logout', label: 'Logout', icon: <LogOut className="h-4 w-4" /> },
  { value: 'register', label: 'Register', icon: <UserPlus className="h-4 w-4" /> },
  { value: 'favorite', label: 'Favorite', icon: <Heart className="h-4 w-4" /> },
  { value: 'share', label: 'Share', icon: <Share2 className="h-4 w-4" /> },
] as const;

const EVENT_TYPE_COLORS: Record<EventType, string> = {
  view: 'bg-blue-100 text-blue-800',
  click: 'bg-green-100 text-green-800',
  search: 'bg-yellow-100 text-yellow-800',
  purchase: 'bg-purple-100 text-purple-800',
  comment: 'bg-pink-100 text-pink-800',
  login: 'bg-cyan-100 text-cyan-800',
  logout: 'bg-orange-100 text-orange-800',
  register: 'bg-indigo-100 text-indigo-800',
  favorite: 'bg-red-100 text-red-800',
  share: 'bg-teal-100 text-teal-800',
};

export default function LogsPage() {
  const router = useRouter();

  // Filter states
  const [page, setPage] = React.useState(1);
  const [pageSize] = React.useState(50);
  const [eventTypeFilter, setEventTypeFilter] = React.useState<EventType | 'ALL'>('ALL');
  const [userIdSearch, setUserIdSearch] = React.useState('');
  const [sessionIdSearch, setSessionIdSearch] = React.useState('');
  const [startTime, setStartTime] = React.useState('');
  const [endTime, setEndTime] = React.useState('');
  const [searchInput, setSearchInput] = React.useState('');

  // Build query params
  const params = React.useMemo(
    () => ({
      page,
      size: pageSize,
      ...(eventTypeFilter !== 'ALL' && { eventType: eventTypeFilter }),
      ...(userIdSearch && { userId: userIdSearch }),
      ...(sessionIdSearch && { sessionId: sessionIdSearch }),
      ...(startTime && { startTime }),
      ...(endTime && { endTime }),
    }),
    [page, pageSize, eventTypeFilter, userIdSearch, sessionIdSearch, startTime, endTime]
  );

  // Queries
  const { data: logsData, isLoading, refetch } = useEventLogs(params);
  const { data: statsData } = useEventStats();

  // Handlers
  const handleSearch = () => {
    setUserIdSearch(searchInput);
    setPage(1);
  };

  const handleClearFilters = () => {
    setEventTypeFilter('ALL');
    setUserIdSearch('');
    setSessionIdSearch('');
    setStartTime('');
    setEndTime('');
    setSearchInput('');
    setPage(1);
  };

  const logs = logsData?.list || [];
  const totalItems = logsData?.total || 0;
  const totalPages = Math.ceil(totalItems / pageSize);
  const stats = statsData || {
    totalEvents: 0,
    uniqueUsers: 0,
    uniqueSessions: 0,
    eventTypeCounts: {},
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Event Logs</h1>
          <p className="text-muted-foreground">
            Search and analyze user behavior events
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Database className="h-4 w-4" />
              Total Events
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="text-2xl font-bold">
              {stats.totalEvents.toLocaleString()}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Users className="h-4 w-4" />
              Unique Users
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="text-2xl font-bold">
              {stats.uniqueUsers.toLocaleString()}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Sessions
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="text-2xl font-bold">
              {stats.uniqueSessions.toLocaleString()}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Top Event Type
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="text-2xl font-bold capitalize">
              {Object.entries(stats.eventTypeCounts).sort((a, b) => b[1] - a[1])[0]?.[0] ||
                '-'}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-end gap-4">
            {/* User ID Search */}
            <div className="flex-1 min-w-[200px]">
              <Label htmlFor="userId" className="text-xs text-muted-foreground">
                User ID
              </Label>
              <div className="flex gap-2 mt-1">
                <Input
                  id="userId"
                  placeholder="Search by user ID..."
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                />
                <Button onClick={handleSearch}>
                  <Search className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Event Type Filter */}
            <div className="w-[150px]">
              <Label className="text-xs text-muted-foreground">Event Type</Label>
              <Select
                value={eventTypeFilter}
                onValueChange={(v) => {
                  setEventTypeFilter(v as EventType | 'ALL');
                  setPage(1);
                }}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {EVENT_TYPE_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      <span className="flex items-center gap-2">
                        {opt.icon}
                        {opt.label}
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Session ID */}
            <div className="w-[200px]">
              <Label className="text-xs text-muted-foreground">Session ID</Label>
              <Input
                className="mt-1"
                placeholder="Session ID..."
                value={sessionIdSearch}
                onChange={(e) => {
                  setSessionIdSearch(e.target.value);
                  setPage(1);
                }}
              />
            </div>

            {/* Time Range */}
            <div className="w-[180px]">
              <Label className="text-xs text-muted-foreground">Start Time</Label>
              <Input
                type="datetime-local"
                className="mt-1"
                value={startTime}
                onChange={(e) => {
                  setStartTime(e.target.value);
                  setPage(1);
                }}
              />
            </div>
            <div className="w-[180px]">
              <Label className="text-xs text-muted-foreground">End Time</Label>
              <Input
                type="datetime-local"
                className="mt-1"
                value={endTime}
                onChange={(e) => {
                  setEndTime(e.target.value);
                  setPage(1);
                }}
              />
            </div>

            {/* Clear Filters */}
            <Button variant="ghost" onClick={handleClearFilters}>
              Clear Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : logs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <FileText className="h-12 w-12 text-muted-foreground/50" />
              <p className="mt-4 text-lg font-medium text-muted-foreground">
                No events found
              </p>
              <p className="text-sm text-muted-foreground">
                Try adjusting your filters or generate some events
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 border-b">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">Timestamp</th>
                    <th className="px-4 py-3 text-left font-medium">Event ID</th>
                    <th className="px-4 py-3 text-left font-medium">Type</th>
                    <th className="px-4 py-3 text-left font-medium">User ID</th>
                    <th className="px-4 py-3 text-left font-medium">Page URL</th>
                    <th className="px-4 py-3 text-left font-medium">Session</th>
                    <th className="px-4 py-3 text-left font-medium">IP Address</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((event) => (
                    <tr
                      key={event.eventId}
                      className="border-b hover:bg-muted/30 cursor-pointer"
                      onClick={() => router.push(`/logs/${event.eventId}`)}
                    >
                      <td className="px-4 py-3 whitespace-nowrap font-mono text-xs">
                        {format(new Date(event.timestamp), 'yyyy-MM-dd HH:mm:ss.SSS')}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                        {event.eventId.slice(0, 8)}...
                      </td>
                      <td className="px-4 py-3">
                        <Badge className={EVENT_TYPE_COLORS[event.eventType]}>
                          {event.eventType}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs">{event.userId}</td>
                      <td className="px-4 py-3 max-w-[200px] truncate text-xs">
                        {event.pageUrl || '-'}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                        {event.sessionId ? `${event.sessionId.slice(0, 8)}...` : '-'}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs">
                        {event.ipAddress || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t">
              <p className="text-sm text-muted-foreground">
                Showing {(page - 1) * pageSize + 1} -{' '}
                {Math.min(page * pageSize, totalItems)} of {totalItems}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Previous
                </Button>
                <span className="text-sm">
                  Page {page} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
