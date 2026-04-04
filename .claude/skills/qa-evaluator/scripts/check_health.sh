#!/bin/bash
#
# 服务健康检查脚本
# 检查所有微服务的健康状态
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 服务配置
SERVICES=(
    "behavior_mock:8001"
    "behavior_rules:8002"
    "behavior_insight:8003"
    "behavior_audit:8004"
)

# 基础设施服务
INFRA_SERVICES=(
    "pulsar:6650"
    "postgres:5432"
    "redis:6379"
)

check_http_health() {
    local name=$1
    local port=$2
    local url="http://localhost:${port}/health"

    if curl -sf "${url}" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} ${name} (port ${port}) - healthy"
        return 0
    else
        echo -e "${RED}✗${NC} ${name} (port ${port}) - unhealthy or not running"
        return 1
    fi
}

check_tcp_health() {
    local name=$1
    local port=$2
    local host="localhost"

    if (echo > /dev/tcp/${host}/${port}) 2>/dev/null; then
        echo -e "${GREEN}✓${NC} ${name} (port ${port}) - reachable"
        return 0
    else
        echo -e "${RED}✗${NC} ${name} (port ${port}) - not reachable"
        return 1
    fi
}

echo "================================"
echo "BehaviorSense 健康检查"
echo "================================"
echo ""

echo "应用服务状态:"
echo "----------------"
app_status=0
for service in "${SERVICES[@]}"; do
    name="${service%%:*}"
    port="${service##*:}"
    check_http_health "${name}" "${port}" || app_status=1
done

echo ""
echo "基础设施状态:"
echo "----------------"
infra_status=0
for service in "${INFRA_SERVICES[@]}"; do
    name="${service%%:*}"
    port="${service##*:}"
    check_tcp_health "${name}" "${port}" || infra_status=1
done

echo ""
echo "================================"
if [ $app_status -eq 0 ] && [ $infra_status -eq 0 ]; then
    echo -e "${GREEN}所有服务健康${NC}"
    exit 0
else
    echo -e "${YELLOW}部分服务异常${NC}"
    exit 1
fi
