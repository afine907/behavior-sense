'use client';

import * as React from 'react';
import { use } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AuditDetail } from '@/components/audit';
import { useAuditOrder, useReviewAuditOrder } from '@/lib/hooks/use-audit';
import { useToast } from '@/components/ui/use-toast';
import { ArrowLeft, RefreshCw, AlertCircle } from 'lucide-react';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function AuditOrderDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();

  // Queries
  const { data: orderData, isLoading, error, refetch } = useAuditOrder(id);
  const reviewMutation = useReviewAuditOrder();

  // Mock events for demonstration (in real app, these would come from the API)
  const events = React.useMemo(() => {
    if (!orderData?.events) {
      // Generate mock events based on triggerData
      const triggerData = orderData?.triggerData || {};
      const mockEvents = [];

      // Add events based on trigger data
      if (triggerData.loginFailCount) {
        for (let i = 0; i < (triggerData.loginFailCount as number); i++) {
          mockEvents.push({
            time: new Date(Date.now() - i * 60000 * 5).toISOString(),
            eventType: 'LOGIN_FAIL',
            description: `Failed login attempt from IP: ${triggerData.ipAddress || '192.168.1.' + (100 + i)}`,
            metadata: {
              ip: triggerData.ipAddress || `192.168.1.${100 + i}`,
              attempt: i + 1,
            },
          });
        }
      }

      if (triggerData.purchaseAmount) {
        mockEvents.push({
          time: new Date(Date.now() - 3600000).toISOString(),
          eventType: 'PURCHASE',
          description: `Purchase of ${triggerData.purchaseAmount}`,
          metadata: {
            amount: triggerData.purchaseAmount,
            productId: triggerData.productId,
          },
        });
      }

      // Add a generic event if no specific events
      if (mockEvents.length === 0) {
        mockEvents.push({
          time: orderData?.createTime || new Date().toISOString(),
          eventType: 'RULE_TRIGGER',
          description: 'Rule condition matched',
          metadata: triggerData,
        });
      }

      return mockEvents;
    }
    return orderData.events;
  }, [orderData]);

  // Handlers
  const handleReview = async (data: { status: 'APPROVED' | 'REJECTED'; reviewerNote?: string }) => {
    try {
      await reviewMutation.mutateAsync({
        id,
        data,
      });
      toast({
        title: 'Review Submitted',
        description: `Audit order has been ${data.status.toLowerCase()}`,
        variant: data.status === 'APPROVED' ? 'success' : 'destructive',
      });
      // Navigate back to the list after successful review
      setTimeout(() => {
        router.push('/audit');
      }, 1500);
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to submit review',
        variant: 'destructive',
      });
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href="/audit">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Audit List
            </Button>
          </Link>
        </div>
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  // Error state
  if (error || !orderData) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link href="/audit">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Audit List
            </Button>
          </Link>
        </div>
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="h-12 w-12 text-destructive" />
            <p className="mt-4 text-lg font-medium text-destructive">Failed to load audit order</p>
            <p className="text-sm text-muted-foreground">
              The audit order may not exist or you may not have permission to view it.
            </p>
            <Button variant="outline" className="mt-4" onClick={() => refetch()}>
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back Navigation */}
      <div className="flex items-center justify-between">
        <Link href="/audit">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Audit List
          </Button>
        </Link>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Audit Detail */}
      <AuditDetail
        order={orderData}
        events={events}
        onReview={handleReview}
        isReviewing={reviewMutation.isPending}
      />
    </div>
  );
}
