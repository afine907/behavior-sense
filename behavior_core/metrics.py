"""
Prometheus 指标模块

提供统一的 Prometheus 指标定义和收集功能。
"""
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry
from functools import wraps
import time
from typing import Callable


# 创建独立的注册表，避免全局污染
METRICS_REGISTRY = CollectorRegistry()

# ===== HTTP 指标 =====

# HTTP 请求总数
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=METRICS_REGISTRY,
)

# HTTP 请求延迟
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=METRICS_REGISTRY,
)

# 活跃连接数
ACTIVE_CONNECTIONS = Gauge(
    "active_connections",
    "Number of active connections",
    ["service"],
    registry=METRICS_REGISTRY,
)

# ===== 业务指标 =====

# 用户事件处理总数
USER_EVENTS_TOTAL = Counter(
    "user_events_total",
    "Total number of user events processed",
    ["event_type", "source"],
    registry=METRICS_REGISTRY,
)

# 规则匹配总数
RULE_MATCHES_TOTAL = Counter(
    "rule_matches_total",
    "Total number of rule matches",
    ["rule_id", "rule_name"],
    registry=METRICS_REGISTRY,
)

# 审核工单总数
AUDIT_ORDERS_TOTAL = Counter(
    "audit_orders_total",
    "Total number of audit orders",
    ["status", "level"],
    registry=METRICS_REGISTRY,
)

# 审核工单待处理数
AUDIT_ORDERS_PENDING = Gauge(
    "audit_orders_pending",
    "Number of pending audit orders",
    ["level"],
    registry=METRICS_REGISTRY,
)

# 标签操作总数
TAG_OPERATIONS_TOTAL = Counter(
    "tag_operations_total",
    "Total number of tag operations",
    ["operation", "source"],
    registry=METRICS_REGISTRY,
)

# ===== 服务信息 =====

SERVICE_INFO = Info(
    "service",
    "Service information",
    registry=METRICS_REGISTRY,
)


def set_service_info(service_name: str, version: str = "1.0.0"):
    """
    设置服务信息

    Args:
        service_name: 服务名称
        version: 服务版本
    """
    SERVICE_INFO.info({
        "name": service_name,
        "version": version,
    })


def track_request_duration(method: str, endpoint: str):
    """
    跟踪请求延迟的上下文管理器

    Args:
        method: HTTP 方法
        endpoint: 端点路径

    Usage:
        with track_request_duration("GET", "/api/users"):
            # 处理请求
    """
    return HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).time()


def increment_request_counter(method: str, endpoint: str, status_code: int):
    """
    增加请求计数

    Args:
        method: HTTP 方法
        endpoint: 端点路径
        status_code: HTTP 状态码
    """
    HTTP_REQUESTS_TOTAL.labels(
        method=method,
        endpoint=endpoint,
        status_code=str(status_code),
    ).inc()


def track_user_event(event_type: str, source: str = "api"):
    """
    跟踪用户事件

    Args:
        event_type: 事件类型
        source: 事件来源
    """
    USER_EVENTS_TOTAL.labels(event_type=event_type, source=source).inc()


def track_rule_match(rule_id: str, rule_name: str):
    """
    跟踪规则匹配

    Args:
        rule_id: 规则ID
        rule_name: 规则名称
    """
    RULE_MATCHES_TOTAL.labels(rule_id=rule_id, rule_name=rule_name).inc()


def track_audit_order(status: str, level: str):
    """
    跟踪审核工单

    Args:
        status: 工单状态
        level: 审核级别
    """
    AUDIT_ORDERS_TOTAL.labels(status=status, level=level).inc()


def set_pending_audit_orders(level: str, count: int):
    """
    设置待处理审核工单数

    Args:
        level: 审核级别
        count: 数量
    """
    AUDIT_ORDERS_PENDING.labels(level=level).set(count)


def track_tag_operation(operation: str, source: str = "api"):
    """
    跟踪标签操作

    Args:
        operation: 操作类型 (create, update, delete, get)
        source: 操作来源
    """
    TAG_OPERATIONS_TOTAL.labels(operation=operation, source=source).inc()


def get_metrics() -> str:
    """
    获取 Prometheus 格式的指标数据

    Returns:
        Prometheus 格式的指标字符串
    """
    from prometheus_client import generate_latest
    return generate_latest(METRICS_REGISTRY).decode("utf-8")


def metrics_middleware(request_path: str) -> Callable:
    """
    创建指标中间件装饰器

    Args:
        request_path: 请求路径

    Returns:
        装饰器函数
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = 500
                raise
            finally:
                duration = time.time() - start_time
                HTTP_REQUEST_DURATION_SECONDS.labels(
                    method="UNKNOWN",
                    endpoint=request_path,
                ).observe(duration)
                HTTP_REQUESTS_TOTAL.labels(
                    method="UNKNOWN",
                    endpoint=request_path,
                    status_code=str(status_code),
                ).inc()

        return wrapper
    return decorator
