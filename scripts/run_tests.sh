#!/bin/bash
# BehaviorSense 集成测试运行脚本
#
# 使用方式：
#   ./scripts/run_tests.sh           # 运行 Mock 模式测试（快速，无外部依赖）
#   ./scripts/run_tests.sh --real    # 运行真实依赖测试（需要 Docker）
#   ./scripts/run_tests.sh --all     # 运行所有测试
#   ./scripts/run_tests.sh --ci      # CI 模式

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  BehaviorSense 集成测试${NC}"
echo -e "${BLUE}================================================${NC}"

# 解析参数
MODE="mock"
COVERAGE=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --real)
            MODE="real"
            shift
            ;;
        --all)
            MODE="all"
            shift
            ;;
        --ci)
            MODE="ci"
            COVERAGE="--cov=libs --cov=packages --cov-report=xml --cov-report=html"
            shift
            ;;
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        *)
            echo "未知参数: $1"
            exit 1
            ;;
    esac
done

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo -e "${RED}错误: uv 未安装${NC}"
    echo "请运行: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 安装依赖
echo -e "${YELLOW}正在安装依赖...${NC}"
uv sync

run_mock_tests() {
    echo -e "${GREEN}运行 Mock 模式测试（无外部依赖）...${NC}"
    uv run pytest tests/test_api/test_mock_api.py tests/test_api/test_rules_api.py tests/test_integration/test_basic_integration.py $VERBOSE $COVERAGE
}

run_real_tests() {
    echo -e "${GREEN}运行真实依赖测试...${NC}"

    # 启动测试依赖
    echo -e "${YELLOW}启动测试依赖容器...${NC}"
    docker-compose -f docker-compose.test.yml up -d

    # 等待服务就绪
    echo -e "${YELLOW}等待服务就绪...${NC}"
    sleep 5

    # 检查服务健康状态
    if ! docker-compose -f docker-compose.test.yml ps | grep -q "healthy"; then
        echo -e "${YELLOW}等待服务健康...${NC}"
        sleep 5
    fi

    # 设置测试环境变量
    export TEST_REAL_DEPS=1
    export POSTGRES_HOST=localhost
    export POSTGRES_PORT=5433
    export POSTGRES_USER=postgres
    export POSTGRES_PASSWORD=postgres
    export POSTGRES_DB=behavior_sense_test
    export REDIS_URL=redis://localhost:6380

    # 运行测试
    uv run pytest tests/ $VERBOSE $COVERAGE

    # 清理
    echo -e "${YELLOW}清理测试容器...${NC}"
    docker-compose -f docker-compose.test.yml down -v
}

run_ci_tests() {
    echo -e "${GREEN}运行 CI 模式测试...${NC}"

    # CI 模式下服务由 GitHub Actions 提供
    export TEST_REAL_DEPS=1
    export POSTGRES_HOST=localhost
    export POSTGRES_PORT=5432
    export POSTGRES_USER=postgres
    export POSTGRES_PASSWORD=postgres
    export POSTGRES_DB=behavior_sense
    export REDIS_URL=redis://localhost:6379

    uv run pytest tests/ $VERBOSE $COVERAGE
}

# 执行测试
case $MODE in
    mock)
        run_mock_tests
        ;;
    real)
        run_real_tests
        ;;
    all)
        run_mock_tests
        run_real_tests
        ;;
    ci)
        run_ci_tests
        ;;
esac

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  测试完成！${NC}"
echo -e "${GREEN}================================================${NC}"
