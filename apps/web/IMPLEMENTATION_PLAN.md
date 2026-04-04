# BehaviorSense 前端控制台开发计划

> 多 Agent 协作的高质量前端开发方案

---

## 一、项目目标

基于已有的技术方案 (`wiki/frontend-console-plan.md`) 和交互设计 (`wiki/frontend-interaction-design.md`)，在 `apps/web/` 目录下开发一个完整的前端控制台。

### 核心交付物

| 交付物 | 说明 |
|--------|------|
| Next.js 14 项目 | App Router + TypeScript |
| UI 组件库 | shadcn/ui + 业务组件 |
| 6 个核心模块 | Dashboard, Mock, Rules, Insight, Audit, Monitor |
| API 集成层 | BFF 代理 + TanStack Query |
| 认证系统 | JWT + 角色权限 |

---

## 二、Agent 调研与分工

### 2.1 可用 Agent 类型

| Agent | 能力 | 适用场景 |
|-------|------|----------|
| **general-purpose** | 通用任务执行、代码搜索、多步骤任务 | 复杂功能开发、代码实现 |
| **Explore** | 快速代码库探索、文件搜索、代码搜索 | 技术调研、依赖分析 |
| **Plan** | 架构设计、实现方案规划 | 技术方案细化 |
| **qa-evaluator** | 全栈效果评估、代码质量验证 | 功能验收、质量把关 |

### 2.2 任务-Agent 映射

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Frontend Console Development                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Phase 1: Project Init                                                  │
│  ┌─────────────────────┐                                                │
│  │ Direct Execution    │ ← 直接执行 (配置文件、脚手架)                   │
│  │ - Next.js 初始化    │                                                │
│  │ - 依赖安装          │                                                │
│  │ - 目录结构创建      │                                                │
│  └─────────────────────┘                                                │
│                                                                          │
│  Phase 2: Research & Architecture                                       │
│  ┌─────────────────────┐ ┌─────────────────────┐                       │
│  │ Explore Agent       │ │ Plan Agent          │                       │
│  │ - shadcn/ui 最佳实践│ │ - API 层架构设计    │                       │
│  │ - TanStack Query    │ │ - 状态管理方案      │                       │
│  │ - Next.js 14 特性   │ │ - 认证流程设计      │                       │
│  └─────────────────────┘ └─────────────────────┘                       │
│                                                                          │
│  Phase 3: Core Development (并行)                                       │
│  ┌─────────────────────┐ ┌─────────────────────┐ ┌───────────────────┐ │
│  │ Agent-A: 基础架构   │ │ Agent-B: 认证模块   │ │ Agent-C: 布局组件 │ │
│  │ - API 客户端       │ │ - 登录页面         │ │ - Sidebar         │ │
│  │ - Query 配置       │ │ - JWT 处理         │ │ - Header          │ │
│  │ - 工具函数         │ │ - 路由守卫         │ │ - NavItem         │ │
│  └─────────────────────┘ └─────────────────────┘ └───────────────────┘ │
│                                                                          │
│  Phase 4: Feature Modules (并行)                                        │
│  ┌─────────────────────┐ ┌─────────────────────┐ ┌───────────────────┐ │
│  │ Agent-D: Dashboard  │ │ Agent-E: Rules      │ │ Agent-F: Audit    │ │
│  │ - 指标卡片         │ │ - 规则列表         │ │ - 待办列表        │ │
│  │ - 服务状态         │ │ - 规则编辑器       │ │ - 审核详情        │ │
│  │ - 趋势图表         │ │ - 条件构建器       │ │ - 审核表单        │ │
│  └─────────────────────┘ └─────────────────────┘ └───────────────────┘ │
│                                                                          │
│  ┌─────────────────────┐ ┌─────────────────────┐                       │
│  │ Agent-G: Insight    │ │ Agent-H: Mock       │                       │
│  │ - 用户搜索         │ │ - 事件生成         │                       │
│  │ - 用户画像         │ │ - 场景模拟         │                       │
│  │ - 标签管理         │ │ - 实时流           │                       │
│  └─────────────────────┘ └─────────────────────┘                       │
│                                                                          │
│  Phase 5: QA & Polish                                                   │
│  ┌─────────────────────┐ ┌─────────────────────┐                       │
│  │ qa-evaluator Agent  │ │ general-purpose     │                       │
│  │ - 功能验证         │ │ - Bug 修复          │                       │
│  │ - 代码质量         │ │ - 性能优化          │                       │
│  │ - 集成测试         │ │ - 文档补充          │                       │
│  └─────────────────────┘ └─────────────────────┘                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 三、详细执行计划

### Phase 1: 项目初始化 (直接执行)

**执行方式**: 直接执行 (非 Agent)

**任务清单**:

| # | 任务 | 命令/操作 | 预期产出 |
|---|------|-----------|----------|
| 1.1 | 创建 Next.js 项目 | `pnpm create next-app@latest web` | apps/web/ 目录 |
| 1.2 | 配置 TypeScript | 修改 tsconfig.json | strict 模式启用 |
| 1.3 | 安装核心依赖 | `pnpm add tanstack/react-query zustand ...` | package.json |
| 1.4 | 安装 shadcn/ui | `pnpm dlx shadcn-ui@latest init` | components.json |
| 1.5 | 创建目录结构 | mkdir -p src/{app,components,lib,types} | 项目骨架 |
| 1.6 | 配置 ESLint/Prettier | 添加 .eslintrc, .prettierrc | 代码规范 |
| 1.7 | 创建环境变量 | .env.development, .env.example | 环境配置 |

**验收标准**:
- [ ] `pnpm dev` 启动成功
- [ ] `pnpm build` 构建成功
- [ ] `pnpm lint` 无错误
- [ ] 目录结构符合设计

---

### Phase 2: 技术调研与架构设计 (并行 Agent)

#### 2.1 Explore Agent: 前端技术调研

**任务描述**: 调研 Next.js 14、shadcn/ui、TanStack Query 的最佳实践

**Agent Prompt**:
```
Research the following technologies and provide implementation guidelines:

1. Next.js 14 App Router:
   - Server Components vs Client Components
   - Data fetching patterns
   - Route groups and layouts
   - API Routes best practices

2. shadcn/ui:
   - Installation and configuration
   - Theming and customization
   - Common component patterns (DataTable, Form, Dialog)
   - Integration with react-hook-form and zod

3. TanStack Query v5:
   - QueryClient setup
   - useQuery/useMutation patterns
   - Cache invalidation strategies
   - Prefetching and optimistic updates

4. Zustand:
   - Store structure for auth and UI state
   - Persist middleware
   - DevTools integration

Focus on practical code examples that can be directly applied to the BehaviorSense admin console project.

Output a markdown document with:
- Key concepts
- Code snippets
- Common patterns
- Potential pitfalls
```

**产出**: `apps/web/docs/RESEARCH.md`

#### 2.2 Plan Agent: 架构设计

**任务描述**: 设计 API 层、状态管理、认证流程的详细方案

**Agent Prompt**:
```
Design the architecture for a Next.js 14 admin console with the following requirements:

## Context
- Backend: 4 FastAPI microservices (mock:8001, rules:8002, insight:8003, audit:8004)
- Authentication: JWT tokens with roles (ADMIN, ANALYST, AUDITOR, MONITOR)
- State: Server state (TanStack Query) + Client state (Zustand)

## Design Tasks

1. API Layer Architecture:
   - BFF (Backend for Frontend) pattern with Next.js API routes
   - Proxy configuration for multiple backend services
   - Type-safe API client design
   - Error handling and retry strategies

2. Authentication Flow:
   - Login process with JWT
   - Token storage (httpOnly cookie vs localStorage)
   - Token refresh mechanism
   - Route protection middleware

3. State Management:
   - Auth store (user, token, roles, permissions)
   - UI store (sidebar collapsed, theme)
   - Query cache configuration

4. Component Architecture:
   - Server vs Client component boundaries
   - Layout component hierarchy
   - Shared component patterns

Provide:
- Architecture diagrams (ASCII)
- Code structure
- Key implementation files
- TypeScript interfaces
```

**产出**: `apps/web/docs/ARCHITECTURE.md`

---

### Phase 3: 核心开发 (并行 Agent)

#### 3.1 Agent-A: 基础架构层

**任务描述**: 实现 API 客户端、TanStack Query 配置、工具函数

**Agent Prompt**:
```
Implement the foundational infrastructure for the BehaviorSense admin console.

## Working Directory: apps/web/

## Tasks

### 1. API Client (src/lib/api/)
Create a type-safe HTTP client:

```typescript
// src/lib/api/client.ts
- Base configuration with ky
- Request/response interceptors
- Error handling
- Auth header injection
```

### 2. Service API Modules (src/lib/api/)
Create typed API functions for each backend service:

```typescript
// src/lib/api/mock.ts - Event generation, scenarios
// src/lib/api/rules.ts - CRUD, testing
// src/lib/api/insight.ts - User profiles, tags
// src/lib/api/audit.ts - Audit orders, review
```

### 3. TanStack Query Setup (src/lib/query/)
```typescript
// src/lib/query/provider.tsx - QueryClientProvider
// src/lib/query/hooks.ts - Custom hooks for each API
```

### 4. Utility Functions (src/lib/utils/)
```typescript
// src/lib/utils/cn.ts - Class name utility
// src/lib/utils/format.ts - Number, date formatting
// src/lib/utils/date.ts - Date parsing with date-fns
```

### 5. Type Definitions (src/types/)
```typescript
// src/types/api.ts - ApiResponse, PaginatedResponse
// src/types/rule.ts - Rule, Condition, Action
// src/types/user.ts - User, Tag, Profile
// src/types/audit.ts - AuditOrder, ReviewStatus
```

## Requirements
- All code must be TypeScript with strict types
- Use Zod for runtime validation where needed
- Follow existing patterns from wiki/frontend-console-plan.md
```

**产出文件**:
- `src/lib/api/*.ts`
- `src/lib/query/*.ts`
- `src/lib/utils/*.ts`
- `src/types/*.ts`

#### 3.2 Agent-B: 认证模块

**任务描述**: 实现登录页面、JWT 处理、路由守卫

**Agent Prompt**:
```
Implement the authentication system for the BehaviorSense admin console.

## Working Directory: apps/web/

## Tasks

### 1. Auth Store (src/lib/stores/auth.ts)
```typescript
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (credentials: LoginInput) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}
```

### 2. Login Page (src/app/(auth)/login/page.tsx)
- Form with username/password
- Validation with Zod + react-hook-form
- Error display
- Remember me checkbox
- Redirect after successful login

### 3. Auth Layout (src/app/(auth)/layout.tsx)
- Centered card layout
- Logo and branding

### 4. Session Management (src/lib/auth/session.ts)
- Token storage (use localStorage for now)
- Token decode and validation
- Auto-logout on token expiry

### 5. Route Protection
- Middleware or layout-level check
- Redirect to login if not authenticated
- Store intended URL for redirect after login

### 6. Auth API Hook (src/lib/hooks/use-auth.ts)
- useLogin mutation
- useLogout mutation
- useCurrentUser query

## Reference
- See wiki/frontend-interaction-design.md for login page wireframe
- Backend login endpoint: POST /api/auth with JWT response
```

**产出文件**:
- `src/lib/stores/auth.ts`
- `src/app/(auth)/**/*`
- `src/lib/auth/**/*`
- `src/lib/hooks/use-auth.ts`

#### 3.3 Agent-C: 布局组件

**任务描述**: 实现 Sidebar、Header、主布局

**Agent Prompt**:
```
Implement the main layout components for the BehaviorSense admin console.

## Working Directory: apps/web/

## Tasks

### 1. Sidebar (src/components/layout/sidebar.tsx)
Features:
- Collapsible (240px → 64px)
- Navigation items with icons
- Active state highlighting
- Role-based menu filtering
- Logo at top

Menu structure:
- Dashboard (/)
- Event Simulation (/mock)
- Rules Management (/rules)
- User Insight (/insight)
- Audit Workbench (/audit)
- System Monitor (/monitor)

### 2. Header (src/components/layout/header.tsx)
Features:
- Breadcrumb navigation
- User avatar with dropdown
  - Profile
  - Settings
  - Logout
- Collapse sidebar button
- Theme toggle (optional)

### 3. Nav Item (src/components/layout/nav-item.tsx)
Features:
- Icon + label
- Active state
- Tooltip when collapsed
- Link wrapper

### 4. Dashboard Layout (src/app/(dashboard)/layout.tsx)
- Protect route (check auth)
- Render sidebar + header + main content
- Handle responsive breakpoints

### 5. UI Store (src/lib/stores/ui.ts)
```typescript
interface UIState {
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
}
```

## Reference
- See wiki/frontend-interaction-design.md Section 1.2 for layout specs
- Use Lucide icons
- Use shadcn/ui components as base
```

**产出文件**:
- `src/components/layout/*.tsx`
- `src/app/(dashboard)/layout.tsx`
- `src/lib/stores/ui.ts`

---

### Phase 4: 功能模块开发 (并行 Agent)

#### 4.1 Agent-D: Dashboard 仪表盘

**任务描述**: 实现首页仪表盘，包含指标卡片、服务状态、趋势图表

**Agent Prompt**:
```
Implement the Dashboard page for the BehaviorSense admin console.

## Working Directory: apps/web/

## Page: src/app/(dashboard)/page.tsx

## Components to Create

### 1. MetricCard (src/components/dashboard/metric-card.tsx)
```typescript
interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  trend?: 'up' | 'down' | 'neutral';
  icon?: React.ReactNode;
  href?: string;
}
```
- Card with icon, title, value
- Percentage change with color
- Click to navigate
- Loading skeleton

### 2. ServiceStatus (src/components/dashboard/service-status.tsx)
```typescript
interface ServiceStatusProps {
  services: Array<{
    name: string;
    port: number;
    status: 'healthy' | 'unhealthy' | 'unknown';
    latency?: number;
  }>;
}
```
- Status indicator (green/red/gray dot)
- Service name and port
- Response latency
- Grid layout

### 3. TrendChart (src/components/dashboard/trend-chart.tsx)
```typescript
interface TrendChartProps {
  title: string;
  data: Array<{ time: string; value: number }>;
  timeRange: '1h' | '6h' | '24h' | '7d';
  onTimeRangeChange: (range: string) => void;
}
```
- Line chart with Recharts
- Time range selector
- Responsive

### 4. RecentList (src/components/dashboard/recent-list.tsx)
- Rule triggers list
- Pending audits list
- Click to navigate

## Data Hooks
Create useDashboardMetrics hook that:
- Fetches metrics from multiple services
- Aggregates data
- Handles loading/error states

## Layout
- 4 metric cards in a row
- 2-column below (chart | service status)
- 2-column below (recent triggers | pending audits)

## Reference
- wiki/frontend-interaction-design.md Section 3
```

#### 4.2 Agent-E: 规则管理模块

**任务描述**: 实现规则列表、规则编辑器、条件构建器

**Agent Prompt**:
```
Implement the Rules Management module for the BehaviorSense admin console.

## Working Directory: apps/web/

## Pages
- src/app/(dashboard)/rules/page.tsx - List
- src/app/(dashboard)/rules/create/page.tsx - Create
- src/app/(dashboard)/rules/[id]/page.tsx - Edit

## Components

### 1. RuleList (src/components/rules/rule-list.tsx)
- DataTable with columns: Name, Priority, Status, Triggers, Actions
- Search input
- Status filter (All/Enabled/Disabled)
- Priority filter
- Pagination
- Actions: Edit, Test, Duplicate, Delete

### 2. RuleForm (src/components/rules/rule-form.tsx)
Sections:
- Basic Info: Name, Description, Priority, Enabled toggle
- Condition Builder
- Actions Editor
- Test Panel

### 3. ConditionBuilder (src/components/rules/condition-builder.tsx)
Features:
- Add condition row
- Field selector (dropdown)
- Operator selector (>, <, =, etc.)
- Value input
- AND/OR toggle
- Remove condition
- Nested groups (optional)

Mode toggle: Builder | Advanced (raw expression)

### 4. ActionEditor (src/components/rules/action-editor.tsx)
Features:
- Add action button
- Action type selector:
  - TAG_USER: tags input
  - TRIGGER_AUDIT: level selector
- Remove action

### 5. RuleTest (src/components/rules/rule-test.tsx)
Features:
- JSON input for test data
- Run test button
- Show matched/not matched result
- Show which conditions matched

## Hooks
- useRules(params) - List with pagination
- useRule(id) - Single rule
- useCreateRule() - Mutation
- useUpdateRule() - Mutation
- useDeleteRule() - Mutation
- useTestRule() - Test mutation

## Reference
- wiki/frontend-interaction-design.md Section 5
- Backend API: wiki/api.md
```

#### 4.3 Agent-F: 审核工作台模块

**任务描述**: 实现审核列表、审核详情、审核表单

**Agent Prompt**:
```
Implement the Audit Workbench module for the BehaviorSense admin console.

## Working Directory: apps/web/

## Pages
- src/app/(dashboard)/audit/page.tsx - All orders
- src/app/(dashboard)/audit/todo/page.tsx - My todo
- src/app/(dashboard)/audit/order/[id]/page.tsx - Detail

## Components

### 1. AuditList (src/components/audit/audit-list.tsx)
Features:
- Filter by status (PENDING, IN_REVIEW, APPROVED, REJECTED)
- Filter by level (HIGH, MEDIUM, LOW)
- Search by user ID
- Sort by created time
- Cards layout (not table)

### 2. AuditCard (src/components/audit/audit-card.tsx)
```typescript
interface AuditCardProps {
  orderId: string;
  userId: string;
  level: 'HIGH' | 'MEDIUM' | 'LOW';
  ruleName: string;
  triggerSummary: string;
  createdAt: string;
  onViewDetails: () => void;
}
```
- Level badge (color coded)
- User ID
- Rule name
- Trigger summary
- Created time
- View Details button

### 3. AuditDetail (src/components/audit/audit-detail.tsx)
Sections:
- Status header (badge)
- Trigger info card
- User profile card (summary + link)
- Event timeline
- Review form

### 4. EventTimeline (src/components/audit/event-timeline.tsx)
Features:
- Vertical timeline layout
- Event type icon
- Time, description
- Expandable metadata
- Load more

### 5. ReviewForm (src/components/audit/review-form.tsx)
Features:
- Radio group: Approve / Reject / Escalate
- Notes textarea
- Submit button
- Confirmation dialog for submit

## Hooks
- useAuditOrders(params) - List
- useAuditTodo() - My todo list
- useAuditOrder(id) - Single order
- useSubmitReview() - Mutation

## Reference
- wiki/frontend-interaction-design.md Section 7
```

#### 4.4 Agent-G: 用户洞察模块

**任务描述**: 实现用户搜索、用户画像、标签管理

**Agent Prompt**:
```
Implement the User Insight module for the BehaviorSense admin console.

## Working Directory: apps/web/

## Pages
- src/app/(dashboard)/insight/page.tsx - Search
- src/app/(dashboard)/insight/user/[id]/page.tsx - Profile

## Components

### 1. UserSearch (src/components/insight/user-search.tsx)
Features:
- Search input (user ID or phone)
- Recent searches (localStorage)
- Tag statistics cards

### 2. TagStatistics (src/components/insight/tag-statistics.tsx)
Features:
- Tag selector
- Distribution chart (pie/bar)
- Total count

### 3. UserProfile (src/components/insight/user-profile.tsx)
Sections:
- Basic info card
- Behavior tags grid
- Statistics card (views, purchases, etc.)
- Risk profile card

### 4. TagBadge (src/components/insight/tag-badge.tsx)
```typescript
interface TagBadgeProps {
  name: string;
  value: string;
  updateTime?: string;
  source?: 'auto' | 'manual';
  onRemove?: () => void;
}
```
- Colored badge
- Update time on hover
- Remove button (if editable)

### 5. RiskScore (src/components/insight/risk-score.tsx)
Features:
- Progress bar (0-100)
- Color based on level
- Risk factors list

### 6. EditTagsDialog (src/components/insight/edit-tags-dialog.tsx)
Features:
- Current tags display
- Add tag from predefined list
- Create custom tag
- Save/Cancel

## Hooks
- useSearchUser() - Search mutation
- useUserProfile(id) - Profile query
- useUserTags(id) - Tags query
- useUpdateTag() - Mutation
- useTagStatistics(name) - Statistics query

## Reference
- wiki/frontend-interaction-design.md Section 6
```

#### 4.5 Agent-H: 事件模拟模块

**任务描述**: 实现事件生成、场景模拟、实时事件流

**Agent Prompt**:
```
Implement the Event Simulation module for the BehaviorSense admin console.

## Working Directory: apps/web/

## Page: src/app/(dashboard)/mock/page.tsx

## Components

### 1. Tabs
- Tab 1: Manual Generate
- Tab 2: Scenario Simulation

### 2. ManualGenerateForm (src/components/mock/manual-generate-form.tsx)
Features:
- Event count input
- User count input
- Time range input
- Event types checkboxes:
  - VIEW, CLICK, SEARCH, PURCHASE, COMMENT, LOGIN, LOGOUT
- Generate button

### 3. ScenarioCard (src/components/mock/scenario-card.tsx)
```typescript
interface ScenarioCardProps {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  status: 'idle' | 'running' | 'completed';
  onStart: () => void;
  onStop: () => void;
}
```
- Card with icon and name
- Status badge
- Start/Stop button
- Stats when running

### 4. ActiveScenariosList (src/components/mock/active-scenarios-list.tsx)
Features:
- List of running scenarios
- Real-time event count
- Stop button

### 5. LiveEventStream (src/components/mock/live-event-stream.tsx)
Features:
- Auto-scrolling log view
- JSON formatted events
- Pause/Resume button
- Clear button
- Max 1000 events (auto trim)

## Hooks
- useGenerateEvents() - Mutation
- useScenarios() - List scenarios
- useStartScenario() - Mutation
- useStopScenario() - Mutation
- useEventStream() - WebSocket connection

## WebSocket
Connect to ws://localhost:8001/api/ws/events for real-time events.

## Reference
- wiki/frontend-interaction-design.md Section 4
```

---

### Phase 5: 质量验收 (qa-evaluator Agent)

**任务描述**: 全面评估前端项目质量

**Agent Prompt**:
```
Evaluate the quality of the BehaviorSense frontend console implementation.

## Project Location: apps/web/

## Evaluation Scope

### 1. Frontend Quality
- Component structure and organization
- TypeScript type coverage
- Code style consistency
- Performance (bundle size, render optimization)
- Accessibility (ARIA, keyboard navigation)

### 2. Integration Quality
- API client implementation
- Error handling
- Loading states
- Cache management

### 3. UI Quality
- Visual consistency
- Responsive design
- Interactive feedback
- Error boundaries

### 4. Feature Completeness
Check each module:
- [ ] Dashboard: metrics, status, charts
- [ ] Event Simulation: generate, scenarios, stream
- [ ] Rules: CRUD, condition builder, test
- [ ] Insight: search, profile, tags
- [ ] Audit: list, detail, review
- [ ] Monitor: service health, metrics

## Output
Generate a report at apps/web/docs/QA_REPORT.md with:
- Overall score (0-100)
- Category scores
- Issues found (critical, major, minor)
- Recommendations
```

---

## 四、执行时间线

```
Week 1
├── Day 1: Phase 1 (Project Init) - Direct
├── Day 2: Phase 2 (Research) - 2 Agents parallel
└── Day 3-4: Phase 3 (Core) - 3 Agents parallel

Week 2
├── Day 5-7: Phase 4 (Modules) - 5 Agents parallel
└── Day 8: Phase 5 (QA) - qa-evaluator

Buffer: 2 days for bug fixes and polish
```

---

## 五、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Agent 产出不一致 | 高 | 提供详细 prompt、统一代码规范 |
| 并行开发冲突 | 中 | 明确文件边界、避免交叉修改 |
| API 类型不匹配 | 中 | 先定义类型文件、共享 types |
| 组件样式不一致 | 中 | 统一使用 shadcn/ui、定义设计 token |

---

## 六、执行命令

### 启动 Phase 1 (直接执行)

```bash
# 1. 创建项目
cd apps
pnpm create next-app@latest web --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"

# 2. 安装依赖
cd web
pnpm add @tanstack/react-query zustand ky date-fns recharts lucide-react
pnpm add react-hook-form @hookform/resolvers zod
pnpm add -D @types/node

# 3. 初始化 shadcn/ui
pnpm dlx shadcn-ui@latest init

# 4. 安装常用组件
pnpm dlx shadcn-ui@latest add button card dialog form input select table tabs toast
```

### 启动并行 Agent

执行顺序:
1. Phase 2: 同时启动 Explore Agent + Plan Agent
2. Phase 3: 同时启动 Agent-A + Agent-B + Agent-C
3. Phase 4: 同时启动 Agent-D + Agent-E + Agent-F + Agent-G + Agent-H
4. Phase 5: 启动 qa-evaluator Agent

---

## 七、验收清单

### Phase 1
- [ ] Next.js 项目创建成功
- [ ] 所有依赖安装完成
- [ ] shadcn/ui 初始化完成
- [ ] 目录结构符合设计
- [ ] ESLint/Prettier 配置完成

### Phase 2
- [ ] RESEARCH.md 产出
- [ ] ARCHITECTURE.md 产出

### Phase 3
- [ ] API 客户端实现
- [ ] 登录页面实现
- [ ] 布局组件实现

### Phase 4
- [ ] Dashboard 完成
- [ ] Rules 模块完成
- [ ] Audit 模块完成
- [ ] Insight 模块完成
- [ ] Mock 模块完成

### Phase 5
- [ ] QA 报告产出
- [ ] 所有关键问题修复
