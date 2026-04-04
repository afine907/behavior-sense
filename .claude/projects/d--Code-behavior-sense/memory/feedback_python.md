---
name: feedback_python_stack
description: 用户对项目技术栈和工具的偏好
type: feedback
---

# 技术栈偏好

## 规则: 使用 Python 技术栈

**Why**: 用户明确要求使用 Python 实现整个项目，而不是 Java。

**How to apply**:
- 所有模块使用 Python 3.11+ 实现
- Web 框架使用 FastAPI
- 流处理使用 Faust (纯 Python) 而非 PyFlink
- 遵循 Python 代码风格和最佳实践

## 规则: 使用 uv 包管理器

**Why**: uv 比 Poetry 快 10-100 倍，原生支持 monorepo workspace，配置更简单。

**How to apply**:
- 使用 `uv sync` 安装依赖
- 使用 `uv run` 执行命令
- 使用 `uv add` 添加依赖
- CI/CD 使用 `astral-sh/setup-uv@v3`

## 规则: 最佳实践写入项目 Wiki

**Why**: 用户要求将框架最佳实践写入项目 wiki 目录，而不是创建全局技能文件。

**How to apply**:
- 框架最佳实践写入 wiki/best-practices.md
- 代码审查时参考该文档
- 不需要创建全局 .claude/skills/ 文件
