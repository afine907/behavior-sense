'use client';

import { use } from 'react';
import { useSearchParams } from 'next/navigation';
import { RuleForm } from '@/components/rules';

interface EditRulePageProps {
  params: Promise<{ id: string }>;
}

export default function EditRulePage({ params }: EditRulePageProps) {
  const { id } = use(params);
  const searchParams = useSearchParams();
  const isDuplicate = searchParams.get('duplicate') === id;

  return (
    <div className="max-w-4xl mx-auto">
      <RuleForm
        ruleId={isDuplicate ? undefined : id}
        duplicateFrom={isDuplicate ? id : undefined}
      />
    </div>
  );
}
