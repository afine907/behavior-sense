'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  MoreHorizontal,
  Pencil,
  Copy,
  Trash2,
  Play,
  ToggleLeft,
  ToggleRight,
} from 'lucide-react';
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui';
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
import { useToast } from '@/components/ui/use-toast';
import { useRules, useDeleteRule, useToggleRule } from '@/lib/hooks/use-rules';
import type { Rule } from '@/types/rule';

interface RuleListProps {
  onCreateNew?: () => void;
}

export function RuleList({ onCreateNew }: RuleListProps) {
  const router = useRouter();
  const { toast } = useToast();

  // Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'enabled' | 'disabled'>('all');
  const [priorityFilter, setPriorityFilter] = useState<'all' | string>('all');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  // Queries and mutations
  const { data, isLoading, error, refetch } = useRules({
    page,
    size: pageSize,
    enabled: statusFilter === 'all' ? undefined : statusFilter === 'enabled',
  });

  const deleteRule = useDeleteRule();
  const toggleRule = useToggleRule();

  // Delete confirmation state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [ruleToDelete, setRuleToDelete] = useState<Rule | null>(null);

  // Filter rules client-side for search and priority
  const filteredRules = useMemo(() => {
    if (!data?.list) return [];

    return data.list.filter((rule) => {
      const matchesSearch = searchQuery === '' ||
        rule.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        rule.description?.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesPriority = priorityFilter === 'all' ||
        rule.priority.toString() === priorityFilter;

      return matchesSearch && matchesPriority;
    });
  }, [data?.list, searchQuery, priorityFilter]);

  // Handlers
  const handleDelete = async () => {
    if (!ruleToDelete) return;

    try {
      await deleteRule.mutateAsync(ruleToDelete.ruleId);
      toast({
        title: 'Rule deleted',
        description: `Rule "${ruleToDelete.name}" has been deleted.`,
        variant: 'success',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete rule. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setDeleteDialogOpen(false);
      setRuleToDelete(null);
    }
  };

  const handleToggle = async (rule: Rule) => {
    try {
      await toggleRule.mutateAsync({
        id: rule.ruleId,
        enabled: !rule.enabled,
      });
      toast({
        title: rule.enabled ? 'Rule disabled' : 'Rule enabled',
        description: `Rule "${rule.name}" has been ${rule.enabled ? 'disabled' : 'enabled'}.`,
        variant: 'success',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to toggle rule. Please try again.',
        variant: 'destructive',
      });
    }
  };

  const handleDuplicate = (rule: Rule) => {
    // Navigate to create page with duplicate data
    router.push(`/rules/create?duplicate=${rule.ruleId}`);
  };

  const handleTest = (rule: Rule) => {
    router.push(`/rules/${rule.ruleId}?test=true`);
  };

  const openDeleteDialog = (rule: Rule) => {
    setRuleToDelete(rule);
    setDeleteDialogOpen(true);
  };

  // Priority options
  const priorityOptions = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'];

  if (error) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <p className="text-destructive mb-4">Failed to load rules</p>
          <Button variant="outline" onClick={() => refetch()}>
            Try Again
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-1 gap-3">
              {/* Search */}
              <div className="relative flex-1 max-w-sm">
                <Input
                  placeholder="Search rules..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              {/* Status Filter */}
              <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as typeof statusFilter)}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="enabled">Enabled</SelectItem>
                  <SelectItem value="disabled">Disabled</SelectItem>
                </SelectContent>
              </Select>

              {/* Priority Filter */}
              <Select value={priorityFilter} onValueChange={setPriorityFilter}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Priority" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Priority</SelectItem>
                  {priorityOptions.map((p) => (
                    <SelectItem key={p} value={p}>
                      Priority {p}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button onClick={() => router.push('/rules/create')}>
              Create Rule
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Rules Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-3 text-left text-sm font-medium">Name</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Priority</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Actions Count</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Updated</th>
                  <th className="px-4 py-3 text-right text-sm font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  // Loading skeleton
                  Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i} className="border-b">
                      <td className="px-4 py-3">
                        <div className="h-4 w-40 animate-pulse rounded bg-muted" />
                      </td>
                      <td className="px-4 py-3">
                        <div className="h-4 w-8 animate-pulse rounded bg-muted" />
                      </td>
                      <td className="px-4 py-3">
                        <div className="h-4 w-16 animate-pulse rounded bg-muted" />
                      </td>
                      <td className="px-4 py-3">
                        <div className="h-4 w-8 animate-pulse rounded bg-muted" />
                      </td>
                      <td className="px-4 py-3">
                        <div className="h-4 w-24 animate-pulse rounded bg-muted" />
                      </td>
                      <td className="px-4 py-3">
                        <div className="h-4 w-8 animate-pulse rounded bg-muted" />
                      </td>
                    </tr>
                  ))
                ) : filteredRules.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-12 text-center">
                      <div className="flex flex-col items-center gap-2">
                        <p className="text-muted-foreground">No rules found</p>
                        {(searchQuery || statusFilter !== 'all' || priorityFilter !== 'all') && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setSearchQuery('');
                              setStatusFilter('all');
                              setPriorityFilter('all');
                            }}
                          >
                            Clear Filters
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ) : (
                  filteredRules.map((rule) => (
                    <tr
                      key={rule.ruleId}
                      className="border-b transition-colors hover:bg-muted/50"
                    >
                      <td className="px-4 py-3">
                        <Link
                          href={`/rules/${rule.ruleId}`}
                          className="font-medium hover:underline"
                        >
                          {rule.name}
                        </Link>
                        {rule.description && (
                          <p className="text-xs text-muted-foreground truncate max-w-xs">
                            {rule.description}
                          </p>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant={
                            rule.priority <= 3
                              ? 'destructive'
                              : rule.priority <= 6
                              ? 'warning'
                              : 'secondary'
                          }
                        >
                          {rule.priority}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => handleToggle(rule)}
                          className="flex items-center gap-1.5"
                          disabled={toggleRule.isPending}
                        >
                          {rule.enabled ? (
                            <>
                              <ToggleRight className="h-4 w-4 text-green-500" />
                              <span className="text-sm text-green-600">ON</span>
                            </>
                          ) : (
                            <>
                              <ToggleLeft className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm text-muted-foreground">OFF</span>
                            </>
                          )}
                        </button>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline">{rule.actions?.length || 0}</Badge>
                      </td>
                      <td className="px-4 py-3 text-sm text-muted-foreground">
                        {new Date(rule.updateTime).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex justify-end">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem asChild>
                                <Link href={`/rules/${rule.ruleId}`}>
                                  <Pencil className="mr-2 h-4 w-4" />
                                  Edit
                                </Link>
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => handleTest(rule)}>
                                <Play className="mr-2 h-4 w-4" />
                                Test
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => handleDuplicate(rule)}>
                                <Copy className="mr-2 h-4 w-4" />
                                Duplicate
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                className="text-destructive"
                                onClick={() => openDeleteDialog(rule)}
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {data && data.total > pageSize && (
            <div className="flex items-center justify-between border-t px-4 py-3">
              <p className="text-sm text-muted-foreground">
                Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, data.total)} of {data.total} rules
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => p + 1)}
                  disabled={page * pageSize >= data.total}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Rule</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete &quot;{ruleToDelete?.name}&quot;? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
