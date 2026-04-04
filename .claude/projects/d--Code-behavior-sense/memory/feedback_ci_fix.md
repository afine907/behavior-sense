---
name: feedback_ci_fix
description: CI问题修复的工作方式反馈
type: feedback
---

# CI 修复规范

## 规则: CI问题应该一次性彻底修复，而不是多次迭代

**Why**: 用户反馈 CI 问题修改了很多次都没有改好，这表明需要更系统性地分析和解决问题，而不是修修补补。

**How to apply**:
1. **先完整运行所有CI命令** - 不要只测试部分命令
2. **分析所有错误类型** - 分类错误，确定修复策略
3. **一次性修复所有相关问题** - 避免多次提交修复同类问题
4. **本地验证所有CI步骤** - 确保lint、mypy、test全部通过
5. **必要时调整配置** - 如mypy strict mode不适合所有模块

## 典型错误案例

❌ 错误做法:
- 只修复 `libs/core` 的 mypy，忽略 `packages/*/src`
- 多次提交修复同类错误
- 本地测试命令与CI命令不一致

✅ 正确做法:
```bash
# 完整运行所有CI检查命令
uv run ruff check libs/ packages/
uv run mypy libs/core/src/behavior_core --ignore-missing-imports
uv run mypy packages/*/src --ignore-missing-imports
uv run pytest tests/
```

## 配置调整原则

对于第三方库类型问题（SQLAlchemy、Redis等），应该在 `pyproject.toml` 中配置：

```toml
[tool.mypy]
# packages 使用宽松模式，core 使用严格模式
disable_error_code = ["arg-type", "attr-defined", ...]

[[tool.mypy.overrides]]
module = "behavior_core.*"
strict = true
```
