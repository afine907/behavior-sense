# 前端控制台技术实现方案

> BehaviorSense Admin Console - 技术架构与实现规划

## 一、技术栈选型

### 1.1 核心框架

| 类别 | 技术选型 | 版本 | 选择理由 |
|------|----------|------|----------|
| 框架 | Next.js | 14.x | App Router、RSC、API Routes |
| 语言 | TypeScript | 5.x | 类型安全、IDE 支持 |
| 包管理 | pnpm | 8.x | 与 uv 对应、workspace 支持 |
| 样式 | Tailwind CSS | 3.x | 原子化、快速开发 |

### 1.2 UI 组件库

| 类别 | 技术选型 | 说明 |
|------|----------|------|
| 组件库 | shadcn/ui | 可定制、基于 Radix UI |
| 图标 | Lucide React | 轻量、一致性好 |
| 表格 | TanStack Table | 强大、灵活 |
| 表单 | React Hook Form + Zod | 类型安全验证 |
| 图表 | Recharts | React 原生、轻量 |
| 日期 | date-fns | 轻量、Tree-shakable |

### 1.3 状态与数据

| 类别 | 技术选型 | 说明 |
|------|----------|------|
| 服务端状态 | TanStack Query v5 | 缓存、同步、后台更新 |
| 客户端状态 | Zustand | 轻量、简单 |
| 路由状态 | Next.js Router | 内置 |
| 表单状态 | React Hook Form | 高性能 |

### 1.4 开发工具

| 类别 | 工具 | 说明 |
|------|------|------|
| 代码规范 | ESLint + Prettier | 统一风格 |
| 类型检查 | TypeScript strict | 严格模式 |
| HTTP 客户端 | ky / fetch | 轻量、类型友好 |
| Mock | MSW | API Mock |

---

## 二、项目结构

```
apps/web/
├── src/
│   ├── app/                          # Next.js App Router
│   │   ├── (auth)/                   # 认证布局组
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   └── layout.tsx
│   │   │
│   │   ├── (dashboard)/              # 主应用布局组
│   │   │   ├── layout.tsx            # 侧边栏 + Header
│   │   │   ├── page.tsx              # Dashboard 首页
│   │   │   │
│   │   │   ├── mock/                 # 事件模拟
│   │   │   │   ├── page.tsx
│   │   │   │   └── scenarios/
│   │   │   │       └── page.tsx
│   │   │   │
│   │   │   ├── rules/                # 规则管理
│   │   │   │   ├── page.tsx          # 规则列表
│   │   │   │   ├── [id]/
│   │   │   │   │   └── page.tsx      # 规则详情/编辑
│   │   │   │   └── create/
│   │   │   │       └── page.tsx      # 新建规则
│   │   │   │
│   │   │   ├── insight/              # 用户洞察
│   │   │   │   ├── page.tsx          # 用户搜索
│   │   │   │   └── user/
│   │   │   │       └── [id]/
│   │   │   │           └── page.tsx  # 用户画像
│   │   │   │
│   │   │   ├── audit/                # 审核工作台
│   │   │   │   ├── page.tsx          # 审核列表
│   │   │   │   ├── todo/
│   │   │   │   │   └── page.tsx      # 我的待办
│   │   │   │   └── order/
│   │   │   │       └── [id]/
│   │   │   │           └── page.tsx  # 审核详情
│   │   │   │
│   │   │   └── monitor/              # 系统监控
│   │   │       └── page.tsx
│   │   │
│   │   ├── api/                      # API Routes (BFF)
│   │   │   ├── auth/
│   │   │   │   └── route.ts
│   │   │   └── [...proxy]/
│   │   │       └── route.ts          # 代理后端 API
│   │   │
│   │   └── layout.tsx                # 根布局
│   │
│   ├── components/                   # 组件
│   │   ├── ui/                       # shadcn/ui 组件
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── form.tsx
│   │   │   ├── table.tsx
│   │   │   └── ...
│   │   │
│   │   ├── layout/                   # 布局组件
│   │   │   ├── sidebar.tsx
│   │   │   ├── header.tsx
│   │   │   └── nav-item.tsx
│   │   │
│   │   ├── dashboard/                # Dashboard 组件
│   │   │   ├── metric-card.tsx
│   │   │   ├── service-status.tsx
│   │   │   └── trend-chart.tsx
│   │   │
│   │   ├── rules/                    # 规则模块组件
│   │   │   ├── rule-form.tsx
│   │   │   ├── rule-editor.tsx       # 条件编辑器
│   │   │   └── rule-test.tsx
│   │   │
│   │   ├── insight/                  # 用户洞察组件
│   │   │   ├── user-profile.tsx
│   │   │   ├── tag-list.tsx
│   │   │   └── tag-statistics.tsx
│   │   │
│   │   └── audit/                    # 审核组件
│   │       ├── order-card.tsx
│   │       ├── review-form.tsx
│   │       └── status-badge.tsx
│   │
│   ├── lib/                          # 工具库
│   │   ├── api/                      # API 客户端
│   │   │   ├── client.ts             # HTTP 客户端封装
│   │   │   ├── mock.ts               # Mock Service API
│   │   │   ├── rules.ts              # Rules Service API
│   │   │   ├── insight.ts            # Insight Service API
│   │   │   └── audit.ts              # Audit Service API
│   │   │
│   │   ├── auth/                     # 认证
│   │   │   ├── jwt.ts
│   │   │   └── session.ts
│   │   │
│   │   ├── hooks/                    # 自定义 Hooks
│   │   │   ├── use-user.ts
│   │   │   ├── use-rules.ts
│   │   │   └── use-websocket.ts
│   │   │
│   │   └── utils/                    # 工具函数
│   │       ├── cn.ts                 # classnames
│   │       ├── format.ts             # 格式化
│   │       └── date.ts               # 日期处理
│   │
│   ├── types/                        # 类型定义
│   │   ├── api.ts                    # API 响应类型
│   │   ├── rule.ts                   # 规则类型
│   │   ├── user.ts                   # 用户类型
│   │   └── audit.ts                  # 审核类型
│   │
│   └── styles/
│       └── globals.css
│
├── public/
├── .env.local
├── .env.development
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
├── components.json                   # shadcn/ui 配置
└── package.json
```

---

## 三、API 集成策略

### 3.1 服务端代理 (BFF 模式)

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Browser   │────▶│  Next.js BFF    │────▶│  Backend APIs   │
│             │     │  (API Routes)   │     │                 │
└─────────────┘     └─────────────────┘     └─────────────────┘
       │                    │                       │
       │   /api/xxx         │   http://xxx:800x     │
       └────────────────────┴───────────────────────┘
```

**优势**:
- 隐藏后端服务地址
- 统一认证处理
- 解决 CORS 问题
- 类型安全的 API 层

### 3.2 API 客户端设计

```typescript
// lib/api/client.ts
import ky from 'ky';

const api = ky.create({
  prefixUrl: '/api',
  hooks: {
    beforeRequest: [
      (request) => {
        const token = getToken();
        if (token) {
          request.headers.set('Authorization', `Bearer ${token}`);
        }
      },
    ],
    afterResponse: [
      (_request, _options, response) => {
        // 统一处理响应
      },
    ],
  },
});

// lib/api/rules.ts
import type { Rule, RuleListResponse } from '@/types/rule';

export const rulesApi = {
  list: (params: { page?: number; size?: number }) =>
    api.get('rules', { searchParams: params }).json<RuleListResponse>(),

  get: (id: string) =>
    api.get(`rules/${id}`).json<{ data: Rule }>(),

  create: (data: CreateRuleInput) =>
    api.post('rules', { json: data }).json<{ data: { ruleId: string } }>(),

  update: (id: string, data: UpdateRuleInput) =>
    api.put(`rules/${id}`, { json: data }),

  delete: (id: string) =>
    api.delete(`rules/${id}`),
};
```

### 3.3 TanStack Query 集成

```typescript
// lib/hooks/use-rules.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { rulesApi } from '@/lib/api/rules';

export function useRules(params: { page: number; size: number }) {
  return useQuery({
    queryKey: ['rules', 'list', params],
    queryFn: () => rulesApi.list(params),
  });
}

export function useRule(id: string) {
  return useQuery({
    queryKey: ['rules', 'detail', id],
    queryFn: () => rulesApi.get(id),
    enabled: !!id,
  });
}

export function useCreateRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: rulesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] });
    },
  });
}
```

---

## 四、状态管理方案

### 4.1 服务端状态 (TanStack Query)

```typescript
// 缓存策略
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5 分钟内认为数据新鲜
      gcTime: 10 * 60 * 1000,        // 10 分钟后清理
      retry: 1,                       // 失败重试 1 次
      refetchOnWindowFocus: false,    // 窗口聚焦不自动刷新
    },
  },
});
```

### 4.2 客户端状态 (Zustand)

```typescript
// lib/stores/auth.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  token: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: 'auth-storage' }
  )
);

// lib/stores/sidebar.ts
interface SidebarState {
  collapsed: boolean;
  toggle: () => void;
}

export const useSidebarStore = create<SidebarState>((set) => ({
  collapsed: false,
  toggle: () => set((state) => ({ collapsed: !state.collapsed })),
}));
```

---

## 五、认证与权限

### 5.1 认证流程

```
┌─────────────┐                      ┌─────────────┐
│   Login     │───POST /api/auth────▶│  Validate   │
│   Page      │                      │  JWT        │
└─────────────┘                      └──────┬──────┘
       │                                    │
       │  Redirect to Dashboard             │  Set Cookie
       └────────────────────────────────────┘
```

### 5.2 路由守卫

```typescript
// app/(dashboard)/layout.tsx
import { redirect } from 'next/navigation';
import { getServerSession } from '@/lib/auth/session';

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getServerSession();

  if (!session) {
    redirect('/login');
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Header user={session.user} />
        {children}
      </main>
    </div>
  );
}
```

### 5.3 权限控制

```typescript
// types/user.ts
export type Role = 'ADMIN' | 'ANALYST' | 'AUDITOR' | 'MONITOR';

export const PERMISSIONS: Record<Role, string[]> = {
  ADMIN: ['mock', 'rules', 'insight', 'audit', 'monitor'],
  ANALYST: ['insight', 'monitor'],
  AUDITOR: ['audit', 'insight'],
  MONITOR: ['monitor'],
};

// components/layout/sidebar.tsx
function Sidebar() {
  const { user } = useAuthStore();
  const permissions = PERMISSIONS[user.role];

  const navItems = [
    { key: 'mock', label: '事件模拟', href: '/mock' },
    { key: 'rules', label: '规则管理', href: '/rules' },
    { key: 'insight', label: '用户洞察', href: '/insight' },
    { key: 'audit', label: '审核工作台', href: '/audit' },
    { key: 'monitor', label: '系统监控', href: '/monitor' },
  ].filter(item => permissions.includes(item.key));

  return <nav>{/* ... */}</nav>;
}
```

---

## 六、实时通信

### 6.1 WebSocket 集成

```typescript
// lib/hooks/use-websocket.ts
import { useEffect, useRef, useState } from 'react';

interface UseWebSocketOptions<T> {
  url: string;
  onMessage: (data: T) => void;
  enabled?: boolean;
}

export function useWebSocket<T>({
  url,
  onMessage,
  enabled = true,
}: UseWebSocketOptions<T>) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!enabled) return;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    return () => ws.close();
  }, [url, enabled, onMessage]);

  const subscribe = (topic: string) => {
    wsRef.current?.send(JSON.stringify({ type: 'SUBSCRIBE', topic }));
  };

  return { connected, subscribe };
}

// 使用示例
function AuditTodoPage() {
  const queryClient = useQueryClient();

  useWebSocket({
    url: 'ws://localhost:8004/api/ws/realtime',
    onMessage: (data) => {
      if (data.topic === 'audit_order') {
        queryClient.invalidateQueries({ queryKey: ['audit', 'todo'] });
      }
    },
  });

  return <AuditTodoList />;
}
```

---

## 七、开发阶段规划

### Phase 1: 项目初始化 (1 天)

| 任务 | 说明 |
|------|------|
| 初始化 Next.js 项目 | `pnpm create next-app@latest web` |
| 配置 TypeScript | strict 模式、路径别名 |
| 配置 Tailwind CSS | 基础样式、CSS 变量 |
| 安装 shadcn/ui | 初始化组件库 |
| 配置 ESLint + Prettier | 代码规范 |
| 创建目录结构 | 按上述结构创建 |

### Phase 2: 基础架构 (2 天)

| 任务 | 说明 |
|------|------|
| API 客户端封装 | ky + 统一错误处理 |
| TanStack Query 配置 | Provider、默认配置 |
| Zustand Store | 认证状态、UI 状态 |
| 布局组件 | Sidebar、Header |
| 认证流程 | 登录页、路由守卫 |
| 类型定义 | API 响应、业务实体 |

### Phase 3: 核心页面 (5 天)

| 任务 | 页面 | 天数 |
|------|------|------|
| Dashboard | 首页、指标卡片、图表 | 1 |
| 规则管理 | 列表、创建、编辑、测试 | 2 |
| 审核工作台 | 列表、待办、详情、审核 | 1 |
| 用户洞察 | 搜索、画像、标签管理 | 1 |

### Phase 4: 增强功能 (2 天)

| 任务 | 说明 |
|------|------|
| 事件模拟页面 | 手动生成、场景管理 |
| 系统监控页面 | 服务状态、流处理状态 |
| WebSocket 实时更新 | 审核通知、指标更新 |
| 错误边界 | 优雅的错误处理 |

### Phase 5: 优化与测试 (2 天)

| 任务 | 说明 |
|------|------|
| 性能优化 | 懒加载、骨架屏 |
| 响应式适配 | 移动端支持 |
| E2E 测试 | Playwright 关键流程 |
| 文档 | README、组件文档 |

---

## 八、环境配置

### 8.1 环境变量

```bash
# .env.development
NEXT_PUBLIC_API_MOCK=http://localhost:8001
NEXT_PUBLIC_API_RULES=http://localhost:8002
NEXT_PUBLIC_API_INSIGHT=http://localhost:8003
NEXT_PUBLIC_API_AUDIT=http://localhost:8004

# .env.production
NEXT_PUBLIC_API_MOCK=http://mock.behavior-sense.internal
NEXT_PUBLIC_API_RULES=http://rules.behavior-sense.internal
NEXT_PUBLIC_API_INSIGHT=http://insight.behavior-sense.internal
NEXT_PUBLIC_API_AUDIT=http://audit.behavior-sense.internal
```

### 8.2 Next.js 配置

```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  async rewrites() {
    return [
      {
        source: '/api/mock/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_MOCK}/api/:path*`,
      },
      {
        source: '/api/rules/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_RULES}/api/:path*`,
      },
      {
        source: '/api/insight/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_INSIGHT}/api/:path*`,
      },
      {
        source: '/api/audit/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_AUDIT}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
```

---

## 九、依赖清单

```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",

    "@tanstack/react-query": "^5.0.0",
    "@tanstack/react-table": "^8.0.0",

    "zustand": "^4.5.0",
    "react-hook-form": "^7.50.0",
    "zod": "^3.22.0",
    "@hookform/resolvers": "^3.3.0",

    "ky": "^1.1.0",
    "date-fns": "^3.0.0",

    "recharts": "^2.10.0",
    "lucide-react": "^0.300.0",

    "tailwindcss": "^3.4.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0",

    "@radix-ui/react-dialog": "^1.0.0",
    "@radix-ui/react-dropdown-menu": "^2.0.0",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-tabs": "^1.0.0",
    "@radix-ui/react-toast": "^1.1.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/node": "^20.0.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",

    "eslint": "^8.0.0",
    "eslint-config-next": "^14.0.0",
    "prettier": "^3.2.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

---

## 十、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 后端 API 变更 | 高 | 使用 MSW Mock、契约测试 |
| WebSocket 断连 | 中 | 自动重连、离线提示 |
| 大数据量表格性能 | 中 | 虚拟滚动、分页 |
| 权限复杂度 | 低 | 明确角色定义、单元测试 |

---

## 十一、总结

本方案采用 **Next.js 14 + TypeScript + Tailwind + shadcn/ui** 技术栈，与后端 Python 微服务形成清晰分层：

- **BFF 层**: Next.js API Routes 处理代理和认证
- **数据层**: TanStack Query 管理服务端状态
- **状态层**: Zustand 管理客户端状态
- **UI 层**: shadcn/ui 保证一致性和开发效率

预计总开发时间: **12 人天**
