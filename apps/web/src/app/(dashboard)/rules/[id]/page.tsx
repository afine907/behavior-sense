'use client';

import { useSearchParams } from 'next/navigation';
import { RuleForm } from '@/components/rules';

interface EditRulePageProps {
  params: {
    id: string;
  };
}

export default function EditRulePage({ params }: EditRulePageProps) {
  const searchParams = useSearchParams();
  const isDuplicate = searchParams.get('duplicate') === params.id;

  return (
    <div className="max-w-4xl mx-auto">
      <RuleForm
        ruleId={isDuplicate ? undefined : params.id}
        duplicateFrom={isDuplicate ? params.id : undefined}
      />
    </div>
  );
}
