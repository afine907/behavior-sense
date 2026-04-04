'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { TagBadge } from './tag-badge';
import { RiskScore, type RiskFactor } from './risk-score';
import { EditTagsDialog } from './edit-tags-dialog';
import { useUserTags, useUserProfile } from '@/lib/hooks/use-insight';
import { formatDate, formatDateShort, formatRelative } from '@/lib/utils/date';
import { cn } from '@/lib/utils/cn';
import {
  User,
  Calendar,
  MapPin,
  Clock,
  Eye,
  MousePointerClick,
  Search,
  ShoppingCart,
  DollarSign,
  Edit3,
  ArrowRight,
  RefreshCw,
  Loader2,
} from 'lucide-react';
import type { UserTag } from '@/types/user';

export interface UserProfileProps {
  userId: string;
  className?: string;
}

interface StatItemProps {
  icon: typeof Eye;
  label: string;
  value: string | number;
  className?: string;
}

function StatItem({ icon: Icon, label, value, className }: StatItemProps) {
  return (
    <div className={cn('flex items-center gap-3 rounded-lg bg-muted/50 p-3', className)}>
      <div className="rounded-md bg-background p-2">
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-lg font-semibold">{value}</p>
      </div>
    </div>
  );
}

export function UserProfile({ userId, className }: UserProfileProps) {
  const [editTagsOpen, setEditTagsOpen] = useState(false);

  const {
    data: tagsData,
    isLoading: tagsLoading,
    error: tagsError,
    refetch: refetchTags,
  } = useUserTags(userId);

  const {
    data: profileData,
    isLoading: profileLoading,
    error: profileError,
    refetch: refetchProfile,
  } = useUserProfile(userId);

  const isLoading = tagsLoading || profileLoading;
  const error = tagsError || profileError;

  // Convert tags to array for display
  const tagEntries = tagsData?.tags
    ? Object.entries(tagsData.tags).map(([name, tag]) => ({
        name,
        value: tag.value,
        updateTime: tag.updateTime,
        source: tag.source,
      }))
    : [];

  // Mock statistics (would come from API in real implementation)
  const statistics = {
    views: 1234,
    clicks: 567,
    searches: 89,
    purchases: 15,
    amount: '¥2,340',
  };

  // Risk factors from risk profile
  const riskFactors: RiskFactor[] = profileData?.riskProfile
    ? [
        {
          name: 'Login Anomalies',
          count: (profileData.riskProfile.loginAnomalyCount as number) || 0,
        },
        {
          name: 'Payment Anomalies',
          count: (profileData.riskProfile.paymentAnomalyCount as number) || 0,
        },
        {
          name: 'Behavior Anomalies',
          count: (profileData.riskProfile.behaviorAnomalyCount as number) || 0,
        },
      ]
    : [];

  const riskScore = (profileData?.riskProfile?.riskScore as number) || 0;

  const handleRefresh = () => {
    refetchTags();
    refetchProfile();
  };

  if (isLoading) {
    return (
      <div className={cn('space-y-6', className)}>
        <div className="flex h-[400px] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn('space-y-6', className)}>
        <Card>
          <CardContent className="flex h-[400px] flex-col items-center justify-center gap-4">
            <p className="text-destructive">Failed to load user profile</p>
            <Button variant="outline" onClick={handleRefresh}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header with Edit Button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">
            User Profile: {userId}
          </h2>
          {tagsData?.lastUpdateTime && (
            <p className="text-sm text-muted-foreground">
              Last updated: {formatRelative(tagsData.lastUpdateTime)}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button onClick={() => setEditTagsOpen(true)}>
            <Edit3 className="mr-2 h-4 w-4" />
            Edit Tags
          </Button>
        </div>
      </div>

      {/* Basic Info Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Basic Info
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">User ID</p>
                <p className="font-medium">{userId}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Registered</p>
                <p className="font-medium">
                  {profileData?.basicInfo?.registerTime
                    ? formatDateShort(profileData.basicInfo.registerTime)
                    : '-'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Region</p>
                <p className="font-medium">
                  {profileData?.basicInfo?.region || '-'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Last Active</p>
                <p className="font-medium">
                  {profileData?.basicInfo?.lastActiveTime
                    ? formatRelative(profileData.basicInfo.lastActiveTime)
                    : '-'}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Behavior Tags Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <TagBadge name="" value="Tags" className="bg-transparent p-0 text-inherit" />
              Behavior Tags
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={() => setEditTagsOpen(true)}>
              View all {tagEntries.length} tags
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
          <CardDescription>Tags assigned based on user behavior</CardDescription>
        </CardHeader>
        <CardContent>
          {tagEntries.length === 0 ? (
            <p className="text-sm text-muted-foreground">No tags assigned</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {tagEntries.slice(0, 8).map(({ name, value, updateTime, source }) => (
                <TagBadge
                  key={name}
                  name={name}
                  value={value}
                  updateTime={updateTime}
                  source={source}
                />
              ))}
              {tagEntries.length > 8 && (
                <span className="flex items-center text-sm text-muted-foreground">
                  +{tagEntries.length - 8} more
                </span>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Statistics and Risk Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Statistics Card */}
        <Card>
          <CardHeader>
            <CardTitle>Statistics (Last 30 Days)</CardTitle>
            <CardDescription>User activity metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              <StatItem icon={Eye} label="Views" value={statistics.views.toLocaleString()} />
              <StatItem icon={MousePointerClick} label="Clicks" value={statistics.clicks.toLocaleString()} />
              <StatItem icon={Search} label="Searches" value={statistics.searches.toLocaleString()} />
              <StatItem icon={ShoppingCart} label="Purchases" value={statistics.purchases} />
              <StatItem icon={DollarSign} label="Amount" value={statistics.amount} />
            </div>
          </CardContent>
        </Card>

        {/* Risk Profile Card */}
        <Card>
          <CardHeader>
            <CardTitle>Risk Profile</CardTitle>
            <CardDescription>Risk assessment based on behavior patterns</CardDescription>
          </CardHeader>
          <CardContent>
            <RiskScore score={riskScore} factors={riskFactors} />
          </CardContent>
        </Card>
      </div>

      {/* Edit Tags Dialog */}
      <EditTagsDialog
        open={editTagsOpen}
        onOpenChange={setEditTagsOpen}
        userId={userId}
        tags={tagsData?.tags || {}}
        onSuccess={() => {
          refetchTags();
        }}
      />
    </div>
  );
}
