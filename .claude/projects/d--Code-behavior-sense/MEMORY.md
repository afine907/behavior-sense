# BehaviorSense 项目记忆索引

## 项目记忆

- [项目概览](memory/project_overview.md) — 核心功能、技术栈、项目结构
- [开发进度](memory/project_progress.md) — 模块完成状态、待办事项、优先级

## 快速参考

### 服务端口
| 服务 | 端口 |
|------|------|
| behavior_mock | 8001 |
| behavior_rules | 8002 |
| behavior_insight | 8003 |
| behavior_audit | 8004 |

### 核心命令
```bash
# 安装依赖
pip install -e ".[dev]"

# 启动基础设施
docker-compose up -d

# 启动服务
uvicorn behavior_insight.main:app --port 8003

# 启动流处理
python -m behavior_stream
```

### 关键文件
- [编码计划](PLAN.md)
- [最佳实践](wiki/best-practices.md)
- [API 设计](wiki/api.md)
