'use client';

import { Plus, Trash2, X } from 'lucide-react';
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui';
import type { RuleAction } from '@/types/rule';

interface ActionEditorProps {
  actions: RuleAction[];
  onChange: (actions: RuleAction[]) => void;
}

const ACTION_TYPES = [
  { value: 'TAG_USER', label: 'Tag User', description: 'Add tags to the user profile' },
  { value: 'TRIGGER_AUDIT', label: 'Trigger Audit', description: 'Create an audit record for review' },
] as const;

const AUDIT_LEVELS = ['HIGH', 'MEDIUM', 'LOW'] as const;

export function ActionEditor({ actions, onChange }: ActionEditorProps) {
  const addAction = () => {
    onChange([
      ...actions,
      { type: 'TAG_USER', params: { tags: [] } },
    ]);
  };

  const removeAction = (index: number) => {
    onChange(actions.filter((_, i) => i !== index));
  };

  const updateActionType = (index: number, type: RuleAction['type']) => {
    const newActions = [...actions];
    if (type === 'TAG_USER') {
      newActions[index] = { type, params: { tags: [] } };
    } else {
      newActions[index] = { type, params: { level: 'MEDIUM' } };
    }
    onChange(newActions);
  };

  const updateActionParams = (index: number, params: Record<string, unknown>) => {
    const newActions = [...actions];
    newActions[index] = { ...newActions[index], params: { ...newActions[index].params, ...params } };
    onChange(newActions);
  };

  const addTag = (index: number, tag: string) => {
    if (!tag.trim()) return;
    const currentTags = (actions[index].params.tags as string[]) || [];
    if (!currentTags.includes(tag.trim())) {
      updateActionParams(index, { tags: [...currentTags, tag.trim()] });
    }
  };

  const removeTag = (actionIndex: number, tagIndex: number) => {
    const currentTags = (actions[actionIndex].params.tags as string[]) || [];
    updateActionParams(actionIndex, { tags: currentTags.filter((_, i) => i !== tagIndex) });
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Actions</CardTitle>
          <Button variant="outline" size="sm" onClick={addAction}>
            <Plus className="mr-2 h-4 w-4" />
            Add Action
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {actions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <p className="text-sm text-muted-foreground mb-2">No actions configured</p>
            <p className="text-xs text-muted-foreground">
              Add actions to define what happens when the rule matches
            </p>
          </div>
        ) : (
          actions.map((action, index) => (
            <div
              key={index}
              className="rounded-lg border p-4 space-y-3"
            >
              <div className="flex items-center justify-between">
                <Label className="text-sm font-medium">Action {index + 1}</Label>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-destructive"
                  onClick={() => removeAction(index)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>

              <div className="space-y-2">
                <Label>Action Type</Label>
                <Select
                  value={action.type}
                  onValueChange={(v) => updateActionType(index, v as RuleAction['type'])}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select action type" />
                  </SelectTrigger>
                  <SelectContent>
                    {ACTION_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        <div>
                          <span>{type.label}</span>
                          <span className="block text-xs text-muted-foreground">
                            {type.description}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Dynamic fields based on action type */}
              {action.type === 'TAG_USER' && (
                <div className="space-y-2">
                  <Label>Tags</Label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {((action.params.tags as string[]) || []).map((tag, tagIndex) => (
                      <Badge key={tagIndex} variant="secondary" className="gap-1">
                        {tag}
                        <button
                          type="button"
                          onClick={() => removeTag(index, tagIndex)}
                          className="ml-1 hover:text-destructive"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                  <Input
                    placeholder="Enter tag name and press Enter"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addTag(index, (e.target as HTMLInputElement).value);
                        (e.target as HTMLInputElement).value = '';
                      }
                    }}
                  />
                  <p className="text-xs text-muted-foreground">
                    Press Enter to add a tag
                  </p>
                </div>
              )}

              {action.type === 'TRIGGER_AUDIT' && (
                <div className="space-y-2">
                  <Label>Audit Level</Label>
                  <Select
                    value={(action.params.level as string) || 'MEDIUM'}
                    onValueChange={(v) => updateActionParams(index, { level: v })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select audit level" />
                    </SelectTrigger>
                    <SelectContent>
                      {AUDIT_LEVELS.map((level) => (
                        <SelectItem key={level} value={level}>
                          <div className="flex items-center gap-2">
                            <div
                              className={`h-2 w-2 rounded-full ${
                                level === 'HIGH'
                                  ? 'bg-red-500'
                                  : level === 'MEDIUM'
                                  ? 'bg-yellow-500'
                                  : 'bg-green-500'
                              }`}
                            />
                            {level}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    Higher priority audits appear first in the review queue
                  </p>
                </div>
              )}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
