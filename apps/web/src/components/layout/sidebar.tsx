'use client';

import { useUIStore } from '@/lib/stores/ui';
import { useAuthStore, type UserRole } from '@/lib/stores/auth';
import { NavItem } from './nav-item';
import { cn } from '@/lib/utils/cn';
import {
  LayoutDashboard,
  ScrollText,
  ClipboardCheck,
  ChevronLeft,
  ChevronRight,
  Bot,
  Link2,
  Bell,
  DollarSign,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';

interface NavItemConfig {
  href: string;
  icon: typeof LayoutDashboard;
  label: string;
  roles?: UserRole[]; // If undefined, all roles can access
}

const navItems: NavItemConfig[] = [
  {
    href: '/',
    icon: LayoutDashboard,
    label: 'Overview',
  },
  {
    href: '/agents',
    icon: Bot,
    label: 'Agents',
  },
  {
    href: '/traces',
    icon: Link2,
    label: 'Traces',
  },
  {
    href: '/alerts',
    icon: Bell,
    label: 'Alerts',
  },
  {
    href: '/rules',
    icon: ScrollText,
    label: 'Rules',
  },
  {
    href: '/audit',
    icon: ClipboardCheck,
    label: 'Audit',
  },
  {
    href: '/costs',
    icon: DollarSign,
    label: 'Costs',
  },
];

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
  const { user } = useAuthStore();

  // Get the user's primary role
  const userRole: UserRole = user?.role || (user?.roles?.[0] as UserRole) || 'viewer';

  // Filter nav items based on user role
  const filteredNavItems = navItems.filter((item) => {
    if (!item.roles) return true;
    return item.roles.includes(userRole);
  });

  return (
    <aside
      className={cn(
        'flex h-screen flex-col border-r bg-background transition-all duration-300',
        sidebarCollapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Logo */}
      <div
        className={cn(
          'flex h-16 items-center border-b px-4',
          sidebarCollapsed ? 'justify-center' : 'justify-start'
        )}
      >
        {sidebarCollapsed ? (
          <span className="text-xl font-bold text-primary">BS</span>
        ) : (
          <div>
            <span className="text-xl font-bold text-primary">
              {'\u{1F9E0}'} BehaviorSense
            </span>
            <p className="text-xs text-muted-foreground mt-0.5">AI Agent Analytics</p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-2">
        {filteredNavItems.map((item) => (
          <NavItem
            key={item.href}
            href={item.href}
            icon={item.icon}
            label={item.label}
            collapsed={sidebarCollapsed}
          />
        ))}
      </nav>

      {/* Collapse Toggle & Version */}
      <div className="border-t p-2">
        {!sidebarCollapsed && (
          <div className="mb-2 px-3 py-1 text-xs text-muted-foreground/60">
            <div>BehaviorSense v2.0</div>
            <div>AI Agent Analytics</div>
          </div>
        )}
        <Separator className="mb-2" />
        <Button
          variant="ghost"
          size={sidebarCollapsed ? 'icon' : 'default'}
          className={cn('w-full', !sidebarCollapsed && 'justify-start')}
          onClick={toggleSidebar}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="mr-2 h-4 w-4" />
              <span>Collapse</span>
            </>
          )}
        </Button>
      </div>
    </aside>
  );
}
