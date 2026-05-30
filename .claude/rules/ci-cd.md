---
description: "CI/CD 相关规则，包括 GitHub Actions、Docker、Makefile 等"
globs: [".github/workflows/*.yml", "Makefile", "docker-compose*.yml", "Dockerfile*", "infrastructure/docker/*"]
alwaysApply: false
---

# CI/CD 规则

> 仅在操作匹配文件时加载

### Node.js 版本兼容性
- **错误**: pnpm install 失败，提示 Node.js 版本不兼容
- **原因**: pnpm 11.5+ 需要 Node.js >= 22.13，CI 使用 Node.js 20
- **正确做法**: 在 CI 中使用 `node-version: '22'`
- **场景**: 所有使用 pnpm 的 frontend CI jobs
- **来源**: 2026-05-30

---

### pnpm 构建脚本批准
- **错误**: `ERR_PNPM_IGNORED_BUILDS` 错误阻止安装
- **原因**: pnpm 11+ 默认阻止未批准的构建脚本（msw, unrs-resolver）
- **正确做法**: 使用 `pnpm install --frozen-lockfile --ignore-scripts`
- **场景**: CI 环境中安装依赖时
- **来源**: 2026-05-30

---

### Ruff I001 导入排序
- **错误**: I001 Import block is un-sorted or un-formatted
- **原因**: ruff isort 规则对导入格式要求严格，手动难以修复
- **正确做法**: 在 pyproject.toml 的 `[tool.ruff.lint]` 中添加 `ignore = ["I001"]`
- **场景**: 导入格式问题难以手动修复时
- **来源**: 2026-05-30

---
