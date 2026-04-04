'use client';

import * as React from 'react';
import { useState } from 'react';
import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
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
import { AuditCard } from '@/components/audit';
import { useAuditTodo, useReviewAuditOrder } from '@/lib/hooks/use-audit';
import { useToast } from '@/components/ui/use-toast';
import type { AuditLevel } from '@/types/audit';
import { ClipboardCheck, Search, ChevronLeft, ChevronRight, RefreshCw, Inbox } from 'lucide-react';

const levelOptions: { value: AuditLevel | 'ALL'; label: string }[] = [
  { value: 'ALL', label: 'All Levels' },
  { value: 'HIGH', label: 'High' },
  { value: 'MEDIUM', label: 'Medium' },
  { value: 'LOW', label: 'Low' },
];

const sortOptions = [
  { value: 'createTime-desc', label: 'Newest First' },
  { value: 'createTime-asc', label: 'Oldest First' },
  { value: 'level-desc', label: 'High Priority First' },
  { value: 'level-asc', label: 'Low Priority First' },
];

export default function MyTodoPage() {
  const { toast } = useToast();

  // Filter states
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [levelFilter, setLevelFilter] = useState<AuditLevel | 'ALL'>('ALL');
  const [sort, setSort] = useState('createTime-desc');

  // Queries
  const { data: todoData, isLoading, refetch } = useAuditTodo({ page, size: pageSize });
  const reviewMutation = useReviewAuditOrder();

  // Filter and sort locally since the API might not support all filters
  const filteredOrders = React.useMemo(() => {
    if (!todoData?.list) return [];
    let orders = [...todoData.list];

    // Filter by level
    if (levelFilter !== 'ALL') {
      orders = orders.filter((o) => o.auditLevel === levelFilter);
    }

    // Sort
    const [sortKey, sortOrder] = sort.split('-');
    orders.sort((a, b) => {
      if (sortKey === 'createTime') {
        const dateA = new Date(a.createTime).getTime();
        const dateB = new Date(b.createTime).getTime();
        return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
      }
      if (sortKey === 'level') {
        const levelOrder = { HIGH: 3, MEDIUM: 2, LOW: 1 };
        const levelA = levelOrder[a.auditLevel];
        const levelB = levelOrder[b.auditLevel];
        return sortOrder === 'desc' ? levelB - levelA : levelA - levelB;
      }
      return 0;
    });

    return orders;
  }, [todoData?.list, levelFilter, sort]);

  const totalItems = todoData?.total || 0;
  const totalPages = Math.ceil(totalItems / pageSize);

  // Handlers
  const handleQuickApprove = async (orderId: string) => {
    try {
      await reviewMutation.mutateAsync({
        id: orderId,
        data: { status: 'APPROVED' },
      });
      toast({
        title: 'Approved',
        description: 'Audit order has been approved',
        variant: 'success',
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to approve audit order',
        variant: 'destructive',
      });
    }
  };

  const handleQuickReject = async (orderId: string) => {
    try {
      await reviewMutation.mutateAsync({
        id: orderId,
        data: { status: 'REJECTED' },
      });
      toast({
        title: 'Rejected',
        description: 'Audit order has been rejected',
        variant: 'destructive',
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to reject audit order',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">My Todo</h1>
          <p className="text-muted-foreground">
            {totalItems} pending review{totalItems !== 1 ? 's' : ''} assigned to you
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Link href="/audit">
            <Button variant="outline">
              View All Audits
            </Button>
          </Link>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-end gap-4">
            {/* Level Filter */}
            <div className="w-[150px]">
              <Label className="text-xs text-muted-foreground">Level</Label>
              <Select
                value={levelFilter}
                onValueChange={(v) => setLevelFilter(v as AuditLevel | 'ALL')}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {levelOptions.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Sort */}
            <div className="w-[180px]">
              <Label className="text-xs text-muted-foreground">Sort By</Label>
              <Select value={sort} onValueChange={setSort}>
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {sortOptions.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : filteredOrders.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Inbox className="h-12 w-12 text-muted-foreground/50" />
            <p className="mt-4 text-lg font-medium text-muted-foreground">No pending reviews</p>
            <p className="text-sm text-muted-foreground">
              You&apos;re all caught up! Check back later for new audit orders.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Cards */}
          <div className="space-y-4">
            {filteredOrders.map((order) => (
              <AuditCard
                key={order.orderId}
                orderId={order.orderId}
                userId={order.userId}
                level={order.auditLevel}
                ruleName={order.ruleName || `Rule ${order.ruleId}`}
                triggerSummary={JSON.stringify(order.triggerData).slice(0, 100)}
                createdAt={order.createTime}
                status={order.status}
                onQuickApprove={() => handleQuickApprove(order.orderId)}
                onQuickReject={() => handleQuickReject(order.orderId)}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Showing {(page - 1) * pageSize + 1} - {Math.min(page * pageSize, totalItems)} of{' '}
                {totalItems} items
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  <ChevronLeft className="h-4 w-4" />
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
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
