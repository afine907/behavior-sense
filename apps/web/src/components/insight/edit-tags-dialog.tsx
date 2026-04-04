'use client';

import { useState, useMemo } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { TagBadge } from './tag-badge';
import { useUpdateUserTag } from '@/lib/hooks/use-insight';
import type { UserTag } from '@/types/user';
import { X, Plus, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils/cn';

// Predefined tags configuration
const PREDEFINED_TAGS: Record<string, string[]> = {
  level: ['VIP', 'NORMAL', 'NEW'],
  activity: ['HIGH', 'MEDIUM', 'LOW'],
  risk: ['HIGH', 'MEDIUM', 'LOW'],
  segment: ['核心用户', '活跃用户', '沉默用户', '流失用户'],
};

export interface EditTagsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  userId: string;
  tags: Record<string, UserTag>;
  onSuccess?: () => void;
}

export function EditTagsDialog({
  open,
  onOpenChange,
  userId,
  tags,
  onSuccess,
}: EditTagsDialogProps) {
  const [selectedTagName, setSelectedTagName] = useState<string>('');
  const [selectedTagValue, setSelectedTagValue] = useState<string>('');
  const [customTagName, setCustomTagName] = useState('');
  const [customTagValue, setCustomTagValue] = useState('');
  const [isCustomTag, setIsCustomTag] = useState(false);
  const [pendingRemovals, setPendingRemovals] = useState<Set<string>>(new Set());

  const updateTagMutation = useUpdateUserTag();

  // Available values for selected tag
  const availableValues = useMemo(() => {
    if (!selectedTagName || !PREDEFINED_TAGS[selectedTagName]) return [];
    return PREDEFINED_TAGS[selectedTagName];
  }, [selectedTagName]);

  // Convert tags to array for display
  const tagEntries = useMemo(() => {
    return Object.entries(tags).map(([name, tag]) => ({
      name,
      value: tag.value,
      updateTime: tag.updateTime,
      source: tag.source,
    }));
  }, [tags]);

  const handleAddTag = async () => {
    const tagName = isCustomTag ? customTagName.trim() : selectedTagName;
    const tagValue = isCustomTag ? customTagValue.trim() : selectedTagValue;

    if (!tagName || !tagValue) return;

    try {
      await updateTagMutation.mutateAsync({
        userId,
        data: {
          tagName,
          tagValue,
          source: 'manual',
          operator: 'admin', // TODO: Get from auth context
        },
      });

      // Reset form
      setSelectedTagName('');
      setSelectedTagValue('');
      setCustomTagName('');
      setCustomTagValue('');
      setIsCustomTag(false);

      onSuccess?.();
    } catch (error) {
      console.error('Failed to add tag:', error);
    }
  };

  const handleRemoveTag = async (tagName: string) => {
    setPendingRemovals((prev) => new Set(prev).add(tagName));

    try {
      await updateTagMutation.mutateAsync({
        userId,
        data: {
          tagName,
          tagValue: '', // Empty value removes the tag
          source: 'manual',
          operator: 'admin',
        },
      });

      onSuccess?.();
    } catch (error) {
      console.error('Failed to remove tag:', error);
    } finally {
      setPendingRemovals((prev) => {
        const next = new Set(prev);
        next.delete(tagName);
        return next;
      });
    }
  };

  const handleClose = () => {
    setSelectedTagName('');
    setSelectedTagValue('');
    setCustomTagName('');
    setCustomTagValue('');
    setIsCustomTag(false);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Edit Tags</DialogTitle>
          <DialogDescription>
            Manage behavior tags for user {userId}
          </DialogDescription>
        </DialogHeader>

        {/* Current Tags */}
        <div className="space-y-4">
          <div>
            <Label className="mb-2 block">Current Tags</Label>
            {tagEntries.length === 0 ? (
              <p className="text-sm text-muted-foreground">No tags assigned</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {tagEntries.map(({ name, value, updateTime, source }) => (
                  <div key={name} className="relative">
                    {pendingRemovals.has(name) && (
                      <div className="absolute inset-0 flex items-center justify-center rounded-md bg-background/80">
                        <Loader2 className="h-4 w-4 animate-spin" />
                      </div>
                    )}
                    <TagBadge
                      name={name}
                      value={value}
                      updateTime={updateTime}
                      source={source}
                      editable
                      onRemove={() => handleRemoveTag(name)}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Add Tag Section */}
          <div className="space-y-3 rounded-lg border p-4">
            <div className="flex items-center justify-between">
              <Label>Add New Tag</Label>
              <Button
                variant="ghost"
                size="sm"
                className={cn('text-xs', isCustomTag && 'text-primary')}
                onClick={() => setIsCustomTag(!isCustomTag)}
              >
                {isCustomTag ? 'Use Predefined' : 'Create Custom'}
              </Button>
            </div>

            {isCustomTag ? (
              // Custom Tag Form
              <div className="grid gap-3">
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <Label htmlFor="custom-name" className="text-xs">
                      Tag Name
                    </Label>
                    <Input
                      id="custom-name"
                      value={customTagName}
                      onChange={(e) => setCustomTagName(e.target.value)}
                      placeholder="e.g., custom_tag"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="custom-value" className="text-xs">
                      Value
                    </Label>
                    <Input
                      id="custom-value"
                      value={customTagValue}
                      onChange={(e) => setCustomTagValue(e.target.value)}
                      placeholder="e.g., value"
                    />
                  </div>
                </div>
              </div>
            ) : (
              // Predefined Tag Form
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <Label className="text-xs">Select Tag</Label>
                  <Select value={selectedTagName} onValueChange={setSelectedTagName}>
                    <SelectTrigger>
                      <SelectValue placeholder="Choose tag" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.keys(PREDEFINED_TAGS).map((tag) => (
                        <SelectItem key={tag} value={tag}>
                          {tag.charAt(0).toUpperCase() + tag.slice(1)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Value</Label>
                  <Select
                    value={selectedTagValue}
                    onValueChange={setSelectedTagValue}
                    disabled={!selectedTagName}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Choose value" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableValues.map((value) => (
                        <SelectItem key={value} value={value}>
                          {value}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            )}

            <Button
              size="sm"
              className="w-full"
              onClick={handleAddTag}
              disabled={
                updateTagMutation.isPending ||
                (isCustomTag
                  ? !customTagName.trim() || !customTagValue.trim()
                  : !selectedTagName || !selectedTagValue)
              }
            >
              {updateTagMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Plus className="mr-2 h-4 w-4" />
              )}
              Add Tag
            </Button>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            Done
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
