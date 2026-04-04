'use client';

import { useState, useMemo, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useMutation } from '@tanstack/react-query';
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
import { Separator } from '@/components/ui/separator';
import { AuditCard } from '@/components/audit';
import { useAuditOrders, useAuditStats, useReviewAuditOrder } from '@/lib/hooks/use-audit';
import { useToast } from '@/components/ui/use-toast';
import type { AuditStatus, AuditLevel } from '@/types/audit';
import { ClipboardCheck, Search, ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react';

const statusOptions: { value: AuditStatus | 'ALL'; label: string }[] = [
  { value: 'ALL', label: 'All Status' },
  { value: 'PENDING', label: 'Pending' },
  { value: 'IN_REVIEW', label: 'In Review' },
  { value: 'APPROVED', label: 'Approved' },
  { value: 'REJECTED', label: 'Rejected' },
];

const levelOptions: { value: AuditLevel | 'ALL'; label: string }[] = [
  { value: 'ALL', label: 'All Levels' },
  { value: 'HIGH', label: 'High' },
  { value: 'MEDIUM', label: 'Medium' },
  { value: 'LOW', label: 'Low' },
];

const sortOptions = [
  { value: 'createTime-desc', label: 'Newest First' },
  { value: 'createTime-asc', label: 'Oldest First' },
  { value: 'updateTime-desc', label: 'Recently Updated' },
];

export default function AuditListPage() {
  const router = useRouter();
  const { toast } = useToast();

  // Filter states
  const [page, setPage] = useState(1);
  const [pageSize] = useState(12);
  const [statusFilter, setStatusFilter] = useState<AuditStatus | 'ALL'>('ALL');
  const [levelFilter, setLevelFilter] = useState<AuditLevel | 'ALL'>('ALL');
  const [userIdSearch, setUserIdSearch] = useState('');
  const [sort, setSort] = useState('createTime-desc');
  const [searchInput, setSearchInput] = useState('');

  // Build query params
  const params = useMemo(() => {
    const [sortBy, sortOrder] = sort.split('-') as ['createTime' | 'updateTime', 'asc' | 'desc'];
    return {
      page,
      size: pageSize,
      ...(statusFilter !== 'ALL' && { status: statusFilter }),
      ...(levelFilter !== 'ALL' && { level: levelFilter }),
      ...(userIdSearch && { userId: userIdSearch }),
      sortBy,
      sortOrder,
    };
  }, [page, pageSize, statusFilter, levelFilter, userIdSearch, sort]);

  // Queries
  const { data: ordersData, isLoading: isLoadingOrders, refetch } = useAuditOrders(params);
  const { data: statsData, isLoading: isLoadingStats } = useAuditStats();

  // Mutations
  const reviewMutation = useReviewAuditOrder();

  // Handlers
  const handleSearch = () => {
    setUserIdSearch(searchInput);
    setPage(1);
  };

  const handleQuickApprove = useCallback(async (orderId: string) => {
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
  }, [reviewMutation, toast]);

  const handleQuickReject = useCallback(async (orderId: string) => {
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
  }, [reviewMutation, toast]);

  const orders = ordersData?.list || [];
  const totalItems = ordersData?.total || 0;
  const totalPages = Math.ceil(totalItems / pageSize);
  const stats = statsData || { total: 0, pending: 0, inReview: 0, approved: 0, rejected: 0 };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Audit Workbench</h1>
          <p className="text-muted-foreground">Review and manage audit orders</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Link href="/audit/todo">
            <Button>
              <ClipboardCheck className="mr-2 h-4 w-4" />
              My Todo ({stats.pending})
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-yellow-600">Pending</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="text-2xl font-bold">{stats.pending}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-blue-600">In Review</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="text-2xl font-bold">{stats.inReview}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-green-600">Approved</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="text-2xl font-bold">{stats.approved}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-red-600">Rejected</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="text-2xl font-bold">{stats.rejected}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-end gap-4">
            {/* Search */}
            <div className="flex-1 min-w-[200px]">
              <Label htmlFor="search" className="text-xs text-muted-foreground">
                Search by User ID
              </Label>
              <div className="flex gap-2 mt-1">
                <Input
                  id="search"
                  placeholder="Enter user ID..."
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                />
                <Button onClick={handleSearch}>
                  <Search className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Status Filter */}
            <div className="w-[150px]">
              <Label className="text-xs text-muted-foreground">Status</Label>
              <Select
                value={statusFilter}
                onValueChange={(v) => {
                  setStatusFilter(v as AuditStatus | 'ALL');
                  setPage(1);
                }}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {statusOptions.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Level Filter */}
            <div className="w-[150px]">
              <Label className="text-xs text-muted-foreground">Level</Label>
              <Select
                value={levelFilter}
                onValueChange={(v) => {
                  setLevelFilter(v as AuditLevel | 'ALL');
                  setPage(1);
                }}
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
      {isLoadingOrders ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : orders.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <ClipboardCheck className="h-12 w-12 text-muted-foreground/50" />
            <p className="mt-4 text-lg font-medium text-muted-foreground">No audit orders found</p>
            <p className="text-sm text-muted-foreground">
              Try adjusting your filters or create a new audit order
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Cards Grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {orders.map((order) => (
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
                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum: number;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (page <= 3) {
                      pageNum = i + 1;
                    } else if (page >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = page - 2 + i;
                    }
                    return (
                      <Button
                        key={pageNum}
                        variant={page === pageNum ? 'default' : 'outline'}
                        size="sm"
                        className="w-9"
                        onClick={() => setPage(pageNum)}
                      >
                        {pageNum}
                      </Button>
                    );
                  })}
                </div>
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
