'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft, Save, Loader2 } from 'lucide-react';
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Switch,
} from '@/components/ui';
import { useToast } from '@/components/ui/use-toast';
import { ConditionBuilder } from './condition-builder';
import { ActionEditor } from './action-editor';
import { RuleTestPanel } from './rule-test-panel';
import { useRule, useCreateRule, useUpdateRule } from '@/lib/hooks/use-rules';
import type { Rule, RuleAction } from '@/types/rule';

const ruleFormSchema = z.object({
  name: z.string().min(1, 'Rule name is required').max(100, 'Name too long'),
  description: z.string().max(500, 'Description too long').optional(),
  priority: z.number().min(1).max(10),
  enabled: z.boolean(),
  condition: z.string().min(1, 'Condition is required'),
  actions: z.array(
    z.object({
      type: z.enum(['TAG_USER', 'TRIGGER_AUDIT']),
      params: z.record(z.unknown()),
    })
  ).min(1, 'At least one action is required'),
});

type RuleFormData = z.infer<typeof ruleFormSchema>;

interface RuleFormProps {
  ruleId?: string;
  duplicateFrom?: string;
}

export function RuleForm({ ruleId, duplicateFrom }: RuleFormProps) {
  const router = useRouter();
  const { toast } = useToast();

  const isNewRule = !ruleId;
  const effectiveRuleId = ruleId || duplicateFrom;

  // Fetch existing rule if editing or duplicating
  const { data: existingRule, isLoading: isLoadingRule } = useRule(effectiveRuleId || '');

  const createRule = useCreateRule();
  const updateRule = useUpdateRule();

  // Form setup
  const {
    register,
    handleSubmit,
    control,
    reset,
    watch,
    formState: { errors, isDirty },
  } = useForm<RuleFormData>({
    resolver: zodResolver(ruleFormSchema),
    defaultValues: {
      name: '',
      description: '',
      priority: 5,
      enabled: true,
      condition: '',
      actions: [],
    },
  });

  const currentCondition = watch('condition');

  // Load existing rule data
  useEffect(() => {
    if (existingRule) {
      reset({
        name: duplicateFrom ? `${existingRule.name} (Copy)` : existingRule.name,
        description: existingRule.description || '',
        priority: existingRule.priority,
        enabled: duplicateFrom ? false : existingRule.enabled, // Duplicates start disabled
        condition: existingRule.condition,
        actions: existingRule.actions || [],
      });
    }
  }, [existingRule, reset, duplicateFrom]);

  const onSubmit = async (data: RuleFormData) => {
    try {
      if (isNewRule || duplicateFrom) {
        // Create new rule
        const result = await createRule.mutateAsync(data);
        toast({
          title: 'Rule created',
          description: `Rule "${data.name}" has been created successfully.`,
          variant: 'success',
        });
        router.push(`/rules/${result.ruleId}`);
      } else if (ruleId) {
        // Update existing rule
        await updateRule.mutateAsync({ id: ruleId, data });
        toast({
          title: 'Rule updated',
          description: `Rule "${data.name}" has been updated successfully.`,
          variant: 'success',
        });
        router.push('/rules');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: isNewRule ? 'Failed to create rule. Please try again.' : 'Failed to update rule. Please try again.',
        variant: 'destructive',
      });
    }
  };

  const handleCancel = () => {
    if (isDirty) {
      const confirm = window.confirm('You have unsaved changes. Are you sure you want to leave?');
      if (!confirm) return;
    }
    router.push('/rules');
  };

  if (effectiveRuleId && isLoadingRule) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button type="button" variant="ghost" size="icon" onClick={handleCancel}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">
              {isNewRule && !duplicateFrom && 'Create New Rule'}
              {duplicateFrom && 'Duplicate Rule'}
              {ruleId && !duplicateFrom && 'Edit Rule'}
            </h1>
            {existingRule && (
              <p className="text-sm text-muted-foreground">{existingRule.name}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button type="button" variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={createRule.isPending || updateRule.isPending}
          >
            {(createRule.isPending || updateRule.isPending) ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                {isNewRule || duplicateFrom ? 'Create Rule' : 'Save Changes'}
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Basic Info */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Basic Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="name">Rule Name *</Label>
              <Input
                id="name"
                placeholder="e.g., High Risk User Detection"
                {...register('name')}
                className={errors.name ? 'border-destructive' : ''}
              />
              {errors.name && (
                <p className="text-sm text-destructive">{errors.name.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="priority">Priority (1-10)</Label>
              <Input
                id="priority"
                type="number"
                min={1}
                max={10}
                {...register('priority', { valueAsNumber: true })}
                className={errors.priority ? 'border-destructive' : ''}
              />
              {errors.priority && (
                <p className="text-sm text-destructive">{errors.priority.message}</p>
              )}
              <p className="text-xs text-muted-foreground">
                1 = Highest priority, 10 = Lowest priority
              </p>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              placeholder="Brief description of what this rule does..."
              {...register('description')}
              className={errors.description ? 'border-destructive' : ''}
            />
            {errors.description && (
              <p className="text-sm text-destructive">{errors.description.message}</p>
            )}
          </div>

          <div className="flex items-center gap-3">
            <Controller
              name="enabled"
              control={control}
              render={({ field }) => (
                <Switch
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
              )}
            />
            <div>
              <Label className="cursor-pointer">Enabled</Label>
              <p className="text-xs text-muted-foreground">
                Disabled rules will not be evaluated
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Condition Builder */}
      <ConditionBuilder
        value={currentCondition}
        onChange={(value) => reset((prev) => ({ ...prev, condition: value }))}
        error={errors.condition?.message}
      />

      {/* Actions Editor */}
      <Controller
        name="actions"
        control={control}
        render={({ field }) => (
          <>
            <ActionEditor
              actions={field.value}
              onChange={field.onChange}
            />
            {errors.actions && (
              <p className="text-sm text-destructive">{errors.actions.message}</p>
            )}
          </>
        )}
      />

      {/* Test Panel (only for existing rules) */}
      {ruleId && !duplicateFrom && (
        <RuleTestPanel ruleId={ruleId} disabled={!isDirty} />
      )}
    </form>
  );
}
