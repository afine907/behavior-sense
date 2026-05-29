"""
Agent告警通知系统
"""
import asyncio
import json
import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class NotificationChannel(str, Enum):
    """通知渠道"""
    WEBHOOK = "webhook"
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    TEAMS = "teams"
    CONSOLE = "console"


class NotificationPriority(str, Enum):
    """通知优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationMessage(BaseModel):
    """通知消息"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    channel: NotificationChannel
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    agent_id: str | None = None
    alert_type: str | None = None
    severity: str | None = None
    timestamp: datetime = Field(default_factory=_utc_now)
    sent: bool = False
    error: str | None = None


class WebhookConfig(BaseModel):
    """Webhook配置"""
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    timeout: int = 10
    retry_count: int = 3


class SlackConfig(BaseModel):
    """Slack配置"""
    webhook_url: str
    channel: str = "#alerts"
    username: str = "BehaviorSense"
    icon_emoji: str = ":brain:"


class NotificationService:
    """通知服务"""

    def __init__(self):
        self._webhook_configs: dict[str, WebhookConfig] = {}
        self._slack_configs: dict[str, SlackConfig] = {}
        self._sent_messages: list[NotificationMessage] = []
        self._http_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient()
        return self._http_client

    def register_webhook(self, name: str, config: WebhookConfig) -> None:
        """注册Webhook"""
        self._webhook_configs[name] = config

    def register_slack(self, name: str, config: SlackConfig) -> None:
        """注册Slack"""
        self._slack_configs[name] = config

    async def send(self, message: NotificationMessage) -> bool:
        """发送通知"""
        try:
            if message.channel == NotificationChannel.WEBHOOK:
                return await self._send_webhook(message)
            elif message.channel == NotificationChannel.SLACK:
                return await self._send_slack(message)
            elif message.channel == NotificationChannel.CONSOLE:
                return self._send_console(message)
            else:
                logger.warning(f"Unsupported channel: {message.channel}")
                return False
        except Exception as e:
            message.error = str(e)
            logger.error(f"Failed to send notification: {e}")
            return False
        finally:
            self._sent_messages.append(message)

    async def send_alert(self, alert: dict[str, Any],
                        channels: list[NotificationChannel] | None = None) -> dict[str, bool]:
        """发送告警通知到多个渠道"""
        if channels is None:
            channels = [NotificationChannel.CONSOLE]

        # Build notification message
        severity = alert.get("severity", "medium")
        priority_map = {
            "critical": NotificationPriority.URGENT,
            "high": NotificationPriority.HIGH,
            "medium": NotificationPriority.NORMAL,
            "low": NotificationPriority.LOW,
        }

        message = NotificationMessage(
            channel=NotificationChannel.CONSOLE,  # Will be overridden per channel
            priority=priority_map.get(severity, NotificationPriority.NORMAL),
            title=f"[{severity.upper()}] Agent Alert: {alert.get('alert_type', 'unknown')}",
            message=alert.get("message", "Agent anomaly detected"),
            data=alert,
            agent_id=alert.get("agent_id"),
            alert_type=alert.get("alert_type"),
            severity=severity,
        )

        results = {}
        for channel in channels:
            msg = message.model_copy()
            msg.channel = channel
            results[channel.value] = await self.send(msg)

        return results

    async def _send_webhook(self, message: NotificationMessage) -> bool:
        """发送Webhook"""
        config = list(self._webhook_configs.values())[0] if self._webhook_configs else None
        if not config:
            logger.warning("No webhook configured")
            return False

        client = await self._get_client()
        payload = {
            "id": message.id,
            "title": message.title,
            "message": message.message,
            "priority": message.priority.value,
            "agent_id": message.agent_id,
            "alert_type": message.alert_type,
            "severity": message.severity,
            "data": message.data,
            "timestamp": message.timestamp.isoformat(),
        }

        for attempt in range(config.retry_count):
            try:
                response = await client.post(
                    config.url,
                    json=payload,
                    headers=config.headers,
                    timeout=config.timeout,
                )
                if response.status_code < 300:
                    message.sent = True
                    return True
            except Exception as e:
                if attempt == config.retry_count - 1:
                    raise

        return False

    async def _send_slack(self, message: NotificationMessage) -> bool:
        """发送Slack消息"""
        config = list(self._slack_configs.values())[0] if self._slack_configs else None
        if not config:
            logger.warning("No Slack configured")
            return False

        client = await self._get_client()

        # Build Slack message
        color_map = {
            "critical": "#ff0000",
            "high": "#ff6600",
            "medium": "#ffcc00",
            "low": "#00cc00",
        }

        slack_payload = {
            "channel": config.channel,
            "username": config.username,
            "icon_emoji": config.icon_emoji,
            "attachments": [{
                "color": color_map.get(message.severity, "#cccccc"),
                "title": message.title,
                "text": message.message,
                "fields": [
                    {"title": "Agent", "value": message.agent_id or "N/A", "short": True},
                    {"title": "Severity", "value": message.severity or "N/A", "short": True},
                    {"title": "Alert Type", "value": message.alert_type or "N/A", "short": True},
                    {"title": "Time", "value": message.timestamp.isoformat(), "short": True},
                ],
                "footer": "BehaviorSense Agent Analytics",
            }],
        }

        try:
            response = await client.post(
                config.webhook_url,
                json=slack_payload,
                timeout=10,
            )
            if response.status_code == 200:
                message.sent = True
                return True
        except Exception as e:
            message.error = str(e)

        return False

    def _send_console(self, message: NotificationMessage) -> bool:
        """发送到控制台"""
        severity_colors = {
            "critical": "\033[91m",  # Red
            "high": "\033[93m",      # Yellow
            "medium": "\033[94m",    # Blue
            "low": "\033[92m",       # Green
        }
        reset = "\033[0m"
        color = severity_colors.get(message.severity, "")

        logger.info(f"{color}[{message.severity.upper()}] {message.title}{reset}")
        logger.info(f"  Agent: {message.agent_id}")
        logger.info(f"  Message: {message.message}")

        message.sent = True
        return True

    def get_sent_messages(self, limit: int = 100) -> list[NotificationMessage]:
        """获取已发送消息"""
        return self._sent_messages[-limit:]

    async def close(self) -> None:
        """关闭HTTP客户端"""
        if self._http_client:
            await self._http_client.aclose()
