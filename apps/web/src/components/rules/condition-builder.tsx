'use client';

import { HelpCircle } from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Label,
  Textarea,
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui';

interface ConditionBuilderProps {
  value: string;
  onChange: (condition: string) => void;
  error?: string;
}

const SYNTAX_HELP = `
Condition Syntax Reference:
=====================================

Simple comparisons:
  login_fail_count > 5
  purchase_amount >= 1000
  user_level == "VIP"

Time-based conditions:
  login_fail_count > 5 AND time_window == "30min"
  events_count > 100 AND time_range == "1h"

Logical operators:
  AND, OR, NOT

Comparison operators:
  == (equal), != (not equal)
  >  (greater than), >= (greater or equal)
  <  (less than),    <= (less or equal)
  contains (string contains)
  in (value in list)

Examples:
  login_fail_count > 5 AND ip_count > 3
  purchase_amount >= 1000 OR user_level == "VIP"
  event_type == "purchase" AND amount > 500
`.trim();

const EXAMPLE_CONDITIONS = [
  { label: 'High login failures', value: 'login_fail_count > 5 AND time_window == "30min"' },
  { label: 'High value purchase', value: 'purchase_amount >= 10000' },
  { label: 'Multiple IP access', value: 'ip_count > 3 AND time_window == "1h"' },
  { label: 'VIP user activity', value: 'user_level == "VIP" AND event_type == "purchase"' },
];

export function ConditionBuilder({ value, onChange, error }: ConditionBuilderProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <CardTitle className="text-base">Condition Builder</CardTitle>
          <Tooltip>
            <TooltipTrigger asChild>
              <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
            </TooltipTrigger>
            <TooltipContent side="right" className="max-w-md">
              <pre className="text-xs whitespace-pre-wrap font-mono">{SYNTAX_HELP}</pre>
            </TooltipContent>
          </Tooltip>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="condition">Condition Expression</Label>
          <Textarea
            id="condition"
            placeholder="Enter condition expression..."
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className={`font-mono text-sm min-h-[120px] ${error ? 'border-destructive' : ''}`}
          />
          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label className="text-sm text-muted-foreground">Quick Examples</Label>
          <div className="flex flex-wrap gap-2">
            {EXAMPLE_CONDITIONS.map((example) => (
              <button
                key={example.label}
                type="button"
                onClick={() => onChange(example.value)}
                className="px-2 py-1 text-xs rounded-md bg-muted hover:bg-muted/80 transition-colors"
              >
                {example.label}
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-md bg-muted/50 p-3">
          <p className="text-xs text-muted-foreground">
            <strong>Tip:</strong> Use the syntax help tooltip above for a complete reference.
            The condition is evaluated against incoming event data and user profile attributes.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
