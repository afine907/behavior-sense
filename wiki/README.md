# BehaviorSense Wiki

欢迎来到 BehaviorSense 项目知识库。

## 目录

- [架构设计](architecture.md) - 整体架构与设计原则
- [模块设计](modules.md) - 五大核心模块详细设计
- [技术选型](technology.md) - 技术栈选择与版本建议
- [API 设计](api.md) - 对外接口规范
- [部署方案](deployment.md) - 环境搭建与部署

## 项目概述

**BehaviorSense** - User Behavior Stream Analytics Engine

用户行为流实时分析引擎，核心流程：

```
Mock → Pulsar → PyFlink/Faust → Rules → Insight
       ↓
    Audit (审核服务)
```

## 技术栈

| 组件 | 技术选型 |
|------|----------|
| 语言 | Python 3.11+ |
| Web 框架 | FastAPI |
| 流处理 | PyFlink / Faust |
| 消息队列 | Apache Pulsar |
| 数据库 | PostgreSQL / MySQL |
| 缓存 | Redis |
| 分析存储 | ClickHouse |

## 核心功能

1. **Mock** - 模拟生成用户行为日志
2. **Pulsar** - 数据接入与消息队列
3. **Stream** - 实时流处理计算 (PyFlink/Faust)
4. **Rules** - 规则引擎（规则匹配与触发）
5. **Insight** - 分析洞察（标签生成与可视化）

## 项目结构

```
behavior-sense/
├── behavior_core/          # 核心库
├── behavior_mock/          # 模拟器模块
├── behavior_stream/        # 流处理模块
├── behavior_rules/         # 规则引擎模块
├── behavior_insight/       # 洞察服务模块
├── behavior_audit/         # 审核服务模块
├── tests/                  # 测试
└── docker/                 # Docker 配置
```

## 快速开始

```bash
# 安装依赖
pip install -e ".[dev]"

# 启动开发环境
docker-compose up -d

# 运行 Mock 服务
python -m behavior_mock

# 运行流处理
python -m behavior_stream

# 运行 API 服务
uvicorn behavior_insight.main:app --reload
```

## 相关资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Apache Flink](https://flink.apache.org/)
- [Apache Pulsar](https://pulsar.apache.org/)
- [Faust](https://faust-streaming.github.io/faust/)