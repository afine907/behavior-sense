'use client';

import { X } from 'lucide-react';
import { cn } from '@/lib/utils/cn';
import { formatRelative } from '@/lib/utils/date';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from '@/components/ui/tooltip';
import { Button } from '@/components/ui/button';

export interface TagBadgeProps {
  name: string;
  value: string;
  updateTime?: string;
  source?: 'auto' | 'manual';
  editable?: boolean;
  onRemove?: () => void;
  className?: string;
}

// Tag color mapping based on tag name
const tagColorMap: Record<string, { bg: string; text: string; border: string }> = {
  // User level tags
  level: {
    bg: 'bg-purple-100 dark:bg-purple-900/30',
    text: 'text-purple-700 dark:text-purple-300',
    border: 'border-purple-200 dark:border-purple-800',
  },
  // Activity tags
  activity: {
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    text: 'text-blue-700 dark:text-blue-300',
    border: 'border-blue-200 dark:border-blue-800',
  },
  // Risk tags
  risk: {
    bg: 'bg-red-100 dark:bg-red-900/30',
    text: 'text-red-700 dark:text-red-300',
    border: 'border-red-200 dark:border-red-800',
  },
  // Segment tags
  segment: {
    bg: 'bg-green-100 dark:bg-green-900/30',
    text: 'text-green-700 dark:text-green-300',
    border: 'border-green-200 dark:border-green-800',
  },
  // Preference tags
  preference: {
    bg: 'bg-orange-100 dark:bg-orange-900/30',
    text: 'text-orange-700 dark:text-orange-300',
    border: 'border-orange-200 dark:border-orange-800',
  },
  // Default
  default: {
    bg: 'bg-gray-100 dark:bg-gray-800',
    text: 'text-gray-700 dark:text-gray-300',
    border: 'border-gray-200 dark:border-gray-700',
  },
};

// Value-based color overrides for specific values
const valueColorOverride: Record<string, { bg: string; text: string; border: string }> = {
  VIP: {
    bg: 'bg-amber-100 dark:bg-amber-900/30',
    text: 'text-amber-700 dark:text-amber-300',
    border: 'border-amber-200 dark:border-amber-800',
  },
  HIGH: {
    bg: 'bg-red-100 dark:bg-red-900/30',
    text: 'text-red-700 dark:text-red-300',
    border: 'border-red-200 dark:border-red-800',
  },
  MEDIUM: {
    bg: 'bg-yellow-100 dark:bg-yellow-900/30',
    text: 'text-yellow-700 dark:text-yellow-300',
    border: 'border-yellow-200 dark:border-yellow-800',
  },
  LOW: {
    bg: 'bg-green-100 dark:bg-green-900/30',
    text: 'text-green-700 dark:text-green-300',
    border: 'border-green-200 dark:border-green-800',
  },
  NEW: {
    bg: 'bg-cyan-100 dark:bg-cyan-900/30',
    text: 'text-cyan-700 dark:text-cyan-300',
    border: 'border-cyan-200 dark:border-cyan-800',
  },
};

function getTagColors(name: string, value: string) {
  // Check for value-based override first
  if (valueColorOverride[value]) {
    return valueColorOverride[value];
  }
  // Then check for name-based mapping
  const lowerName = name.toLowerCase();
  for (const [key, colors] of Object.entries(tagColorMap)) {
    if (lowerName.includes(key)) {
      return colors;
    }
  }
  return tagColorMap.default;
}

export function TagBadge({
  name,
  value,
  updateTime,
  source = 'auto',
  editable = false,
  onRemove,
  className,
}: TagBadgeProps) {
  const colors = getTagColors(name, value);

  const badgeContent = (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-sm font-medium transition-colors',
        colors.bg,
        colors.text,
        source === 'manual' ? 'border border-dashed' : `border ${colors.border}`,
        editable && 'pr-1',
        className
      )}
    >
      <span className="text-xs opacity-70">{name}:</span>
      <span>{value}</span>
      {editable && onRemove && (
        <Button
          variant="ghost"
          size="icon"
          className="h-4 w-4 p-0 opacity-60 hover:opacity-100"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
        >
          <X className="h-3 w-3" />
        </Button>
      )}
    </span>
  );

  if (updateTime) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>{badgeContent}</TooltipTrigger>
          <TooltipContent side="top">
            <div className="text-xs">
              <div>
                {source === 'manual' ? 'Manual' : 'Auto'} tag
              </div>
              <div className="text-muted-foreground">
                Updated: {formatRelative(updateTime)}
              </div>
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return badgeContent;
}
