'use client';

import * as React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { cn } from '@/lib/utils/cn';

const reviewSchema = z.object({
  decision: z.enum(['APPROVE', 'REJECT', 'ESCALATE'], {
    required_error: 'Please select a decision',
  }),
  notes: z.string().optional(),
});

type ReviewFormData = z.infer<typeof reviewSchema>;

interface ReviewFormProps {
  onSubmit: (data: { status: 'APPROVED' | 'REJECTED'; reviewerNote?: string }) => void;
  isSubmitting?: boolean;
  disabled?: boolean;
}

const decisionOptions = [
  {
    value: 'APPROVE',
    label: 'Approve',
    description: 'This is normal behavior',
    className: 'text-green-600',
  },
  {
    value: 'REJECT',
    label: 'Reject',
    description: 'Suspicious activity confirmed',
    className: 'text-red-600',
  },
  {
    value: 'ESCALATE',
    label: 'Escalate',
    description: 'Need senior review',
    className: 'text-yellow-600',
  },
] as const;

export function ReviewForm({ onSubmit, isSubmitting = false, disabled = false }: ReviewFormProps) {
  const [showConfirm, setShowConfirm] = React.useState(false);
  const [pendingData, setPendingData] = React.useState<ReviewFormData | null>(null);

  const {
    watch,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<ReviewFormData>({
    resolver: zodResolver(reviewSchema),
    defaultValues: {
      decision: undefined,
      notes: '',
    },
  });

  const selectedDecision = watch('decision');

  const handleFormSubmit = (data: ReviewFormData) => {
    setPendingData(data);
    setShowConfirm(true);
  };

  const handleConfirm = () => {
    if (pendingData) {
      // Map ESCALATE to IN_REVIEW status (or handle as needed)
      const status = pendingData.decision === 'APPROVE' ? 'APPROVED' : 'REJECTED';
      onSubmit({
        status,
        reviewerNote: pendingData.notes,
      });
    }
    setShowConfirm(false);
  };

  return (
    <>
      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
        <div className="space-y-3">
          <Label className="text-base font-semibold">Review Decision</Label>
          <RadioGroup
            value={selectedDecision}
            onValueChange={(value) => setValue('decision', value as ReviewFormData['decision'])}
            disabled={disabled || isSubmitting}
            className="space-y-3"
          >
            {decisionOptions.map((option) => (
              <div
                key={option.value}
                className={cn(
                  'flex items-start space-x-3 rounded-md border p-3 transition-colors',
                  selectedDecision === option.value
                    ? 'border-primary bg-primary/5'
                    : 'hover:bg-muted/50'
                )}
              >
                <RadioGroupItem value={option.value} id={option.value} className="mt-0.5" />
                <div className="flex-1">
                  <Label
                    htmlFor={option.value}
                    className={cn('cursor-pointer font-medium', option.className)}
                  >
                    {option.label}
                  </Label>
                  <p className="text-sm text-muted-foreground">{option.description}</p>
                </div>
              </div>
            ))}
          </RadioGroup>
          {errors.decision && (
            <p className="text-sm text-destructive">{errors.decision.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="notes">Notes (Optional)</Label>
          <Textarea
            id="notes"
            placeholder="Add review notes..."
            disabled={disabled || isSubmitting}
            onChange={(e) => setValue('notes', e.target.value)}
          />
        </div>

        <div className="flex justify-end gap-3">
          <Button
            type="submit"
            disabled={!selectedDecision || disabled || isSubmitting}
          >
            {isSubmitting ? 'Submitting...' : 'Submit Review'}
          </Button>
        </div>
      </form>

      <AlertDialog open={showConfirm} onOpenChange={setShowConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirm your decision?</AlertDialogTitle>
            <AlertDialogDescription>
              You are about to{' '}
              <span className="font-semibold">
                {pendingData?.decision === 'APPROVE'
                  ? 'APPROVE'
                  : pendingData?.decision === 'REJECT'
                    ? 'REJECT'
                    : 'ESCALATE'}
              </span>{' '}
              this audit order.
              {pendingData?.decision === 'REJECT' && (
                <span className="block mt-2 text-destructive">
                  This action may affect the user&apos;s account status.
                </span>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirm}>Confirm</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
