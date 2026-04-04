'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Search, X, Clock, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils/cn';

const RECENT_SEARCHES_KEY = 'behaviorsense_recent_searches';
const MAX_RECENT_SEARCHES = 5;

export interface UserSearchProps {
  className?: string;
  onSearch?: (userId: string) => void;
  placeholder?: string;
}

function getRecentSearches(): string[] {
  if (typeof window === 'undefined') return [];
  try {
    const stored = localStorage.getItem(RECENT_SEARCHES_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

function saveRecentSearch(userId: string): void {
  const recent = getRecentSearches();
  // Remove if exists, then add to front
  const filtered = recent.filter((id) => id !== userId);
  const updated = [userId, ...filtered].slice(0, MAX_RECENT_SEARCHES);
  localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(updated));
}

function clearRecentSearches(): void {
  localStorage.removeItem(RECENT_SEARCHES_KEY);
}

export function UserSearch({
  className,
  onSearch,
  placeholder = 'Search by User ID...',
}: UserSearchProps) {
  const router = useRouter();
  const [searchValue, setSearchValue] = useState('');
  const [recentSearches, setRecentSearches] = useState<string[]>([]);

  // Load recent searches on mount
  useEffect(() => {
    setRecentSearches(getRecentSearches());
  }, []);

  const handleSearch = useCallback(
    (userId: string) => {
      if (!userId.trim()) return;

      // Save to recent searches
      saveRecentSearch(userId.trim());
      setRecentSearches(getRecentSearches());

      // Call callback or navigate
      if (onSearch) {
        onSearch(userId.trim());
      } else {
        router.push(`/insight/user/${encodeURIComponent(userId.trim())}`);
      }
    },
    [onSearch, router]
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch(searchValue);
  };

  const handleClearHistory = () => {
    clearRecentSearches();
    setRecentSearches([]);
  };

  const handleRemoveRecent = (userId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const updated = recentSearches.filter((id) => id !== userId);
    localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(updated));
    setRecentSearches(updated);
  };

  return (
    <div className={cn('space-y-4', className)}>
      {/* Search Input */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="text"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder={placeholder}
            className="pl-10"
          />
          {searchValue && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="absolute right-1 top-1/2 h-7 w-7 -translate-y-1/2"
              onClick={() => setSearchValue('')}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
        <Button type="submit" disabled={!searchValue.trim()}>
          Search
        </Button>
      </form>

      {/* Recent Searches */}
      {recentSearches.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>Recent Searches</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 gap-1 text-xs text-muted-foreground"
              onClick={handleClearHistory}
            >
              <Trash2 className="h-3 w-3" />
              Clear
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {recentSearches.map((userId) => (
              <button
                key={userId}
                type="button"
                onClick={() => handleSearch(userId)}
                className="group flex items-center gap-1.5 rounded-full bg-muted px-3 py-1.5 text-sm transition-colors hover:bg-muted/80"
              >
                <span>{userId}</span>
                <span
                  role="button"
                  tabIndex={0}
                  className="rounded-full p-0.5 opacity-0 transition-opacity hover:bg-muted-foreground/20 group-hover:opacity-100"
                  onClick={(e) => handleRemoveRecent(userId, e)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      handleRemoveRecent(userId, e as unknown as React.MouseEvent);
                    }
                  }}
                >
                  <X className="h-3 w-3" />
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
