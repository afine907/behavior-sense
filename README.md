# BehaviorSense

**User Behavior Stream Analytics Engine** - 用户行为流实时分析引擎

## 核心功能

1. **Mock** - 模拟生成用户行为日志
2. **Pulsar** - 数据接入与消息队列
3. **Stream** - 实时流处理计算 (Faust)
4. **Rules** - 规则引擎（规则匹配与触发）
5. **Insight** - 分析洞察（标签生成与可视化）
6. **Audit** - 人工审核服务

## 技术栈

| 组件 | 技术选型 |
|------|----------|
| 语言 | Python 3.11+ |
| Web 框架 | FastAPI |
| 流处理 | Faust |
| 消息队列 | Apache Pulsar |
| 数据库 | PostgreSQL |
| 缓存 | Redis |
| 分析存储 | ClickHouse |

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
├── docker/                 # Docker 配置
└── wiki/                   # 知识库
```

## 快速开始

```bash
# 安装依赖
pip install -e ".[dev]"

# 启动基础设施
docker-compose up -d

# 运行 Mock 服务
python -m behavior_mock

# 运行流处理
python -m behavior_stream

# 运行 API 服务
uvicorn behavior_insight.main:app --reload --port 8003
```

## 服务端口

| 服务 | 端口 |
|------|------|
| behavior_mock | 8001 |
| behavior_rules | 8002 |
| behavior_insight | 8003 |
| behavior_audit | 8004 |

## 文档

- [架构设计](wiki/architecture.md)
- [模块设计](wiki/modules.md)
- [技术选型](wiki/technology.md)
- [API 设计](wiki/api.md)
- [部署方案](wiki/deployment.md)
- [编码计划](PLAN.md)

## License

MIT
