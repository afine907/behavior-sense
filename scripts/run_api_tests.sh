#!/bin/bash
# BehaviorSense 测试运行脚本

set -e

echo "=== BehaviorSense Test Runner ==="

# 检查测试模式
TEST_MODE="${1:-mock}"

if [ "$TEST_MODE" = "real" ] || [ "$TEST_MODE" = "all" ]; then
    echo "检查测试依赖..."

    # 检查 PostgreSQL
    if ! docker exec behavior-test-postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo "启动测试数据库..."
        docker-compose -f docker-compose.test.yml up -d
        sleep 5
    fi

    # 检查 Redis
    if ! docker exec behavior-redis redis-cli ping > /dev/null 2>&1; then
        echo "警告: Redis 未运行，部分测试可能失败"
    fi
fi

# 设置测试环境变量
export TEST_REAL_DEPS=0
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5433
export POSTGRES_DB=behavior_sense_test
export POSTGRES_PASSWORD=postgres
export REDIS_URL="redis://localhost:6379/1"

case "$TEST_MODE" in
    "mock")
        echo "运行 Mock 模式测试..."
        uv run pytest tests/test_api/test_mock_api.py tests/test_api/test_rules_api.py -v --tb=short
        ;;
    "real")
        echo "运行真实依赖测试..."
        export TEST_REAL_DEPS=1
        uv run pytest tests/test_api/ -v --tb=short
        ;;
    "all")
        echo "运行所有测试..."
        export TEST_REAL_DEPS=1
        uv run pytest tests/test_api/ -v --tb=short
        ;;
    *)
        echo "用法: $0 [mock|real|all]"
        echo "  mock - 无外部依赖测试 (默认)"
        echo "  real - 真实依赖测试"
        echo "  all  - 所有测试"
        exit 1
        ;;
esac

echo "=== 测试完成 ==="
