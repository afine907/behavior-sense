'use client';

import { useState } from 'react';
import { Play, ChevronDown, ChevronUp, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Label,
  Textarea,
} from '@/components/ui';
import { useTestRule } from '@/lib/hooks/use-rules';
import type { RuleTestResult } from '@/types/rule';

interface RuleTestPanelProps {
  ruleId: string;
  disabled?: boolean;
}

const SAMPLE_TEST_DATA = {
  user_id: 'user_001',
  login_fail_count: 6,
  ip_count: 2,
  time_window: '30min',
  event_type: 'login',
  purchase_amount: 0,
  user_level: 'NORMAL',
};

export function RuleTestPanel({ ruleId, disabled }: RuleTestPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [testInput, setTestInput] = useState(JSON.stringify(SAMPLE_TEST_DATA, null, 2));
  const [testResult, setTestResult] = useState<RuleTestResult | null>(null);
  const [inputError, setInputError] = useState<string | null>(null);

  const testRule = useTestRule();

  const handleTest = async () => {
    // Validate JSON input
    try {
      const parsed = JSON.parse(testInput);
      setInputError(null);
      setTestResult(null);

      const result = await testRule.mutateAsync({
        id: ruleId,
        testData: parsed,
      });

      setTestResult(result);
    } catch (e) {
      if (e instanceof SyntaxError) {
        setInputError('Invalid JSON format');
      }
    }
  };

  const loadSampleData = () => {
    setTestInput(JSON.stringify(SAMPLE_TEST_DATA, null, 2));
    setTestResult(null);
    setInputError(null);
  };

  return (
    <Card>
      <CardHeader className="cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle className="text-base">Test Panel</CardTitle>
            {testResult && (
              <Badge variant={testResult.matched ? 'success' : 'secondary'}>
                {testResult.matched ? 'Matched' : 'Not Matched'}
              </Badge>
            )}
          </div>
          {isExpanded ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Test Data (JSON)</Label>
              <Button variant="ghost" size="sm" onClick={loadSampleData}>
                Load Sample
              </Button>
            </div>
            <Textarea
              value={testInput}
              onChange={(e) => {
                setTestInput(e.target.value);
                setInputError(null);
              }}
              placeholder='{"user_id": "user_001", ...}'
              className={`font-mono text-sm min-h-[150px] ${inputError ? 'border-destructive' : ''}`}
              disabled={disabled || testRule.isPending}
            />
            {inputError && (
              <p className="text-sm text-destructive">{inputError}</p>
            )}
          </div>

          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={loadSampleData}
              disabled={disabled || testRule.isPending}
            >
              Reset
            </Button>
            <Button
              onClick={handleTest}
              disabled={disabled || testRule.isPending}
            >
              {testRule.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Testing...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Run Test
                </>
              )}
            </Button>
          </div>

          {/* Test Result */}
          {testResult && (
            <div className="rounded-md border p-4 space-y-3">
              <div className="flex items-center gap-2">
                {testResult.matched ? (
                  <>
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span className="font-medium text-green-600">Condition Matched</span>
                  </>
                ) : (
                  <>
                    <XCircle className="h-5 w-5 text-red-500" />
                    <span className="font-medium text-red-600">Condition Not Matched</span>
                  </>
                )}
              </div>

              {testResult.details && (
                <div className="mt-2">
                  <Label className="text-sm text-muted-foreground">Details</Label>
                  <pre className="mt-1 p-2 rounded-md bg-muted text-xs overflow-auto">
                    {JSON.stringify(testResult.details as object, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
