---
name: project_overview
description: BehaviorSense 项目核心功能和技术架构概览
type: project
---

# BehaviorSense 项目概览

## 项目定位
**User Behavior Stream Analytics Engine** - 用户行为流实时分析引擎

## 核心功能
1. **Mock** - 模拟生成用户行为日志
2. **Pulsar** - 数据接入与消息队列
3. **Stream** - 实时流处理计算 (Faust)
4. **Rules** - 规则引擎（规则匹配与触发）
5. **Insight** - 分析洞察（标签生成与可视化）
6. **Audit** - 人工审核服务

## 数据流
```
Mock → Pulsar → Faust(Stream) → Rules → Insight
                                    ↓
                                 Audit (人工审核)
```

## 技术栈
- **语言**: Python 3.11+
- **包管理**: uv (Astral)
- **Web框架**: FastAPI
- **数据验证**: Pydantic v2
- **消息队列**: Apache Pulsar
- **流处理**: Faust
- **数据库**: PostgreSQL (SQLAlchemy async)
- **缓存**: Redis
- **分析存储**: ClickHouse
- **日志**: structlog

## 项目结构 (Monorepo)
```
behavior-sense/
├── pyproject.toml           # 根配置 + uv workspace
├── uv.lock                   # 依赖锁定文件
├── pnpm-workspace.yaml       # 前端 workspace 配置
│
├── libs/                     # Python 共享库
│   └── core/                 # behavior-core
│       └── src/behavior_core/
│
├── packages/                 # Python 微服务
│   ├── audit/                # behavior-audit (端口 8004)
│   ├── insight/              # behavior-insight (端口 8003)
│   ├── mock/                 # behavior-mock (端口 8001)
│   ├── rules/                # behavior-rules (端口 8002)
│   └── stream/               # behavior-stream
│
├── apps/                     # 前端应用 (预留)
│   └── web/                  # Next.js 应用
│
├── infrastructure/           # 基础设施配置
│   └── docker/               # Dockerfile, docker-compose
│
├── tests/                    # 集成测试
└── wiki/                     # 项目文档
```

## Why:
- Monorepo 结构便于管理多服务依赖和共享代码
- uv 包管理器比 Poetry 快 10-100 倍，原生支持 workspace
- src 布局避免导入冲突，符合 Python 最佳实践

## How to apply:
- 开发新功能时参考 wiki/ 目录下的架构设计
- 遵循 wiki/best-practices.md 的代码规范
- 各模块独立开发，通过 Pulsar 消息队列通信
- 使用 `uv sync` 安装依赖，`uv run` 执行命令
