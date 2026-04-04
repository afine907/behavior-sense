# BehaviorSense

[![CI](https://github.com/behaviorsense/behavior-sense/actions/workflows/ci.yml/badge.svg)](https://github.com/behaviorsense/behavior-sense/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-orange.svg)](https://docs.astral.sh/ruff/)

**User Behavior Stream Analytics Engine** - A real-time user behavior stream processing and analysis platform.

[English](#overview) | [中文文档](#中文文档)

---

## Overview

BehaviorSense is a real-time user behavior stream analytics engine designed for low-latency (< 1s) event processing, flexible rule matching, and intelligent user tagging.

### Key Features

- **Real-time Stream Processing** - Built on Faust for sub-second latency event processing
- **Flexible Rule Engine** - AST-based rule parsing with hot-reload support
- **Intelligent Tagging** - Automatic user profiling and tag management
- **Human-in-the-loop Audit** - Built-in workflow for manual review process
- **Monorepo Architecture** - Clean separation of concerns with shared libraries
- **Modern Python Stack** - FastAPI, Pydantic v2, asyncio throughout

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            BehaviorSense                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌────────┐│
│   │  Mock   │───▶│ Pulsar  │───▶│  Stream │───▶│  Rules  │───▶│ Insight││
│   │ FastAPI │    │  Queue   │    │  Faust  │    │ Engine  │    │ FastAPI││
│   └─────────┘    └─────────┘    └─────────┘    └─────────┘    └────────┘│
│        │                                                        │        │
│        │              ┌─────────────────────────────────────────┘        │
│        │              ▼                                                  │
│        │       ┌─────────────┐                                          │
│        └──────▶│   Audit     │◀──────── Human Review Workflow           │
│                │   FastAPI   │                                          │
│                └─────────────┘                                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Language | Python 3.11+ | Runtime |
| Package Manager | [uv](https://docs.astral.sh/uv/) | Dependency management |
| Web Framework | FastAPI | REST API services |
| Stream Processing | Faust | Real-time event processing |
| Message Queue | Apache Pulsar | Event streaming |
| Database | PostgreSQL | Persistent storage |
| Cache | Redis | Caching & pub/sub |
| Analytics | ClickHouse | OLAP queries |

## Project Structure

```
behavior-sense/
├── libs/                     # Shared libraries
│   └── core/                 # behavior-core
│       └── src/behavior_core/
│           ├── config/       # Configuration management
│           ├── models/       # Data models
│           ├── security/     # Auth & JWT
│           ├── middleware/   # Rate limiting, tracing
│           └── utils/        # Utilities
│
├── packages/                 # Microservices
│   ├── mock/                 # behavior-mock (port 8001)
│   ├── rules/                # behavior-rules (port 8002)
│   ├── insight/              # behavior-insight (port 8003)
│   ├── audit/                # behavior-audit (port 8004)
│   └── stream/               # behavior-stream (Faust)
│
├── apps/                     # Frontend applications
│   └── web/                  # Next.js app (reserved)
│
├── infrastructure/           # Infrastructure configs
│   └── docker/               # Dockerfile, docker-compose
│
├── tests/                    # Test suites
└── wiki/                     # Documentation
```

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker & Docker Compose

### Installation

```bash
# Clone the repository
git clone https://github.com/behaviorsense/behavior-sense.git
cd behavior-sense

# Install dependencies
uv sync

# Copy environment config
cp .env.example .env

# Start infrastructure services
docker-compose up -d
```

### Running Services

```bash
# Run mock service (generates test events)
uv run uvicorn behavior_mock.main:app --port 8001

# Run stream processor
uv run python -m behavior_stream

# Run insight API
uv run uvicorn behavior_insight.main:app --port 8003

# Run audit service
uv run uvicorn behavior_audit.main:app --port 8004
```

### Running Tests

```bash
# Run all tests
uv run pytest tests/

# Run with coverage
uv run pytest tests/ --cov=libs --cov=packages --cov-report=html
```

## Service Ports

| Service | Port | Description |
|---------|------|-------------|
| behavior-mock | 8001 | Event generator |
| behavior-rules | 8002 | Rule engine API |
| behavior-insight | 8003 | User insight API |
| behavior-audit | 8004 | Audit workflow API |
| Pulsar | 6650 | Message queue |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache |
| ClickHouse | 8123 | Analytics |

## API Documentation

Each service provides OpenAPI documentation:

- Mock: http://localhost:8001/docs
- Rules: http://localhost:8002/docs
- Insight: http://localhost:8003/docs
- Audit: http://localhost:8004/docs

## Development

### Adding Dependencies

```bash
# Add to root project
uv add httpx

# Add to specific package
uv add --package behavior-audit httpx

# Add dev dependency
uv add --group dev black
```

### Code Quality

```bash
# Lint
uv run ruff check libs/ packages/

# Format
uv run ruff format libs/ packages/

# Type check
uv run mypy libs/core/src packages/*/src
```

### Docker Build

```bash
# Build specific service
docker build -f infrastructure/docker/Dockerfile --build-arg SERVICE=insight -t behaviorsense/insight:latest .
```

## Documentation

- [Architecture Design](wiki/architecture.md)
- [Module Design](wiki/modules.md)
- [Technology Stack](wiki/technology.md)
- [API Design](wiki/api.md)
- [Deployment Guide](wiki/deployment.md)
- [Best Practices](wiki/best-practices.md)
- [Development Plan](PLAN.md)

## Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes using [Conventional Commits](https://www.conventionalcommits.org/)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Convention

All commit messages must follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

# Examples
feat(audit): add audit state machine for review workflow
fix(rules): prevent eval injection with AST parser
docs(api): update endpoint documentation
test(core): add unit tests for models
refactor: migrate to monorepo structure
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 中文文档

### 项目简介

BehaviorSense 是一个用户行为流实时分析引擎，专为低延迟 (< 1秒) 事件处理、灵活规则匹配和智能用户打标设计。

### 核心功能

1. **Mock** - 模拟生成用户行为日志
2. **Stream** - 实时流处理计算 (Faust)
3. **Rules** - 规则引擎（规则匹配与触发）
4. **Insight** - 分析洞察（标签生成与画像）
5. **Audit** - 人工审核服务

### 快速开始

```bash
# 安装依赖
uv sync

# 启动基础设施
docker-compose up -d

# 运行服务
uv run uvicorn behavior_insight.main:app --port 8003
```

### 文档

- [架构设计](wiki/architecture.md)
- [模块设计](wiki/modules.md)
- [技术选型](wiki/technology.md)
- [最佳实践](wiki/best-practices.md)
