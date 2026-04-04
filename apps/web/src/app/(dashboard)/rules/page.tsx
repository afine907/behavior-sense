'use client';

import { ScrollText } from 'lucide-react';
import { RuleList } from '@/components/rules';

export default function RulesPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center gap-3">
        <ScrollText className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Rules</h1>
          <p className="text-muted-foreground">
            Create and manage behavior detection rules
          </p>
        </div>
      </div>

      {/* Rules List */}
      <RuleList />
    </div>
  );
}
