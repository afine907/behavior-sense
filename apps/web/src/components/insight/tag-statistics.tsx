'use client';

import { useState } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { useTagStatistics } from '@/lib/hooks/use-insight';
import { cn } from '@/lib/utils/cn';
import { Download, BarChart3, PieChart as PieChartIcon } from 'lucide-react';

// Predefined tag names for selection
const AVAILABLE_TAGS = [
  { value: 'level', label: 'User Level' },
  { value: 'activity', label: 'Activity Level' },
  { value: 'risk', label: 'Risk Level' },
  { value: 'segment', label: 'User Segment' },
];

// Colors for chart
const CHART_COLORS = [
  '#6366f1', // indigo
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#f43f5e', // rose
  '#f97316', // orange
  '#eab308', // yellow
  '#22c55e', // green
  '#14b8a6', // teal
  '#06b6d4', // cyan
  '#3b82f6', // blue
];

export interface TagStatisticsProps {
  className?: string;
  defaultTagName?: string;
}

export function TagStatistics({ className, defaultTagName = 'level' }: TagStatisticsProps) {
  const [selectedTag, setSelectedTag] = useState(defaultTagName);
  const [chartType, setChartType] = useState<'pie' | 'bar'>('pie');

  const { data: statistics, isLoading, error } = useTagStatistics(selectedTag);

  // Transform distribution data for charts
  const chartData = statistics?.distribution
    ? Object.entries(statistics.distribution).map(([name, value]) => ({
        name,
        value,
      }))
    : [];

  const handleExport = () => {
    if (!statistics) return;

    const csvContent = [
      ['Tag Value', 'Count'],
      ...Object.entries(statistics.distribution).map(([key, value]) => [key, String(value)]),
      ['Total', String(statistics.total)],
    ]
      .map((row) => row.join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${selectedTag}_statistics.csv`;
    link.click();
  };

  const renderPieChart = () => (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
          outerRadius={100}
          fill="#8884d8"
          dataKey="value"
        >
          {chartData.map((_, index) => (
            <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value: number) => [value.toLocaleString(), 'Count']}
          contentStyle={{
            backgroundColor: 'hsl(var(--popover))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '8px',
          }}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );

  const renderBarChart = () => (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis dataKey="name" className="text-xs" />
        <YAxis className="text-xs" />
        <Tooltip
          formatter={(value: number) => [value.toLocaleString(), 'Count']}
          contentStyle={{
            backgroundColor: 'hsl(var(--popover))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '8px',
          }}
        />
        <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]}>
          {chartData.map((_, index) => (
            <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );

  return (
    <Card className={cn('', className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Tag Statistics</CardTitle>
            <CardDescription>Distribution of tag values across users</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {/* Tag Selector */}
            <Select value={selectedTag} onValueChange={setSelectedTag}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Select tag" />
              </SelectTrigger>
              <SelectContent>
                {AVAILABLE_TAGS.map((tag) => (
                  <SelectItem key={tag.value} value={tag.value}>
                    {tag.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex h-[300px] items-center justify-center text-muted-foreground">
            Loading statistics...
          </div>
        ) : error ? (
          <div className="flex h-[300px] items-center justify-center text-destructive">
            Failed to load statistics
          </div>
        ) : chartData.length === 0 ? (
          <div className="flex h-[300px] items-center justify-center text-muted-foreground">
            No data available for this tag
          </div>
        ) : (
          <>
            {/* Summary Stats */}
            <div className="mb-4 flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                Total users with this tag:{' '}
                <span className="font-semibold text-foreground">
                  {statistics?.total.toLocaleString() ?? 0}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {/* Chart Type Toggle */}
                <div className="flex rounded-md border p-1">
                  <Button
                    variant={chartType === 'pie' ? 'secondary' : 'ghost'}
                    size="icon"
                    className="h-7 w-7"
                    onClick={() => setChartType('pie')}
                  >
                    <PieChartIcon className="h-4 w-4" />
                  </Button>
                  <Button
                    variant={chartType === 'bar' ? 'secondary' : 'ghost'}
                    size="icon"
                    className="h-7 w-7"
                    onClick={() => setChartType('bar')}
                  >
                    <BarChart3 className="h-4 w-4" />
                  </Button>
                </div>
                {/* Export Button */}
                <Button variant="outline" size="sm" onClick={handleExport}>
                  <Download className="mr-1 h-4 w-4" />
                  Export
                </Button>
              </div>
            </div>

            {/* Chart */}
            {chartType === 'pie' ? renderPieChart() : renderBarChart()}
          </>
        )}
      </CardContent>
    </Card>
  );
}
