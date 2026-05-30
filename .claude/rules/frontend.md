---
description: "前端相关规则，包括 Next.js、TypeScript、React 等"
globs: ["apps/web/**/*.tsx", "apps/web/**/*.ts", "apps/web/tsconfig.json"]
alwaysApply: false
---

# 前端规则

> 仅在操作匹配文件时加载

### Next.js 路由组避免重复页面
- **错误**: `You cannot have two parallel pages that resolve to the same path`
- **原因**: 在路由组 `(dashboard)` 和根目录 `/` 都有相同路径的页面
- **正确做法**: 只在路由组中定义页面，删除根目录的重复页面
- **场景**: 使用 Next.js 路由组时
- **来源**: 2026-05-30

---

### TypeScript Set 迭代配置
- **错误**: `Type 'Set<string>' can only be iterated through when using the '--downlevelIteration' flag`
- **原因**: TypeScript 默认 target 不支持 Set 迭代
- **正确做法**: 在 tsconfig.json 中添加 `target: "es2017"` 和 `downlevelIteration: true`
- **场景**: 使用 `for...of` 遍历 Set 或 Map 时
- **来源**: 2026-05-30

---
