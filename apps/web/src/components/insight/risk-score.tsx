'use client';

import { cn } from '@/lib/utils/cn';
import { AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react';

export interface RiskFactor {
  name: string;
  count: number;
}

export interface RiskScoreProps {
  score: number; // 0-100
  factors?: RiskFactor[];
  className?: string;
}

type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

function getRiskLevel(score: number): RiskLevel {
  if (score <= 30) return 'LOW';
  if (score <= 70) return 'MEDIUM';
  return 'HIGH';
}

function getRiskConfig(level: RiskLevel) {
  switch (level) {
    case 'LOW':
      return {
        label: 'Low Risk',
        color: 'text-green-600 dark:text-green-400',
        bgColor: 'bg-green-100 dark:bg-green-900/30',
        progressColor: 'bg-green-500',
        icon: CheckCircle,
      };
    case 'MEDIUM':
      return {
        label: 'Medium Risk',
        color: 'text-yellow-600 dark:text-yellow-400',
        bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
        progressColor: 'bg-yellow-500',
        icon: AlertCircle,
      };
    case 'HIGH':
      return {
        label: 'High Risk',
        color: 'text-red-600 dark:text-red-400',
        bgColor: 'bg-red-100 dark:bg-red-900/30',
        progressColor: 'bg-red-500',
        icon: AlertTriangle,
      };
  }
}

export function RiskScore({ score, factors = [], className }: RiskScoreProps) {
  const level = getRiskLevel(score);
  const config = getRiskConfig(level);
  const Icon = config.icon;

  // Calculate gradient stops for the progress bar
  const getGradientStyle = () => {
    if (score <= 30) {
      // Green zone
      return { backgroundColor: '#22c55e' };
    } else if (score <= 70) {
      // Yellow zone - gradient from green to yellow
      return {
        background: `linear-gradient(to right, #22c55e, #eab308)`,
      };
    } else {
      // Red zone - gradient from yellow to red
      return {
        background: `linear-gradient(to right, #22c55e, #eab308, #ef4444)`,
      };
    }
  };

  return (
    <div className={cn('space-y-4', className)}>
      {/* Score Display */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className={cn('h-5 w-5', config.color)} />
          <span className={cn('text-lg font-semibold', config.color)}>
            {config.label}
          </span>
        </div>
        <div className="text-2xl font-bold">
          <span className={config.color}>{score}</span>
          <span className="text-muted-foreground">/100</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="relative h-3 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            ...getGradientStyle(),
            width: `${score}%`,
          }}
        />
        {/* Score indicator arrow */}
        <div
          className="absolute top-full mt-1 -translate-x-1/2 transform"
          style={{ left: `${score}%` }}
        >
          <div
            className={cn(
              'rounded px-1.5 py-0.5 text-xs font-medium text-white',
              level === 'LOW'
                ? 'bg-green-500'
                : level === 'MEDIUM'
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
            )}
          >
            {score}
          </div>
        </div>
      </div>

      {/* Risk Zone Labels */}
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>Low (0-30)</span>
        <span>Medium (31-70)</span>
        <span>High (71-100)</span>
      </div>

      {/* Risk Factors */}
      {factors.length > 0 && (
        <div className="mt-6 space-y-2">
          <h4 className="text-sm font-medium text-muted-foreground">
            Risk Factors
          </h4>
          <div className="space-y-2">
            {factors.map((factor) => (
              <div
                key={factor.name}
                className="flex items-center justify-between rounded-md bg-muted/50 p-2"
              >
                <span className="text-sm">{factor.name}</span>
                <span
                  className={cn(
                    'text-sm font-medium',
                    factor.count > 0 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'
                  )}
                >
                  {factor.count} {factor.count === 1 ? 'time' : 'times'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
