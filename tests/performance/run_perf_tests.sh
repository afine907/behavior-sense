#!/bin/bash
# BehaviorSense 性能测试运行脚本

echo "=== BehaviorSense 性能测试 ==="

# 测试配置
HOST="${1:-http://localhost:8001}"
USERS="${2:-50}"
SPAWN_RATE="${3:-10}"
RUN_TIME="${4:-60s}"

echo "目标主机: $HOST"
echo "并发用户: $USERS"
echo "启动速率: $SPAWN_RATE/s"
echo "运行时间: $RUN_TIME"

# 安装 locust (如果未安装)
if ! command -v locust &> /dev/null; then
    echo "安装 locust..."
    pip install locust
fi

# 运行性能测试
echo ""
echo "开始性能测试..."
locust -f tests/performance/locustfile.py \
    --host "$HOST" \
    --users "$USERS" \
    --spawn-rate "$SPAWN_RATE" \
    --run-time "$RUN_TIME" \
    --headless \
    --html reports/performance_report.html \
    --csv reports/performance

echo ""
echo "测试完成! 报告已保存到 reports/performance_report.html"
