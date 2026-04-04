'use client';

import * as React from 'react';
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { useGenerateEvents } from '@/lib/hooks/use-mock';
import type { EventType } from '@/types/event';
import { Sparkles, Zap } from 'lucide-react';

const EVENT_TYPES: { id: EventType; label: string }[] = [
  { id: 'VIEW', label: 'VIEW' },
  { id: 'CLICK', label: 'CLICK' },
  { id: 'SEARCH', label: 'SEARCH' },
  { id: 'PURCHASE', label: 'PURCHASE' },
  { id: 'COMMENT', label: 'COMMENT' },
  { id: 'LOGIN', label: 'LOGIN' },
  { id: 'LOGOUT', label: 'LOGOUT' },
];

const TIME_RANGE_OPTIONS = [
  { value: '1h', label: '1 Hour' },
  { value: '6h', label: '6 Hours' },
  { value: '24h', label: '24 Hours' },
];

interface ManualGenerateFormProps {
  onGenerateSuccess?: (count: number) => void;
}

export function ManualGenerateForm({ onGenerateSuccess }: ManualGenerateFormProps) {
  const [eventCount, setEventCount] = useState(100);
  const [userCount, setUserCount] = useState(50);
  const [timeRange, setTimeRange] = useState('1h');
  const [selectedTypes, setSelectedTypes] = useState<EventType[]>(['VIEW', 'CLICK', 'LOGIN']);
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);

  const generateMutation = useGenerateEvents();

  const handleTypeToggle = (type: EventType) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const handleSelectAll = () => {
    setSelectedTypes(EVENT_TYPES.map((t) => t.id));
  };

  const handleDeselectAll = () => {
    setSelectedTypes([]);
  };

  const handleGenerate = async () => {
    if (selectedTypes.length === 0) {
      return;
    }

    setIsGenerating(true);
    setProgress(0);

    // Simulate progress updates
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return prev;
        }
        return prev + Math.random() * 15;
      });
    }, 200);

    try {
      const result = await generateMutation.mutateAsync({
        count: eventCount,
        eventTypes: selectedTypes,
        userCount,
      });

      setProgress(100);

      setTimeout(() => {
        setIsGenerating(false);
        setProgress(0);
        onGenerateSuccess?.(result.generatedCount);
      }, 500);
    } catch (error) {
      clearInterval(progressInterval);
      setIsGenerating(false);
      setProgress(0);
      console.error('Failed to generate events:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-6 md:grid-cols-2">
        {/* Configuration Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="event-count">Event Count</Label>
              <Input
                id="event-count"
                type="number"
                min={1}
                max={10000}
                value={eventCount}
                onChange={(e) => setEventCount(Math.min(10000, Math.max(1, parseInt(e.target.value) || 1)))}
                disabled={isGenerating}
              />
              <p className="text-xs text-muted-foreground">Max: 10,000 events</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="user-count">User Count</Label>
              <Input
                id="user-count"
                type="number"
                min={1}
                value={userCount}
                onChange={(e) => setUserCount(Math.max(1, parseInt(e.target.value) || 1))}
                disabled={isGenerating}
              />
            </div>

            <div className="space-y-2">
              <Label>Time Range</Label>
              <Select value={timeRange} onValueChange={setTimeRange} disabled={isGenerating}>
                <SelectTrigger>
                  <SelectValue placeholder="Select time range" />
                </SelectTrigger>
                <SelectContent>
                  {TIME_RANGE_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Event Types Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Event Types</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleSelectAll}
                disabled={isGenerating}
              >
                Select All
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleDeselectAll}
                disabled={isGenerating}
              >
                Deselect All
              </Button>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {EVENT_TYPES.map((type) => (
                <div key={type.id} className="flex items-center space-x-2">
                  <Checkbox
                    id={`type-${type.id}`}
                    checked={selectedTypes.includes(type.id)}
                    onCheckedChange={() => handleTypeToggle(type.id)}
                    disabled={isGenerating}
                  />
                  <Label
                    htmlFor={`type-${type.id}`}
                    className="text-sm font-normal cursor-pointer"
                  >
                    {type.label}
                  </Label>
                </div>
              ))}
            </div>

            {selectedTypes.length === 0 && (
              <p className="text-sm text-destructive">Please select at least one event type</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Generate Button and Progress */}
      <div className="space-y-4">
        <Button
          onClick={handleGenerate}
          disabled={isGenerating || selectedTypes.length === 0}
          className="w-full md:w-auto"
          size="lg"
        >
          {isGenerating ? (
            <>
              <Zap className="mr-2 h-4 w-4 animate-pulse" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-4 w-4" />
              Generate Events
            </>
          )}
        </Button>

        {isGenerating && (
          <div className="space-y-2">
            <Progress value={progress} className="h-2" />
            <p className="text-sm text-muted-foreground text-center">
              Generating events... {Math.round(progress)}%
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
