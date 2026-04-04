'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useUIStore } from '@/lib/stores/ui';
import { useAuthStore } from '@/lib/stores/auth';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Menu, User, Settings, LogOut, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils/cn';

// Breadcrumb mapping
const breadcrumbMap: Record<string, string> = {
  '/': 'Dashboard',
  '/mock': 'Event Simulation',
  '/rules': 'Rules Management',
  '/insight': 'User Insight',
  '/audit': 'Audit Workbench',
  '/monitor': 'System Monitor',
};

export function Header() {
  const { toggleSidebar } = useUIStore();
  const { user, logout } = useAuthStore();
  const pathname = usePathname();

  // Generate breadcrumbs
  const pathSegments = pathname.split('/').filter(Boolean);
  const breadcrumbs: string[] = pathSegments.reduce<string[]>(
    (acc: string[], segment: string, index: number) => {
      const path =
        '/' +
        pathname
          .split('/')
          .filter(Boolean)
          .slice(0, index + 1)
          .join('/');
      const label = breadcrumbMap[path] || segment;
      acc.push(label);
      return acc;
    },
    []
  );

  const handleLogout = () => {
    logout();
    // In production, redirect to login
    window.location.href = '/';
  };

  // Get display name for user
  const displayName = user?.username || 'User';
  const displayEmail = user?.email || `${user?.username}@behaviorsense.com`;
  const displayRole = user?.role || (user?.roles?.[0] as string) || 'viewer';

  return (
    <header className="flex h-16 items-center justify-between border-b bg-background px-4">
      {/* Left side: Menu button + Breadcrumbs */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className="md:flex"
        >
          <Menu className="h-5 w-5" />
        </Button>

        {/* Breadcrumbs */}
        <nav className="hidden items-center gap-1 text-sm md:flex">
          <Link
            href="/"
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            Home
          </Link>
          {breadcrumbs.map((crumb: string, index: number) => (
            <div key={index} className="flex items-center gap-1">
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
              <span
                className={cn(
                  'transition-colors',
                  index === breadcrumbs.length - 1
                    ? 'font-medium text-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                {crumb}
              </span>
            </div>
          ))}
        </nav>
      </div>

      {/* Right side: User dropdown */}
      <div className="flex items-center gap-4">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-9 w-9 rounded-full">
              <Avatar className="h-9 w-9">
                <AvatarImage src={user?.avatar} alt={displayName} />
                <AvatarFallback>
                  {displayName?.charAt(0).toUpperCase() || 'U'}
                </AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56" align="end" forceMount>
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">{displayName}</p>
                <p className="text-xs leading-none text-muted-foreground">
                  {displayEmail}
                </p>
                <p className="text-xs leading-none text-muted-foreground capitalize">
                  Role: {displayRole}
                </p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/profile" className="cursor-pointer">
                <User className="mr-2 h-4 w-4" />
                <span>Profile</span>
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href="/settings" className="cursor-pointer">
                <Settings className="mr-2 h-4 w-4" />
                <span>Settings</span>
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} className="cursor-pointer">
              <LogOut className="mr-2 h-4 w-4" />
              <span>Logout</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
