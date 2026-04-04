# BehaviorSense 前端控制台 - Code Review 报告

**审查时间**: 2026-04-04
**审查范围**: apps/web/
**并行 Agent**: 4 个

---

## 总体评估

| 类别 | 评分 | 状态 |
|------|------|------|
| UI 组件 | 85/100 | ⚠️ 需改进 |
| 安全性 | 45/100 | 🚨 严重问题 |
| API 与 Hooks | 80/100 | ⚠️ 需改进 |
| 业务模块 | 75/100 | ⚠️ 需改进 |

---

## 🔴 CRITICAL - 必须立即修复

### 1. 安全漏洞

| 问题 | 文件 | 风险 |
|------|------|------|
| 硬编码明文密码 | `api/auth/login/route.ts:9-34` | 凭据泄露 |
| 假 JWT Token | `api/auth/login/route.ts:47-48` | 无安全验证 |
| 自动登录后门 | `lib/auth/protected.tsx:16-31` | 完全绕过认证 |
| JWT Secret 暴露 | `.env.example:12` | 密钥泄露 |

### 2. 无障碍访问缺失

| 问题 | 文件 | 影响 |
|------|------|------|
| Progress 缺少 ARIA | `ui/progress.tsx:11-26` | 屏幕阅读器无法识别 |

### 3. 内存泄漏

| 问题 | 文件 | 影响 |
|------|------|------|
| Interval 未正确清理 | `mock/page.tsx:70,178-182` | 内存泄漏 |
| setTimeout 未清理 | `audit/order/[id]/page.tsx:89-91` | 组件卸载后导航 |

---

## 🟠 HIGH - 需尽快修复

### UI 组件

| 问题 | 文件 | 建议 |
|------|------|------|
| Badge 缺少 forwardRef | `ui/badge.tsx:49` | 添加 ref 转发 |
| Context 未 memoize | `ui/use-toast.tsx:38` | 使用 useMemo |
| 弱 ID 生成 | `ui/use-toast.tsx:32` | 使用 crypto.randomUUID() |
| TypeScript 类型错误 | `ui/card.tsx:28` | HTMLParagraphElement → HTMLHeadingElement |

### API 层

| 问题 | 文件 | 建议 |
|------|------|------|
| 错误处理不可达代码 | `lib/api/client.ts:46-53` | 重构错误处理 |
| 缺少错误边界 | `lib/query/provider.tsx` | 添加全局错误处理 |
| 不安全的类型断言 | `lib/api/audit.ts:13` | 创建类型安全的转换函数 |

### 业务模块

| 问题 | 文件 | 建议 |
|------|------|------|
| 缺少 Error Boundary | 所有页面 | 创建 error.tsx |
| 事件处理未 memoize | `audit/page.tsx:88-126` | 使用 useCallback |
| params 类型错误 | `rules/[id]/page.tsx:6-10` | params 应为 Promise |

---

## 🟡 MEDIUM - 建议修复

### 代码一致性

| 问题 | 文件数 | 建议 |
|------|--------|------|
| 'use client' 缺失 | 5 | 添加到使用 forwardRef 的组件 |
| 导入风格不一致 | 6 | 统一使用命名导入 |
| 未使用的导入 | 3 | 清理无用导入 |

### 性能优化

| 问题 | 文件 | 影响 |
|------|------|------|
| 缺少 React.memo | `audit-card.tsx` | 不必要重渲染 |
| 缺少乐观更新 | `use-audit.ts:78-85` | UX 体验差 |
| 内联对象创建 | `mock/page.tsx:236-268` | 每次渲染新建对象 |

### 表单验证

| 问题 | 文件 | 建议 |
|------|------|------|
| 搜索无验证 | `insight/page.tsx:20-22` | 添加空值检查 |
| 标签验证简单 | `edit-tags-dialog.tsx:76-104` | 使用 Zod |

---

## 🟢 LOW - 可在后续迭代修复

### 代码风格

- 硬编码颜色值 (`badge.tsx:28-34`)
- 动画类重复 (`dialog.tsx`, `alert-dialog.tsx`)
- 魔法数字 (`progress.tsx:11`)

### 文档

- 缺少组件 JSDoc
- 缺少类型导出 (`ui/index.ts`)

---

## 修复优先级清单

### P0 - 立即修复 (安全)

```typescript
// 1. 移除硬编码密码 (api/auth/login/route.ts)
// 使用环境变量或真实后端认证

// 2. 移除自动登录后门 (lib/auth/protected.tsx:16-31)
// 删除或添加环境检查:
if (process.env.NODE_ENV === 'development' && !isAuthenticated) {
  // 仅开发模式
}

// 3. 修复 JWT Secret 暴露
// 重命名: NEXT_PUBLIC_JWT_SECRET → JWT_SECRET
```

### P0 - 立即修复 (Bug)

```typescript
// 1. 添加 ARIA 到 Progress (ui/progress.tsx:11)
<div
  role="progressbar"
  aria-valuenow={value}
  aria-valuemin={0}
  aria-valuemax={100}
  aria-label="Progress"
>

// 2. 修复内存泄漏 (mock/page.tsx:178)
useEffect(() => {
  return () => {
    setRunningScenarios((current) => {
      current.forEach(({ intervalId }) => clearInterval(intervalId));
      return current;
    });
  };
}, []);

// 3. 清理 setTimeout (audit/order/[id]/page.tsx:89)
useEffect(() => {
  const timer = setTimeout(() => router.push('/audit'), 1500);
  return () => clearTimeout(timer);
}, [router]);
```

### P1 - 本周修复

```typescript
// 1. 添加 Error Boundary (每个路由目录)
// src/app/(dashboard)/audit/error.tsx
'use client';
export default function AuditError({ error, reset }: { error: Error; reset: () => void }) {
  return <ErrorUI error={error} onRetry={reset} />;
}

// 2. 添加 useCallback (audit/page.tsx)
const handleQuickApprove = useCallback(async (orderId: string) => {
  // ...
}, [reviewMutation, toast]);

// 3. 修复 params 类型 (rules/[id]/page.tsx)
interface Props { params: Promise<{ id: string }>; }
```

### P2 - 下个迭代

- 添加组件 displayName
- 导出类型定义
- 统一导入风格
- 添加 React.memo

---

## 积极发现

| 类别 | 说明 |
|------|------|
| Query Keys 设计良好 | 层次化结构，易于管理 |
| 使用 Radix UI 原语 | 无障碍基础良好 |
| CVA 变体系统 | Button/Badge 实现优雅 |
| 错误处理统一 | ApiClientError 类设计合理 |
| Toast 系统完整 | 通知机制完善 |

---

## 建议下一步

1. **立即**: 修复 P0 安全问题
2. **本周**: 添加 Error Boundary
3. **下个迭代**: 优化性能和代码风格
4. **持续**: 添加单元测试覆盖

---

**审查完成时间**: 2026-04-04
**建议复审时间**: 修复 P0 问题后
