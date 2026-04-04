'use client';

import { useRouter } from 'next/navigation';
import { UserSearch, TagStatistics } from '@/components/insight';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Users, TrendingUp, AlertTriangle, Star } from 'lucide-react';

// Popular/Quick access tags
const popularTags = [
  { name: 'level', value: 'VIP', count: 1234, icon: Star },
  { name: 'activity', value: 'HIGH', count: 5678, icon: TrendingUp },
  { name: 'risk', value: 'HIGH', count: 89, icon: AlertTriangle },
  { name: 'segment', value: '核心用户', count: 456, icon: Users },
];

export default function InsightPage() {
  const router = useRouter();

  const handleSearch = (userId: string) => {
    router.push(`/insight/user/${encodeURIComponent(userId)}`);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">User Insight</h1>
        <p className="text-muted-foreground">
          Search and analyze user profiles and behavior tags
        </p>
      </div>

      {/* Search Section */}
      <Card>
        <CardHeader>
          <CardTitle>Search User</CardTitle>
          <CardDescription>
            Enter a user ID to view their profile and behavior tags
          </CardDescription>
        </CardHeader>
        <CardContent>
          <UserSearch onSearch={handleSearch} />
        </CardContent>
      </Card>

      {/* Quick Access Tags */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Popular Tags
          </CardTitle>
          <CardDescription>Quick access to common tag distributions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {popularTags.map((tag) => (
              <Button
                key={`${tag.name}-${tag.value}`}
                variant="outline"
                className="h-auto justify-start p-4"
                onClick={() => {
                  // Navigate to a filtered view or show statistics
                  // For now, scroll to the statistics section
                  document
                    .getElementById('tag-statistics')
                    ?.scrollIntoView({ behavior: 'smooth' });
                }}
              >
                <div className="flex items-center gap-3">
                  <div className="rounded-md bg-primary/10 p-2">
                    <tag.icon className="h-4 w-4 text-primary" />
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-medium">
                      {tag.name}: {tag.value}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {tag.count.toLocaleString()} users
                    </p>
                  </div>
                </div>
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Tag Statistics Section */}
      <div id="tag-statistics">
        <TagStatistics />
      </div>
    </div>
  );
}
