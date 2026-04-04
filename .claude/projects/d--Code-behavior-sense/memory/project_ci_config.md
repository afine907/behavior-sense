---
name: project_ci_config
description: CI/CD 配置关键信息
type: project
---

# CI/CD 配置

## GitHub Actions 流程

**Why**: 记录CI配置关键点，避免后续修改时踩坑

**How to apply**: 修改CI时参考此配置

---

## CI Job 结构

| Job | 说明 | 条件 |
|-----|------|------|
| lint | ruff + mypy 检查 | 所有 push/PR |
| test | pytest + 覆盖率 | 所有 push/PR |
| build | Docker 镜像构建 | main/master 分支 |

## Mypy 配置

```toml
[tool.mypy]
python_version = "3.11"
ignore_missing_imports = true
# packages 使用宽松模式
disable_error_code = ["arg-type", "attr-defined", "assignment", ...]

[[tool.mypy.overrides]]
module = "behavior_core.*"
strict = true  # core 使用严格模式
```

## Docker 镜像构建

**镜像仓库**: GitHub Container Registry (ghcr.io)

**Why**: 使用 ghcr.io 而非 Docker Hub，因为：
- 无需手动配置 secrets
- GITHUB_TOKEN 自动可用
- 免费存储

**镜像格式**:
```
ghcr.io/{owner}/behavior-sense/{service}:latest
ghcr.io/{owner}/behavior-sense/{service}:{sha}
```

**服务列表**: audit, insight, mock, rules, stream

## CI 命令速查

```bash
# Lint
uv run ruff check libs/ packages/

# Mypy
uv run mypy libs/core/src/behavior_core --ignore-missing-imports
uv run mypy packages/*/src --ignore-missing-imports

# Test
uv run pytest tests/ --cov=libs --cov=packages --cov-report=xml
```
