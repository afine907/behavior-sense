# BehaviorSense 项目记忆索引

## 项目记忆

- [项目概览](memory/project_overview.md) — 核心功能、技术栈、Monorepo 结构
- [开发进度](memory/project_progress.md) — 模块完成状态、CI修复完成
- [CI 配置](memory/project_ci_config.md) — GitHub Actions、Docker镜像、Mypy配置

## 开发规范

- [Commit 规范](memory/feedback_commit.md) — Git commit 消息必须使用英文
- [技术栈偏好](memory/feedback_python.md) — Python 技术栈约束
- [CI 修复规范](memory/feedback_ci_fix.md) — CI问题一次性彻底修复

## 快速参考

### 服务端口
| 服务 | 端口 |
|------|------|
| packages/mock | 8001 |
| packages/rules | 8002 |
| packages/insight | 8003 |
| packages/audit | 8004 |

### 核心命令
```bash
# 安装依赖
uv sync

# 运行测试
uv run pytest tests/

# 启动基础设施
docker-compose up -d

# 启动服务
uv run uvicorn behavior_insight.main:app --port 8003

# 添加依赖
uv add httpx                    # 添加到根项目
uv add --package behavior-audit httpx  # 添加到指定包
```

### 关键文件
- [编码计划](PLAN.md)
- [最佳实践](wiki/best-practices.md)
- [API 设计](wiki/api.md)
