"""
Agent Analytics结构化日志
"""
import logging
import sys
from datetime import UTC, datetime
from typing import Any

import structlog


def _utc_now() -> datetime:
    return datetime.now(UTC)


def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    json_format: bool = False,
) -> None:
    """设置结构化日志"""

    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))


def get_agent_logger(agent_id: str) -> structlog.BoundLogger:
    """获取Agent专用logger"""
    return structlog.get_logger().bind(agent_id=agent_id)


def get_service_logger(service_name: str) -> structlog.BoundLogger:
    """获取服务专用logger"""
    return structlog.get_logger().bind(service=service_name)


class AgentEventLogger:
    """Agent事件日志记录器"""

    def __init__(self, service_name: str):
        self.logger = structlog.get_logger().bind(service=service_name)

    def log_event_received(self, event: dict[str, Any]) -> None:
        """记录事件接收"""
        self.logger.info(
            "agent_event_received",
            agent_id=event.get("agent_id"),
            event_type=event.get("event_type"),
            trace_id=event.get("trace_id"),
        )

    def log_event_processed(self, event: dict[str, Any], latency_ms: float) -> None:
        """记录事件处理完成"""
        self.logger.info(
            "agent_event_processed",
            agent_id=event.get("agent_id"),
            event_type=event.get("event_type"),
            latency_ms=latency_ms,
        )

    def log_event_failed(self, event: dict[str, Any], error: str) -> None:
        """记录事件处理失败"""
        self.logger.error(
            "agent_event_failed",
            agent_id=event.get("agent_id"),
            event_type=event.get("event_type"),
            error=error,
        )

    def log_alert_generated(self, alert: dict[str, Any]) -> None:
        """记录告警生成"""
        self.logger.warning(
            "agent_alert_generated",
            agent_id=alert.get("agent_id"),
            alert_type=alert.get("alert_type"),
            severity=alert.get("severity"),
        )

    def log_detection_result(self, agent_id: str, detector: str,
                            detected: bool, details: dict | None = None) -> None:
        """记录检测结果"""
        self.logger.info(
            "anomaly_detection",
            agent_id=agent_id,
            detector=detector,
            detected=detected,
            details=details,
        )

    def log_cost_update(self, agent_id: str, cost_usd: float,
                       total_cost: float) -> None:
        """记录成本更新"""
        self.logger.info(
            "cost_update",
            agent_id=agent_id,
            cost_usd=cost_usd,
            total_cost_usd=total_cost,
        )

    def log_token_usage(self, agent_id: str, tokens: int, model: str) -> None:
        """记录Token使用"""
        self.logger.info(
            "token_usage",
            agent_id=agent_id,
            tokens=tokens,
            model=model,
        )


class PerformanceLogger:
    """性能日志记录器"""

    def __init__(self, service_name: str):
        self.logger = structlog.get_logger().bind(service=service_name)

    def log_request(self, method: str, path: str, status_code: int,
                   latency_ms: float) -> None:
        """记录HTTP请求"""
        level = "warning" if latency_ms > 1000 else "info"
        getattr(self.logger, level)(
            "http_request",
            method=method,
            path=path,
            status_code=status_code,
            latency_ms=latency_ms,
        )

    def log_database_query(self, query: str, latency_ms: float,
                          rows_affected: int = 0) -> None:
        """记录数据库查询"""
        self.logger.info(
            "database_query",
            query=query[:100],  # Truncate long queries
            latency_ms=latency_ms,
            rows_affected=rows_affected,
        )

    def log_cache_operation(self, operation: str, key: str, hit: bool) -> None:
        """记录缓存操作"""
        self.logger.debug(
            "cache_operation",
            operation=operation,
            key=key,
            hit=hit,
        )
