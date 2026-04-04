---
name: feedback_commit_convention
description: Git commit 消息规范约束
type: feedback
---

# Git Commit 规范

## 规则: 所有 commit 消息必须使用英文

**Why**: 这是一个开源项目，需要面向国际开发者社区，英文 commit 消息更易于全球开发者理解和协作。

**How to apply**:
- 所有 commit 标题和描述使用英文
- 遵循 Conventional Commits 规范
- 格式: `<type>(<scope>): <description>`

## Commit 类型

| Type | 说明 | 示例 |
|------|------|------|
| feat | 新功能 | feat(stream): add window aggregation operator |
| fix | Bug 修复 | fix(rules): prevent eval injection with AST parser |
| docs | 文档更新 | docs(api): update endpoint documentation |
| test | 测试相关 | test(core): add unit tests for models |
| refactor | 重构 | refactor: migrate to monorepo structure |
| chore | 杂项 | chore(ci): update to use uv package manager |
| perf | 性能优化 | perf(stream): optimize window operator |

## 示例

```
feat(audit): add audit state machine for review workflow

- Implement AuditStateMachine with status transitions
- Add API endpoints for audit operations
- Integrate with PostgreSQL for persistence
```

## 反例

❌ `feat(qa): 添加全栈效果评估Skill和MCP配置`
✅ `feat(qa): add fullstack evaluation skill and mcp config`
