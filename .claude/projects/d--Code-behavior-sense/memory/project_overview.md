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
- **Web框架**: FastAPI
- **数据验证**: Pydantic v2
- **消息队列**: Apache Pulsar
- **流处理**: Faust
- **数据库**: PostgreSQL (SQLAlchemy async)
- **缓存**: Redis
- **分析存储**: ClickHouse
- **日志**: structlog

## 项目结构
```
behavior-sense/
├── behavior_core/          # 核心库 (数据模型、配置、工具)
├── behavior_mock/          # 模拟器模块 (端口 8001)
├── behavior_stream/        # 流处理模块 (Faust)
├── behavior_rules/         # 规则引擎模块 (端口 8002)
├── behavior_insight/       # 洞察服务模块 (端口 8003)
├── behavior_audit/         # 审核服务模块 (端口 8004)
├── wiki/                   # 知识库文档
├── docker/                 # Docker 配置
└── tests/                  # 测试文件
```

## Why:
- 这是用户行为分析的核心业务，需要实时处理用户事件流
- 采用流处理架构保证低延迟 (< 1秒)
- 规则引擎支持灵活的业务规则配置

## How to apply:
- 开发新功能时参考 wiki/ 目录下的架构设计
- 遵循 wiki/best-practices.md 的代码规范
- 各模块独立开发，通过 Pulsar 消息队列通信
